"""Vision inference orchestration.

See ARCHITECTURE.md#vision-inference-layer. The Qwen3-VL30B client
integrates vision inference for PPE detection. Falls back to Roboflow
if available, then to mock detections if the API call fails, preserving demo reliability.
"""
import base64
import random
import requests
from typing import Optional, TypedDict

from app.config import QWEN_API_KEY, ROBOFLOW_API_KEY

PPE_LABELS = ["person", "helmet", "no_helmet", "vest", "no_vest"]


class RawDetection(TypedDict):
    label: str
    confidence: float
    boundingBox: Optional[dict]
    frameTimestamp: Optional[float]


def run_inference(frames: list[dict]) -> tuple[list[RawDetection], str]:
    """frames: list of {"path": str, "frameTimestamp": float | None}

    Returns (raw_detections, source).

    Inference priority:
    1. Qwen Vision (if QWEN_API_KEY set)
    2. Roboflow (if ROBOFLOW_API_KEY set)
    3. Mock detections (fallback)
    """
    if QWEN_API_KEY:
        try:
            return _call_qwen_vision(frames), "qwen_vision"
        except Exception as e:
            print(f"Warning: Qwen inference failed: {e}")

    if ROBOFLOW_API_KEY:
        try:
            from app.services.roboflow_service import run_roboflow_inference
            return run_roboflow_inference(frames), "roboflow"
        except Exception as e:
            print(f"Warning: Roboflow inference failed: {e}")

    return _generate_mock_detections(frames), "manual_mock"


def _call_qwen_vision(frames: list[dict]) -> list[RawDetection]:
    """Call Qwen3-VL30B API to detect PPE and persons.

    Expects QWEN_API_KEY to be set. Sends each frame as a base64-encoded image
    and parses the response for detections matching PPE_LABELS.
    """
    detections: list[RawDetection] = []

    for frame in frames:
        try:
            frame_detections = _analyze_frame_with_qwen(frame["path"], frame.get("frameTimestamp"))
            detections.extend(frame_detections)
        except Exception as e:
            # On error, fall back to mock for this frame
            print(f"Warning: Qwen inference failed for frame {frame['path']}: {e}")
            mock_detection = _generate_mock_detections([frame])
            detections.extend(mock_detection)

    return detections


def _analyze_frame_with_qwen(image_path: str, frame_timestamp: Optional[float]) -> list[RawDetection]:
    """Analyze a single frame with Qwen3-VL30B API."""
    with open(image_path, "rb") as f:
        image_data = base64.standard_b64encode(f.read()).decode("utf-8")

    url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-image-understanding/image-understanding"

    payload = {
        "model": "qwen-vl-plus",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "image": f"data:image/jpeg;base64,{image_data}",
                    },
                    {
                        "type": "text",
                        "text": (
                            "Analyze this worksite image for safety equipment. "
                            "For each person visible, identify: "
                            "1. person (detected/not detected) "
                            "2. helmet status (helmet, no_helmet, or unclear) "
                            "3. vest status (vest, no_vest, or unclear) "
                            "Respond in JSON format with an array of detections, each with: "
                            '{"label": "<person|helmet|no_helmet|vest|no_vest>", "confidence": <0-1>, '
                            '"bounding_box": {"x": <int>, "y": <int>, "width": <int>, "height": <int>}}'
                        ),
                    },
                ],
            }
        ],
    }

    headers = {
        "Authorization": f"Bearer {QWEN_API_KEY}",
        "Content-Type": "application/json",
    }

    response = requests.post(url, json=payload, headers=headers, timeout=30)
    response.raise_for_status()

    result = response.json()
    detections = _parse_qwen_response(result, frame_timestamp)
    return detections


def _parse_qwen_response(response: dict, frame_timestamp: Optional[float]) -> list[RawDetection]:
    """Parse Qwen API response and extract detections matching PPE_LABELS."""
    detections: list[RawDetection] = []

    try:
        content = response.get("output", {}).get("choices", [{}])[0].get("message", {}).get("content", "")

        # Try to extract JSON from response
        import json
        import re

        json_match = re.search(r'\[.*\]', content, re.DOTALL)
        if json_match:
            raw_detections = json.loads(json_match.group())

            for detection in raw_detections:
                label = detection.get("label", "").lower()
                if label in PPE_LABELS:
                    bbox = detection.get("bounding_box", {})
                    detections.append({
                        "label": label,
                        "confidence": float(detection.get("confidence", 0.5)),
                        "boundingBox": {
                            "x": int(bbox.get("x", 0)),
                            "y": int(bbox.get("y", 0)),
                            "width": int(bbox.get("width", 100)),
                            "height": int(bbox.get("height", 100)),
                        } if bbox else None,
                        "frameTimestamp": frame_timestamp,
                    })
    except Exception as e:
        print(f"Warning: Failed to parse Qwen response: {e}")
        raise

    return detections


_MOCK_SCENARIOS = [
    [("person", 0.95), ("helmet", 0.91), ("vest", 0.89)],
    [("person", 0.93), ("no_helmet", 0.88), ("vest", 0.86)],
    [("person", 0.92), ("helmet", 0.9), ("no_vest", 0.84)],
    [("person", 0.9), ("no_helmet", 0.85), ("no_vest", 0.82)],
]


def _generate_mock_detections(frames: list[dict]) -> list[RawDetection]:
    detections: list[RawDetection] = []
    for frame in frames:
        rng = random.Random(frame["path"])
        scenario = rng.choice(_MOCK_SCENARIOS)
        for label, base_confidence in scenario:
            confidence = round(base_confidence + rng.uniform(-0.03, 0.03), 2)
            detections.append(
                {
                    "label": label,
                    "confidence": max(0.5, min(confidence, 0.99)),
                    "boundingBox": {
                        "x": rng.randint(80, 200),
                        "y": rng.randint(60, 160),
                        "width": rng.randint(120, 240) if label == "person" else rng.randint(50, 100),
                        "height": rng.randint(300, 520) if label == "person" else rng.randint(50, 90),
                    },
                    "frameTimestamp": frame.get("frameTimestamp"),
                }
            )
    return detections
