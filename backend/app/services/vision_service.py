from __future__ import annotations

"""Vision inference orchestration.

See ARCHITECTURE.md#vision-inference-layer. Roboflow is the preferred PPE
object detector for operational events. Qwen Vision remains available as an
experimental provider and comparison path, with mock detections preserving demo
reliability when configured model providers are unavailable.
"""
import base64
import random
import requests
from typing import Literal, Optional, TypedDict

from app.config import QWEN_API_KEY, ROBOFLOW_API_KEY

PPE_LABELS = ["person", "helmet", "no_helmet", "vest", "no_vest"]
ModelProvider = Literal["auto", "roboflow", "qwen_vision", "manual_mock"]


class RawDetection(TypedDict):
    label: str
    confidence: float
    boundingBox: Optional[dict]
    frameTimestamp: Optional[float]


def run_inference(
    frames: list[dict],
    provider: ModelProvider = "auto",
) -> tuple[list[RawDetection], str]:
    """frames: list of {"path": str, "frameTimestamp": float | None}

    Returns (raw_detections, source).

    Auto inference priority:
    1. Roboflow (if ROBOFLOW_API_KEY set)
    2. Qwen Vision (if QWEN_API_KEY set)
    3. Mock detections (fallback)
    """
    if provider == "manual_mock":
        return _generate_mock_detections(frames), "manual_mock"

    if provider == "roboflow":
        return _run_roboflow_or_raise(frames), "roboflow"

    if provider == "qwen_vision":
        return _call_qwen_vision(frames), "qwen_vision"

    if ROBOFLOW_API_KEY:
        try:
            return _run_roboflow_or_raise(frames), "roboflow"
        except Exception as e:
            print(f"Warning: Roboflow inference failed: {e}")

    if QWEN_API_KEY:
        try:
            return _call_qwen_vision(frames), "qwen_vision"
        except Exception as e:
            print(f"Warning: Qwen inference failed: {e}")

    return _generate_mock_detections(frames), "manual_mock"


def run_inference_with_fallback(
    frames: list[dict],
    provider: ModelProvider,
) -> tuple[list[RawDetection], str]:
    """Run an explicit provider, falling back to mock for demo reliability."""
    try:
        return run_inference(frames, provider)
    except Exception as e:
        print(f"Warning: {provider} inference failed, using mock fallback: {e}")
        return _generate_mock_detections(frames), "manual_mock"


def run_comparison(frames: list[dict]) -> dict:
    """Run Roboflow and Qwen side by side for evaluation reporting.

    Roboflow remains the preferred primary source when available. Qwen results
    are returned only for comparison and are not persisted as operational truth.
    """
    roboflow_result = _run_provider_for_comparison(frames, "roboflow")
    qwen_result = _run_provider_for_comparison(frames, "qwen_vision")

    primary = roboflow_result
    if not primary["available"] or primary["error"]:
        primary_detections, primary_source = run_inference(frames, "auto")
        primary = {
            "provider": "auto",
            "source": primary_source,
            "available": True,
            "error": None,
            "detections": primary_detections,
        }

    return {
        "primary": primary,
        "comparison": {
            "roboflow": roboflow_result,
            "qwen": qwen_result,
            "agreement": compare_detection_sets(
                roboflow_result["detections"],
                qwen_result["detections"],
            ),
        },
    }


