"""Zone-aware rule engine tests. DB-free: models are used as plain holders."""

import json

from app.models.detection_result import DetectionResult
from app.models.zone import Zone
from app.services import rule_engine


def _det(label, confidence=0.9, frame_timestamp=None):
    return DetectionResult(
        id=f"det_{label}",
        upload_id="upl_1",
        frame_timestamp=frame_timestamp,
        label=label,
        confidence=confidence,
        source="manual_mock",
    )


def _zone(zone_id, display_name, required_ppe, severity_overrides=None):
    return Zone(
        id=zone_id,
        display_name=display_name,
        required_ppe=json.dumps(required_ppe),
        severity_overrides=json.dumps(severity_overrides or {}),
    )


def test_no_zone_uses_global_rules_unchanged():
    detections = [_det("person"), _det("no_helmet"), _det("no_vest")]
    events = rule_engine.evaluate(detections, "upl_1", zone=None)
    by_type = {(e.event_type, e.violation_type): e for e in events}
    assert by_type[("ppe_violation", "no_helmet")].severity == "high"
    assert by_type[("ppe_violation", "no_vest")].severity == "medium"


def test_required_violation_escalated_by_override():
    zone = _zone("loading-dock", "Loading Dock", ["vest"], {"no_vest": "high"})
    events = rule_engine.evaluate([_det("person"), _det("no_vest")], "upl_1", zone)
    assert len(events) == 1
    event = events[0]
    assert event.event_type == "ppe_violation"
    assert event.violation_type == "no_vest"
    assert event.severity == "high"
    assert "Loading Dock" in event.suggested_action


def test_violation_suppressed_when_ppe_not_required():
    # no_vest on a helmet-only floor produces no event...
    zone = _zone("general-floor", "General Floor", ["helmet"])
    events = rule_engine.evaluate([_det("person"), _det("no_vest")], "upl_1", zone)
    assert events == []


def test_no_helmet_suppressed_in_vest_only_zone():
    zone = _zone("loading-dock", "Loading Dock", ["vest"], {"no_vest": "high"})
    events = rule_engine.evaluate([_det("person"), _det("no_helmet")], "upl_1", zone)
    assert events == []


def test_positive_only_for_required_ppe():
    zone = _zone("general-floor", "General Floor", ["helmet"])
    # The rule engine only emits events when a person is present in the frame
    # (see rule_engine.evaluate). helmet is required -> positive; vest present
    # but not required -> no event.
    events = rule_engine.evaluate([_det("person"), _det("helmet"), _det("vest")], "upl_1", zone)
    assert len(events) == 1
    assert events[0].event_type == "positive_observation"
    assert "General Floor" in events[0].suggested_action


def test_uncertain_review_when_person_without_ppe():
    zone = _zone("loading-dock", "Loading Dock", ["vest"], {"no_vest": "high"})
    events = rule_engine.evaluate([_det("person")], "upl_1", zone)
    assert len(events) == 1
    assert events[0].event_type == "uncertain_review"
