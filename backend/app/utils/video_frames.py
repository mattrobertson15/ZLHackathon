import os

import cv2

MIN_FRAME_INTERVAL_SECONDS = 1.0
MAX_FRAME_INTERVAL_SECONDS = 2.0
MAX_FRAMES = 30


def extract_frames(video_path: str, output_dir: str, max_frames: int = MAX_FRAMES):
    """Sample frames from a video at 1-2 second intervals, capped at max_frames.

    Returns a list of dicts: {"framePath": str, "frameTimestamp": float}
    """
    os.makedirs(output_dir, exist_ok=True)

    capture = cv2.VideoCapture(video_path)
    if not capture.isOpened():
        raise ValueError(f"Could not open video file: {video_path}")

    frame_rate = capture.get(cv2.CAP_PROP_FPS) or 30
    total_frames = capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0
    duration_seconds = total_frames / frame_rate if frame_rate else 0

    interval_seconds = MIN_FRAME_INTERVAL_SECONDS
    if duration_seconds > 0:
        # Spread sampling across the whole video while staying within bounds.
        interval_seconds = max(
            MIN_FRAME_INTERVAL_SECONDS,
            min(MAX_FRAME_INTERVAL_SECONDS, duration_seconds / max_frames),
        )

    frame_step = max(1, int(round(interval_seconds * frame_rate)))

    extracted = []
    frame_index = 0
    base_name = os.path.splitext(os.path.basename(video_path))[0]

    while len(extracted) < max_frames:
        capture.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
        success, frame = capture.read()
        if not success:
            break

        timestamp_seconds = frame_index / frame_rate if frame_rate else 0
        frame_file = os.path.join(
            output_dir, f"{base_name}_frame_{len(extracted):03d}.jpg"
        )
        cv2.imwrite(frame_file, frame)
        extracted.append({"framePath": frame_file, "frameTimestamp": timestamp_seconds})

        frame_index += frame_step

    capture.release()
    return extracted
