import os
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
QWEN_API_KEY = os.getenv("QWEN_API_KEY", "")
UPLOAD_STORAGE_PATH = os.getenv("UPLOAD_STORAGE_PATH", "./uploads")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./safety_sentinel.db")

os.makedirs(UPLOAD_STORAGE_PATH, exist_ok=True)
