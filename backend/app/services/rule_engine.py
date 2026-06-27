from collections import defaultdict

from app.models.detection_result import DetectionResult
from app.models.safety_event import SafetyEvent
from app.utils.ids import generate_id
from app.utils.timestamps import now_utc

# See ARCHITECTURE.md#rule-engine for the MVP rule definitions.
_PPE_RULES = {
    "helmet": {
        "eventType": "positive_observation",
        "violationType": None,
        "severity": "low",
        "suggestedAction": "Helmet compliance observed.",
    },
    "no_helmet": {
        "eventType": "ppe_violation",
        "violationType": "no_helmet",
        "severity": "high",
        "suggestedAction": "Supervisor review recommended. Helmet appears missing.",
    },
    "vest": {
        "eventType": "positive_observation",
        "violationType": None,
        "severity": "low",
        "suggestedAction": "Vest compliance observed.",
    },
    "no_vest": {
        "eventType": "ppe_violation",
        "violationType": "no_vest",
        "severity": "medium",
        "suggestedAction": "Coaching reminder recommended. Safety vest appears missing.",
    },
}


def evaluate(detections: list[DetectionResult], upload_id: str) -> list[SafetyEvent]:
    """Convert detections into SafetyEvent rows, grouped by frame."""
    frames = defaultdict(list)
    for detection in detections:
        frames[detection.frame_timestamp].append(detection)

    events: list[SafetyEvent] = []
    for frame_timestamp, frame_detections in frames.items():
        person = next((d for d in frame_detections if d.label == "person"), None)
        if person is None:
            continue

        ppe_detections = [d for d in frame_detections if d.label in _PPE_RULES]
        if not ppe_detections:
            events.append(_build_event(upload_id, person, "uncertain_review", None, "medium",
                                        "PPE status unclear. Manual review recommended."))
            continue

        for detection in ppe_detections:
            rule = _PPE_RULES[detection.label]
            events.append(
                _build_event(
                    upload_id,
                    detection,
                    rule["eventType"],
                    rule["violationType"],
                    rule["severity"],
                    rule["suggestedAction"],
                )
            )

    return events


def _build_event(upload_id, detection, event_type, violation_type, severity, suggested_action) -> SafetyEvent:
    return SafetyEvent(
        id=generate_id("evt"),
        upload_id=upload_id,
        event_type=event_type,
        violation_type=violation_type,
        severity=severity,
        confidence=detection.confidence,
        status="open",
        suggested_action=suggested_action,
        created_at=now_utc(),
    )
