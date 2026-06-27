from collections import defaultdict
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.db.repositories import list_safety_events_since

# See ARCHITECTURE.md#analytics-layer for the MVP metric definitions.
OVERVIEW_PERIODS = {"daily", "weekly", "monthly", "all"}
TREND_PERIODS = {"daily", "weekly", "monthly"}

_OVERVIEW_WINDOWS = {
    "daily": timedelta(days=1),
    "weekly": timedelta(days=7),
    "monthly": timedelta(days=30),
}

_TREND_CONFIG = {
    "daily": {"bucket": "day", "window": timedelta(days=14)},
    "weekly": {"bucket": "week", "window": timedelta(weeks=8)},
    "monthly": {"bucket": "month", "window": timedelta(days=180)},
}


def _compliance_percentage(positive: int, total: int) -> float:
    if total == 0:
        return 0.0
    return round(positive / total * 100, 1)


def get_overview(db: Session, period: str = "all") -> dict:
    if period not in OVERVIEW_PERIODS:
        period = "all"

    since = None
    if period in _OVERVIEW_WINDOWS:
        since = datetime.now(timezone.utc) - _OVERVIEW_WINDOWS[period]
    events = list_safety_events_since(db, since)

    positive_observations = sum(1 for e in events if e.event_type == "positive_observation")
    violations = [e for e in events if e.event_type == "ppe_violation"]
    total_observations = len(events)
    open_events = sum(1 for e in events if e.status == "open")

    severity_breakdown: dict[str, int] = defaultdict(int)
    violation_breakdown: dict[str, int] = defaultdict(int)
    for event in violations:
        severity_breakdown[event.severity] += 1
        if event.violation_type:
            violation_breakdown[event.violation_type] += 1

    return {
        "period": period,
        "compliancePercentage": _compliance_percentage(positive_observations, total_observations),
        "totalObservations": total_observations,
        "totalViolations": len(violations),
        "positiveObservations": positive_observations,
        "openEvents": open_events,
        "severityBreakdown": dict(severity_breakdown),
        "violationBreakdown": dict(violation_breakdown),
    }


def _bucket_key(dt: datetime, bucket: str) -> str:
    if bucket == "day":
        return dt.strftime("%Y-%m-%d")
    if bucket == "week":
        week_start = dt - timedelta(days=dt.weekday())
        return week_start.strftime("%Y-%m-%d")
    return dt.strftime("%Y-%m-01")


def get_trends(db: Session, period: str = "daily") -> dict:
    if period not in TREND_PERIODS:
        period = "daily"
    config = _TREND_CONFIG[period]
    since = datetime.now(timezone.utc) - config["window"]
    events = list_safety_events_since(db, since)

    buckets: dict[str, dict] = {}
    for event in events:
        key = _bucket_key(event.created_at, config["bucket"])
        bucket = buckets.setdefault(
            key,
            {"positive": 0, "total": 0, "totalViolations": 0, "noHelmet": 0, "noVest": 0},
        )
        bucket["total"] += 1
        if event.event_type == "positive_observation":
            bucket["positive"] += 1
        elif event.event_type == "ppe_violation":
            bucket["totalViolations"] += 1
            if event.violation_type == "no_helmet":
                bucket["noHelmet"] += 1
            elif event.violation_type == "no_vest":
                bucket["noVest"] += 1

    points = [
        {
            "date": key,
            "compliancePercentage": _compliance_percentage(buckets[key]["positive"], buckets[key]["total"]),
            "totalViolations": buckets[key]["totalViolations"],
            "noHelmet": buckets[key]["noHelmet"],
            "noVest": buckets[key]["noVest"],
        }
        for key in sorted(buckets)
    ]

    return {"period": period, "points": points}
