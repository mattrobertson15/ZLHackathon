"""AI summary generation (demo step 9) with the Anthropic client stubbed.

``fake_anthropic`` replaces the real client so no network call is made; the test
asserts the route parses Claude's reply into the four stored sections and that
the summary is then listable/retrievable.
"""


def _generate(client):
    return client.post(
        "/summaries/generate",
        json={
            "period": "weekly",
            "startDate": "2026-06-22T00:00:00Z",
            "endDate": "2026-06-28T00:00:00Z",
        },
    )


def test_generate_summary_parses_sections(client, fake_anthropic):
    client.post("/admin/demo-scenario")
    res = _generate(client)
    assert res.status_code == 200
    summary = res.json()

    assert summary["period"] == "weekly"
    assert summary["id"].startswith("summary_")
    # Each of the four sections should be populated from the canned reply.
    assert "compliance" in summary["executiveSummary"].lower()
    assert summary["topViolations"]
    assert summary["trendAnalysis"]
    assert summary["recommendedActions"]


def test_generated_summary_is_listable_and_fetchable(client, fake_anthropic):
    summary_id = _generate(client).json()["id"]

    listing = client.get("/summaries").json()["summaries"]
    assert any(s["id"] == summary_id for s in listing)

    detail = client.get(f"/summaries/{summary_id}")
    assert detail.status_code == 200
    assert detail.json()["id"] == summary_id


def test_summary_not_found_404(client):
    res = client.get("/summaries/summary_missing")
    assert res.status_code == 404
