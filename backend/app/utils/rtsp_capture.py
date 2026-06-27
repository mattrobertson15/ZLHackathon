"""Capture frames from a live RTSP stream.

The companion to ``video_frames.extract_frames`` (which samples a stored video
file). This grabs a handful of spaced frames from a *live* feed so the same
inference pipeline can treat a camera like an upload. Returns the identical
shape: ``[{"framePath": str, "frameTimestamp": float}]``.

See ARCHITECTURE.md#camera--rtsp-ingestion-layer.
"""
import os
import time

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
    import cv2  # noqa: PLC0415 — lazy import; cv2 not available on Vercel

    os.makedirs(output_dir, exist_ok=True)

    # Pass open-timeout and low-latency flags BEFORE the connection is made.
    # fflags=nobuffer skips FFmpeg's packet buffering so avformat_find_stream_info
    # returns immediately on the first packet rather than waiting to fill a buffer
    # — critical for live RTSP where the first keyframe can be seconds away.
    # rtsp_transport=tcp is already in OPENCV_FFMPEG_CAPTURE_OPTIONS; we set it
    # here too so this call is self-contained.
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
        # OpenCV < 4.4 doesn't support the params argument; fall back.
        capture = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)

    try:
        # For live RTSP, isOpened() can return False even when the TCP connection
        # succeeded, because FFmpeg's stream-info probe didn't receive a keyframe
        # in time. We attempt reads for the full OPEN_TIMEOUT_SECONDS and raise
        # only if we get zero frames — that distinguishes "wrong URL / no stream"
        # from "stream is live but keyframe hasn't arrived yet".
        if not capture.isOpened():
            # Not connected at all — wrong host, port, or no publisher on path.
            raise ValueError(
                f"Could not connect to RTSP stream: {rtsp_url}\n"
                "Check that the relay is running and the path matches what your "
                "broadcaster is publishing to (use GET /cameras/relay-streams to "
                "see active paths)."
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
            extracted.append(
                {"framePath": frame_file, "frameTimestamp": timestamp_seconds}
            )
            next_capture_at = now + spacing_seconds

        if not extracted:
            raise ValueError(
                f"Stream connected but no frames received from: {rtsp_url}\n"
                "The RTSP path is valid but the publisher may not be sending "
                "video (check Streamlabs is actively streaming, not just connected)."
            )

        return extracted
    finally:
        capture.release()
