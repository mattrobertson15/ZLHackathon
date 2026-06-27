from collections import defaultdict

from app.models.detection_result import DetectionResult
from app.models.safety_event import SafetyEvent
from app.models.zone import Zone
from app.utils.ids import generate_id
from app.utils.timestamps import now_utc

# See ARCHITECTURE.md#rule-engine and ZONE_CAMERA_PLAN.md#3-zone-aware-rule-engine.
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

# Map between positive PPE items and their corresponding violation labels.
_POSITIVE_LABELS = {"helmet", "vest"}
_VIOLATION_TO_PPE = {"no_helmet": "helmet", "no_vest": "vest"}
_PPE_DISPLAY = {"helmet": "Helmet", "vest": "Safety vest"}


def evaluate(
    detections: list[DetectionResult],
    upload_id: str,
    zone: Zone | None = None,
) -> list[SafetyEvent]:
    """Convert detections into SafetyEvent rows, grouped by frame.

    When ``zone`` is None the legacy global PPE rules apply unchanged. When a
    zone is supplied, only PPE items the zone requires produce events, and
    violation severities can be escalated by the zone's severity overrides.
    """
    frames = defaultdict(list)
    for detection in detections:
        frames[detection.frame_timestamp].append(detection)

    events: list[SafetyEvent] = []
    for frame_detections in frames.values():
        ppe_detections = [d for d in frame_detections if d.label in _PPE_RULES]
        person = next((d for d in frame_detections if d.label == "person"), None)

        if ppe_detections:
            # PPE labels imply a person is present; create events directly.
            for detection in ppe_detections:
                event = _evaluate_detection(upload_id, detection, zone)
                if event is not None:
                    events.append(event)
        elif person is not None:
            # Person visible but no PPE status could be determined.
            events.append(
                _build_event(
                    upload_id,
                    person,
                    "uncertain_review",
                    None,
                    "medium",
                    "PPE status unclear. Manual review recommended.",
                )
            )

    return events


def _evaluate_detection(
    upload_id: str, detection: DetectionResult, zone: Zone | None
) -> SafetyEvent | None:
    """Build a SafetyEvent for a single PPE detection, honoring zone policy."""
    label = detection.label

    if zone is None:
        rule = _PPE_RULES[label]
        return _build_event(
            upload_id,
            detection,
            rule["eventType"],
            rule["violationType"],
            rule["severity"],
            rule["suggestedAction"],
        )

    required = zone.required_ppe_items()

    if label in _POSITIVE_LABELS:
        if label not in required:
            return None  # PPE not required in this zone -> not a positive event
        return _build_event(
            upload_id,
            detection,
            "positive_observation",
            None,
            "low",
            f"{_PPE_DISPLAY[label]} compliance observed in {zone.display_name}.",
        )

    # Violation label (no_helmet / no_vest)
    ppe = _VIOLATION_TO_PPE[label]
    if ppe not in required:
        return None  # not required in this zone -> suppressed, no event

    severity = zone.severity_overrides_map().get(label) or _PPE_RULES[label]["severity"]
    return _build_event(
        upload_id,
        detection,
        "ppe_violation",
        label,
        severity,
        _violation_action(label, severity, zone),
    )


def _violation_action(label: str, severity: str, zone: Zone) -> str:
    item = _PPE_DISPLAY[_VIOLATION_TO_PPE[label]]
    if severity == "high":
        lead = "Supervisor review recommended."
    elif severity == "medium":
        lead = "Coaching reminder recommended."
    else:
        lead = "Review recommended."
    return f"{lead} {item} required in {zone.display_name}. {item} appears missing."


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
