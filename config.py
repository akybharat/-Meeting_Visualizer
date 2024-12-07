import os
from pathlib import Path

# Base directory of the project
BASE_DIR = Path(__file__).resolve().parent

# Directory for recordings
RECORDINGS_DIR = BASE_DIR / "recordings"

# Create necessary directories
RECORDINGS_DIR.mkdir(exist_ok=True)

# Whisper model configuration
WHISPER_MODEL = "base"

# Audio recording configuration
AUDIO_SAMPLE_RATE = 44100
AUDIO_CHANNELS = 1
MAX_RECORDING_HOURS = 1

# OpenAI configuration
GPT_MODEL = "gpt-4o" 