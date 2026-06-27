# Safety Sentinel backend — FastAPI + the live camera (RTSP) monitor.
# Unlike the Vercel deployment, this image runs a long-lived process so the
# background camera monitor can poll RTSP feeds continuously.
FROM python:3.11-slim

# libglib2.0-0 covers a runtime dependency some opencv operations expect.
# (opencv-python-headless bundles its own ffmpeg for RTSP capture.)
RUN apt-get update \
    && apt-get install -y --no-install-recommends libglib2.0-0 ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Persisted via a volume in docker-compose so DB + captured frames survive restarts.
ENV DATABASE_URL=sqlite:////data/safety_sentinel.db \
    UPLOAD_STORAGE_PATH=/data/uploads \
    OPENCV_FFMPEG_CAPTURE_OPTIONS="rtsp_transport;tcp"

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
