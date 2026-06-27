"""Upload -> analyze flow (demo step 3-6) using the deterministic mock provider.

These exercise the real POST /uploads multipart handler, file persistence, and
POST /uploads/{id}/analyze pipeline (vision -> detections -> rule engine ->
events -> alerts) without any external model API.
"""

VALID_LABELS = {"person", "helmet", "no_helmet", "vest", "no_vest"}
VALID_EVENT_TYPES = {"positive_observation", "ppe_violation", "uncertain_review"}
VALID_SEVERITIES = {"low", "medium", "high"}


def _upload_image(client, sample_image_bytes, **data):
    return client.post(
        "/uploads",
        files={"file": ("worksite.jpg", sample_image_bytes, "image/jpeg")},
        data=data,
    )


def test_upload_image_returns_metadata(client, sample_image_bytes):
    res = _upload_image(client, sample_image_bytes, zoneId="loading-dock")
    assert res.status_code == 200
    upload = res.json()["upload"]
    assert upload["id"].startswith("upl_")
    assert upload["fileType"] == "image"
    assert upload["zoneId"] == "loading-dock"
    assert upload["zoneDisplayName"] == "Loading Dock"
    assert upload["status"] == "uploaded"
    assert upload["sourceType"] == "upload"


def test_upload_unknown_zone_rejected(client, sample_image_bytes):
    res = _upload_image(client, sample_image_bytes, zoneId="nope")
    assert res.status_code == 400
    assert res.json()["error"]["code"] == "ZONE_NOT_FOUND"


def test_analyze_mock_produces_detections_events_alerts(client, sample_image_bytes):
    # No zone -> global rules, so every mock scenario (person + PPE) yields >=1 event.
    upload_id = _upload_image(client, sample_image_bytes).json()["upload"]["id"]

    res = client.post(f"/uploads/{upload_id}/analyze", json={"modelProvider": "manual_mock"})
    assert res.status_code == 200
    body = res.json()

    assert body["uploadId"] == upload_id
    assert body["status"] == "processed"
    assert body["primarySource"] == "manual_mock"

    detections = body["detections"]
    assert len(detections) >= 1
    for det in detections:
        assert det["label"] in VALID_LABELS
        assert 0.0 <= det["confidence"] <= 1.0
        assert det["source"] == "manual_mock"
        assert det["uploadId"] == upload_id

    events = body["events"]
    assert len(events) >= 1
    event_ids = set()
    for evt in events:
        assert evt["eventType"] in VALID_EVENT_TYPES
        assert evt["severity"] in VALID_SEVERITIES
        assert evt["status"] == "open"
        event_ids.add(evt["id"])

    # Every alert must reference one of the events we just created, and
    # positive observations must never generate an alert.
    for alert in body["alerts"]:
        assert alert["safetyEventId"] in event_ids
    positive_ids = {e["id"] for e in events if e["eventType"] == "positive_observation"}
    alerted_ids = {a["safetyEventId"] for a in body["alerts"]}
    assert positive_ids.isdisjoint(alerted_ids)


def test_analyze_persists_results_for_results_endpoint(client, sample_image_bytes):
    upload_id = _upload_image(client, sample_image_bytes).json()["upload"]["id"]
    analyze = client.post(f"/uploads/{upload_id}/analyze", json={"modelProvider": "manual_mock"}).json()

    # The read-only results snapshot should reflect what analyze persisted.
    results = client.get(f"/uploads/{upload_id}/results")
    assert results.status_code == 200
    snap = results.json()
    assert snap["upload"]["status"] == "processed"
    assert len(snap["detections"]) == len(analyze["detections"])
    assert len(snap["events"]) == len(analyze["events"])


def test_analyze_unknown_upload_404(client):
    res = client.post("/uploads/upl_missing/analyze", json={"modelProvider": "manual_mock"})
    assert res.status_code == 404
    assert res.json()["error"]["code"] == "UPLOAD_NOT_FOUND"


def test_analyze_invalid_provider_400(client, sample_image_bytes):
    upload_id = _upload_image(client, sample_image_bytes).json()["upload"]["id"]
    res = client.post(f"/uploads/{upload_id}/analyze", json={"modelProvider": "totally-bogus"})
    assert res.status_code == 400
    assert res.json()["error"]["code"] == "INVALID_MODEL_PROVIDER"


def test_zone_aware_suppression_loading_dock(client, sample_image_bytes):
    """At the Loading Dock (vest required, helmet not), any produced events must
    be vest-related — no_helmet/helmet detections are suppressed."""
    upload_id = _upload_image(client, sample_image_bytes, zoneId="loading-dock").json()["upload"]["id"]
    events = client.post(
        f"/uploads/{upload_id}/analyze", json={"modelProvider": "manual_mock"}
    ).json()["events"]
    for evt in events:
        if evt["eventType"] == "ppe_violation":
            assert evt["violationType"] == "no_vest"
