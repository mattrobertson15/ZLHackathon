# Safety Sentinel — Getting Started

## Prerequisites

- Docker Desktop (recommended path — runs everything)
- Node.js 18+ (only needed for local frontend dev)
- Python 3.10+ (only needed for local backend dev)

## Quickstart (Docker — recommended)

This is the fastest way to get the full stack running, including the emulated RTSP camera feeds.

### 1. Add API keys

Create `.env.local` in the project root (next to `docker-compose.yml`):

```bash
ANTHROPIC_API_KEY=your_key_here
QWEN_API_KEY=your_key_here
```

Both keys are needed for PPE analysis and AI safety summaries. The backend reads this file automatically via `docker-compose.yml`.

### 2. Start the stack

```bash
docker compose up --build
```

This starts:
- **mediamtx** — RTSP server on port 8554
- **ffmpeg** / **ffmpeg-dock** / **ffmpeg-welding** — loops the three demo video clips into mediamtx
- **backend** — FastAPI on port 8000, with all three seeded cameras auto-monitoring

First run builds the backend Docker image, which takes ~1–2 minutes.

### 3. Start the frontend

In a separate terminal:

```bash
cd frontend
npm install   # first time only
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

### 4. Load demo data (optional)

Go to **Settings → Load Demo Scenario** in the app, or hit the API directly:

```bash
curl -X POST http://localhost:8000/admin/demo-scenario
```

This seeds historical safety events, detections, and alerts so the dashboard and analytics pages look populated immediately.

---

## What runs where

| Service    | URL                           | Notes                                      |
|------------|-------------------------------|--------------------------------------------|
| Frontend   | http://localhost:3000         | Next.js dev server                         |
| Backend    | http://localhost:8000         | FastAPI; health check at `/health`         |
| RTSP feeds | rtsp://localhost:8554/\<path\> | Three feeds: `worksite-demo`, `loading-dock`, `welding-bay` |

---

## Camera feeds

Three cameras are seeded automatically on first startup:

| Camera            | Zone            | RTSP path          |
|-------------------|-----------------|--------------------|
| Floor Entry Cam   | General Floor   | `worksite-demo`    |
| Dock Camera North | Loading Dock    | `loading-dock`     |
| Welding Bay Cam   | Welding Station | `welding-bay`      |

When running via `docker compose`, all three cameras start monitoring automatically (`SEED_CAMERA_MONITORING=true`). Snapshots appear on the **Cameras** page within a few seconds.

> **Troubleshooting — no feed visible:** If cameras show "Waiting for first capture…" and no Start Monitoring button appears, the cameras may have been seeded before the RTSP URL column existed. Fix:
> ```bash
> curl -X DELETE http://localhost:8000/cameras/cam-01
> curl -X DELETE http://localhost:8000/cameras/cam-02
> curl -X DELETE http://localhost:8000/cameras/cam-03
> docker compose restart backend
> ```

---

## Local development (without Docker)

Use this if you want fast iteration on backend or frontend code without rebuilding containers.

### Backend

```bash
cd backend
cp .env.example .env   # then fill in your API keys
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The backend will still seed the three cameras, but their RTSP URLs will point to `rtsp://localhost:8554/...`. The feeds will only be live if mediamtx and ffmpeg are also running (via `docker compose up mediamtx ffmpeg ffmpeg-dock ffmpeg-welding`).

### Frontend

```bash
cd frontend
npm install
npm run dev
```

No extra env file needed for local dev — the frontend defaults to `http://localhost:8000` for the API.

---

## Project structure

```
.
├── backend/                # FastAPI backend
│   ├── app/
│   │   ├── main.py         # App entry point and router registration
│   │   ├── routes/         # API route handlers (uploads, cameras, events, etc.)
│   │   ├── services/       # Business logic (camera monitor, analysis pipeline)
│   │   ├── db/             # SQLAlchemy models, repositories, seed data
│   │   └── utils/          # RTSP capture, ID generation, timestamps
│   ├── requirements.txt
│   └── .env.example
├── emulator/
│   ├── media/              # Demo video clips (demo-worksite.mp4, loading-dock.mp4, welding-bay.mp4)
│   └── make-sample-video.sh  # One-time script to build clips from source footage
├── frontend/               # Next.js frontend
│   ├── app/app/            # App pages (dashboard, cameras, events, upload, etc.)
│   ├── components/         # Shared UI components
│   └── lib/                # API client and TypeScript types
├── relay/                  # Fly.io MediaMTX relay for phone demo
├── docker-compose.yml      # Full local stack (backend + RTSP emulator)
├── vercel.json             # Vercel deployment config (frontend + backend serverless)
├── ARCHITECTURE.md         # System design and component overview
├── API.md                  # API endpoint reference
└── DEMOSCRIPT.md           # Demo walkthrough guide
```

---

## Vercel deployment

The `vercel.json` routes both services through a single Vercel project:

- Frontend (Next.js) at `/`
- Backend (FastAPI) at `/_/backend`

Set these environment variables in the Vercel dashboard:

```
ANTHROPIC_API_KEY=...
QWEN_API_KEY=...
```

The backend uses `/tmp` for SQLite and file storage on Vercel — data is ephemeral per serverless instance. The always-on camera monitor cannot run on Vercel; use a persistent host (Fly.io, Render, Railway, or a VM) for live camera feeds.
