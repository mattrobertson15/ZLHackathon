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

Core Resources

Upload
DetectionResult
SafetyEvent
AlertRecord
SafetySummary

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

locationLabel: string
notes: string

Response

{
  "upload": {
    "id": "upl_123",
    "fileName": "warehouse-floor.jpg",
    "fileType": "image",
    "fileUrl": "/media/warehouse-floor.jpg",
    "uploadedAt": "2026-06-27T14:30:00Z",
    "status": "uploaded"
  }
}

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

GET /uploads/{upload_id}/results

Read-only snapshot of everything generated from one upload: detections,
safety events, and alerts. Unlike `POST /uploads/{upload_id}/analyze`, this
endpoint never runs inference and has no side effects, so it is safe to call
repeatedly (e.g. on page load or refresh). This is the endpoint the
`/app/results/[uploadId]` frontend page uses to render the full
upload -> detections -> events -> alerts story in one fetch.

Response

{
  "upload": {
    "id": "upl_123",
    "fileName": "warehouse-floor.jpg",
    "fileType": "image",
    "fileUrl": "/media/warehouse-floor.jpg",
    "uploadedAt": "2026-06-27T14:30:00Z",
    "status": "processed"
  },
  "detections": [
    {
      "id": "det_001",
      "uploadId": "upl_123",
      "frameTimestamp": null,
      "label": "no_helmet",
      "confidence": 0.88,
      "boundingBox": { "x": 150, "y": 85, "width": 80, "height": 70 },
      "frameUrl": "/media/warehouse-floor.jpg",
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

Errors

404 UPLOAD_NOT_FOUND if no upload exists for the given id.

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
      "frameUrl": null,
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
      "frameUrl": null,
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
      "frameUrl": null,
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
      "createdAt": "2026-06-27T14:31:02Z"
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
    "createdAt": "2026-06-27T14:31:02Z"
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
alertType?: supervisor_review | coaching_reminder | manual_review
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
    "uploads": 3,
    "detections": 9,
    "events": 6,
    "alerts": 4
  }
}

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
  }
}

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
    "compliancePercentage": 87,
    "totalViolations": 32,
    "topViolationTypes": ["no_vest", "no_helmet"],
    "summaryText": "This week, Safety Sentinel analyzed 248 visual safety observations. Overall PPE compliance was 87%. The most common issue was missing safety vests, followed by missing helmets.",
    "recommendedActions": [
      "Reinforce vest requirements during pre-shift briefings.",
      "Review PPE signage near high-traffic work zones.",
      "Route high-severity helmet violations for supervisor review."
    ],
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
      "compliancePercentage": 87,
      "totalViolations": 32,
      "topViolationTypes": ["no_vest", "no_helmet"],
      "summaryText": "This week, Safety Sentinel analyzed 248 visual safety observations...",
      "recommendedActions": [
        "Reinforce vest requirements during pre-shift briefings.",
        "Review PPE signage near high-traffic work zones."
      ],
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
    "compliancePercentage": 87,
    "totalViolations": 32,
    "topViolationTypes": ["no_vest", "no_helmet"],
    "summaryText": "This week, Safety Sentinel analyzed 248 visual safety observations...",
    "recommendedActions": [
      "Reinforce vest requirements during pre-shift briefings.",
      "Review PPE signage near high-traffic work zones."
    ],
    "createdAt": "2026-06-27T15:00:00Z"
  }
}

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
INFERENCE_FAILED
EVENT_NOT_FOUND
ALERT_NOT_FOUND
SUMMARY_NOT_FOUND
SUMMARY_GENERATION_FAILED

Notes for Hackathon Implementation

For the MVP, it is acceptable to mock some data paths while preserving the final API shape.

Recommended shortcuts:

* Store files locally.
* Use SQLite or in-memory storage.
* Mock alerts instead of sending real messages.
* Use a small set of sample uploads.
* Fall back to deterministic mock detections if model integration breaks.
* Make the dashboard work even with seeded sample events.
