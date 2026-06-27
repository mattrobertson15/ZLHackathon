"""Demo-scenario seeding + analytics (demo steps 1, 2, 8).

This is the backbone of the live demo: loading the warehouse-shift scenario and
showing the dashboard. These tests assert the seed populates the shared tables
and that analytics aggregates them into the documented overview/trends shapes.
"""


def _load_demo(client):
    res = client.post("/admin/demo-scenario")
    assert res.status_code == 200
    return res.json()


def test_demo_scenario_seeds_records(client):
    body = _load_demo(client)
    assert body["status"] == "success"
    counts = body["counts"]
    for key in ("uploads", "detections", "events", "alerts"):
        assert counts[key] > 0

    # The seed should be visible through the public list endpoints.
    assert len(client.get("/events").json()["events"]) >= counts["events"] - 0
    assert len(client.get("/alerts").json()["alerts"]) >= 1


def test_demo_scenario_idempotent(client):
    """Re-running must not duplicate the built-in demo rows."""
    first = _load_demo(client)["counts"]
    events_after_first = len(client.get("/events").json()["events"])

    second = _load_demo(client)["counts"]
    events_after_second = len(client.get("/events").json()["events"])

    assert first == second
    assert events_after_first == events_after_second


def test_analytics_overview_shape(client):
    _load_demo(client)
    res = client.get("/analytics/overview", params={"period": "all"})
    assert res.status_code == 200
    body = res.json()

    for key in (
        "compliancePercentage",
        "totalObservations",
        "totalViolations",
        "positiveObservations",
        "openEvents",
        "severityBreakdown",
        "violationBreakdown",
        "repeatedViolations",
    ):
        assert key in body

    assert 0 <= body["compliancePercentage"] <= 100
    # Violation breakdown must sum to the reported total violations.
    assert sum(body["violationBreakdown"].values()) == body["totalViolations"]
    assert sum(body["severityBreakdown"].values()) == body["totalViolations"]


def test_analytics_surfaces_repeated_zone_violation(client):
    """The seed includes 3 Loading Dock no-vest violations in the week -> a
    repeated-zone violation should surface on the overview."""
    _load_demo(client)
    repeated = client.get("/analytics/overview", params={"period": "weekly"}).json()[
        "repeatedViolations"
    ]
    assert len(repeated) >= 1
    dock = next((r for r in repeated if r["violationType"] == "no_vest"), None)
    assert dock is not None
    assert dock["count"] >= 3


def test_analytics_trends_shape(client):
    _load_demo(client)
    res = client.get("/analytics/trends", params={"period": "daily"})
    assert res.status_code == 200
    body = res.json()
    assert body["period"] == "daily"
    assert isinstance(body["points"], list)
    for point in body["points"]:
        assert "date" in point
        assert 0 <= point["compliancePercentage"] <= 100


def test_admin_reset_clears_incidents(client):
    _load_demo(client)
    assert len(client.get("/events").json()["events"]) > 0

    res = client.post("/admin/reset")
    assert res.status_code == 200
    assert client.get("/events").json()["events"] == []
    assert client.get("/alerts").json()["alerts"] == []
