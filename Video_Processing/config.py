"""
Configuration settings for the video processing pipeline
"""

import os
from pathlib import Path

# Base directories
BASE_DIR = Path(__file__).parent
UPLOAD_FOLDER = BASE_DIR / 'uploads'
CHUNKS_FOLDER = BASE_DIR / 'chunks'
AUDIO_FOLDER = BASE_DIR / 'audio'
PROCESSED_FOLDER = BASE_DIR / 'processed'

# Create directories
for folder in [UPLOAD_FOLDER, CHUNKS_FOLDER, AUDIO_FOLDER, PROCESSED_FOLDER]:
    folder.mkdir(exist_ok=True)

# Processing settings
CHUNK_DURATION = 5  # seconds
AMPLITUDE_SAMPLE_RATE = 100  # samples per second for amplitude array

# Transcription settings
TRANSCRIPTION_MODEL = 'whisper-tiny'  # Options: whisper-tiny, whisper-base, whisper-small, wav2vec2, vosk
TRANSCRIPTION_LANGUAGE = 'en'

# Video processing settings
VIDEO_CODEC = 'libx264'
AUDIO_CODEC = 'aac'
VIDEO_PRESET = 'ultrafast'  # Faster encoding for real-time processing

# Audio extraction settings
AUDIO_SAMPLE_RATE = 16000  # Hz - optimal for transcription
AUDIO_CHANNELS = 1  # Mono
MP3_BITRATE = '192k'

# API settings
MAX_CONCURRENT_SESSIONS = 5
SESSION_TIMEOUT = 3600  # seconds

# Flask settings
FLASK_HOST = '0.0.0.0'
FLASK_PORT = 5000
FLASK_DEBUG = True

# Logging
LOG_LEVEL = 'INFO'
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# PythonAnywhere specific settings
PYTHONANYWHERE_USERNAME = os.getenv('PYTHONANYWHERE_USERNAME', '')
PYTHONANYWHERE_DOMAIN = f"{PYTHONANYWHERE_USERNAME}.pythonanywhere.com" if PYTHONANYWHERE_USERNAME else ''

# Security
SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
ALLOWED_ORIGINS = os.getenv('ALLOWED_ORIGINS', '*').split(',')

# File size limits
MAX_VIDEO_SIZE_MB = 500
MAX_CHUNK_SIZE_MB = 50

# Cleanup settings
AUTO_CLEANUP_ENABLED = True
CLEANUP_AFTER_HOURS = 24