"""Background monitor that turns live RTSP cameras into SafetyEvents.

A single daemon thread (started from main.py on startup) periodically captures
frames from every camera with ``monitoring=True`` and runs them through the
shared analysis pipeline. Each capture cycle is recorded as an Upload row
(``source_type="camera"``) so events flow into the existing dashboard, events,
alerts, and analytics unchanged.

Disabled on Vercel (``IS_VERCEL``) where there is no long-lived process.

See ARCHITECTURE.md#camera--rtsp-ingestion-layer.
"""
import os
import threading
import time

from sqlalchemy.orm import Session

from app.config import IS_VERCEL, UPLOAD_STORAGE_PATH
from app.db.database import SessionLocal
from app.db.repositories import (
    create_upload,
    delete_safety_events_with_alerts,
    find_recent_open_violation_for_camera,
    get_zone,
    list_monitoring_cameras,
    update_camera,
    update_upload_status,
)
from app.models.camera import Camera
from app.models.upload import Upload
from app.services.analysis_pipeline import run_analysis_pipeline
from app.utils.ids import generate_id
from app.utils.rtsp_capture import capture_frames_from_rtsp
from app.utils.timestamps import now_utc

# How often the loop wakes up to check which cameras are due for a capture.
# Kept low so a 1–2s capture interval (snappy walk-by demo) is actually honored.
MONITOR_TICK_SECONDS = 1.0

# Suppress duplicate violation events/alerts for the same person lingering in
# frame: at most one event per (camera, violation_type) within this window.
DEDUP_WINDOW_SECONDS = 30

# Live captures favor a snappy cycle over many frames; one or two frames is
# enough to catch a walk-by while keeping inference cost and latency low.
LIVE_CAPTURE_NUM_FRAMES = 2
LIVE_CAPTURE_SPACING_SECONDS = 0.5

_stop_event: threading.Event | None = None
_thread: threading.Thread | None = None


def capture_and_analyze(db: Session, camera: Camera) -> dict:
    """Capture frames from one camera and run the full analysis pipeline.

    Creates an Upload (source_type="camera") that inherits the camera's zone, so
    captures get the same zone-aware rules as uploads. Persists
    detections/events/alerts and updates the camera's stream_status /
    last_capture_at. Raises on capture failure after marking the camera errored.
    """
    upload_id = generate_id("cam_upl")
    frame_dir = os.path.join(UPLOAD_STORAGE_PATH, f"{upload_id}_frames")

    upload = Upload(
        id=upload_id,
        file_name=f"{camera.display_name} capture",
        file_type="video",
        file_url="",  # set to the first captured frame below
        location_label=camera.display_name,
        zone_id=camera.zone_id,
        notes=f"Live capture from camera {camera.id} ({camera.rtsp_url}).",
        status="processing",
        source_type="camera",
        camera_id=camera.id,
        uploaded_at=now_utc(),
    )
    upload = create_upload(db, upload)

    try:
        captured = capture_frames_from_rtsp(
            camera.rtsp_url,
            frame_dir,
            num_frames=LIVE_CAPTURE_NUM_FRAMES,
            spacing_seconds=LIVE_CAPTURE_SPACING_SECONDS,
        )
    except Exception as exc:
        update_upload_status(db, upload_id, "failed")
        camera.stream_status = "error"
        camera.last_error = str(exc)
        camera.last_capture_at = now_utc()
        update_camera(db, camera)
        raise

    frames = [
        {"path": f["framePath"], "frameTimestamp": f["frameTimestamp"]}
        for f in captured
    ]
    frame_url_by_timestamp = {
        f["frameTimestamp"]: f"/media/{upload_id}_frames/{os.path.basename(f['path'])}"
        for f in captured
    }

    # Point the upload (and the camera snapshot) at the first captured frame.
    upload.file_url = next(iter(frame_url_by_timestamp.values()))
    db.commit()

    zone = get_zone(db, camera.zone_id) if camera.zone_id else None
    result = run_analysis_pipeline(
        db,
        upload_id,
        frames,
        frame_url_by_timestamp,
        provider="auto",
        create_events=True,
        create_alerts_flag=True,
        zone=zone,
    )

    result["events"] = _dedup_violation_events(db, camera, upload_id, result["events"])

    update_upload_status(db, upload_id, "processed")

    camera.stream_status = "live"
    camera.last_error = None
    camera.last_capture_at = now_utc()
    update_camera(db, camera)

    return result


def _dedup_violation_events(db, camera, upload_id, events):
    """Keep at most one open event per (camera, violation_type) within the dedup
    window. Drops both intra-capture duplicates (the rule engine fires once per
    frame) and repeats of a violation already open from a recent cycle, deleting
    the redundant events and their alerts. Non-violation events pass through.
    """
    kept = []
    removed_ids = []
    seen_types = set()
    for event in events:
        if event.event_type != "ppe_violation" or not event.violation_type:
            kept.append(event)
            continue
        vtype = event.violation_type
        is_duplicate = vtype in seen_types or (
            find_recent_open_violation_for_camera(
                db, camera.id, vtype, DEDUP_WINDOW_SECONDS, exclude_upload_id=upload_id
            )
            is not None
        )
        if is_duplicate:
            removed_ids.append(event.id)
            continue
        seen_types.add(vtype)
        kept.append(event)

    if removed_ids:
        delete_safety_events_with_alerts(db, removed_ids)
    return kept


def _is_due(camera: Camera) -> bool:
    if camera.last_capture_at is None:
        return True
    elapsed = (now_utc() - _as_utc(camera.last_capture_at)).total_seconds()
    return elapsed >= camera.capture_interval_seconds


def _as_utc(dt):
    # SQLite returns naive datetimes; treat them as UTC for elapsed math.
    from datetime import timezone

    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def _monitor_loop(stop_event: threading.Event) -> None:
    while not stop_event.is_set():
        db = SessionLocal()
        try:
            for camera in list_monitoring_cameras(db):
                if not _is_due(camera):
                    continue
                try:
                    capture_and_analyze(db, camera)
                except Exception as exc:  # noqa: BLE001 — never let one feed kill the loop
                    print(f"Camera monitor: capture failed for {camera.id}: {exc}")
        except Exception as exc:  # noqa: BLE001
            print(f"Camera monitor: loop iteration error: {exc}")
        finally:
            db.close()
        stop_event.wait(MONITOR_TICK_SECONDS)


def start_monitor() -> None:
    """Start the background monitor thread (no-op on Vercel or if already running)."""
    global _stop_event, _thread
    if IS_VERCEL:
        return
    if _thread is not None and _thread.is_alive():
        return
    _stop_event = threading.Event()
    _thread = threading.Thread(target=_monitor_loop, args=(_stop_event,), daemon=True)
    _thread.start()


def stop_monitor() -> None:
    global _stop_event, _thread
    if _stop_event is not None:
        _stop_event.set()
    if _thread is not None:
        _thread.join(timeout=MONITOR_TICK_SECONDS + 1)
    _stop_event = None
    _thread = None
