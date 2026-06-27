ARCHITECTURE.md

Safety Sentinel Architecture

Safety Sentinel is a hackathon MVP for AI-powered PPE safety intelligence. The system analyzes uploaded images and videos from industrial worksites, detects PPE compliance, converts detections into structured safety events, and generates dashboard analytics, mock alerts, and AI safety summaries.

System Goals

The architecture is optimized for:

* Fast hackathon development
* Clear separation between frontend, backend, model inference, and reporting
* Support for uploaded images and short videos
* Easy extension to live camera feeds later
* Transparent safety-event generation from model outputs
* Simple dashboard analytics and trend reporting
* Mock alert workflows without requiring real messaging integrations

High-Level Architecture

User
  |
  v
Next.js Frontend
  |
  | upload image/video
  v
FastAPI Backend
  |
  | store file metadata
  | process media
  v
Vision Inference Layer
  |
  | PPE detections
  v
Detection Parser + Rule Engine
  |
  | structured events
  v
Safety Event Store
  |
  +--> Dashboard Analytics
  +--> Mock Alert Center
  +--> Claude Summary Generator

Main Components

1. Next.js Frontend

The frontend provides the user-facing interface for uploading media, viewing results, reviewing safety events, exploring analytics, and reading generated safety summaries.

Suggested Pages

/
  Landing / project overview
/upload
  Upload image or video for analysis
/results/[uploadId]
  View annotated results and generated safety events
/dashboard
  Compliance metrics, trends, and violation breakdowns
/demo
  Guided hackathon demo scenario loader and walkthrough links
/library
  All uploads with status badges and links to their results
/events
  Safety event log
/alerts
  Mock alert center
/summaries
  Daily, weekly, and monthly AI-generated safety summaries

Frontend Responsibilities

* Upload images and videos
* Display processing status
* Render annotated detection results
* Show compliance metrics
* Display event logs
* Display mock alerts
* Request AI summaries
* Export markdown safety reports from dashboard metrics and generated summaries
* Visualize trends using Recharts
* Load the built-in warehouse shift demo scenario for reliable product walkthroughs

2. FastAPI Backend

The backend handles uploads, inference orchestration, event generation, analytics, and summary generation.

Backend Responsibilities

* Accept uploaded images and videos
* Store upload metadata
* Extract frames from video when needed
* Send images or frames to the vision model
* Normalize detection results
* Apply PPE compliance rules
* Create safety events
* Create mock alert records
* Return dashboard metrics
* Generate summary prompts for Claude
* Store generated summaries
* Seed repeatable demo data through the admin demo-scenario endpoint

3. Vision Inference Layer

The vision layer detects people and PPE-related conditions.

Initial Detection Targets

* person
* helmet
* no_helmet
* vest
* no_vest

Preferred Model Path

Use the available Qwen Vision model for PPE detection if it produces usable structured outputs.

The model should return, where possible:

* Label
* Confidence
* Bounding box
* Frame timestamp for video
* Short explanation of the detected condition

Fallback Model Path

If Qwen Vision is not reliable enough for bounding boxes or class-level PPE detection, use one of the following:

* Roboflow-hosted inference API
* YOLO model trained or exported from Roboflow PPE datasets
* Hybrid approach:
    * YOLO/Roboflow for detection
    * Qwen Vision for image-level interpretation and explanation

Current Implementation Status

`app/services/vision_service.py` implements the inference routing used by
`POST /uploads/{upload_id}/analyze`.

Default `modelProvider: "auto"` priority (first available wins):

1. **Roboflow** (if `ROBOFLOW_API_KEY` is set)
   - Hosted inference API via `serverless.roboflow.com`
   - Model: personal-protective-equipment-combined-model/8
   - Returns object detections with class, confidence, and bounding box
   - Class mapping: "NO-Safety Vest" → "no_vest", etc.
   - Source: "roboflow"
   - Implementation: `app/services/roboflow_service.py`

