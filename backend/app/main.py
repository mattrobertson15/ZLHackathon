from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.config import UPLOAD_STORAGE_PATH
from app.db.database import init_db
from app.routes import admin, alerts, analytics, events, inference, summaries, uploads

app = FastAPI(title="Safety Sentinel API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc: HTTPException):
    detail = exc.detail
    if isinstance(detail, dict) and "error" in detail:
        return JSONResponse(status_code=exc.status_code, content=detail)
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": "HTTP_ERROR", "message": str(detail)}},
    )


@app.on_event("startup")
def on_startup():
    init_db()


app.include_router(uploads.router)
app.include_router(inference.router)
app.include_router(events.router)
app.include_router(alerts.router)
app.include_router(analytics.router)
app.include_router(summaries.router)
app.include_router(admin.router)
app.mount("/media", StaticFiles(directory=UPLOAD_STORAGE_PATH), name="media")


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "Safety Sentinel API"}
