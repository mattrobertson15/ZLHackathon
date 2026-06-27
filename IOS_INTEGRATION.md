# iOS Integration Contract — Safety Sentinel

Integration reference for a native Swift app that fires local notifications on `no_helmet` violations detected by the Safety Sentinel backend.

---

## 1. Backend Access

**Base URL:** `https://safety-sentinel-api.fly.dev`

- Publicly reachable over the internet (Fly.io, always-on, HTTPS enforced)
- **No authentication** — no API keys, no bearer tokens, no headers required
- CORS is irrelevant for native iOS (browser-only concern)

---

## 2. Getting Detections in Real Time

No WebSocket or SSE stream exists. **Poll REST.**

### Recommended endpoint

```
GET https://safety-sentinel-api.fly.dev/events?violationType=no_helmet&status=open
```

**Supported query params (all optional):**

| Param | Values | Purpose |
|---|---|---|
| `violationType` | `no_helmet` \| `no_vest` | Filter to helmet violations |
| `status` | `open` \| `reviewed` \| `dismissed` \| `resolved` | Filter to unreviewed |
| `eventType` | `ppe_violation` \| `positive_observation` \| `uncertain_review` | Filter by event class |
| `severity` | `low` \| `medium` \| `high` | Filter by severity |
| `limit` | integer | Cap result count |

**Safe poll interval:** every 3–5 seconds for the demo.

### Per-camera events

```
GET https://safety-sentinel-api.fly.dev/cameras/{cameraId}/detail
```

Returns `{ "camera": {...}, "captures": [...], "events": [...] }` with the last 20 events for that camera. No `violationType` or `status` filter supported here.

**Best approach for the demo:** poll `GET /events?violationType=no_helmet&status=open` globally and check `event.upload.cameraId` to match your phone camera.

---

## 3. Detecting "New" Events (avoiding double-notify)

Each event has a stable `id` and a monotonic `createdAt` timestamp.

`GET /events` returns results newest-first. **No `since` / `after` query param is exposed** on this endpoint.

**Recommended dedup strategy:**

1. On each poll response, compare each event's `createdAt` against the max `createdAt` you have stored.
2. Anything strictly newer is a new event — fire a notification.
3. Update your stored max.
4. Alternatively, maintain a `Set<String>` of seen `id` values in UserDefaults.

---

## 4. Payload Shape

### SafetyEvent (from `GET /events`)

```json
{
  "id": "evt_001",
  "uploadId": "upl_123",
  "eventType": "ppe_violation",
  "violationType": "no_helmet",
  "severity": "high",
  "confidence": 0.88,
  "status": "open",
  "statusUpdatedAt": null,
  "reviewNote": null,
  "suggestedAction": "Supervisor review recommended. Helmet appears missing.",
  "createdAt": "2026-06-27T14:31:02Z",
  "upload": {
    "id": "upl_123",
    "fileName": "frame_001.jpg",
    "fileType": "image",
    "fileUrl": "/media/frame_001.jpg",
    "locationLabel": null,
    "zoneId": "general-floor",
    "cameraId": "cam-phone",
    "zoneDisplayName": "General Floor",
    "notes": null,
    "uploadedAt": "2026-06-27T14:31:00Z",
    "status": "processed"
  }
}
```

### AlertRecord (from `GET /alerts`)

```json
{
  "id": "alrt_001",
  "safetyEventId": "evt_001",
  "alertType": "supervisor_review",
  "title": "Missing Helmet Detected",
  "message": "A high-severity PPE violation was detected. Supervisor review is recommended.",
  "status": "draft",
  "createdAt": "2026-06-27T14:31:03Z"
}
```

### Key fields for the iOS notification

| Field | Path | Example |
|---|---|---|
| Event ID | `event.id` | `"evt_001"` |
| Violation type | `event.violationType` | `"no_helmet"` |
| Severity | `event.severity` | `"high"` |
| Confidence | `event.confidence` | `0.88` |
| Timestamp | `event.createdAt` | `"2026-06-27T14:31:02Z"` |
| Camera ID | `event.upload.cameraId` | `"cam-phone"` |
| Zone | `event.upload.zoneDisplayName` | `"General Floor"` |
| Frame image | `event.upload.fileUrl` | `"/media/frame_001.jpg"` |

### Frame image URL

`fileUrl` is a path relative to the backend. Prepend the base URL:

```
https://safety-sentinel-api.fly.dev + event.upload.fileUrl
// → https://safety-sentinel-api.fly.dev/media/frame_001.jpg
```

This is a **public URL, no auth required**. Suitable for use as a `UNNotificationAttachment`.

You can also fetch the latest captured JPEG directly (not tied to a specific event):

```
GET https://safety-sentinel-api.fly.dev/cameras/{cameraId}/snapshot
→ image/jpeg binary
```

---

## 5. Phone Camera ID

The phone feed camera is **registered at demo runtime** — it is not pre-seeded. Register it once at demo start:

```
POST https://safety-sentinel-api.fly.dev/cameras
Content-Type: application/json

{
  "displayName": "Phone Demo Camera",
  "rtspUrl": "rtsp://safety-sentinel-relay.internal:8554/live/phone-demo",
  "zoneId": "general-floor",
  "captureIntervalSeconds": 2
}
```

The response `camera.id` is the value that will appear in `event.upload.cameraId` for all captures from this feed. Store it at registration time.

**Pre-seeded location cameras** (no RTSP, not the phone feed):

| ID | Display Name | Zone |
|---|---|---|
| `cam-01` | Floor Entry Cam | `general-floor` |
| `cam-02` | Dock Camera North | `loading-dock` |
| `cam-03` | Welding Bay Cam | `welding-station` |

---

## 6. Notification Delivery

**The backend has no APNs support** — no device token endpoint, no `.p8` key, no server-side push.

Fire **local `UNUserNotification`s** from the iOS app after detecting new events on each poll. No backend changes needed.

---

## Quick Reference

| | |
|---|---|
| **Base URL** | `https://safety-sentinel-api.fly.dev` |
| **Auth** | None |
| **Poll for new violations** | `GET /events?violationType=no_helmet&status=open` every 3–5s |
| **Dedup strategy** | Track max `createdAt` seen; notify on anything newer |
| **Event ID field** | `event.id` |
| **Timestamp field** | `event.createdAt` (ISO 8601 UTC) |
| **Frame image** | `https://safety-sentinel-api.fly.dev` + `event.upload.fileUrl` |
| **Phone camera ID** | Assigned on `POST /cameras` at demo start; read from response |
| **APNs** | Not implemented; use local iOS notifications |
