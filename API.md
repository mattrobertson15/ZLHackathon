API.md

Safety Sentinel API Specification

This document defines the initial FastAPI backend endpoints for the Safety Sentinel MVP.

The API supports:

* Uploading images and videos
* Running PPE detection
* Creating safety events
* Viewing analytics
* Viewing mock alerts
* Generating AI safety summaries
* Frontend-generated markdown safety report downloads from dashboard and summaries

Base URL

http://localhost:8000

When deployed through the root `vercel.json` services config, the FastAPI
backend is routed under the same Vercel domain at:

/_/backend

The frontend defaults to `http://localhost:8000` during local development and
`/_/backend` in production unless `NEXT_PUBLIC_API_URL` is set.

Note: the `/uploads` path is reserved for the upload API resource
(`POST /uploads`, `GET /uploads`, `GET /uploads/{upload_id}`). To avoid
routing collisions between the resource path and static file serving,
uploaded files are served from `/media/{fileName}` instead. `fileUrl` in
upload responses reflects this, e.g. `/media/warehouse-floor.jpg`.

When the backend is deployed to Vercel with `BLOB_READ_WRITE_TOKEN` set,
uploads go to Vercel Blob instead (Vercel's function filesystem is ephemeral,
so local disk can't be trusted to survive between requests). In that case
`fileUrl` is an absolute Vercel Blob CDN URL instead of a `/media/...` path —
clients should use `fileUrl` as-is rather than assuming it's always relative
to the API base URL. See [ARCHITECTURE.md](ARCHITECTURE.md#static-file-serving)
for details.

Core Resources

Zone
Camera
Upload
DetectionResult
SafetyEvent
AlertRecord
SafetySummary

Zone and Camera form the shared location schema; see
[ZONE_CAMERA_PLAN.md](ZONE_CAMERA_PLAN.md) for the combined zone/camera design.

Health Check

GET /health

Returns backend health status.

Response

{
  "status": "ok",
  "service": "safety-sentinel-api"
}

Uploads

POST /uploads

Upload an image or video for analysis.

Request

Content type:

multipart/form-data

Fields:

file: image or video file

Optional fields:

zoneId: string         (a zone id from GET /zones; sets the upload's zone)
cameraId: string       (a camera id; the upload inherits the camera's zone and
                        overrides zoneId if both are sent)
locationLabel: string  (legacy free-text fallback)
notes: string

If `zoneId`/`cameraId` reference an unknown zone/camera, the request fails with
`400 ZONE_NOT_FOUND` / `400 CAMERA_NOT_FOUND`.

Response

{
  "upload": {
    "id": "upl_123",
    "fileName": "warehouse-floor.jpg",
    "fileType": "image",
    "fileUrl": "/media/warehouse-floor.jpg",
    "locationLabel": null,
    "zoneId": "loading-dock",
    "cameraId": null,
    "zoneDisplayName": "Loading Dock",
    "sourceType": "upload",
    "notes": null,
    "uploadedAt": "2026-06-27T14:30:00Z",
    "status": "uploaded"
  }
}

The `zoneDisplayName` field is a convenience resolved from `zoneId` so clients
can label uploads without a second request. Upload objects carry these same
fields wherever they are embedded (events, demo scenario, etc.).

`sourceType` is `"upload"` for direct file uploads and `"camera"` for rows
created by the live camera monitor (with `cameraId` set to the originating
camera). See [Cameras](#cameras).

GET /uploads

List recent uploads.

Response

{
  "uploads": [
    {
      "id": "upl_123",
      "fileName": "warehouse-floor.jpg",
      "fileType": "image",
      "fileUrl": "/media/warehouse-floor.jpg",
      "uploadedAt": "2026-06-27T14:30:00Z",
      "status": "processed"
    }
  ]
}

GET /uploads/{upload_id}

Get a single upload and its processing status.

Response

{
  "upload": {
    "id": "upl_123",
    "fileName": "warehouse-floor.jpg",
    "fileType": "image",
    "fileUrl": "/media/warehouse-floor.jpg",
    "uploadedAt": "2026-06-27T14:30:00Z",
    "status": "processed"
  }
}

Zones

GET /zones

List all zones and their PPE policies. Used by the upload zone picker.

Response

{
  "zones": [
    {
      "id": "loading-dock",
      "displayName": "Loading Dock",
      "requiredPpe": ["vest"],
      "severityOverrides": { "no_vest": "high" },
      "createdAt": "2026-06-27T14:30:00Z"
    }
  ]
}

GET /zones/{zone_id}

Get a single zone. Returns `404 ZONE_NOT_FOUND` if missing.

Cameras

A camera is a zone-assigned location record that can optionally be a live RTSP
feed. Cameras without an `rtspUrl` are pure location records (e.g. the seeded
demo cameras) used so uploads can inherit a zone. When `rtspUrl` is set, the
background monitor can capture frames on an interval and raise events; each
capture is recorded as a `camera`-sourced Upload that **inherits the camera's
zone**, so live events get the same zone-aware rules and repeated-violation
detection as uploads. See
[ARCHITECTURE.md](ARCHITECTURE.md#12-camera--rtsp-ingestion-layer) and
[ZONE_CAMERA_PLAN.md](ZONE_CAMERA_PLAN.md).

Note: the live monitor only runs on a persistent host, not Vercel.

Camera object

{
  "id": "cam-02",
  "displayName": "Dock Camera North",
  "zoneId": "loading-dock",
  "status": "active",                  // registry state: active | inactive
  "createdAt": "2026-06-27T14:30:00Z",
  "rtspUrl": "rtsp://mediamtx:8554/worksite-demo",  // null for location-only cameras
  "streamStatus": "live",              // feed connectivity: offline | live | error
  "monitoring": true,
  "captureIntervalSeconds": 15,
  "lastCaptureAt": "2026-06-27T16:40:05Z",
  "lastError": null,
  "recentEventCount": 7
}

POST /cameras

Register a camera. `rtspUrl` is optional (omit for a location-only camera);
`zoneId` is optional but, if given, must reference an existing zone.

Request

{
  "displayName": "Loading Dock Camera",
  "rtspUrl": "rtsp://mediamtx:8554/worksite-demo",  // optional
  "zoneId": "loading-dock",                          // optional
  "captureIntervalSeconds": 15                        // optional, default 15, min 1
}

Response: { "camera": { ...Camera } }

Errors: INVALID_INTERVAL (< 1), ZONE_NOT_FOUND (unknown zoneId).

Tip: use `1`–`2` seconds for a snappy live demo (e.g. a walk-by); larger values
reduce inference load for always-on monitoring.

POST /cameras/test-stream

Probe an RTSP URL by grabbing a single frame, without registering a camera. Lets
the user confirm a feed (e.g. a phone pushed to the relay) is reachable from the
backend before starting monitoring. Always returns 200; the `status` field
reports the outcome.

Request

{
  "rtspUrl": "rtsp://safety-sentinel-relay.internal:8554/phone-demo"
}

Response (success)

{
  "status": "connected",
  "width": 1280,
  "height": 720,
  "message": "Stream connected successfully."
}

Response (failure)

{
  "status": "failed",
  "message": "Unable to read a frame from the RTSP stream. Make sure the stream is live and reachable from the backend (for a phone, push to the relay rather than exposing the phone's LAN address)."
}

GET /cameras

List all cameras (seeded location cameras + any registered RTSP feeds).

Response: { "cameras": [ { ...Camera } ] }

GET /cameras/{camera_id}

Get a single camera. Returns `404 CAMERA_NOT_FOUND` if missing.

Response: { "camera": { ...Camera } }

GET /cameras/{camera_id}/detail

Camera plus its recent captures and events (for the camera UI).

Response

{
  "camera": { ...Camera },
  "captures": [ { ...Upload } ],     // recent camera-sourced uploads (sourceType="camera")
  "events": [ { ...SafetyEvent } ]   // recent events from this camera
}

POST /cameras/{camera_id}/start

Enable continuous monitoring and run one immediate capture. Sets `streamStatus`
to `live` on success or `error` (with `lastError`) if the stream can't be
reached. Requires the camera to have an `rtspUrl`.

Response: { "camera": { ...Camera } }

Errors: NO_RTSP_URL (location-only camera), CAMERA_NOT_FOUND.

POST /cameras/{camera_id}/stop

Disable monitoring; sets `streamStatus` to `offline`.

Response: { "camera": { ...Camera } }

POST /cameras/{camera_id}/capture

Capture and analyze once, immediately (independent of the monitoring loop).

Response

{
  "camera": { ...Camera },
  "detections": 4,
  "events": [ { ...SafetyEvent } ]
}

Errors: NO_RTSP_URL, CAPTURE_FAILED (502) if the stream can't be opened/read.

GET /cameras/{camera_id}/snapshot

Returns the most recent captured frame as `image/jpeg` (binary). The Cameras
page polls this with a cache-busting query param for a near-live preview.

Errors: NO_SNAPSHOT (404) if no capture exists yet.

DELETE /cameras/{camera_id}

Remove a camera. Its previously created events are left intact.

Response: { "status": "success", "message": "Camera 'cam-02' removed." }

Inference

POST /uploads/{upload_id}/analyze

Run PPE analysis on an uploaded image or video.

The `modelProvider` controls inference routing:

* `auto` (default): Roboflow first, then Qwen Vision, then deterministic mock detections.
* `roboflow`: Roboflow PPE model, with mock fallback if Roboflow fails.
* `qwen_vision`: Qwen Vision structured output, with mock fallback if Qwen fails.
* `manual_mock`: Deterministic mock detections for demo reliability.
* `compare`: Runs Roboflow and Qwen side by side and returns an agreement report.

Roboflow is the preferred detector for operational safety events because it is
trained as an object-detection model for PPE classes. Qwen Vision is available
as an experimental comparison path. In `compare` mode, only the primary source
is persisted and passed into the rule engine; comparison detections are returned
for evaluation/reporting only. When `createAlerts` is true (default), mock
alerts are generated from the created safety events per the routing rule in
[ARCHITECTURE.md#mock-alert-center](ARCHITECTURE.md); `positive_observation`
events never produce an alert, so `alerts` may be shorter than `events` or empty.

If the upload has a `zoneId`, its zone is resolved and passed to the rule engine:
only PPE the zone requires produces events, and violation severities may be
escalated by the zone's overrides (see
[ZONE_CAMERA_PLAN.md](ZONE_CAMERA_PLAN.md)). After events are persisted, a newly
created violation that pushes its zone group to the weekly repeated-violation
threshold (3) adds one `repeated_violation` alert to `alerts`.

Request

{
  "modelProvider": "auto",
  "createEvents": true,
  "createAlerts": true
}

Response

{
  "uploadId": "upl_123",
  "status": "processed",
  "modelProvider": "auto",
  "primarySource": "roboflow",
  "detections": [
    {
      "id": "det_001",
      "uploadId": "upl_123",
      "frameTimestamp": null,
      "label": "person",
      "confidence": 0.94,
      "boundingBox": {
        "x": 120,
        "y": 80,
        "width": 220,
        "height": 520
      },
      "source": "roboflow",
      "createdAt": "2026-06-27T14:31:00Z"
    },
    {
      "id": "det_002",
      "uploadId": "upl_123",
      "frameTimestamp": null,
      "label": "no_helmet",
      "confidence": 0.88,
      "boundingBox": {
        "x": 150,
        "y": 85,
        "width": 80,
        "height": 70
      },
      "source": "roboflow",
      "createdAt": "2026-06-27T14:31:00Z"
    }
  ],
  "events": [
    {
      "id": "evt_001",
      "uploadId": "upl_123",
      "eventType": "ppe_violation",
      "violationType": "no_helmet",
      "severity": "high",
      "confidence": 0.88,
      "status": "open",
      "suggestedAction": "Supervisor review recommended. Helmet appears missing.",
      "createdAt": "2026-06-27T14:31:02Z"
    }
  ],
  "alerts": [
    {
      "id": "alrt_001",
      "safetyEventId": "evt_001",
      "alertType": "supervisor_review",
      "title": "Missing Helmet Detected",
      "message": "A high-severity PPE violation was detected. Supervisor review is recommended.",
      "status": "draft",
      "createdAt": "2026-06-27T14:31:03Z"
    }
  ]
}

Compare response extension

When `modelProvider` is `compare`, the normal response also includes a
`comparison` object. `detections`, `events`, and `alerts` still represent the
primary source only.

{
  "uploadId": "upl_123",
  "status": "processed",
  "modelProvider": "compare",
  "primarySource": "roboflow",
  "detections": [],
  "events": [],
  "alerts": [],
  "comparison": {
    "roboflow": {
      "provider": "roboflow",
      "source": "roboflow",
      "available": true,
      "error": null,
      "detections": []
    },
    "qwen": {
      "provider": "qwen_vision",
      "source": "roboflow",
      "available": true,
      "error": null,
      "detections": []
    },
    "agreement": {
      "matchingLabels": ["person", "helmet"],
      "roboflowOnly": ["no_vest"],
      "qwenOnly": [],
      "conflicts": [],
      "frames": [
        {
          "frameTimestamp": null,
          "matchingLabels": ["person", "helmet"],
          "roboflowOnly": ["no_vest"],
          "qwenOnly": []
        }
      ]
    }
  }
}

Detections

GET /uploads/{upload_id}/detections

Get all detections for an upload.

Response

{
  "uploadId": "upl_123",
  "detections": [
    {
      "id": "det_001",
      "uploadId": "upl_123",
      "frameTimestamp": null,
      "label": "person",
      "confidence": 0.94,
      "boundingBox": {
        "x": 120,
        "y": 80,
        "width": 220,
        "height": 520
      },
      "source": "qwen_vision",
      "createdAt": "2026-06-27T14:31:00Z"
    }
  ]
}

Safety Events

GET /events

List safety events.

Query Parameters

status?: open | reviewed | dismissed | resolved
eventType?: positive_observation | ppe_violation | uncertain_review
violationType?: no_helmet | no_vest
severity?: low | medium | high
limit?: number

Response

{
  "events": [
    {
      "id": "evt_001",
      "uploadId": "upl_123",
      "eventType": "ppe_violation",
      "violationType": "no_helmet",
      "severity": "high",
      "confidence": 0.88,
      "status": "open",
      "suggestedAction": "Supervisor review recommended. Helmet appears missing.",
      "createdAt": "2026-06-27T14:31:02Z",
      "upload": {
        "id": "upl_123",
        "fileName": "warehouse-floor.jpg",
        "fileType": "image",
        "fileUrl": "/media/warehouse-floor.jpg",
        "locationLabel": "Warehouse A",
        "notes": "Forklift aisle review",
        "uploadedAt": "2026-06-27T14:30:00Z",
        "status": "processed"
      }
    }
  ]
}

GET /events/{event_id}

Get one safety event.

Response

{
  "event": {
    "id": "evt_001",
    "uploadId": "upl_123",
    "eventType": "ppe_violation",
    "violationType": "no_helmet",
    "severity": "high",
    "confidence": 0.88,
    "status": "open",
    "suggestedAction": "Supervisor review recommended. Helmet appears missing.",
    "createdAt": "2026-06-27T14:31:02Z",
    "upload": {
      "id": "upl_123",
      "fileName": "warehouse-floor.jpg",
      "fileType": "image",
      "fileUrl": "/media/warehouse-floor.jpg",
      "locationLabel": "Warehouse A",
      "notes": "Forklift aisle review",
      "uploadedAt": "2026-06-27T14:30:00Z",
      "status": "processed"
    }
  }
}

PATCH /events/{event_id}

Update event review status.

Request

{
  "status": "reviewed"
}

Response

{
  "event": {
    "id": "evt_001",
    "status": "reviewed"
  }
}

Alerts

GET /alerts

List mock alerts.

Query Parameters

status?: draft | queued | sent_mock | dismissed
alertType?: supervisor_review | coaching_reminder | manual_review | repeated_violation
limit?: number

Response

{
  "alerts": [
    {
      "id": "alrt_001",
      "safetyEventId": "evt_001",
      "alertType": "supervisor_review",
      "title": "Missing Helmet Detected",
      "message": "A high-severity PPE violation was detected. Supervisor review is recommended.",
      "status": "draft",
      "createdAt": "2026-06-27T14:31:03Z"
    }
  ]
}

PATCH /alerts/{alert_id}

Update mock alert status.

Request

{
  "status": "sent_mock"
}

Response

{
  "alert": {
    "id": "alrt_001",
    "status": "sent_mock"
  }
}

Demo Scenario

POST /admin/demo-scenario

Load a repeatable warehouse shift demo into the same tables used by real uploads,
detections, safety events, alerts, and analytics. This endpoint is intended for
hackathon walkthrough reliability. It replaces prior records for the built-in
demo upload IDs, but does not clear unrelated user-created data.

Response

{
  "status": "success",
  "scenario": "warehouse_shift_review",
  "message": "Warehouse shift demo scenario loaded.",
  "uploads": [
    {
      "id": "demo_loading_dock",
      "fileName": "Loading Dock PPE Review.jpg",
      "fileType": "image",
      "fileUrl": "/media/002823.jpg",
      "locationLabel": "Loading Dock",
      "notes": "Demo scenario: morning inbound freight with missing helmet and vest observations.",
      "uploadedAt": "2026-06-27T14:30:00Z",
      "status": "processed"
    }
  ],
  "counts": {
    "uploads": 7,
    "detections": 16,
    "events": 8,
    "alerts": 6
  }
}

The demo scenario seeds zone-tagged uploads that exercise both zone-aware rules
(a `no_vest` at the Loading Dock is a high-severity violation, the same
detection on the General Floor is suppressed) and repeated-zone detection (three
Loading Dock `no_vest` violations produce one `repeated_violation` alert).

POST /admin/reset

Deletes all `SafetyEvent`, `AlertRecord`, and `DetectionResult` rows. Triggered
manually by the "Reset Incidents" button on the dashboard; data is never cleared
automatically and persists in SQLite until this endpoint is called.

Response

{
  "status": "success",
  "message": "All incidents reset successfully"
}

Error — HTTP 500 with `{ "status": "error", "message": "<detail>" }` if the
delete or commit fails.

Analytics

GET /analytics/overview

Get dashboard overview metrics.

Query Parameters

period?: daily | weekly | monthly | all

Response

{
  "period": "weekly",
  "compliancePercentage": 87,
  "totalObservations": 248,
  "totalViolations": 32,
  "positiveObservations": 216,
  "openEvents": 7,
  "severityBreakdown": {
    "low": 4,
    "medium": 21,
    "high": 7
  },
  "violationBreakdown": {
    "no_helmet": 11,
    "no_vest": 21
  },
  "repeatedViolations": [
    {
      "zoneLabel": "Loading Dock",
      "violationType": "no_vest",
      "count": 3,
      "distinctUploadCount": 3,
      "severity": "high",
      "latestEventId": "evt_123",
      "firstSeenAt": "2026-06-22T08:00:00Z",
      "lastSeenAt": "2026-06-26T18:00:00Z",
      "message": "Loading Dock has 3 no-vest violations in the past week."
    }
  ]
}

`repeatedViolations` groups `ppe_violation` events over a rolling 7-day window by
resolved location (zone, falling back to `locationLabel`) and violation type,
returning groups at or above the threshold (3). It is always computed on the
weekly window regardless of `period`. No employee identity is used. See
[ZONE_CAMERA_PLAN.md](ZONE_CAMERA_PLAN.md).

GET /analytics/trends

Get compliance and violation trends over time.

Query Parameters

period?: daily | weekly | monthly

Response

{
  "period": "daily",
  "points": [
    {
      "date": "2026-06-25",
      "compliancePercentage": 82,
      "totalViolations": 14,
      "noHelmet": 5,
      "noVest": 9
    },
    {
      "date": "2026-06-26",
      "compliancePercentage": 89,
      "totalViolations": 8,
      "noHelmet": 3,
      "noVest": 5
    }
  ]
}

Summaries

POST /summaries/generate

Generate an AI safety summary for a selected period.

Request

{
  "period": "weekly",
  "startDate": "2026-06-22",
  "endDate": "2026-06-28"
}

Response

{
  "summary": {
    "id": "sum_001",
    "period": "weekly",
    "startDate": "2026-06-22",
    "endDate": "2026-06-28",
    "executiveSummary": "This week, Safety Sentinel analyzed 248 visual safety observations. Overall PPE compliance was 87%. The most common issue was missing safety vests, followed by missing helmets.",
    "topViolations": "Missing safety vests were the most common issue, followed by missing helmets.",
    "trendAnalysis": "Compliance was stable compared with the previous period.",
    "recommendedActions": "Reinforce vest requirements during pre-shift briefings.\nReview PPE signage near high-traffic work zones.\nRoute high-severity helmet violations for supervisor review.",
    "createdAt": "2026-06-27T15:00:00Z"
  }
}

GET /summaries

List generated summaries.

Query Parameters

period?: daily | weekly | monthly
limit?: number

Response

{
  "summaries": [
    {
      "id": "sum_001",
      "period": "weekly",
      "startDate": "2026-06-22",
      "endDate": "2026-06-28",
      "executiveSummary": "This week, Safety Sentinel analyzed 248 visual safety observations...",
      "topViolations": "Missing safety vests were the most common issue, followed by missing helmets.",
      "trendAnalysis": "Compliance was stable compared with the previous period.",
      "recommendedActions": "Reinforce vest requirements during pre-shift briefings.\nReview PPE signage near high-traffic work zones.",
      "createdAt": "2026-06-27T15:00:00Z"
    }
  ]
}

GET /summaries/{summary_id}

Get one generated summary.

Response

{
  "summary": {
    "id": "sum_001",
    "period": "weekly",
    "startDate": "2026-06-22",
    "endDate": "2026-06-28",
    "executiveSummary": "This week, Safety Sentinel analyzed 248 visual safety observations...",
    "topViolations": "Missing safety vests were the most common issue, followed by missing helmets.",
    "trendAnalysis": "Compliance was stable compared with the previous period.",
    "recommendedActions": "Reinforce vest requirements during pre-shift briefings.\nReview PPE signage near high-traffic work zones.",
    "createdAt": "2026-06-27T15:00:00Z"
  }
}

Report Downloads

The current MVP exports reports in the frontend without a dedicated backend
endpoint. The Dashboard page builds a markdown report from `GET
/analytics/overview` and `GET /analytics/trends`; the Summaries page builds a
markdown report from each `SafetySummary` returned by `GET /summaries` or `POST
/summaries/generate`.

Downloaded files use the `.md` extension and include manager-ready narrative
sections or dashboard KPI tables. A future backend endpoint could add signed PDF
generation, but that is intentionally out of scope for the hackathon MVP.

Suggested MVP Endpoint Priority

Build endpoints in this order:

1. GET /health
2. POST /uploads
3. POST /uploads/{upload_id}/analyze
4. GET /uploads/{upload_id}/detections
5. GET /events
6. GET /analytics/overview
7. GET /analytics/trends
8. GET /alerts
9. POST /summaries/generate
10. GET /summaries
11. POST /admin/demo-scenario

Error Response Format

Use a consistent error format:

{
  "error": {
    "code": "UPLOAD_NOT_FOUND",
    "message": "No upload found for the provided upload_id."
  }
}

Common Error Codes

INVALID_FILE_TYPE
UPLOAD_NOT_FOUND
ZONE_NOT_FOUND
CAMERA_NOT_FOUND
INFERENCE_FAILED
EVENT_NOT_FOUND
ALERT_NOT_FOUND
SUMMARY_NOT_FOUND
SUMMARY_GENERATION_FAILED
INVALID_INTERVAL
NO_RTSP_URL
CAPTURE_FAILED
NO_SNAPSHOT

Notes for Hackathon Implementation

For the MVP, it is acceptable to mock some data paths while preserving the final API shape.

Recommended shortcuts:

* Store files locally.
* Use SQLite or in-memory storage.
* Mock alerts instead of sending real messages.
* Use a small set of sample uploads.
* Fall back to deterministic mock detections if model integration breaks.
* Make the dashboard work even with seeded sample events.
