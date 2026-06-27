"""Repeated-violation aggregation tests against the pure aggregator."""

import json
from datetime import datetime, timedelta, timezone

from app.models.safety_event import SafetyEvent
from app.models.upload import Upload
from app.models.zone import Zone
from app.services.repeated_violation_service import aggregate_repeated_violations

_NOW = datetime(2026, 6, 27, 12, 0, 0, tzinfo=timezone.utc)


def _event(event_id, upload_id, violation_type, severity="high", minutes_ago=0):
    return SafetyEvent(
        id=event_id,
        upload_id=upload_id,
        event_type="ppe_violation",
        violation_type=violation_type,
        severity=severity,
        confidence=0.9,
        status="open",
        suggested_action="x",
        created_at=_NOW - timedelta(minutes=minutes_ago),
    )


def _upload(upload_id, zone_id=None, location_label=None):
    return Upload(
        id=upload_id,
        file_name="f.jpg",
        file_type="image",
        file_url="/media/f.jpg",
        location_label=location_label,
        zone_id=zone_id,
        uploaded_at=_NOW,
    )


def _zone(zone_id, display_name):
    return Zone(id=zone_id, display_name=display_name, required_ppe=json.dumps([]), severity_overrides=json.dumps({}))


_ZONES = {"loading-dock": _zone("loading-dock", "Loading Dock")}


def test_three_same_zone_same_violation_makes_one_insight():
    uploads = {f"u{i}": _upload(f"u{i}", zone_id="loading-dock") for i in range(3)}
    events = [
        _event("e0", "u0", "no_vest", minutes_ago=30),
        _event("e1", "u1", "no_vest", minutes_ago=20),
        _event("e2", "u2", "no_vest", minutes_ago=10),
    ]
    insights = aggregate_repeated_violations(events, uploads, _ZONES)
    assert len(insights) == 1
    insight = insights[0]
    assert insight["zoneLabel"] == "Loading Dock"
    assert insight["violationType"] == "no_vest"
    assert insight["count"] == 3
    assert insight["distinctUploadCount"] == 3
    assert insight["latestEventId"] == "e2"


def test_different_zones_do_not_combine():
    uploads = {
        "u0": _upload("u0", zone_id="loading-dock"),
        "u1": _upload("u1", zone_id="loading-dock"),
        "u2": _upload("u2", location_label="Packout Line"),
    }
    events = [
        _event("e0", "u0", "no_vest"),
        _event("e1", "u1", "no_vest"),
        _event("e2", "u2", "no_vest"),
    ]
    insights = aggregate_repeated_violations(events, uploads, _ZONES)
    # Only the loading-dock group has < 3; packout has 1 -> no insights
    assert insights == []


def test_different_violation_types_do_not_combine():
    uploads = {f"u{i}": _upload(f"u{i}", zone_id="loading-dock") for i in range(3)}
    events = [
        _event("e0", "u0", "no_vest"),
        _event("e1", "u1", "no_vest"),
        _event("e2", "u2", "no_helmet"),
    ]
    insights = aggregate_repeated_violations(events, uploads, _ZONES)
    assert insights == []


def test_untagged_uploads_ignored():
    uploads = {f"u{i}": _upload(f"u{i}") for i in range(3)}  # no zone, no label
    events = [_event(f"e{i}", f"u{i}", "no_vest") for i in range(3)]
    insights = aggregate_repeated_violations(events, uploads, _ZONES)
    assert insights == []


def test_below_threshold_no_insight():
    uploads = {f"u{i}": _upload(f"u{i}", zone_id="loading-dock") for i in range(2)}
    events = [_event("e0", "u0", "no_vest"), _event("e1", "u1", "no_vest")]
    insights = aggregate_repeated_violations(events, uploads, _ZONES)
    assert insights == []


def test_location_label_fallback_groups():
    uploads = {f"u{i}": _upload(f"u{i}", location_label="Packout Line") for i in range(3)}
    events = [_event(f"e{i}", f"u{i}", "no_vest", severity="medium") for i in range(3)]
    insights = aggregate_repeated_violations(events, uploads, _ZONES)
    assert len(insights) == 1
    assert insights[0]["zoneLabel"] == "Packout Line"
    assert insights[0]["severity"] == "medium"
