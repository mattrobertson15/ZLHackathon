import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env.local if it exists (takes precedence), otherwise .env
env_local = Path(__file__).resolve().parent.parent.parent / ".env.local"
if env_local.exists():
    load_dotenv(env_local)
else:
    load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
QWEN_API_KEY = os.getenv("QWEN_API_KEY", "")
ROBOFLOW_API_KEY = os.getenv("ROBOFLOW_API_KEY", "")
IS_VERCEL = os.getenv("VERCEL") == "1"
UPLOAD_STORAGE_PATH = os.getenv(
    "UPLOAD_STORAGE_PATH",
    "/tmp/safety-sentinel-uploads" if IS_VERCEL else "./uploads",
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DB_PATH = (
    Path("/tmp/safety_sentinel.db")
    if IS_VERCEL
    else PROJECT_ROOT / "backend" / "safety_sentinel.db"
)
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DB_PATH}")

os.makedirs(UPLOAD_STORAGE_PATH, exist_ok=True)
