import http.cookiejar
import os
import shutil
import tempfile
import threading
import urllib.request

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import EMULATOR_MEDIA_PATH, UPLOAD_STORAGE_PATH
from app.db.database import get_db
from app.db.repositories import (
    count_events_for_camera,
    create_camera,
    delete_camera,
    get_camera,
    get_zone,
    list_cameras,
    list_events_for_camera,
    list_uploads_for_camera,
    update_camera,
)
from app.models.camera import Camera
from app.services import camera_monitor
from app.services.serializers import serialize_event, serialize_upload
from app.utils.ids import generate_id
from app.utils.rtsp_capture import capture_frames_from_rtsp
from app.utils.timestamps import now_utc, to_iso

router = APIRouter(prefix="/cameras", tags=["cameras"])


def _error(code: str, message: str):
    return {"error": {"code": code, "message": message}}


def serialize_camera(camera: Camera, recent_event_count: int = 0) -> dict:
    """Superset serializer: location-registry fields (main) + live-feed fields.

    Clients that only know the registry shape (displayName/zoneId/status) keep
    working; the RTSP feature reads the additional stream fields.
    """
    return {
        "id": camera.id,
        "displayName": camera.display_name,
        "zoneId": camera.zone_id,
        "status": camera.status,
        "createdAt": to_iso(camera.created_at),
        # Live RTSP feed
        "rtspUrl": camera.rtsp_url,
        "streamStatus": camera.stream_status,
        "monitoring": camera.monitoring,
        "captureIntervalSeconds": camera.capture_interval_seconds,
        "lastCaptureAt": to_iso(camera.last_capture_at) if camera.last_capture_at else None,
        "lastError": camera.last_error,
        "recentEventCount": recent_event_count,
    }


class CreateCameraRequest(BaseModel):
    displayName: str
    rtspUrl: str | None = None
    zoneId: str | None = None
    captureIntervalSeconds: int = 15


class TestStreamRequest(BaseModel):
    rtspUrl: str


def _camera_payload(db: Session, camera: Camera) -> dict:
    return serialize_camera(camera, recent_event_count=count_events_for_camera(db, camera.id))


def _get_or_404(db: Session, camera_id: str) -> Camera:
    camera = get_camera(db, camera_id)
    if camera is None:
        raise HTTPException(
            status_code=404,
            detail=_error("CAMERA_NOT_FOUND", f"No camera found for id '{camera_id}'."),
        )
    return camera


@router.post("")
def register_camera(request: CreateCameraRequest, db: Session = Depends(get_db)):
    if request.captureIntervalSeconds < 1:
        raise HTTPException(
            status_code=400,
            detail=_error("INVALID_INTERVAL", "captureIntervalSeconds must be at least 1."),
        )
    if request.zoneId and get_zone(db, request.zoneId) is None:
        raise HTTPException(
            status_code=400,
            detail=_error("ZONE_NOT_FOUND", f"No zone found for id '{request.zoneId}'."),
        )

    camera = Camera(
        id=generate_id("cam"),
        display_name=request.displayName,
        zone_id=request.zoneId,
        status="active",
        created_at=now_utc(),
        rtsp_url=request.rtspUrl,
        stream_status="offline",
        monitoring=False,
        capture_interval_seconds=request.captureIntervalSeconds,
    )
    camera = create_camera(db, camera)
    return {"camera": _camera_payload(db, camera)}


@router.get("")
def get_cameras(db: Session = Depends(get_db)):
    return {"cameras": [_camera_payload(db, c) for c in list_cameras(db)]}


@router.post("/test-stream")
def test_stream(request: TestStreamRequest):
    """Probe an RTSP URL by grabbing a single frame, without registering a camera.

    Lets the user confirm the phone/relay feed is reachable before they start
    monitoring. Returns the frame dimensions on success, or the actual error on
    failure (the most common cause is path mismatch between the RTMP publisher
    and the RTSP URL, or the stream not being live). See API.md#test-rtsp-stream.
    """
    scratch_dir = tempfile.mkdtemp(prefix="test_stream_", dir=UPLOAD_STORAGE_PATH)
    try:
        captured = capture_frames_from_rtsp(
            request.rtspUrl, scratch_dir, num_frames=1, spacing_seconds=0
        )
        import cv2  # noqa: PLC0415 — lazy import; cv2 not available on Vercel
        frame = cv2.imread(captured[0]["framePath"])
        if frame is None:
            raise ValueError("Captured frame could not be decoded.")
        height, width = frame.shape[:2]
        return {
            "status": "connected",
            "width": int(width),
            "height": int(height),
            "message": "Stream connected successfully.",
        }
    except ValueError as exc:
        return {
            "status": "failed",
            "message": str(exc),
            "hint": (
                "Make sure the stream is live and reachable from the backend. "
                "For Streamlabs: set Server=rtmp://safety-sentinel-relay.fly.dev:1935/live "
                "and Stream Key=phone-demo, then read from "
                "rtsp://safety-sentinel-relay.internal:8554/live/phone-demo. "
                "Use GET /cameras/relay-streams to see which paths mediamtx has live."
            ),
        }
    except Exception as exc:
        return {
            "status": "failed",
            "message": f"{type(exc).__name__}: {exc}",
            "hint": (
                "Unexpected error — check that the relay is deployed and reachable. "
                "Use GET /cameras/relay-streams to confirm mediamtx connectivity."
            ),
        }
    finally:
        shutil.rmtree(scratch_dir, ignore_errors=True)


