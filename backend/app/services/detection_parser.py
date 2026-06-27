from app.models.detection_result import DetectionResult
from app.utils.ids import generate_id
from app.utils.timestamps import now_utc


def normalize_detections(raw_detections: list[dict], upload_id: str, source: str) -> list[DetectionResult]:
    """Convert raw vision-model output into DetectionResult rows.

    See ARCHITECTURE.md#detection-parser for the normalized shape.
    """
    normalized = []
    for raw in raw_detections:
        bbox = raw.get("boundingBox") or {}
        normalized.append(
            DetectionResult(
                id=generate_id("det"),
                upload_id=upload_id,
                frame_timestamp=raw.get("frameTimestamp"),
                label=raw["label"],
                confidence=raw["confidence"],
                bbox_x=bbox.get("x"),
                bbox_y=bbox.get("y"),
                bbox_width=bbox.get("width"),
                bbox_height=bbox.get("height"),
                source=source,
                created_at=now_utc(),
            )
        )
    return normalized
