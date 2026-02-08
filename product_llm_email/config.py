import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# OpenAI / Gemini API key
LLM_API_KEY = os.getenv("LLM_API_KEY", "")

# Recipients for demo
RECIPIENT_LIST = ["customer1@example.com", "customer2@example.com"]

# Safety & confidence thresholds
BLOCKED_KEYWORDS = {"injury", "hurt", "down", "medical"}
CONFIDENCE_THRESHOLD = 0.8