@router.get("/relay-streams")
def relay_streams():
    """Proxy the mediamtx API to show which RTMP/RTSP paths are currently live.

    Useful for confirming a phone publisher (Streamlabs/Larix) is actually
    reaching the relay before debugging RTSP read failures. Returns the path
    list from mediamtx's /v3/paths/list endpoint, or an error if the relay
    is unreachable from this backend instance.
    """
    import json
    import urllib.request

    try:
        url = "http://safety-sentinel-relay.internal:9997/v3/paths/list"
        with urllib.request.urlopen(url, timeout=5) as resp:
            data = json.loads(resp.read())
        paths = [
            {
                "name": p["name"],
                "ready": p.get("ready", False),
                "readyTime": p.get("readyTime"),
                "readers": len(p.get("readers", [])),
                "bytesReceived": p.get("bytesReceived", 0),
            }
            for p in data.get("items", [])
        ]
        return {"relay": "reachable", "paths": paths}
    except Exception as exc:
        return {
            "relay": "unreachable",
            "error": f"{type(exc).__name__}: {exc}",
            "note": (
                "The relay is only reachable from within Fly's private network. "
                "If the backend is running locally, this endpoint will always fail."
            ),
        }


@router.get("/{camera_id}")
def get_camera_by_id(camera_id: str, db: Session = Depends(get_db)):
    camera = _get_or_404(db, camera_id)
    return {"camera": _camera_payload(db, camera)}


@router.get("/{camera_id}/detail")
def get_camera_detail(camera_id: str, db: Session = Depends(get_db)):
    """Camera plus its recent captures and events (for the camera UI)."""
    camera = _get_or_404(db, camera_id)
    uploads = list_uploads_for_camera(db, camera_id, limit=10)
    events = list_events_for_camera(db, camera_id, limit=100)
    return {
        "camera": _camera_payload(db, camera),
        "captures": [serialize_upload(u) for u in uploads],
        "events": [serialize_event(e) for e in events],
    }


def _require_rtsp(camera: Camera) -> None:
    if not camera.rtsp_url:
        raise HTTPException(
            status_code=400,
            detail=_error(
                "NO_RTSP_URL",
                f"Camera '{camera.id}' has no rtspUrl; it is a location-only camera.",
            ),
        )


@router.post("/{camera_id}/start")
def start_camera(camera_id: str, db: Session = Depends(get_db)):
    camera = _get_or_404(db, camera_id)
    _require_rtsp(camera)
    camera.monitoring = True
    update_camera(db, camera)

    # Immediate capture so the user gets instant feedback and stream_status flips.
    try:
        camera_monitor.capture_and_analyze(db, camera)
    except Exception:
        # capture_and_analyze already recorded stream_status="error" + last_error.
        pass

    db.refresh(camera)
    return {"camera": _camera_payload(db, camera)}


@router.post("/{camera_id}/stop")
def stop_camera(camera_id: str, db: Session = Depends(get_db)):
    camera = _get_or_404(db, camera_id)
    camera.monitoring = False
    camera.stream_status = "offline"
    update_camera(db, camera)
    return {"camera": _camera_payload(db, camera)}


@router.post("/{camera_id}/capture")
def capture_now(camera_id: str, db: Session = Depends(get_db)):
    camera = _get_or_404(db, camera_id)
    _require_rtsp(camera)
    try:
        result = camera_monitor.capture_and_analyze(db, camera)
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=_error("CAPTURE_FAILED", f"Could not capture from camera: {exc}"),
        ) from exc

    db.refresh(camera)
    return {
        "camera": _camera_payload(db, camera),
        "detections": len(result["detections"]),
        "events": [serialize_event(e) for e in result["events"]],
    }


_MEDIAMTX_HLS_BASE = os.environ.get("MEDIAMTX_HLS_URL", "http://mediamtx:8888")

# Per-camera cookie jars — mediamtx issues an hlsSession cookie after the
# cookieCheck handshake; we need to reuse it across manifest + segment requests.
_hls_jars: dict[str, http.cookiejar.CookieJar] = {}
_hls_jars_lock = threading.Lock()