def compare_detection_sets(
    roboflow_detections: list[RawDetection],
    qwen_detections: list[RawDetection],
) -> dict:
    roboflow_labels = _labels_by_frame(roboflow_detections)
    qwen_labels = _labels_by_frame(qwen_detections)
    frame_keys = sorted(set(roboflow_labels) | set(qwen_labels), key=lambda value: str(value))

    frame_reports = []
    matching_labels = set()
    roboflow_only = set()
    qwen_only = set()
    conflicts = []

    for frame_key in frame_keys:
        roboflow_frame_labels = roboflow_labels.get(frame_key, set())
        qwen_frame_labels = qwen_labels.get(frame_key, set())
        frame_matching = roboflow_frame_labels & qwen_frame_labels
        frame_roboflow_only = roboflow_frame_labels - qwen_frame_labels
        frame_qwen_only = qwen_frame_labels - roboflow_frame_labels

        matching_labels.update(frame_matching)
        roboflow_only.update(frame_roboflow_only)
        qwen_only.update(frame_qwen_only)
        conflicts.extend(_status_conflicts(frame_key, roboflow_frame_labels, qwen_frame_labels))

        frame_reports.append(
            {
                "frameTimestamp": frame_key,
                "matchingLabels": sorted(frame_matching),
                "roboflowOnly": sorted(frame_roboflow_only),
                "qwenOnly": sorted(frame_qwen_only),
            }
        )

    return {
        "matchingLabels": sorted(matching_labels),
        "roboflowOnly": sorted(roboflow_only),
        "qwenOnly": sorted(qwen_only),
        "conflicts": conflicts,
        "frames": frame_reports,
    }


def _run_provider_for_comparison(frames: list[dict], provider: ModelProvider) -> dict:
    configured = (provider == "roboflow" and bool(ROBOFLOW_API_KEY)) or (
        provider == "qwen_vision" and bool(QWEN_API_KEY)
    )
    source_name = provider
    if not configured:
        return {
            "provider": provider,
            "source": source_name,
            "available": False,
            "error": f"{provider} is not configured.",
            "detections": [],
        }

    try:
        detections, source = run_inference(frames, provider)
        return {
            "provider": provider,
            "source": source,
            "available": True,
            "error": None,
            "detections": detections,
        }
    except Exception as e:
        return {
            "provider": provider,
            "source": source_name,
            "available": True,
            "error": str(e),
            "detections": [],
        }


def _labels_by_frame(detections: list[RawDetection]) -> dict[Optional[float], set[str]]:
    labels: dict[Optional[float], set[str]] = {}
    for detection in detections:
        labels.setdefault(detection.get("frameTimestamp"), set()).add(detection["label"])
    return labels


def _status_conflicts(
    frame_key: Optional[float],
    roboflow_labels: set[str],
    qwen_labels: set[str],
) -> list[str]:
    conflicts = []
    for present_label, missing_label, item_name in (
        ("helmet", "no_helmet", "helmet"),
        ("vest", "no_vest", "vest"),
    ):
        if present_label in roboflow_labels and missing_label in qwen_labels:
            conflicts.append(f"Frame {frame_key}: Roboflow sees {item_name}; Qwen sees missing {item_name}.")
        if missing_label in roboflow_labels and present_label in qwen_labels:
            conflicts.append(f"Frame {frame_key}: Roboflow sees missing {item_name}; Qwen sees {item_name}.")
    return conflicts


def _run_roboflow_or_raise(frames: list[dict]) -> list[RawDetection]:
    if not ROBOFLOW_API_KEY:
        raise ValueError("ROBOFLOW_API_KEY not set in environment")
    from app.services.roboflow_service import run_roboflow_inference

    return run_roboflow_inference(frames)


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
            print(f"Warning: Qwen inference failed for frame {frame['path']}: {e}")
            raise

    return detections


def _analyze_frame_with_qwen(image_path: str, frame_timestamp: Optional[float]) -> list[RawDetection]:
    """Analyze a single frame with Qwen3-VL30B API (Dashscope)."""
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


def _normalize_bbox(bbox) -> Optional[dict]:
    """Qwen isn't given a strict output schema, so bounding_box may arrive as
    a dict ({"x", "y", "width", "height"}) or a plain [x, y, width, height] list."""
    if isinstance(bbox, dict):
        return {
            "x": int(bbox.get("x", 0)),
            "y": int(bbox.get("y", 0)),
            "width": int(bbox.get("width", 100)),
            "height": int(bbox.get("height", 100)),
        }
    if isinstance(bbox, (list, tuple)) and len(bbox) == 4:
        x, y, width, height = bbox
        return {"x": int(x), "y": int(y), "width": int(width), "height": int(height)}
    return None


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
                    bbox = detection.get("bounding_box")
                    detections.append({
                        "label": label,
                        "confidence": float(detection.get("confidence", 0.5)),
                        "boundingBox": _normalize_bbox(bbox),
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
