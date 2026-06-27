# Safety Sentinel — Hackathon Build Plan

## Phase 1: Foundation & Infrastructure
- [x] Set up FastAPI backend project structure
- [ ] Set up Next.js frontend project structure
- [x] Configure environment variables (.env files)
  - `ANTHROPIC_API_KEY` for Claude summaries
  - `QWEN_API_KEY` for vision model
  - `UPLOAD_STORAGE_PATH` for local image/video storage
- [x] Create SQLite database schema (uploads done; detections, safety_events, alerts, summaries pending later phases)
- [x] Set up database ORM/query layer (SQLAlchemy or similar)
- [x] Create base API health check endpoint (`GET /health`)

## Phase 2: Upload & Storage
- [x] Implement file upload handler (`POST /uploads`)
- [x] Store uploaded files locally (use `UPLOAD_STORAGE_PATH`)
- [x] Implement upload retrieval (`GET /uploads`, `GET /uploads/{upload_id}`)
- [x] Add video frame extraction utility (sample 1 frame per 1-2 seconds, cap at 20-30 frames)
- [x] Implement upload status tracking (uploaded → processing → processed → failed)

## Phase 3: Vision Inference Integration
- [x] Create detection parser to normalize Qwen outputs (`app/services/detection_parser.py`)
- [x] Implement inference endpoint (`POST /uploads/{upload_id}/analyze`)
- [x] Add mock detection fallback (for demo reliability if Qwen fails) — this is the active default until Phase 3.5 lands (`app/services/vision_service.py`)
- [x] Store raw detection results in database (`detection_results` table)

## Phase 3.5: Qwen Vision Client (Deferred — needs QWEN_API_KEY)
- [x] Integrate Qwen3-VL30B API client
  - Detection targets: person, helmet, no_helmet, vest, no_vest
  - Extract: label, confidence, bounding box, frame timestamp (for video)
- [x] Implement `_call_qwen_vision` in `app/services/vision_service.py` (currently raises `NotImplementedError`)
- [x] Verify real Qwen output shape matches `RawDetection`/detection-parser expectations; adjust parser if not
- [x] Confirm mock-fallback-on-failure behavior still works once the real client is live

## Phase 4: Rule Engine & Safety Events
- [x] Implement rule engine that converts detections → safety events (`app/services/rule_engine.py`)
  - person + helmet → positive observation
  - person + no_helmet → high-severity violation
  - person + vest → positive observation
  - person + no_vest → medium-severity violation
  - person + unclear PPE → uncertain_review
- [x] Create safety event creation logic
- [x] Implement event retrieval (`GET /events`, `GET /events/{event_id}`)
- [x] Implement event status updates (`PATCH /events/{event_id}`)

## Phase 5: Mock Alert Generation
- [x] Implement alert creation from safety events (`app/services/alert_service.py`)
  - High severity → supervisor_review
  - Medium severity → coaching_reminder
  - Low confidence or uncertain_review → manual_review
- [x] Create alert retrieval (`GET /alerts`)
- [x] Implement alert status updates (`PATCH /alerts/{alert_id}`)
- [x] Store alerts in database (`alert_records` table)

## Phase 6: Analytics
- [x] Calculate compliance percentage (positive_obs / total_observations * 100)
- [x] Aggregate violation breakdown (no_helmet vs no_vest counts)
- [x] Implement trending (daily, weekly, monthly compliance)
- [x] Create analytics endpoints (`GET /analytics/overview`, `GET /analytics/trends`)
- [x] Support period filters (daily, weekly, monthly, all)

## Phase 7: AI Safety Summaries
- [x] Integrate Claude API client
- [x] Implement summary generation endpoint (`POST /summaries/generate`)
  - Input: period, startDate, endDate
  - Claude generates: executive summary, top violations, trend, recommended actions
- [x] Implement summary retrieval (`GET /summaries`, `GET /summaries/{summary_id}`)
- [x] Store generated summaries in database

## Phase 8: Frontend - Core Pages
- [x] Create landing/home page (project overview)
- [x] Create upload page (`/app/upload`)
  - Drag-and-drop file input
  - Support image and video
- [x] Create results page (`/app/results/[uploadId]`)
  - Display detections
  - Show analysis details
- [x] Create dashboard page (`/app/dashboard`)
  - Compliance percentage card
  - Violation count card
  - Violation type breakdown
  - Compliance trend table
- [x] Create events page (`/app/events`)
  - Event table with filters (status, severity, type)
  - Event detail view
- [x] Create API client (lib/api.ts) with all endpoints
- [x] Create TypeScript types (lib/types.ts) from API specs

## Phase 9: Frontend - Alerts & Summaries
- [x] Create alerts page (`/alerts`)
  - Filter sidebar (status, alert type)
  - Quick stats cards (draft/queued/sent/total)
  - Timeline-style alert list
  - Alert detail modal
  - Status update workflow
- [x] Create summaries page (`/summaries`)
  - Summary generator form (period + date range)
  - Quick-select shortcuts (This Week/Month/Today)
  - Generated summary display with 4 sections
  - Summary list with click-to-view modal

## Phase 10: Frontend - UI Components
- [ ] UploadDropzone component
- [ ] DetectionViewer component (annotated image with bounding boxes)
- [ ] ComplianceScoreCard component
- [ ] ViolationBreakdownChart component (Recharts)
- [ ] TrendChart component (Recharts)
- [ ] EventTable component
- [ ] AlertCard component
- [ ] SummaryCard component

## Phase 11: Integration & Testing
- [ ] Test full upload → analyze → events → alerts flow
- [ ] Test analytics calculation with sample data
- [ ] Test Claude summary generation with real event data
- [ ] Test video frame extraction with sample video
- [ ] Manual UI testing across all pages

## Phase 12: Demo Preparation
- [ ] Seed database with sample safety events for demo
- [ ] Create demo script notes in UI
- [ ] Test demo flow end-to-end
- [ ] Prepare sample worksite images/videos for demo
- [ ] Document any manual "backup" steps if Qwen inference fails

## Image Dataset Storage Decision
**Chosen: Local file storage with database references**
- Store uploaded images locally in `UPLOAD_STORAGE_PATH` (./uploads by default)
- Store file paths and metadata in SQLite database
- Keep file URLs relative (e.g., `/uploads/warehouse-floor.jpg`)
- For hackathon, this avoids cloud storage setup and API costs
- Can be migrated to cloud storage (S3/GCS) later if needed
- Seed demo images into ./uploads directory before demo

## Notes
- Use SQLite for simplicity (no external DB setup needed)
- Mock alerts instead of real Slack/email delivery
- Use Qwen3-VL30B for vision, Claude API for summaries
- Prioritize demo flow: dashboard → upload → analyze → events → alerts → summary
- If Qwen inference fails mid-demo, fall back to seeded detection data