def _hls_fetch(camera_id: str, url: str) -> tuple[bytes, str]:
    """Fetch an HLS resource from mediamtx, bootstrapping the session if needed.

    mediamtx requires a two-step cookie handshake before serving HLS:
      1. Client hits ?cookieCheck=1 with Cookie: cookieCheck=1
         → mediamtx returns content + Set-Cookie: hlsSession=<uuid>
      2. All subsequent requests (sub-manifests, segments) send Cookie: hlsSession=<uuid>

    We pre-seed cookieCheck into the jar so the HTTPCookieProcessor sends it,
    then reuse the jar (which now holds hlsSession) for every later request.
    """
    with _hls_jars_lock:
        jar = _hls_jars.get(camera_id)
        if jar is None:
            jar = http.cookiejar.CookieJar()
            _hls_jars[camera_id] = jar

    has_session = any(c.name == "hlsSession" for c in jar)

    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))

    if not has_session:
        # Bootstrap: hit the cookieCheck URL with the required cookie header.
        # urllib doesn't let us pre-seed jar cookies easily, so we send the
        # header manually on this one call; the opener stores the hlsSession
        # Set-Cookie that mediamtx returns.
        parsed = url.split("?")[0]
        base = parsed.rsplit("/", 1)[0]
        bootstrap_url = f"{base}/index.m3u8?cookieCheck=1"
        req = urllib.request.Request(bootstrap_url, headers={"Cookie": "cookieCheck=1"})
        with opener.open(req, timeout=10) as resp:
            resp.read()  # consume; we only care about the Set-Cookie

    with opener.open(url, timeout=10) as resp:
        body = resp.read()
        content_type = resp.headers.get("Content-Type", "application/octet-stream")

    return body, content_type


@router.get("/{camera_id}/hls/{hls_path:path}")
def camera_hls_proxy(camera_id: str, hls_path: str, request: Request, db: Session = Depends(get_db)):
    """Proxy mediamtx HLS through the backend to avoid cross-origin cookie issues."""
    camera = _get_or_404(db, camera_id)
    if not camera.rtsp_url:
        raise HTTPException(status_code=404, detail=_error("NO_HLS", "No RTSP feed."))
    try:
        rtsp_path = camera.rtsp_url.split(":8554/", 1)[-1].strip("/")
    except Exception:
        raise HTTPException(status_code=404, detail=_error("NO_HLS", "Bad RTSP URL."))

    qs = str(request.query_params)
    target = f"{_MEDIAMTX_HLS_BASE}/{rtsp_path}/{hls_path}"
    if qs:
        target += f"?{qs}"

    try:
        body, content_type = _hls_fetch(camera_id, target)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=_error("HLS_PROXY_ERROR", str(exc)))

    return Response(content=body, media_type=content_type)


@router.get("/{camera_id}/snapshot")
def camera_snapshot(camera_id: str, db: Session = Depends(get_db)):
    _get_or_404(db, camera_id)
    uploads = list_uploads_for_camera(db, camera_id, limit=1)
    if not uploads or not uploads[0].file_url:
        raise HTTPException(
            status_code=404,
            detail=_error("NO_SNAPSHOT", "No capture available for this camera yet."),
        )

    stored_name = uploads[0].file_url.removeprefix("/media/")
    disk_path = os.path.join(UPLOAD_STORAGE_PATH, stored_name)
    if not os.path.exists(disk_path):
        raise HTTPException(
            status_code=404,
            detail=_error("NO_SNAPSHOT", "Snapshot frame is no longer on disk."),
        )
    return FileResponse(disk_path, media_type="image/jpeg")


_RTSP_PATH_TO_MP4: dict[str, str] = {
    "worksite-demo": "demo-worksite.mp4",
    "loading-dock": "loading-dock.mp4",
    "welding-bay": "welding-bay.mp4",
}


@router.get("/{camera_id}/video")
def camera_video(camera_id: str, db: Session = Depends(get_db)):
    """Serve the demo MP4 clip that corresponds to this camera's RTSP stream path.

    Returns 404 for location-only cameras or any camera whose RTSP path isn't
    one of the three known emulator clips, so the frontend can fall back to the
    JPEG snapshot gracefully.
    """
    camera = _get_or_404(db, camera_id)
    if not camera.rtsp_url:
        raise HTTPException(
            status_code=404,
            detail=_error("NO_VIDEO", "This camera has no RTSP feed."),
        )
    stream_path = camera.rtsp_url.rstrip("/").rsplit("/", 1)[-1]
    filename = _RTSP_PATH_TO_MP4.get(stream_path)
    if not filename:
        raise HTTPException(
            status_code=404,
            detail=_error("NO_VIDEO", f"No demo clip mapped for stream path '{stream_path}'."),
        )
    disk_path = os.path.join(EMULATOR_MEDIA_PATH, filename)
    if not os.path.exists(disk_path):
        raise HTTPException(
            status_code=404,
            detail=_error("NO_VIDEO", f"Demo clip '{filename}' not found on disk."),
        )
    return FileResponse(disk_path, media_type="video/mp4")


@router.delete("/{camera_id}")
def remove_camera(camera_id: str, db: Session = Depends(get_db)):
    _get_or_404(db, camera_id)
    delete_camera(db, camera_id)
    return {"status": "success", "message": f"Camera '{camera_id}' removed."}
