"""Repeated zone violation detection.

Groups ``ppe_violation`` events over a rolling weekly window by a resolved
location key (zone_id, falling back to location_label) and violation type. When
a group reaches the threshold it becomes a dashboard insight and can spawn a
single mock ``repeated_violation`` alert.

No employee identity is used — this is intentionally "same zone / same violation
type" only. See ZONE_CAMERA_PLAN.md#4-repeated-zone-violation-detection.
"""

from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.db.repositories import list_safety_events_since
from app.models.alert_record import AlertRecord
from app.models.camera import Camera  # noqa: F401  (kept for type clarity in callers)
from app.models.safety_event import SafetyEvent
from app.models.upload import Upload
from app.models.zone import Zone
from app.utils.ids import generate_id
from app.utils.timestamps import now_utc, to_iso

WEEKLY_WINDOW = timedelta(days=7)
REPEATED_VIOLATION_THRESHOLD = 3

_SEVERITY_RANK = {"low": 0, "medium": 1, "high": 2}
_VIOLATION_TEXT = {"no_helmet": "no-helmet", "no_vest": "no-vest"}
_VIOLATION_TITLE = {"no_helmet": "Repeated Helmet Issue", "no_vest": "Repeated Vest Issue"}


def _resolved_key_label(upload: Upload, zones_by_id: dict[str, Zone]) -> tuple[str | None, str | None]:
    """Return the (grouping key, display label) for an upload, or (None, None)."""
    if upload is None:
        return None, None
    if upload.zone_id:
        zone = zones_by_id.get(upload.zone_id)
        label = zone.display_name if zone else upload.zone_id
        return upload.zone_id, label
    if upload.location_label:
        return upload.location_label, upload.location_label
    return None, None


def aggregate_repeated_violations(
    events: list[SafetyEvent],
    uploads_by_id: dict[str, Upload],
    zones_by_id: dict[str, Zone],
    threshold: int = REPEATED_VIOLATION_THRESHOLD,
) -> list[dict]:
    """Pure aggregation: group ppe_violations by (resolved key, violation type).

    ``events`` should already be limited to the desired time window. Groups with
    fewer than ``threshold`` events are dropped. DB-free so it is unit testable.
    """
    groups: dict[tuple[str, str], dict] = {}
    for event in events:
        if event.event_type != "ppe_violation" or not event.violation_type:
            continue
        upload = uploads_by_id.get(event.upload_id)
        key, label = _resolved_key_label(upload, zones_by_id)
        if key is None:
            continue  # untagged uploads do not participate

        group = groups.setdefault(
            (key, event.violation_type),
            {
                "zoneLabel": label,
                "violationType": event.violation_type,
                "events": [],
                "uploadIds": set(),
            },
        )
        group["events"].append(event)
        group["uploadIds"].add(event.upload_id)

    insights: list[dict] = []
    for group in groups.values():
        group_events = group["events"]
        if len(group_events) < threshold:
            continue
        ordered = sorted(group_events, key=lambda e: e.created_at)
        max_severity = max(group_events, key=lambda e: _SEVERITY_RANK.get(e.severity, 0)).severity
        count = len(group_events)
        violation_text = _VIOLATION_TEXT.get(group["violationType"], group["violationType"])
        insights.append(
            {
                "zoneLabel": group["zoneLabel"],
                "violationType": group["violationType"],
                "count": count,
                "distinctUploadCount": len(group["uploadIds"]),
                "severity": max_severity,
                "latestEventId": ordered[-1].id,
                "firstSeenAt": to_iso(ordered[0].created_at),
                "lastSeenAt": to_iso(ordered[-1].created_at),
                "message": (
                    f"{group['zoneLabel']} has {count} {violation_text} "
                    f"violations in the past week."
                ),
            }
        )

    insights.sort(key=lambda i: i["count"], reverse=True)
    return insights


