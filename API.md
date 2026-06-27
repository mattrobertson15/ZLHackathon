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
    "fileUrl": "/uploads/warehouse-floor.jpg",
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
      "fileUrl": "/uploads/warehouse-floor.jpg",
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
    "fileUrl": "/uploads/warehouse-floor.jpg",
    "uploadedAt": "2026-06-27T14:30:00Z",
    "status": "processed"
  }
}

Inference

POST /uploads/{upload_id}/analyze

Run PPE analysis on an uploaded image or video.

Request

{
  "modelProvider": "qwen_vision",
  "createEvents": true,
  "createAlerts": true
}

Response

{
  "uploadId": "upl_123",
  "status": "processed",
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
      "source": "qwen_vision",
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