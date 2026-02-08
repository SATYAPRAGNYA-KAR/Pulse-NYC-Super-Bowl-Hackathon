import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# OpenAI / Gemini API key
LLM_API_KEY = os.getenv("LLM_API_KEY", "")

# Recipients for demo
RECIPIENT_LIST = ["nilarnabdebnath@gmail.com", "mathurshipra33@gmail.com"]

# Safety & confidence thresholds
BLOCKED_KEYWORDS = {"injury", "hurt", "down", "medical"}
CONFIDENCE_THRESHOLD = 0.8