def _load_window(db: Session) -> tuple[list[SafetyEvent], dict[str, Upload], dict[str, Zone]]:
    since = now_utc() - WEEKLY_WINDOW
    events = [
        e
        for e in list_safety_events_since(db, since)
        if e.event_type == "ppe_violation" and e.violation_type
    ]
    upload_ids = {e.upload_id for e in events}
    uploads_by_id = {
        upload.id: upload
        for upload in db.query(Upload).filter(Upload.id.in_(upload_ids)).all()
    } if upload_ids else {}
    zones_by_id = {zone.id: zone for zone in db.query(Zone).all()}
    return events, uploads_by_id, zones_by_id


def compute_repeated_violations(db: Session) -> list[dict]:
    """Weekly-window repeated-violation insights for the dashboard."""
    events, uploads_by_id, zones_by_id = _load_window(db)
    return aggregate_repeated_violations(events, uploads_by_id, zones_by_id)


def _covered_groups(db: Session, uploads_by_id: dict[str, Upload], zones_by_id: dict[str, Zone]) -> set:
    """Groups that already have a repeated_violation alert within the window."""
    existing = db.query(AlertRecord).filter(AlertRecord.alert_type == "repeated_violation").all()
    if not existing:
        return set()
    event_ids = {a.safety_event_id for a in existing}
    events = db.query(SafetyEvent).filter(SafetyEvent.id.in_(event_ids)).all()
    events_by_id = {e.id: e for e in events}
    covered = set()
    for alert in existing:
        event = events_by_id.get(alert.safety_event_id)
        if event is None:
            continue
        upload = uploads_by_id.get(event.upload_id) or _get_upload(db, event.upload_id, uploads_by_id)
        key, _ = _resolved_key_label(upload, zones_by_id)
        if key is not None and event.violation_type:
            covered.add((key, event.violation_type))
    return covered


def _get_upload(db: Session, upload_id: str, cache: dict[str, Upload]) -> Upload | None:
    upload = db.query(Upload).filter(Upload.id == upload_id).first()
    if upload is not None:
        cache[upload_id] = upload
    return upload


def generate_repeated_violation_alerts(
    db: Session, new_events: list[SafetyEvent]
) -> list[AlertRecord]:
    """Create (unpersisted) repeated_violation alerts triggered by new events.

    Only groups touched by ``new_events`` that have reached the threshold and are
    not already covered by an existing repeated_violation alert produce an alert.
    Returns the new AlertRecord objects for the caller to persist.
    """
    candidate_keys = {
        e.violation_type
        for e in new_events
        if e.event_type == "ppe_violation" and e.violation_type
    }
    if not candidate_keys:
        return []

    events, uploads_by_id, zones_by_id = _load_window(db)

    # Which (key, violation_type) groups did the new events touch?
    touched: set = set()
    for event in new_events:
        if event.event_type != "ppe_violation" or not event.violation_type:
            continue
        upload = uploads_by_id.get(event.upload_id) or _get_upload(db, event.upload_id, uploads_by_id)
        key, _ = _resolved_key_label(upload, zones_by_id)
        if key is not None:
            touched.add((key, event.violation_type))
    if not touched:
        return []

    insights = aggregate_repeated_violations(events, uploads_by_id, zones_by_id)
    covered = _covered_groups(db, uploads_by_id, zones_by_id)

    alerts: list[AlertRecord] = []
    created_at = now_utc()
    for insight in insights:
        # Match an insight back to a touched group by zoneLabel + violation type.
        matching = next(
            (k for k in touched if k[1] == insight["violationType"] and _label_for_key(k[0], zones_by_id) == insight["zoneLabel"]),
            None,
        )
        if matching is None or matching in covered:
            continue
        covered.add(matching)
        alerts.append(
            AlertRecord(
                id=generate_id("alrt"),
                safety_event_id=insight["latestEventId"],
                alert_type="repeated_violation",
                title=_VIOLATION_TITLE.get(insight["violationType"], "Repeated PPE Issue"),
                message=(
                    f"{insight['message']} Supervisor coaching review is recommended."
                ),
                status="draft",
                created_at=created_at,
            )
        )
    return alerts


def _label_for_key(key: str, zones_by_id: dict[str, Zone]) -> str:
    zone = zones_by_id.get(key)
    return zone.display_name if zone else key