2. **Qwen Vision** (if `QWEN_API_KEY` and `QWEN_BASE_URL` are set)
   - Self-hosted Qwen3-VL model served behind a Nebius AI Studio instance,
     called via its OpenAI-compatible `/chat/completions` endpoint
   - Env vars: `QWEN_API_KEY` (bearer token), `QWEN_BASE_URL` (instance base
     URL, e.g. `http://<host>:8080/v1`), `QWEN_MODEL` (defaults to
     `Qwen/Qwen3-VL-30B-A3B-Instruct-FP8` — must match an id returned by the
     instance's `/v1/models`, including the `Qwen/` prefix)
   - Experimental structured output for person, helmet, no_helmet, vest, no_vest
   - The endpoint doesn't enforce a response schema, so `bounding_box` can come
     back as either a `{x, y, width, height}` object or a `[x, y, width, height]`
     array; `_normalize_bbox()` in `vision_service.py` handles both
   - Source: "qwen_vision"
   - Best used as a comparison or explanation path, not the primary operational detector

3. **Mock Generator** (fallback, always available)
   - Deterministic-per-frame mock generator
   - Produces realistic person/PPE detection mixes
   - Source: "manual_mock"

The analyze request can also set `modelProvider` to `"roboflow"`,
`"qwen_vision"`, `"manual_mock"`, or `"compare"`. Explicit Roboflow/Qwen
requests fall back to mock detections if the requested provider fails. Compare
mode runs Roboflow and Qwen side by side, returns an agreement report, and uses
Roboflow as the primary source when available. Only primary detections are
persisted and passed into the rule engine.

4. Detection Parser

The detection parser converts raw model outputs into a normalized internal format.

Normalized Detection Format

type DetectionResult = {
  id: string;
  uploadId: string;
  frameTimestamp?: number;
  label: "person" | "helmet" | "no_helmet" | "vest" | "no_vest";
  confidence: number;
  boundingBox?: {
    x: number;
    y: number;
    width: number;
    height: number;
  };
  source: "qwen_vision" | "roboflow" | "manual_mock";
  createdAt: string;
};

Zones & Cameras (Location Schema)

The shared location schema underpins both zone-aware rules and repeated-zone
analytics. Zones and demo cameras are seeded at startup
(`app/db/seeds.py`) when their tables are empty; they are read via
`GET /zones` and `GET /cameras`.

type Zone = {
  id: string;                    // slug, e.g. "loading-dock"
  displayName: string;
  requiredPpe: string[];         // e.g. ["vest"]
  severityOverrides: Record<string, string>; // e.g. { "no_vest": "high" }
  createdAt: string;
};

type Camera = {
  id: string;                    // slug, e.g. "cam-02"
  displayName: string;
  zoneId: string;                // -> Zone.id
  status: "active" | "inactive";
  createdAt: string;
};

An Upload carries a nullable `zoneId` (canonical location) and `cameraId`. When
an upload is assigned to a camera, it inherits the camera's zone. The legacy
`locationLabel` is retained as a free-text fallback. The "resolved location" for
grouping/analytics is `zoneId || locationLabel`. Authenticated camera ingest and
API-key issuance are intentionally out of scope; see
[ZONE_CAMERA_PLAN.md](ZONE_CAMERA_PLAN.md).

5. Rule Engine

The rule engine converts detections into compliance statuses and safety events.

MVP Rules

If person detected and helmet detected:
  create positive observation or mark helmet compliant
If person detected and no_helmet detected:
  create high-severity PPE violation
If person detected and vest detected:
  create positive observation or mark vest compliant
If person detected and no_vest detected:
  create medium-severity PPE violation
If person detected but PPE state is unclear:
  create uncertain review event

Severity Defaults

no_helmet -> high
no_vest -> medium
uncertain_review -> low or medium
positive_observation -> low

Zone-Aware Rules (implemented)

`rule_engine.evaluate(detections, upload_id, zone=None)` resolves the upload's
zone (from `upload.zone_id`) and applies zone policy:

* When `zone` is None, the global MVP rules above apply unchanged (legacy /
  untagged uploads).
* When a zone is present, a PPE item only produces an event if the zone requires
  it. A `no_vest` in a vest-required zone is a violation; the same `no_vest` in a
  helmet-only zone produces no event at all.
* A zone's `severityOverrides` can escalate a required violation (e.g. the
  Loading Dock escalates `no_vest` from the default `medium` to `high`).

See [ZONE_CAMERA_PLAN.md](ZONE_CAMERA_PLAN.md) and the zones/cameras component
below.

Future Rules

* Confidence threshold overrides
* Shift-level trend analysis
* Supervisor approval workflows

6. Safety Event Store

Safety events are the core operational data object of the system.

