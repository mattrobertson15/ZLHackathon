"""Events and alerts list/filter/patch (demo steps 6 & 7).

Built on the demo scenario so there is a realistic mix of event types,
severities, and alert types to filter and transition.
"""

import pytest


@pytest.fixture
def seeded(client):
    client.post("/admin/demo-scenario")
    return client


def test_events_list_includes_upload_metadata(seeded):
    events = seeded.get("/events").json()["events"]
    assert len(events) > 0
    sample = events[0]
    # The events API enriches each row with its source upload for the review panel.
    assert "upload" in sample and sample["upload"]["id"] == sample["uploadId"]


def test_events_filter_by_violation_type(seeded):
    events = seeded.get("/events", params={"violationType": "no_vest"}).json()["events"]
    assert len(events) > 0
    assert all(e["violationType"] == "no_vest" for e in events)


def test_events_filter_by_severity(seeded):
    events = seeded.get("/events", params={"severity": "high"}).json()["events"]
    assert all(e["severity"] == "high" for e in events)


def test_event_patch_status(seeded):
    open_events = seeded.get("/events", params={"status": "open"}).json()["events"]
    assert len(open_events) > 0
    event_id = open_events[0]["id"]

    res = seeded.patch(f"/events/{event_id}", json={"status": "reviewed"})
    assert res.status_code == 200

    detail = seeded.get(f"/events/{event_id}").json()["event"]
    assert detail["status"] == "reviewed"


def test_event_detail_404(seeded):
    res = seeded.get("/events/evt_missing")
    assert res.status_code == 404


def test_alerts_filter_by_type(seeded):
    repeated = seeded.get("/alerts", params={"alertType": "repeated_violation"}).json()["alerts"]
    # The demo seed creates a repeated-zone alert for the Loading Dock.
    assert len(repeated) >= 1
    assert all(a["alertType"] == "repeated_violation" for a in repeated)


def test_alert_patch_status(seeded):
    alerts = seeded.get("/alerts").json()["alerts"]
    assert len(alerts) > 0
    alert_id = alerts[0]["id"]

    res = seeded.patch(f"/alerts/{alert_id}", json={"status": "sent_mock"})
    assert res.status_code == 200

    after = seeded.get("/alerts").json()["alerts"]
    patched = next(a for a in after if a["id"] == alert_id)
    assert patched["status"] == "sent_mock"
