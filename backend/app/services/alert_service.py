from app.models.alert_record import AlertRecord
from app.models.safety_event import SafetyEvent
from app.utils.ids import generate_id
from app.utils.timestamps import now_utc

# See ARCHITECTURE.md#mock-alert-center for the MVP alert-routing rules.
LOW_CONFIDENCE_THRESHOLD = 0.75

_VIOLATION_TITLES = {
    "no_helmet": "Missing Helmet Detected",
    "no_vest": "Missing Vest Detected",
}

_ALERT_MESSAGES = {
    "supervisor_review": "A {severity}-severity PPE violation was detected. Supervisor review is recommended.",
    "coaching_reminder": "A {severity}-severity PPE violation was detected. A coaching reminder is recommended.",
    "manual_review": "Detection confidence was low or PPE status was unclear. Manual review is recommended.",
}


def generate_alerts(events: list[SafetyEvent]) -> list[AlertRecord]:
    """Convert safety events into mock alert records.

    Positive observations are not actionable, so they don't generate alerts.
    Among the rest, low-confidence detections and uncertain reviews always
    route to manual_review regardless of severity, since they need a human
    to verify the underlying detection before anyone acts on it.
    """
    alerts: list[AlertRecord] = []
    for event in events:
        if event.event_type == "positive_observation":
            continue

        if event.confidence < LOW_CONFIDENCE_THRESHOLD or event.event_type == "uncertain_review":
            alert_type = "manual_review"
        elif event.severity == "high":
            alert_type = "supervisor_review"
        elif event.severity == "medium":
            alert_type = "coaching_reminder"
        else:
            alert_type = "manual_review"

        alerts.append(_build_alert(event, alert_type))
    return alerts


def _build_alert(event: SafetyEvent, alert_type: str) -> AlertRecord:
    title = _VIOLATION_TITLES.get(event.violation_type, "PPE Status Unclear")
    message = _ALERT_MESSAGES[alert_type].format(severity=event.severity)
    return AlertRecord(
        id=generate_id("alrt"),
        safety_event_id=event.id,
        alert_type=alert_type,
        title=title,
        message=message,
        status="draft",
        created_at=now_utc(),
    )
