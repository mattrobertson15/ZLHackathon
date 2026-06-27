import os
from datetime import datetime, timezone
from typing import Optional

import anthropic
from sqlalchemy.orm import Session

from app.db.repositories import list_safety_events_in_range
from app.services.analytics_service import _compliance_percentage
from app.utils.ids import generate_id


def generate_summary(
    db: Session,
    period: str,
    start_date: datetime,
    end_date: datetime,
) -> dict:
    """Generate an AI-powered safety summary for a given period using Claude."""

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not set in environment")

    events = list_safety_events_in_range(db, start_date, end_date)

    positive_observations = sum(1 for e in events if e.event_type == "positive_observation")
    violations = [e for e in events if e.event_type == "ppe_violation"]
    total_observations = len(events)

    no_helmet_count = sum(1 for v in violations if v.violation_type == "no_helmet")
    no_vest_count = sum(1 for v in violations if v.violation_type == "no_vest")
    high_severity_count = sum(1 for v in violations if v.severity == "high")
    medium_severity_count = sum(1 for v in violations if v.severity == "medium")

    compliance_pct = _compliance_percentage(positive_observations, total_observations)

    context = f"""
Safety Compliance Summary for Period: {period}
Start Date: {start_date.strftime('%Y-%m-%d')}
End Date: {end_date.strftime('%Y-%m-%d')}

Key Metrics:
- Total Observations: {total_observations}
- Positive Observations: {positive_observations}
- Total Violations: {len(violations)}
- Compliance Percentage: {compliance_pct}%
- No Helmet Violations: {no_helmet_count}
- No Vest Violations: {no_vest_count}
- High Severity Issues: {high_severity_count}
- Medium Severity Issues: {medium_severity_count}

Based on these metrics, provide a safety summary in the following format:

1. Executive Summary: A 2-3 sentence overview of the period's safety performance
2. Top Violations: List the 3 most common safety violations observed
3. Trend Analysis: Describe the trend in compliance (improving, declining, stable)
4. Recommended Actions: 3-4 specific actionable recommendations to improve safety
"""

    client = anthropic.Anthropic(api_key=api_key)
    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[{"role": "user", "content": context}],
    )

    summary_text = response.content[0].text

    summary_id = generate_id("summary")

    sections = _parse_summary_sections(summary_text)

    from app.models.summary import Summary

    db_summary = Summary(
        id=summary_id,
        period=period,
        start_date=start_date,
        end_date=end_date,
        executive_summary=sections.get("executive_summary", ""),
        top_violations=sections.get("top_violations", ""),
        trend_analysis=sections.get("trend_analysis", ""),
        recommended_actions=sections.get("recommended_actions", ""),
        created_at=datetime.now(timezone.utc),
    )
    db.add(db_summary)
    db.commit()
    db.refresh(db_summary)

    return {
        "id": db_summary.id,
        "period": db_summary.period,
        "startDate": db_summary.start_date.isoformat(),
        "endDate": db_summary.end_date.isoformat(),
        "executiveSummary": db_summary.executive_summary,
        "topViolations": db_summary.top_violations,
        "trendAnalysis": db_summary.trend_analysis,
        "recommendedActions": db_summary.recommended_actions,
        "createdAt": db_summary.created_at.isoformat(),
    }


def get_summaries(db: Session) -> list[dict]:
    """Retrieve all generated summaries."""
    from app.models.summary import Summary

    summaries = db.query(Summary).order_by(Summary.created_at.desc()).all()
    return [
        {
            "id": s.id,
            "period": s.period,
            "startDate": s.start_date.isoformat(),
            "endDate": s.end_date.isoformat(),
            "executiveSummary": s.executive_summary,
            "topViolations": s.top_violations,
            "trendAnalysis": s.trend_analysis,
            "recommendedActions": s.recommended_actions,
            "createdAt": s.created_at.isoformat(),
        }
        for s in summaries
    ]


def get_summary_by_id(db: Session, summary_id: str) -> Optional[dict]:
    """Retrieve a specific summary by ID."""
    from app.models.summary import Summary

    s = db.query(Summary).filter(Summary.id == summary_id).first()
    if not s:
        return None

    return {
        "id": s.id,
        "period": s.period,
        "startDate": s.start_date.isoformat(),
        "endDate": s.end_date.isoformat(),
        "executiveSummary": s.executive_summary,
        "topViolations": s.top_violations,
        "trendAnalysis": s.trend_analysis,
        "recommendedActions": s.recommended_actions,
        "createdAt": s.created_at.isoformat(),
    }


def _parse_summary_sections(text: str) -> dict[str, str]:
    """Parse Claude's response into structured sections."""
    sections = {
        "executive_summary": "",
        "top_violations": "",
        "trend_analysis": "",
        "recommended_actions": "",
    }

    lines = text.split("\n")
    current_section = None

    for line in lines:
        line_lower = line.lower()

        if "executive summary" in line_lower:
            current_section = "executive_summary"
        elif "top violations" in line_lower:
            current_section = "top_violations"
        elif "trend analysis" in line_lower:
            current_section = "trend_analysis"
        elif "recommended actions" in line_lower:
            current_section = "recommended_actions"
        elif current_section and line.strip():
            sections[current_section] += line + "\n"

    for key in sections:
        sections[key] = sections[key].strip()

    return sections
