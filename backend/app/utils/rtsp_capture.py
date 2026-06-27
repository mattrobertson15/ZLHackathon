"""Capture frames from a live RTSP stream.

The companion to ``video_frames.extract_frames`` (which samples a stored video
file). This grabs a handful of spaced frames from a *live* feed so the same
inference pipeline can treat a camera like an upload. Returns the identical
shape: ``[{"framePath": str, "frameTimestamp": float}]``.

See ARCHITECTURE.md#camera--rtsp-ingestion-layer.
"""
import os
import time

import cv2

DEFAULT_NUM_FRAMES = 4
DEFAULT_SPACING_SECONDS = 1.0
# Guard against a dead/blocked stream wedging the capture loop.
OPEN_TIMEOUT_SECONDS = 15.0


def capture_frames_from_rtsp(
    rtsp_url: str,
    output_dir: str,
    num_frames: int = DEFAULT_NUM_FRAMES,
    spacing_seconds: float = DEFAULT_SPACING_SECONDS,
):
    """Open ``rtsp_url`` and write ``num_frames`` JPEGs spaced ~``spacing_seconds`` apart.

    Raises ValueError if the stream cannot be opened or yields no frames.
    """
    os.makedirs(output_dir, exist_ok=True)

    capture = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)
    try:
        if not capture.isOpened():
            raise ValueError(f"Could not open RTSP stream: {rtsp_url}")

        extracted = []
        start = time.monotonic()
        next_capture_at = start

        while len(extracted) < num_frames:
            if time.monotonic() - start > OPEN_TIMEOUT_SECONDS:
                break

            # grab() cheaply advances the decoder; retrieve() decodes the frame.
            success, frame = capture.read()
            if not success or frame is None:
                # Transient read miss on a live feed — retry briefly.
                if time.monotonic() - start > OPEN_TIMEOUT_SECONDS:
                    break
                time.sleep(0.05)
                continue

            now = time.monotonic()
            if now < next_capture_at and extracted:
                continue

            timestamp_seconds = round(now - start, 3)
            frame_file = os.path.join(output_dir, f"frame_{len(extracted):03d}.jpg")
            cv2.imwrite(frame_file, frame)
            extracted.append(
                {"framePath": frame_file, "frameTimestamp": timestamp_seconds}
            )
            next_capture_at = now + spacing_seconds

        if not extracted:
            raise ValueError(f"No frames could be read from RTSP stream: {rtsp_url}")

        return extracted
    finally:
        capture.release()
