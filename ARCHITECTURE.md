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

2. **Qwen Vision** (if `QWEN_API_KEY` is set)
   - Real Qwen client via `dashscope.aliyuncs.com`
   - Experimental structured output for person, helmet, no_helmet, vest, no_vest
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

Future Rules

* Zone-specific PPE requirements
* Confidence threshold overrides
* Repeated violation detection
* Location-aware escalation
* Shift-level trend analysis
* Supervisor approval workflows

6. Safety Event Store

Safety events are the core operational data object of the system.

The app should store every safety-relevant observation as a structured event.

type SafetyEvent = {
  id: string;
  uploadId: string;
  eventType: "positive_observation" | "ppe_violation" | "uncertain_review";
  violationType?: "no_helmet" | "no_vest";
  severity: "low" | "medium" | "high";
  confidence: number;
  status: "open" | "reviewed" | "dismissed" | "resolved";
  statusUpdatedAt: string | null;
  reviewNote?: string | null;
  suggestedAction: string;
  createdAt: string;
};

Human Review Workflow

Events move through `status` via `PATCH /events/{event_id}` (see
[API.md#safety-events](API.md)). Three reviewer actions cover the lifecycle:

* **Mark reviewed** — a supervisor has seen the event; no note needed.
* **Dismiss** — the event is a false positive; `reviewNote` should capture why
  (e.g. "shadow on hard hat").
* **Resolve** — the underlying violation was addressed; `reviewNote` should
  capture how (e.g. "spoke with worker, vest now worn").

`status_updated_at` is refreshed on every transition so the UI can show how
long an event has sat in its current status. The frontend events page
(`frontend/app/app/events/page.tsx`) and `EventTable` component expose these
as one-click row actions (with an optional note prompt for dismiss/resolve)
so triage doesn't require opening the detail panel first. The dashboard's
Review Status card (`ReviewStatusCard`, fed by `statusBreakdown` from
`GET /analytics/overview`) gives an at-a-glance view of the review queue and
links into `/app/events?status=...` for drill-in.

7. Mock Alert Center

The alert center demonstrates how Safety Sentinel could route safety events to supervisors or approved stakeholders.

The MVP should not send real alerts. Instead, it should create mock alert records stored and displayed inside the app.

type AlertRecord = {
  id: string;
  safetyEventId: string;
  alertType: "supervisor_review" | "coaching_reminder" | "manual_review";
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
  `totalViolations`. `statusBreakdown` (`open`/`reviewed`/`dismissed`/`resolved`
  counts) is computed over all events in the window and powers the dashboard's
  Review Status widget — see "Human Review Workflow" below.
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
* Key observations
* Top violation types
* Trend interpretation
* Recommended corrective actions
* Coaching-oriented safety reminders

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
      summaries.py        [pending: Phase 7]
    services/
      vision_service.py   [done — Roboflow-first auto routing, Qwen comparison, mock fallback]
      detection_parser.py [done]
      rule_engine.py       [done]
      media_service.py     [pending: not yet broken out, frame extraction lives in utils/video_frames.py]
      analytics_service.py [done]
      alert_service.py     [done]
      summary_service.py   [pending: Phase 7]
    models/
      upload.py          [done]
      detection_result.py [done]
      safety_event.py     [done]
      alert_record.py      [done]
      safety_summary.py    [pending: Phase 7]
    db/
      database.py
      repositories.py
    utils/
      ids.py
      timestamps.py
      video_frames.py

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
    chart-utils.ts

Processing Flow

Image Upload Flow

1. User uploads image.
2. Frontend sends image to FastAPI.
3. Backend stores file and creates Upload record.
4. Backend sends image to vision model.
5. Vision model returns detections.
6. Detection parser normalizes results.
7. Rule engine creates safety events.
8. Alert service creates mock alerts when needed.
9. Backend returns upload, detections, events, and alerts.
10. Frontend displays annotated image and safety results.

Video Upload Flow

1. User uploads video.
2. Backend stores video and creates Upload record.
3. Backend samples frames from the video.
4. Each sampled frame is sent to vision model.
5. Detections are normalized with frame timestamps.
6. Rule engine creates safety events.
7. Similar events may be grouped or deduplicated.
8. Alert service creates mock alerts.
9. Frontend displays summary results and key frames.

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
QWEN_API_KEY=your_qwen_key_here
ROBOFLOW_API_KEY=your_roboflow_key_here
# Storage
UPLOAD_STORAGE_PATH=./uploads
DATABASE_URL=sqlite:///./safety_sentinel.db
# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000

Note: API keys can be omitted individually. The default `auto` provider tries
Roboflow first, then Qwen, then deterministic mock detections. Roboflow requires
an API key to `serverless.roboflow.com` for the
personal-protective-equipment-combined-model/8.

`inference-sdk` (the Roboflow client) unconditionally depends on `supervision`
(pulls in matplotlib + scipy, ~125MB installed) and `opencv-python` (the GUI/Qt
build, which can fail to import on minimal Linux runtimes missing `libGL`),
even though this project only calls `client.infer()` with a single image path —
a code path that never touches either package's actual functionality. Vercel's
Python function has a 500MB size cap, and the real dependency tree blew past it.
`backend/vendor/supervision_stub` and `backend/vendor/opencv_python_stub` are
minimal local packages that satisfy pip's dependency resolution for those two
names without installing the real heavy/GUI packages; `opencv-python-headless`
(already a direct dependency) remains the sole real provider of `cv2`. See
`backend/requirements.txt` for how they're wired in.

Vercel deployment uses the root `vercel.json` services config:

* `frontend` serves the Next.js app at `/`
* `backend` serves FastAPI at `/_/backend`

In local development, the frontend calls `http://localhost:8000` by default. In
production, it calls `/_/backend` unless `NEXT_PUBLIC_API_URL` is set. When the
backend detects `VERCEL=1`, SQLite and upload defaults move to `/tmp` because the
deployed runtime filesystem is ephemeral and only `/tmp` is writable.

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

* Live camera ingestion
* Real-time stream processing
* Multi-site dashboards
* Zone-specific PPE policies
* Role-based access control
* Reviewer identity tracking and audit trail for review actions (the MVP
  review workflow — see "Human Review Workflow" in section 6 — has no
  authentication, so it can't attribute who reviewed/dismissed/resolved an
  event)
* Integrations with Slack, Teams, email, and SMS
* Integration with EHS systems
* Custom model fine-tuning per worksite
* Edge deployment for on-premise inference
* Audit-ready PDF exports