The app should store every safety-relevant observation as a structured event.

type SafetyEvent = {
  id: string;
  uploadId: string;
  upload?: Upload;
  eventType: "positive_observation" | "ppe_violation" | "uncertain_review";
  violationType?: "no_helmet" | "no_vest";
  severity: "low" | "medium" | "high";
  confidence: number;
  status: "open" | "reviewed" | "dismissed" | "resolved";
  suggestedAction: string;
  createdAt: string;
};

Safety event rows store the `uploadId` as the durable media reference. The
events API enriches list/detail responses with the related upload metadata so
the frontend review panel can display the source image or video while a
supervisor marks the event as reviewed, dismissed, or resolved.

7. Mock Alert Center

The alert center demonstrates how Safety Sentinel could route safety events to supervisors or approved stakeholders.

The MVP should not send real alerts. Instead, it should create mock alert records stored and displayed inside the app.

type AlertRecord = {
  id: string;
  safetyEventId: string;
  alertType:
    | "supervisor_review"
    | "coaching_reminder"
    | "manual_review"
    | "repeated_violation";
  title: string;
  message: string;
  status: "draft" | "queued" | "sent_mock" | "dismissed";
  createdAt: string;
};

Implemented in `app/services/alert_service.py` (`generate_alerts`), called from
`POST /uploads/{upload_id}/analyze` right after the rule engine creates safety
events. Routing rule:

* `positive_observation` events never generate an alert (nothing to act on).
* `confidence < 0.75` (`LOW_CONFIDENCE_THRESHOLD`), or `eventType ==
  "uncertain_review"`, → `manual_review`, regardless of severity — a human
  should confirm the underlying detection before anyone acts on it.
* Otherwise `severity == "high"` → `supervisor_review`.
* Otherwise `severity == "medium"` → `coaching_reminder`.
* Any remaining case (e.g. a non-positive low-severity event) falls back to
  `manual_review`.

In addition, `repeated_violation_service.generate_repeated_violation_alerts` runs
after events are persisted: if a new violation pushes its resolved-location group
to the weekly threshold (3) and no `repeated_violation` alert already covers that
group, one `repeated_violation` alert is created, linked to the latest event in
the group. Dedup resolves each existing repeated alert back to its group, so
re-analysis does not produce duplicates.

