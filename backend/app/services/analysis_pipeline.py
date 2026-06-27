"""Shared frames -> detections -> events -> alerts pipeline.

Extracted from the upload analyze route so both the upload flow and the live
camera monitor run identical logic (DRY). Given a set of frames already on disk,
this runs vision inference, persists detections, applies the rule engine, and
generates mock alerts.

See ARCHITECTURE.md#processing-flow.
"""
from typing import Optional

from sqlalchemy.orm import Session

from app.db.repositories import (
    create_alerts,
    create_detection_results,
    create_safety_events,
)
from app.models.alert_record import AlertRecord
from app.models.safety_event import SafetyEvent
from app.models.zone import Zone
from app.services import (
    alert_service,
    repeated_violation_service,
    rule_engine,
    vision_service,
)
from app.services.detection_parser import normalize_detections


def run_analysis_pipeline(
    db: Session,
    upload_id: str,
    frames: list[dict],
    frame_url_by_timestamp: Optional[dict] = None,
    provider: str = "auto",
    create_events: bool = True,
    create_alerts_flag: bool = True,
    zone: Optional[Zone] = None,
) -> dict:
    """Run inference over ``frames`` and persist the resulting records.

    frames: list of {"path": str, "frameTimestamp": float | None}
    frame_url_by_timestamp: maps a frame timestamp to a servable /media URL.
    zone: when set, the rule engine applies the zone's required-PPE + severity
    overrides (see ZONE_CAMERA_PLAN.md). Uploads/captures inherit their zone.

    Returns a dict with keys: detections, events, alerts, source, comparison.
    The ``compare`` provider additionally populates ``comparison`` (raw dict).
    """
    frame_url_by_timestamp = frame_url_by_timestamp or {}

    comparison = None
    if provider == "compare":
        comparison_result = vision_service.run_comparison(frames)
        primary = comparison_result["primary"]
        raw_detections = primary["detections"]
        source = primary["source"]
        comparison = comparison_result["comparison"]
    elif provider in {"roboflow", "qwen_vision"}:
        raw_detections, source = vision_service.run_inference_with_fallback(
            frames, provider
        )
    else:
        raw_detections, source = vision_service.run_inference(frames, provider)

    for raw in raw_detections:
        raw["frameUrl"] = frame_url_by_timestamp.get(raw.get("frameTimestamp"))

    detections = normalize_detections(raw_detections, upload_id, source)
    detections = create_detection_results(db, detections)

    events: list[SafetyEvent] = []
    if create_events:
        events = rule_engine.evaluate(detections, upload_id, zone)
        events = create_safety_events(db, events)

    alerts: list[AlertRecord] = []
    if create_alerts_flag and events:
        new_alerts = alert_service.generate_alerts(events)
        # A newly created violation may push its zone group over the weekly
        # repeated-violation threshold; see ZONE_CAMERA_PLAN.md#4.
        new_alerts += repeated_violation_service.generate_repeated_violation_alerts(
            db, events
        )
        alerts = create_alerts(db, new_alerts)

    return {
        "detections": detections,
        "events": events,
        "alerts": alerts,
        "source": source,
        "comparison": comparison,
    }
