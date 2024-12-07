import streamlit as st
from streamlit_mermaid import st_mermaid

# Title for the app
st.title("Mermaid Diagram Visualization")

# Updated Mermaid diagram code
diagram_code = """
graph TD
    A[Meeting Start] --> B[Next Product Launch Discussion]
    B --> C[Marketing Strategy Assignment]
    C --> D[Assign Marketing Task to Sam]
    D --> |Assigned| E[Outline Detailed Marketing Campaign]
    E --> F[Sam]
    F --> G[Deadline: Next Tuesday]
    style D fill:#ff9999,stroke:#000,stroke-width:2px
    style F fill:#99ff99,stroke:#000,stroke-width:2px
"""

# Display the Mermaid diagram
st_mermaid(diagram_code, height=600)