Alerts are stored in the `alert_records` table and exposed via `GET /alerts`
(filterable by `status`/`alertType`) and `PATCH /alerts/{alert_id}` for mock
status transitions. See [API.md#alerts](API.md) for the full spec.

Alert Philosophy

* Supervisor review is the default path.
* No employee identification is used.
* Alerts are coaching-oriented, not punitive.
* Low-confidence events should go to manual review.

8. Analytics Layer

The analytics layer aggregates safety events into dashboard metrics.

MVP Metrics

* Overall compliance percentage
* Total violation count
* Violation type breakdown
* Trend over time
* Positive safety observations
* Open events
* Events by severity
* Repeated zone violations (weekly window)

Repeated Zone Violations

`repeated_violation_service.compute_repeated_violations` groups `ppe_violation`
events over a rolling 7-day window by resolved location (`zoneId ||
locationLabel`) and violation type, surfacing groups at or above the threshold
(3) as `repeatedViolations` on `GET /analytics/overview`. The aggregation is a
pure function (`aggregate_repeated_violations`) so it is unit-tested without a
DB. No employee identity is used — grouping is "same zone / same violation type"
only.

Compliance Percentage

Suggested MVP formula:

compliance_percentage =
  positive_observations / total_safety_observations * 100

Where:

total_safety_observations =
  positive_observations + ppe_violations + uncertain_review_events

Alternative formula:

compliance_percentage =
  compliant_ppe_checks / total_ppe_checks * 100

Use the simpler event-based calculation for the hackathon MVP.

Implemented in `app/services/analytics_service.py` (`get_overview`, `get_trends`),
exposed via `GET /analytics/overview` and `GET /analytics/trends`.

* `get_overview(period)` — `period` is a rolling window ending now: `daily` (last
  1 day), `weekly` (last 7 days), `monthly` (last 30 days), or `all` (no
  filter, the default). `severityBreakdown` and `violationBreakdown` are
  computed over `ppe_violation` events only, so their counts sum to
  `totalViolations`.
* `get_trends(period)` — buckets events into points over a fixed lookback
  window: `daily` (last 14 days, one point per calendar day), `weekly` (last 8
  weeks, one point per ISO week start), `monthly` (last 6 months, one point
  per calendar month). Only buckets containing at least one event are
  returned (no zero-filled gaps).
* Both reuse `list_safety_events_since` (`app/db/repositories.py`) for the
  underlying date-range query.

9. Demo Scenario Loader

The demo loader provides a repeatable product walkthrough path without requiring
live model inference during judging or stakeholder demos.

Implemented as `POST /admin/demo-scenario` in `app/routes/admin.py`, the loader
seeds:

* 3 processed uploads using bundled sample worksite images
* 9 normalized detection results with `source: "manual_mock"`
* 6 safety events across violations, positive observations, and manual review
* 4 mock alerts covering supervisor review, coaching reminder, and manual review

The endpoint is idempotent for the built-in scenario. Re-running it deletes and
recreates records for the demo upload IDs only, so unrelated uploads and
incidents are preserved. The frontend exposes this workflow at `/app/demo` and
links from Upload for users who want a reliable walkthrough instead of a live
ingestion run.

10. Claude Summary Generator

The summary generator converts event and analytics data into readable safety reports.

Summary Types

* Daily summary
* Weekly summary
* Monthly summary

Summary Input

The backend should send Claude a structured summary object:

{
  "period": "weekly",
  "startDate": "2026-06-22",
  "endDate": "2026-06-28",
  "compliancePercentage": 87,
  "totalObservations": 248,
  "totalViolations": 32,
  "violationBreakdown": {
    "no_helmet": 11,
    "no_vest": 21
  },
  "severityBreakdown": {
    "low": 4,
    "medium": 21,
    "high": 7
  },
  "trend": "Violations decreased 12% compared to the previous period."
}

Summary Output

Claude should produce:

* Executive summary
* Top violation types
* Trend interpretation
* Recommended corrective actions
* Coaching-oriented safety reminders

Current implementation stores the generated report as `executiveSummary`,
`topViolations`, `trendAnalysis`, and `recommendedActions` fields on the
`summaries` table. `POST /summaries/generate` and `GET /summaries/{summary_id}`
return a `{ "summary": ... }` envelope; `GET /summaries` returns
`{ "summaries": [...] }`.

11. Exportable Safety Reports

The MVP exports manager-ready markdown reports entirely in the frontend via
`frontend/lib/report.ts`.

Report types:

* Dashboard report: compliance percentage, total observations, violations,
  pending reviews, violation breakdown, severity breakdown, and daily trend
  table.
* Summary report: reporting period, generated timestamp, executive summary, top
  violations, trend analysis, and recommended actions.

This avoids adding a backend report-generation surface while still giving
managers a portable artifact they can open, share, or print. PDF generation is a
future enhancement.

12. Camera / RTSP Ingestion Layer

Safety Sentinel can treat a live RTSP camera feed as a source, in addition to
one-off file uploads. For demos this is driven by an **emulated** camera: a
video file looped into an RTSP server (`ffmpeg` + `mediamtx`) that the backend
consumes exactly like a real CCTV stream. See [DEMOSCRIPT.md](DEMOSCRIPT.md) and
[emulator/README.md](emulator/README.md).

Why this reuses the existing pipeline. The inference chain (frames → detections
→ events → alerts) is frame-source-agnostic — it only needs a list of
`{path, frameTimestamp}`. So a camera capture plugs into the same code an upload
uses. The shared core was extracted into
`app/services/analysis_pipeline.py:run_analysis_pipeline`, called by both
`POST /uploads/{upload_id}/analyze` and the camera monitor.

Unified Camera data model (`app/models/camera.py`, table `cameras`). This is the
same `cameras` table used by the location schema (see
[ZONE_CAMERA_PLAN.md](ZONE_CAMERA_PLAN.md#1-shared-location-schema)) — a camera
is a zone-assigned location record that can *optionally* be a live RTSP feed:

type Camera = {
  id: string;
  displayName: string;
  zoneId?: string;                 // inherited by uploads/captures for zone-aware rules
  status: "active" | "inactive";   // registry state
  createdAt: string;
  // Live RTSP feed (optional; null/offline for location-only cameras)
  rtspUrl?: string;
  streamStatus: "offline" | "live" | "error";   // feed connectivity
  monitoring: boolean;
  captureIntervalSeconds: number;   // default 15, min 5
  lastCaptureAt?: string;
  lastError?: string;
};

Capture-as-Upload. Each capture cycle is recorded as an `Upload` row so events,
alerts, dashboard, and analytics work unchanged. The capture upload sets
`camera_id` and inherits the camera's `zone_id`, so live captures get the same
zone-aware PPE rules + repeated-violation detection as file uploads. The
`uploads` table gained nullable columns (via the `_apply_migrations` ALTER
pattern in `db/database.py`):

* `source_type` — `"upload"` (default) or `"camera"`
* `camera_id` — set for camera captures, used to attribute events back to a camera
* `zone_id` — the camera's zone (also set directly for zone-tagged uploads)

Frame capture. `app/utils/rtsp_capture.py:capture_frames_from_rtsp` opens the
stream with `cv2.VideoCapture` (OpenCV's bundled ffmpeg backend — no new
dependency) and writes a few spaced JPEGs into `UPLOAD_STORAGE_PATH`, returning
the same `{framePath, frameTimestamp}` shape as `utils/video_frames.py`. RTSP is
read over TCP (`OPENCV_FFMPEG_CAPTURE_OPTIONS=rtsp_transport;tcp`, defaulted in
`config.py`) for reliability.

Background monitor. `app/services/camera_monitor.py` runs one daemon thread,
started from `main.py` on startup and stopped on shutdown. Each tick it captures
from every `monitoring=True` camera that is due (per its interval), runs the
shared pipeline, and updates `stream_status`/`lastCaptureAt`/`lastError`. Each camera is
wrapped in try/except so one dead feed cannot stop the loop. The monitor is a
**no-op on Vercel** (`IS_VERCEL`) — serverless has no long-lived process, cannot
hold an RTSP connection, and cannot run ffmpeg. Continuous monitoring therefore
requires a persistent container host (see Deployment below).

Camera API. `app/routes/cameras.py` exposes register/list/detail, start/stop
monitoring, capture-now, a latest-frame `snapshot` (JPEG, polled by the UI for a
live preview), and delete. See [API.md#cameras](API.md).

Camera processing flow:

1. User registers a camera (RTSP URL) and clicks Start.
2. Backend marks `monitoring=true` and runs one immediate capture for instant feedback.
3. The monitor thread captures frames on the interval thereafter.
4. Each cycle creates a `camera` Upload, runs `run_analysis_pipeline`, and persists detections/events/alerts.
5. Events flow into the existing Dashboard, Events, Alerts, and Analytics views.
6. The Cameras page polls `snapshot` + camera state for a near-live view.

Backend Folder Structure

backend/
  app/
    main.py
    config.py
    routes/
      uploads.py        [done]
      inference.py       [done — analyze + detections]
      events.py          [done]
      analytics.py        [done]
      alerts.py           [done]
      summaries.py        [done]
    routes/
      cameras.py         [done — register/start/stop/capture/snapshot]
    services/
      vision_service.py   [done — Roboflow-first auto routing, Qwen comparison, mock fallback]
      detection_parser.py [done]
      rule_engine.py       [done]
      analysis_pipeline.py [done — shared frames→detections→events→alerts core]
      camera_monitor.py    [done — background RTSP capture loop]
      repeated_violation_service.py [done — weekly per-zone repeat detection]
      media_service.py     [implemented in utils/video_frames.py]
      analytics_service.py [done]
      alert_service.py     [done]
      summary_service.py   [done]
    models/
      upload.py          [done — + source_type / camera_id]
      camera.py          [done]
      detection_result.py [done]
      safety_event.py     [done]
      alert_record.py      [done]
      summary.py           [done]
    db/
      database.py
      repositories.py
    utils/
      ids.py
      timestamps.py
      video_frames.py
      rtsp_capture.py    [done — live RTSP frame capture]

Suggested Frontend Folder Structure

frontend/
  app/
    page.tsx
    upload/
      page.tsx
    results/
      [uploadId]/
        page.tsx
    dashboard/
      page.tsx
    demo/
      page.tsx
    cameras/
      page.tsx
    events/
      page.tsx
    alerts/
      page.tsx
    summaries/
      page.tsx
  components/
    UploadDropzone.tsx
    DetectionViewer.tsx
    ComplianceScoreCard.tsx
    ViolationBreakdownChart.tsx
    TrendChart.tsx
    EventTable.tsx
    AlertCard.tsx
    SummaryCard.tsx
  lib/
    api.ts
    types.ts
    report.ts
    chart-utils.ts

Processing Flow

Steps 4-9 of both upload flows and the camera capture flow share a single
implementation: `app/services/analysis_pipeline.py:run_analysis_pipeline`. This
keeps the inference → detection → event → alert logic DRY across all three
entry points.

Image Upload Flow

1. User uploads image.
2. Frontend sends image to FastAPI.
3. Backend stores file and creates Upload record.
4-9. `run_analysis_pipeline` runs vision inference, normalizes detections,
   applies zone-aware rule engine, and generates mock alerts.
10. Backend returns upload, detections, events, and alerts.
11. Frontend displays annotated image and safety results.

Video Upload Flow

1. User uploads video.
2. Backend stores video and creates Upload record.
3. Backend samples frames from the video.
4-9. `run_analysis_pipeline` runs inference on each sampled frame, normalizes
   detections with frame timestamps, applies rule engine, and generates alerts.
10. Frontend displays summary results and key frames.

RTSP Camera Capture Flow

See [§12 Camera / RTSP Ingestion Layer](#12-camera--rtsp-ingestion-layer) for
the full flow. In brief:

1. Camera monitor thread wakes for each `monitoring=True` camera that is due.
2. `rtsp_capture.py` opens the RTSP stream (over TCP via OpenCV/ffmpeg) and
   saves a few spaced JPEGs.
3. A `camera`-sourced Upload row is created, inheriting the camera's `zone_id`.
4-9. Same `run_analysis_pipeline` as the upload flows.
10. Events appear in Dashboard, Events, and Alerts; camera state updated.

Video Sampling Strategy

For the MVP, avoid processing every frame.

Recommended approach:

Sample 1 frame every 1-2 seconds.
Limit total frames per video to 20-30.
Run inference on sampled frames.
Aggregate repeated violations.

This keeps inference fast and manageable.

Static File Serving

Uploaded files are saved to UPLOAD_STORAGE_PATH and served at /media/{fileName}.
This is a separate path from the /uploads API resource (POST /uploads, GET
/uploads, GET /uploads/{upload_id}) to avoid routing collisions between the
REST resource and static file serving.

On Vercel, UPLOAD_STORAGE_PATH resolves to /tmp, which is ephemeral per
function invocation and not shared across instances. A file written during
upload can disappear before a later request reads it back. To keep the
deployed demo working, the backend uploads to Vercel Blob instead whenever
`VERCEL=1` and `BLOB_READ_WRITE_TOKEN` is set (see `USE_BLOB_STORAGE` in
`backend/app/config.py`): `Upload.file_url` becomes the public Blob CDN URL
returned by the upload, rather than a `/media/...` path, and the frontend
(`resolveMediaUrl` in `frontend/lib/api.ts`) renders that URL directly instead
of prefixing it with the API base URL. There is no official Vercel Blob
Python SDK, so `backend/app/services/blob_service.py` calls the same REST
endpoint (`https://vercel.com/api/blob`) the JS SDK uses, for `put` (upload)
and a plain `GET` for download. When inference needs a local file path (image
analysis, video frame extraction), the upload route downloads the blob back
into `UPLOAD_STORAGE_PATH` as a scratch copy for that request only — this
ephemeral re-download is fine since it doesn't need to persist past the
request. In local development (no `VERCEL` env var), uploads still go straight
to local disk under `./uploads`.

Data Storage Options

For hackathon speed, use one of these paths:

Option A: In-memory / local JSON

Fastest possible. Good for demo only.

Option B: SQLite

Still simple and more realistic.

Option C: Supabase / Postgres

Best if the team already has Supabase experience and wants a more production-like backend.

Recommended MVP choice:

SQLite or Supabase, depending on team speed.

Environment Variables

# Backend
ANTHROPIC_API_KEY=your_anthropic_key_here
QWEN_API_KEY=your_nebius_bearer_token_here
QWEN_BASE_URL=http://<nebius-instance-host>:8080/v1
QWEN_MODEL=Qwen/Qwen3-VL-30B-A3B-Instruct-FP8
ROBOFLOW_API_KEY=your_roboflow_key_here
# Storage
UPLOAD_STORAGE_PATH=./uploads
DATABASE_URL=sqlite:///./safety_sentinel.db
# Camera / RTSP emulation
DEMO_RTSP_URL=rtsp://localhost:8554/worksite-demo
OPENCV_FFMPEG_CAPTURE_OPTIONS=rtsp_transport;tcp
# Vercel Blob (only used when VERCEL=1; falls back to local disk otherwise)
BLOB_READ_WRITE_TOKEN=your_vercel_blob_rw_token_here
# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000

Note: API keys can be omitted individually. The default `auto` provider tries
Roboflow first, then Qwen, then deterministic mock detections. Roboflow requires
an API key to `serverless.roboflow.com` for the
personal-protective-equipment-combined-model/8. Qwen requires both
`QWEN_API_KEY` and `QWEN_BASE_URL` to be considered configured.

The Roboflow integration calls the hosted REST API directly with `requests`.
This avoids the `inference-sdk` dependency tree, which pulls in large packages
such as `supervision`, `matplotlib`, `scipy`, and the GUI `opencv-python`
package. The backend keeps `opencv-python-headless` as the only OpenCV
dependency for video frame extraction, which keeps Vercel's Python function
bundle smaller and avoids local path dependency resolution during deploy.
Do not add local path package dependencies (for example `./vendor/...`) to
`backend/requirements.txt`; Vercel resolves backend dependencies from the
service root and can turn those into invalid nested paths during `uv lock`.

Vercel deployment uses the root `vercel.json` services config:

* `frontend` serves the Next.js app at `/`
* `backend` serves FastAPI at `/_/backend`

In local development, the frontend calls `http://localhost:8000` by default. In
production, it calls `/_/backend` unless `NEXT_PUBLIC_API_URL` is set. When the
backend detects `VERCEL=1`, SQLite and upload defaults move to `/tmp` because the
deployed runtime filesystem is ephemeral and only `/tmp` is writable.

Container-Host Deployment (for live cameras)

Continuous RTSP monitoring cannot run on Vercel — serverless functions are
request-scoped, so there is no always-on process to poll a feed, hold an RTSP
connection, or run ffmpeg. To run the camera feature deployed, the backend moves
to a persistent container host (Fly.io / Render / Railway / a VM) packaged with
the emulator via the root `docker-compose.yml`:

* `mediamtx` — RTSP server (the listener `ffmpeg -f rtsp` requires)
* `ffmpeg` — loops `emulator/media/demo-worksite.mp4` into `rtsp://mediamtx:8554/worksite-demo`
* `backend` — FastAPI + the camera monitor, reaching the feed over the private network

Because the three services share a private network, the RTSP stream is never
publicly exposed — only the API on `:8000` is. The Vercel frontend stays as-is;
point its `NEXT_PUBLIC_API_URL` at the container host's public API URL. The
backend Dockerfile (`backend/Dockerfile`) sets `DATABASE_URL` and
`UPLOAD_STORAGE_PATH` to a mounted volume (`/data`) so the DB and captured frames
persist across restarts.

Non-Goals

The MVP intentionally avoids:

* Facial recognition
* Employee identity matching
* Real-time surveillance
* Real alert delivery
* Automated disciplinary workflows
* Production access control
* Legal/compliance guarantees

Future Architecture Extensions

* Live camera ingestion — basic RTSP ingestion shipped (see §12); next: many
  cameras, per-camera workers, reconnection/backoff, and HLS/WebRTC live preview
* Authenticated camera ingestion (API-key issuance/rotation; clip POST endpoint)
* Real-time stream processing — currently interval snapshot capture; next:
  continuous decoding and per-frame streaming
* Multi-site dashboards
* Zone/camera admin UI (zones and cameras are seeded today)
* Configurable repeated-violation thresholds
* Role-based access control

Zone-specific PPE policies and repeated-zone violation detection are implemented;
see the Rule Engine, Analytics Layer sections and
[ZONE_CAMERA_PLAN.md](ZONE_CAMERA_PLAN.md).
* Human review workflows
* Integrations with Slack, Teams, email, and SMS
* Integration with EHS systems
* Custom model fine-tuning per worksite
* Edge deployment for on-premise inference
* Audit-ready PDF exports
