import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env.local if it exists (takes precedence), otherwise .env
env_local = Path(__file__).resolve().parent.parent.parent / ".env.local"
if env_local.exists():
    load_dotenv(env_local)
else:
    load_dotenv()

# RTSP-over-TCP is far more reliable than the UDP default for OpenCV's ffmpeg
# backend. Set before cv2 is imported anywhere so VideoCapture picks it up.
os.environ.setdefault("OPENCV_FFMPEG_CAPTURE_OPTIONS", "rtsp_transport;tcp")

# Convenience default for the demo emulator (mediamtx + ffmpeg). Inside
# docker-compose the backend reaches the stream over the private network.
DEMO_RTSP_URL = os.getenv("DEMO_RTSP_URL", "rtsp://localhost:8554/worksite-demo")

# Base RTSP URL (host:port, no path) the seeded demo cameras attach to. Each
# seeded camera appends its own stream path (e.g. ".../loading-dock"). Inside
# docker-compose this is set to "rtsp://mediamtx:8554"; on the host it defaults
# to localhost. See app/db/seeds.py and docker-compose.yml.
DEMO_RTSP_BASE_URL = os.getenv("DEMO_RTSP_BASE_URL", "rtsp://localhost:8554")

# Whether the seeded demo cameras start with monitoring=True. Off by default so
# a plain local backend (no emulator running) doesn't spew RTSP connection
# errors every tick; docker-compose sets this to "true" so `docker compose up`
# lights all feeds automatically.
SEED_CAMERA_MONITORING = os.getenv("SEED_CAMERA_MONITORING", "false").lower() in (
    "1",
    "true",
    "yes",
)

# Capture interval (seconds) for the seeded demo cameras. Modest by default so
# several simultaneous looped feeds don't overload inference; lower it (1–2) for
# a snappy single-camera walk-by demo.
SEED_CAMERA_CAPTURE_INTERVAL_SECONDS = int(
    os.getenv("SEED_CAMERA_CAPTURE_INTERVAL_SECONDS", "10")
)

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
QWEN_API_KEY = os.getenv("QWEN_API_KEY", "")
ROBOFLOW_API_KEY = os.getenv("ROBOFLOW_API_KEY", "")
IS_VERCEL = os.getenv("VERCEL") == "1"
UPLOAD_STORAGE_PATH = os.getenv(
    "UPLOAD_STORAGE_PATH",
    "/tmp/safety-sentinel-uploads" if IS_VERCEL else "./uploads",
)

BLOB_READ_WRITE_TOKEN = os.getenv("BLOB_READ_WRITE_TOKEN", "")
# Vercel's filesystem is ephemeral per-invocation, so uploads must go to Blob
# storage to survive between requests when deployed there.
USE_BLOB_STORAGE = IS_VERCEL and bool(BLOB_READ_WRITE_TOKEN)

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./safety_sentinel.db")

os.makedirs(UPLOAD_STORAGE_PATH, exist_ok=True)
