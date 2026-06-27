"""Smoke tests: the app boots, health responds, and seeded location data is served."""


def test_health(client):
    res = client.get("/health")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "ok"


def test_zones_seeded(client):
    res = client.get("/zones")
    assert res.status_code == 200
    zones = res.json()["zones"]
    assert len(zones) >= 1
    by_id = {z["id"]: z for z in zones}
    # The demo scenario and zone-aware rules depend on these seeded zones.
    assert "loading-dock" in by_id
    dock = by_id["loading-dock"]
    assert "vest" in dock["requiredPpe"]
    # Loading Dock escalates no_vest to high severity.
    assert dock["severityOverrides"].get("no_vest") == "high"


def test_cameras_seeded(client):
    res = client.get("/cameras")
    assert res.status_code == 200
    cameras = res.json()["cameras"]
    assert isinstance(cameras, list)
    assert len(cameras) >= 1
    # Seeded demo cameras are location-only (no live RTSP feed).
    assert all("zoneId" in c for c in cameras)


def test_unknown_zone_404(client):
    res = client.get("/zones/does-not-exist")
    assert res.status_code == 404
