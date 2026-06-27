# Safety Sentinel — Getting Started

## Prerequisites
- Python 3.10+
- Node.js 18+
- npm or yarn

## Phase 1 Setup

### Backend Setup

1. **Create environment file**:
   ```bash
   cd backend
   cp .env.example .env
   # Add your API keys to .env
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the backend**:
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```
   
   The API will be available at `http://localhost:8000`
   - Health check: `GET http://localhost:8000/health`

### Frontend Setup

1. **Create environment file**:
   ```bash
   cd frontend
   cp .env.local.example .env.local
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Run the dev server**:
   ```bash
   npm run dev
   ```
   
   The frontend will be available at `http://localhost:3000`
   - Landing page: `http://localhost:3000`
   - App dashboard: `http://localhost:3000/app/dashboard`

## Project Structure

```
.
├── backend/                 # FastAPI backend
│   ├── main.py             # Entry point, basic health check
│   ├── requirements.txt     # Python dependencies
│   └── .env.example        # Environment template
├── frontend/               # Next.js frontend
│   ├── app/                # App router
│   │   ├── page.tsx        # Landing page (logo + "Enter App" button)
│   │   └── app/
│   │       └── dashboard/  # Dashboard page (stub)
│   ├── public/
│   │   └── safety_sentinel_logo.png
│   └── .env.local.example  # Environment template
└── GETTING_STARTED.md      # This file
```

## Next Steps (Phase 2+)

Once Phase 1 is complete:
- Implement SQLite database schema
- Set up upload handling endpoints
- Integrate vision model for detection
- Build rule engine for safety events
- Create frontend pages for upload, results, and events
