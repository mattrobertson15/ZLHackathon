# Safety Sentinel — Session Prompts & Context

## Quick Reference

**Project**: Safety Sentinel (Hackathon MVP)  
**Vision Model**: Qwen3-VL30B  
**Summary LLM**: Claude API  
**Storage**: SQLite + local file uploads  
**Tech Stack**: FastAPI (backend), Next.js (frontend), Recharts (charts)

---

## Key Decisions

### 1. Image Dataset Storage
Use **local file storage** with database references:
- Uploaded images and videos stored in `./uploads` directory
- File paths and metadata stored in SQLite
- File URLs are relative (e.g., `/uploads/warehouse-floor.jpg`)
- **Why**: Hackathon speed, no cloud setup, images serve from backend static files
- **Later**: Can migrate to S3/GCS without changing API structure

### 2. Vision Model: Qwen3-VL30B
- Use for PPE detection (person, helmet, no_helmet, vest, no_vest)
- Extract: label, confidence, bounding box, frame timestamp (video)
- Fallback: Use seeded mock detections if API fails (for demo resilience)
- **Environment var**: `QWEN_API_KEY`

### 3. Summary Generation: Claude API
- Claude generates daily/weekly/monthly safety summaries
- Input: structured analytics data (compliance %, violations, breakdown)
- Output: executive summary, key observations, recommended actions
- **Environment var**: `ANTHROPIC_API_KEY`

### 4. Database: SQLite
- Simple, file-based, no external DB server
- Schema: uploads, detection_results, safety_events, alert_records, safety_summaries
- Suitable for hackathon; can migrate to Postgres later

---

## API Endpoints (Priority Order)

1. `GET /health` — Backend health check
2. `POST /uploads` — Upload image/video
3. `POST /uploads/{upload_id}/analyze` — Run vision analysis
4. `GET /uploads/{upload_id}/detections` — Get detections
5. `GET /events` — List safety events
6. `GET /analytics/overview` — Dashboard metrics
7. `GET /analytics/trends` — Compliance trends
8. `GET /alerts` — List mock alerts
9. `POST /summaries/generate` — Generate AI summary
10. `GET /summaries` — List summaries

See [API.md](API.md) for full spec.

---

## Data Model Quick Ref

**Upload**
- id, fileName, fileType (image|video), fileUrl, uploadedAt, status

**DetectionResult**
- id, uploadId, frameTimestamp, label (person|helmet|no_helmet|vest|no_vest), confidence, boundingBox, source

**SafetyEvent**
- id, uploadId, eventType (positive_observation|ppe_violation|uncertain_review), violationType, severity, confidence, status, suggestedAction, createdAt

**AlertRecord**
- id, safetyEventId, alertType (supervisor_review|coaching_reminder|manual_review), title, message, status, createdAt

**SafetySummary**
- id, period (daily|weekly|monthly), startDate, endDate, compliancePercentage, totalViolations, topViolationTypes, summaryText, recommendedActions, createdAt

See [ARCHITECTURE.md](ARCHITECTURE.md#data-models) for full schema.

---

## Rule Engine Logic

Convert detections → safety events using these rules:

```
If person detected AND helmet detected:
  → positive observation (low severity)

If person detected AND no_helmet detected:
  → PPE violation (high severity)

If person detected AND vest detected:
  → positive observation (low severity)

If person detected AND no_vest detected:
  → PPE violation (medium severity)

If person detected AND PPE state unclear:
  → uncertain review (low-medium severity)
```

---

## Compliance Calculation (MVP)

```
compliance_percentage = (positive_observations / total_safety_observations) * 100

where:
  total_safety_observations = 
    positive_observations + ppe_violations + uncertain_reviews
```

---

## Demo Flow

1. **Dashboard** — Show compliance %, violations, trends (0:30-1:00)
2. **Upload** — User uploads a worksite image or video (1:00-1:45)
3. **Analyze** — Run Qwen vision model, show loading (1:45-2:30)
4. **Detections** — Display annotated results with bounding boxes (2:30-3:15)
5. **Events** — Show structured safety events generated from detections (3:15-4:00)
6. **Alerts** — Display mock alerts created from safety events (4:00-4:45)
7. **Dashboard** — Show updated metrics after new upload (4:45-5:30)
8. **Summary** — Generate and display AI safety summary (5:30-6:00)

**Backup**: If Qwen inference fails, use seeded detections and continue.

---

## Environment Variables

```
# Backend
ANTHROPIC_API_KEY=your-anthropic-key
QWEN_API_KEY=your-qwen-key
UPLOAD_STORAGE_PATH=./uploads

# Frontend
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

---

## Frontend Pages

- `/` — Landing / overview
- `/upload` — Upload image or video
- `/results/[uploadId]` — View detections and generated events
- `/dashboard` — Compliance metrics, trends, violation breakdown
- `/events` — Safety event log
- `/alerts` — Mock alert center
- `/summaries` — AI-generated summaries (daily/weekly/monthly)

---

## Hackathon MVP Scope

**Included**
- Uploaded images and videos
- PPE detection (person, helmet, vest, no_helmet, no_vest)
- Structured safety events
- Dashboard analytics
- Mock alerts (no real delivery)
- AI-generated summaries (Claude)

**Not Included**
- Facial recognition
- Employee identification
- Live camera streams
- Real alert delivery (Slack, email, SMS)
- Automated disciplinary workflows

---

## When Starting a New Task

1. Read the relevant doc first ([README.MD](README.MD), [ARCHITECTURE.md](ARCHITECTURE.md), [API.md](API.md), [DEMOSCRIPT.md](DEMOSCRIPT.md))
2. Check [todo.md](todo.md) for phase dependencies
3. Update the relevant documentation when you implement changes
4. Link to docs in commit messages so future readers find context

---

## Questions to Ask Yourself

- **Storage**: Is this image/video dataset accessed frequently? If yes, consider local disk for hackathon speed. If no, can seed it into the `/uploads` directory.
- **Inference**: Should Qwen fail, do I have seeded fallback detections ready for demo?
- **Events**: Am I converting model outputs into structured SafetyEvent records?
- **Alerts**: Are alerts created from high/medium severity violations, and stored in the database?
- **Summaries**: Is Claude API configured correctly? Am I passing the right analytics context?
- **Frontend**: Does the UI reflect the latest event data from the backend?

---

## Commit Message Template

```
<type>: <short summary>

- Detailed change description
- Links to relevant docs: [ARCHITECTURE.md#section](ARCHITECTURE.md#section)
- Relates to phase: [Phase X] from todo.md
```

Example:
```
feat: implement Qwen3-VL30B vision inference layer

- Added QwenVisionClient to integrate Qwen3-VL30B API
- Detections normalized to DetectionResult schema
- Handles image and sampled video frames
- Falls back to seeded detections if API fails
- Links: [ARCHITECTURE.md#vision-inference-layer](ARCHITECTURE.md#vision-inference-layer)
- Phase 3 from todo.md
```
