# Testing Safety Sentinel

This document describes the automated backend test suite and the strategy behind
it. See [ARCHITECTURE.md](ARCHITECTURE.md) for the components under test and
[API.md](API.md) for the endpoint contracts the integration tests assert against.

## Running the tests

```bash
cd backend
pip install -r requirements-dev.txt   # installs requirements.txt + pytest + httpx
pytest
```

`pytest.ini` sets `pythonpath = .` so tests import the app as `app.*` without
extra environment setup. The suite is fully self-contained: it uses a throwaway
temp SQLite DB and upload directory, and never makes a network call.

## Strategy

The suite has two layers:

1. **Unit tests** (DB-free, pure functions) — the rule engine, repeated-violation
   aggregation, and camera dedup logic. Fast and exhaustive on branching logic.
   - `tests/test_rule_engine.py`
   - `tests/test_repeated_violation_service.py`
   - `tests/test_camera_dedup.py`

2. **API/integration tests** (FastAPI `TestClient` + temp SQLite) — exercise the
   real routes end to end, following the demo flow in
   [DEMOSCRIPT.md](DEMOSCRIPT.md):
   - `tests/test_api_smoke.py` — health, seeded zones/cameras.
   - `tests/test_uploads_analyze_api.py` — upload → analyze → detections/events/alerts,
     zone-aware suppression, error paths (404/400).
   - `tests/test_demo_scenario_analytics_api.py` — demo-scenario seed (+ idempotency),
     analytics overview/trends, repeated-zone violation, admin reset.
   - `tests/test_events_alerts_api.py` — event/alert list, filters, status PATCH.
   - `tests/test_summaries_api.py` — AI summary generation with a stubbed Claude client.

Shared fixtures live in `tests/conftest.py`.

## What data the tests use (and why no API keys are needed)

The app ships a **deterministic `manual_mock` vision provider** and a repeatable
**`POST /admin/demo-scenario`** seed. These are the testing backbone:

- **`manual_mock` detections** are seeded by the frame path (every scenario
  includes a `person` + PPE), so `POST /uploads/{id}/analyze` produces stable,
  assertable detections/events/alerts with no Roboflow/Qwen key.
- **The demo scenario** seeds zone-tagged uploads, detections, events, and alerts
  — including the 3 Loading Dock `no_vest` violations that trigger a repeated-zone
  alert — so analytics, events, alerts, and summary tests have realistic data.
- **External boundaries are stubbed, never called:** Roboflow/Qwen keys are
  cleared in `conftest.py` (forcing the mock path), and the Anthropic client is
  monkeypatched by the `fake_anthropic` fixture so summary tests parse a canned
  reply offline.
- **Real bundled images** in `uploads/` provide valid bytes for upload tests.

## Known gaps / next steps

Covered now: the demo-critical happy path + key error paths for uploads, analyze,
events, alerts, analytics, summaries, and the demo scenario.

Not yet covered (candidates for a broader pass):
- Frontend has **no test tooling** yet (no Vitest/Playwright).
- Camera/RTSP monitor loop and `cv2.VideoCapture` capture (would need a fake
  capture); the monitor thread is intentionally not started during tests.
- Video-frame extraction (`utils/video_frames.py`) — no sample clip is bundled.
- `compare` mode and the live Roboflow/Qwen client adapters (only the mock path
  is exercised).
- Vercel Blob storage path and the summaries response envelope mismatch noted
  below.

## Notes found while writing tests

- `tests/test_rule_engine.py::test_positive_only_for_required_ppe` was failing
  before this suite because it omitted the required `person` detection that
  `rule_engine.evaluate` needs before emitting any event. Fixed in the test
  (the implementation matches the documented "if person detected and …" rules).
- `POST /summaries/generate` and `GET /summaries/{id}` return the summary object
  directly, while [API.md](API.md) documents a `{ "summary": ... }` envelope.
  The tests assert the current implementation shape; the doc/impl mismatch is
  worth reconciling.
