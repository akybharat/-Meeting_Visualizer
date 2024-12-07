import streamlit as st
from streamlit_mermaid import st_mermaid
import sounddevice as sd
import soundfile as sf
import whisper
from datetime import datetime
import os
from openai import OpenAI
import pandas as pd
import time 
import logging
import sys

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('app.log')
    ]
)
logger = logging.getLogger(__name__)

# Create a directory for saving recordings if it doesn't exist
if not os.path.exists("recordings"):
    os.makedirs("recordings")

# Initialize OpenAI client
@st.cache_resource
def get_openai_client():
    api_key = st.secrets["OPENAI_API_KEY"]
    if not api_key:
        st.error("Please set the OPENAI_API_KEY in your secrets or environment variables")
        st.stop()
    return OpenAI(api_key=api_key)

client = get_openai_client()

# Initialize Whisper model
@st.cache_resource
def load_whisper_model():
    return whisper.load_model("base")

model = load_whisper_model()

def generate_meeting_summary(transcript):
    """Generate comprehensive meeting summary and detailed mermaid diagram"""
    logger.info("Generating meeting summary")
    prompt = f"""
    Analyze the following meeting transcript and provide a comprehensive analysis with:
    1. A concise executive summary
    2. Detailed action items with assignees and deadlines
    3. A detailed Mermaid diagram that shows:
       - Main discussion topics and their flow
       - Decision points
       - Action items connected to responsible persons
       - Important conclusions
       - Any blockers or dependencies identified
    
    For the Mermaid diagram, strictly follow these rules:
    1. Use only graph TD or graph TB direction
    2. Start the diagram with: 'graph TD'
    3. Use proper Mermaid syntax for nodes and connections
    4. Avoided parentheses or other special characters in node names for cleaner rendering.
    5. Use these node styles:
       - Topics: [Topic Name]
       - Decisions: [Decision Point]
       - Actions: ([Action Item])
       - People: ((Person Name))
    6. Example format:
        graph TD
            A[Meeting Start] --> B[Decision 1]
            B --> |Approved| C([Action Item 1])
            C --> D((John))
            style B fill:#ff9999,stroke:#000,stroke-width:2px
            style D fill:#99ff99,stroke:#000,stroke-width:2px


    Transcript:
    {transcript}
    
    Format the response as JSON with the following structure:
    {{
        "executive_summary": "brief but comprehensive summary",
        "action_items": [
            {{
                "task": "task description",
                "assignee": "person name",
                "deadline": "deadline or timeframe",
                "priority": "high/medium/low",
                "dependencies": ["any dependencies"]
            }}
        ],
        "key_decisions": ["list of key decisions made"],
        "mermaid_diagram": "mermaid diagram code here"
    }}
    """
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": """You are an expert meeting analyzer specializing in creating comprehensive visual representations of meetings.
            Always ensure the Mermaid diagram code is valid and starts with 'graph TD'.
            Use simple shapes and clear connections in the diagram.
            Avoid complex Mermaid syntax that might not be widely supported."""},
            {"role": "user", "content": prompt}
        ],
        response_format={ "type": "json_object" }
    )
    
    logger.info("Meeting summary generated successfully")
    return response.choices[0].message.content

def record_audio_stream():
    """Record audio stream until stopped"""
    logger.info("Starting audio stream recording")
    try:
        return sd.rec(int(44100 * 3600),  # Record up to 1 hour
                     samplerate=44100,
                     channels=1,
                     dtype='float64')
    except Exception as e:
        logger.error(f"Error starting audio recording: {str(e)}")
        raise

def save_audio(recording, samplerate):
    """Save audio recording to file"""
    logger.info("Saving audio recording")
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"recordings/audio_{timestamp}.wav"
        sf.write(filename, recording, samplerate)
        logger.info(f"Audio saved successfully: {filename}")
        return filename
    except Exception as e:
        logger.error(f"Error saving audio: {str(e)}")
        raise

st.title("🎤 Smart Meeting Recorder & Analyzer")
st.write("Record your meeting and get AI-powered insights!")


if 'is_recording' not in st.session_state:
    st.session_state['is_recording'] = False
if 'recording_started' not in st.session_state:
    st.session_state['recording_started'] = False
if 'start_time' not in st.session_state:
    st.session_state['start_time'] = None
if 'elapsed_time' not in st.session_state:
    st.session_state['elapsed_time'] = None

if 'recorder' not in st.session_state:
    st.session_state['recorder'] = None

col1, col2 = st.columns(2)
with col1:
    if st.button("Start Recording") and not st.session_state['is_recording']:
        st.session_state['is_recording'] = True
        st.session_state['start_time'] = time.time()
        st.session_state['recording_started'] = True
        # Start recording
        st.session_state['recorder'] = record_audio_stream()
        st.info("🎙️ Recording... Click 'Stop Recording' when finished.")

with col2:
    if st.button("Stop Recording") and st.session_state['is_recording']:
        if st.session_state['recorder'] is not None:
            st.session_state['is_recording'] = False
            st.session_state['elapsed_time'] = time.time() - st.session_state['start_time']
            
            # Stop recording and get the data
            sd.stop()
            recording = st.session_state['recorder'][:int(st.session_state['elapsed_time'] * 44100)]
            
            # Save the recording
            audio_file = save_audio(recording, 44100)
            st.session_state['last_recording'] = audio_file
            st.success("Recording saved!")
            
            # Process the recording
            with st.spinner("Transcribing audio..."):
                result = model.transcribe(audio_file)
                transcript = result["text"]
                st.session_state['last_transcription'] = transcript
            
            with st.spinner("Analyzing meeting content..."):
                try:
                    analysis = generate_meeting_summary(transcript)
                    analysis_dict = eval(analysis)
                    st.session_state['last_analysis'] = analysis_dict
                except Exception as e:
                    st.error(f"Error analyzing meeting content: {str(e)}")
            
            st.success("Analysis complete!")
            st.session_state['recorder'] = None
        else:
            st.error("No recording in progress!")

if st.session_state['is_recording']:
    st.warning("🔴 Recording in progress...")

# Display results if available
if 'last_transcription' in st.session_state and st.session_state['last_transcription']:
    with st.expander("📝 Meeting Transcript", expanded=False):
        st.write(st.session_state['last_transcription'])

if 'last_analysis' in st.session_state and st.session_state['last_analysis']:
    analysis = st.session_state['last_analysis']
    
    st.header("📊 Meeting Analysis Dashboard")
    
    # Executive Summary
    with st.expander("📋 Executive Summary", expanded=True):
        st.write(analysis['executive_summary'])
    
    # Key Decisions
    with st.expander("🎯 Key Decisions", expanded=True):
        for idx, decision in enumerate(analysis['key_decisions'], 1):
            st.markdown(f"**{idx}.** {decision}")
    
    # Action Items Table
    st.subheader("📝 Action Items Tracker")
    action_items_df = []
    for item in analysis['action_items']:
        action_items_df.append({
            "Task": item['task'],
            "Assignee": item['assignee'],
            "Deadline": item['deadline'],
            "Priority": item['priority'],
            "Dependencies": ", ".join(item['dependencies'])
        })
    
    if action_items_df:
        df = pd.DataFrame(action_items_df)
        # Apply color coding based on priority
        def color_priority(val):
            colors = {
                'high': 'background-color: #ffcccc',
                'medium': 'background-color: #ffffcc',
                'low': 'background-color: #ccffcc'
            }
            return colors.get(val.lower(), '')
        
        st.dataframe(df.style.applymap(color_priority, subset=['Priority']), use_container_width=True)
    
    # Visual Flow Diagram
    st.subheader("🔄 Meeting Flow Visualization")
    with st.expander("Meeting Flow Diagram", expanded=True):
        try:
            # Ensure the diagram starts with graph TD
            diagram_code = analysis['mermaid_diagram']
            print("diagram_code", diagram_code)
            if not diagram_code.strip().startswith('graph'):
                diagram_code = 'graph TD\n' + diagram_code
            
            # Add default styling if not present
            if 'style' not in diagram_code:
                diagram_code += """
                    style default fill:#f9f,stroke:#333,stroke-width:2px
                    style default fill:#bbf,stroke:#333,stroke-width:2px
                """
            
            st_mermaid(diagram_code, height=600)
            
            st.info("""
            �� **Diagram Legend:**
            - 🔷 Topics/Discussions: [Square Brackets]
            - 🔶 Decision Points: {Curly Braces}
            - 🎯 Action Items: (Rounded Brackets)
            - 👤 Team Members: ((Double Circle))
            - ➡️ Flow Direction: Arrows
            - 🎨 Colors indicate priority/status
            """)
        except Exception as e:
            st.error(f"Error rendering diagram. Using simplified version...")
            # Fallback simple diagram
            fallback_diagram = """
            graph TD
                Start[Meeting Start] --> Topics[Key Topics Discussed]
                Topics --> Decisions{Key Decisions}
                Decisions --> Actions([Action Items])
                Actions --> Team((Team Members))
                
                style Start fill:#f9f
                style Decisions fill:#ff9999
                style Actions fill:#99ff99
                style Team fill:#9999ff
            """
            st_mermaid(fallback_diagram, height=400)

# Audio playback
if 'last_recording' in st.session_state:
    st.header("🔊 Playback")
    st.audio(st.session_state['last_recording'])

# Display saved recordings
with st.expander("📼 Saved Recordings", expanded=False):
    saved_recordings = [f for f in os.listdir("recordings") if f.endswith(".wav")]
    saved_recordings.sort(reverse=True)

    for recording in saved_recordings:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.audio(f"recordings/{recording}")
        with col2:
            st.write(recording) 