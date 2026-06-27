"""Capture frames from a live RTSP stream.

The companion to ``video_frames.extract_frames`` (which samples a stored video
file). This grabs a handful of spaced frames from a *live* feed so the same
inference pipeline can treat a camera like an upload. Returns the identical
shape: ``[{"framePath": str, "frameTimestamp": float}]``.

See ARCHITECTURE.md#camera--rtsp-ingestion-layer.

Strategy: prefer system ffmpeg (subprocess) over cv2.VideoCapture.  OpenCV's
FFmpeg integration stalls on ``avformat_find_stream_info`` for live H264 streams
because it waits for a keyframe that may not arrive within its probe window.
The ffmpeg CLI handles this gracefully with ``-fflags nobuffer``.
"""
import os
import shutil
import subprocess
import time

DEFAULT_NUM_FRAMES = 4
DEFAULT_SPACING_SECONDS = 1.0
OPEN_TIMEOUT_SECONDS = 15.0


def _ffmpeg_available() -> bool:
    return shutil.which("ffmpeg") is not None


def _capture_one_frame(rtsp_url: str, out_path: str, timeout: int = 12) -> tuple[bool, str]:
    """Grab a single frame from ``rtsp_url`` and write it to ``out_path``.

    Returns (success, stderr_tail) so callers can surface ffmpeg errors.
    """
    import logging
    result = subprocess.run(
        [
            "ffmpeg", "-y",
            "-rtsp_transport", "tcp",
            "-fflags", "nobuffer+discardcorrupt",
            "-flags", "low_delay",
            "-i", rtsp_url,
            "-vframes", "1",
            "-q:v", "2",
            out_path,
        ],
        capture_output=True,
        timeout=timeout,
    )
    stderr = result.stderr.decode(errors="replace").strip()
    if result.returncode != 0:
        # Log last few lines so it shows up in fly logs
        tail = "\n".join(stderr.splitlines()[-6:]) if stderr else "(no output)"
        logging.getLogger(__name__).warning("ffmpeg RTSP capture failed:\n%s", tail)
        return False, tail
    return os.path.exists(out_path), ""


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

    if _ffmpeg_available():
        return _capture_with_ffmpeg(rtsp_url, output_dir, num_frames, spacing_seconds)
    return _capture_with_opencv(rtsp_url, output_dir, num_frames, spacing_seconds)


def _capture_with_ffmpeg(
    rtsp_url: str,
    output_dir: str,
    num_frames: int,
    spacing_seconds: float,
) -> list:
    extracted = []
    start = time.monotonic()

    for i in range(num_frames):
        if time.monotonic() - start > OPEN_TIMEOUT_SECONDS:
            break
        frame_file = os.path.join(output_dir, f"frame_{i:03d}.jpg")
        remaining = max(5, int(OPEN_TIMEOUT_SECONDS - (time.monotonic() - start)))
        try:
            ok, ffmpeg_err = _capture_one_frame(rtsp_url, frame_file, timeout=remaining)
        except subprocess.TimeoutExpired:
            ok, ffmpeg_err = False, "ffmpeg timed out"

        if not ok:
            if not extracted:
                raise ValueError(
                    f"Could not read a frame from RTSP stream: {rtsp_url}\n"
                    f"ffmpeg error: {ffmpeg_err}"
                )
            break

        timestamp_seconds = round(time.monotonic() - start, 3)
        extracted.append({"framePath": frame_file, "frameTimestamp": timestamp_seconds})

        if i < num_frames - 1 and spacing_seconds > 0:
            time.sleep(spacing_seconds)

    if not extracted:
        raise ValueError(f"No frames could be read from RTSP stream: {rtsp_url}")

    return extracted


def _capture_with_opencv(
    rtsp_url: str,
    output_dir: str,
    num_frames: int,
    spacing_seconds: float,
) -> list:
    import cv2  # noqa: PLC0415 — lazy import; cv2 not available on Vercel

    try:
        capture = cv2.VideoCapture(
            rtsp_url,
            cv2.CAP_FFMPEG,
            [
                cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 15_000,
                cv2.CAP_PROP_READ_TIMEOUT_MSEC, 10_000,
            ],
        )
    except TypeError:
        capture = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)

    try:
        if not capture.isOpened():
            raise ValueError(
                f"Could not connect to RTSP stream: {rtsp_url}\n"
                "Check that the relay is running and a publisher is active."
            )

        extracted = []
        start = time.monotonic()
        next_capture_at = start

        while len(extracted) < num_frames:
            if time.monotonic() - start > OPEN_TIMEOUT_SECONDS:
                break

            success, frame = capture.read()
            if not success or frame is None:
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
            extracted.append({"framePath": frame_file, "frameTimestamp": timestamp_seconds})
            next_capture_at = now + spacing_seconds

        if not extracted:
            raise ValueError(
                f"Stream connected but no frames received from: {rtsp_url}\n"
                "Check that the publisher is actively sending video."
            )

        return extracted
    finally:
        capture.release()
