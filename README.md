# Smart Meeting Recorder & Analyzer

A Streamlit application that records meetings, transcribes them, and provides AI-powered analysis including action items and visual flow diagrams.

## Features
- Real-time audio recording
- Speech-to-text transcription using Whisper
- AI-powered meeting analysis using GPT-4
- Visual meeting flow diagrams using Mermaid
- Action item tracking with assignments
- Meeting playback capabilities

## Setup
1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set up your OpenAI API key in Streamlit secrets:
   ```toml
   OPENAI_API_KEY = "your-api-key"
   ```
4. Run the app: `streamlit run app.py`

## Deployment
The app is configured for deployment on Streamlit Cloud. Make sure to:
1. Set the OpenAI API key in Streamlit Cloud secrets
2. Configure any necessary dependencies
3. Ensure all paths are relative to the project directory

## Logging
Logs are stored in `app.log` and also streamed to stdout for cloud monitoring. 