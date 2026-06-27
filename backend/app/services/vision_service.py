"""Vision inference orchestration.

See ARCHITECTURE.md#vision-inference-layer. The Qwen3-VL30B client
(`_call_qwen_vision`) is a deferred stub — wiring it up requires
QWEN_API_KEY plus a verified request/response contract for the model,
which is tracked as Phase 3.5 in todo.md. Until that lands, every frame
is routed to the mock detector so the rest of the pipeline (parser,
rule engine, events) can be built and demoed without the key.
"""
import random
from typing import Optional, TypedDict

from app.config import QWEN_API_KEY

PPE_LABELS = ["person", "helmet", "no_helmet", "vest", "no_vest"]


class RawDetection(TypedDict):
    label: str
    confidence: float
    boundingBox: Optional[dict]
    frameTimestamp: Optional[float]


def run_inference(frames: list[dict]) -> tuple[list[RawDetection], str]:
    """frames: list of {"path": str, "frameTimestamp": float | None}

    Returns (raw_detections, source).
    """
    if QWEN_API_KEY:
        try:
            return _call_qwen_vision(frames), "qwen_vision"
        except NotImplementedError:
            pass
    return _generate_mock_detections(frames), "manual_mock"


def _call_qwen_vision(frames: list[dict]) -> list[RawDetection]:
    raise NotImplementedError(
        "Qwen3-VL30B integration deferred to session 3.5 (needs QWEN_API_KEY "
        "and a verified request/response contract). See todo.md Phase 3.5."
    )


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
