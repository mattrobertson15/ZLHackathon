import os

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import UPLOAD_STORAGE_PATH
from app.db.database import get_db
from app.db.repositories import (
    get_upload,
    get_zone,
    list_detection_results_for_upload,
    update_upload_status,
)
from app.services.analysis_pipeline import run_analysis_pipeline
from app.services.serializers import serialize_alert, serialize_detection, serialize_event
from app.utils.video_frames import extract_frames

router = APIRouter(tags=["inference"])


def _error(code: str, message: str):
    return {"error": {"code": code, "message": message}}


class AnalyzeRequest(BaseModel):
    modelProvider: str = "auto"
    createEvents: bool = True
    createAlerts: bool = True


def _serialize_raw_detection(upload_id: str, source: str, detection: dict) -> dict:
    return {
        "uploadId": upload_id,
        "frameTimestamp": detection.get("frameTimestamp"),
        "label": detection["label"],
        "confidence": detection["confidence"],
        "boundingBox": detection.get("boundingBox"),
        "source": source,
    }


def _serialize_comparison(upload_id: str, comparison: dict) -> dict:
    return {
        "roboflow": {
            "provider": comparison["roboflow"]["provider"],
            "source": comparison["roboflow"]["source"],
            "available": comparison["roboflow"]["available"],
            "error": comparison["roboflow"]["error"],
            "detections": [
                _serialize_raw_detection(upload_id, comparison["roboflow"]["source"], detection)
                for detection in comparison["roboflow"]["detections"]
            ],
        },
        "qwen": {
            "provider": comparison["qwen"]["provider"],
            "source": comparison["qwen"]["source"],
            "available": comparison["qwen"]["available"],
            "error": comparison["qwen"]["error"],
            "detections": [
                _serialize_raw_detection(upload_id, comparison["qwen"]["source"], detection)
                for detection in comparison["qwen"]["detections"]
            ],
        },
        "agreement": comparison["agreement"],
    }


def _resolve_disk_path(file_url: str) -> str:
    stored_name = file_url.removeprefix("/media/")
    return os.path.join(UPLOAD_STORAGE_PATH, stored_name)


@router.post("/uploads/{upload_id}/analyze")
def analyze_upload(upload_id: str, request: AnalyzeRequest, db: Session = Depends(get_db)):
    valid_providers = {"auto", "roboflow", "qwen_vision", "manual_mock", "compare"}
    if request.modelProvider not in valid_providers:
        raise HTTPException(
            status_code=400,
            detail=_error(
                "INVALID_MODEL_PROVIDER",
                f"modelProvider must be one of {sorted(valid_providers)}.",
            ),
        )

    upload = get_upload(db, upload_id)
    if upload is None:
        raise HTTPException(
            status_code=404,
            detail=_error("UPLOAD_NOT_FOUND", f"No upload found for id '{upload_id}'."),
        )

    update_upload_status(db, upload_id, "processing")

    try:
        disk_path = _resolve_disk_path(upload.file_url)
        if upload.file_type == "image":
            frames = [{"path": disk_path, "frameTimestamp": None}]
            frame_url_by_timestamp = {None: upload.file_url}
        else:
            frame_dir = os.path.join(UPLOAD_STORAGE_PATH, f"{upload_id}_frames")
            frames = [
                {"path": f["framePath"], "frameTimestamp": f["frameTimestamp"]}
                for f in extract_frames(disk_path, frame_dir)
            ]
            frame_url_by_timestamp = {
                f["frameTimestamp"]: f"/media/{upload_id}_frames/{os.path.basename(f['path'])}"
                for f in frames
            }

        # Zone-aware rules: an upload assigned to a zone (directly or via its
        # camera) gets that zone's required-PPE + severity overrides.
        zone = get_zone(db, upload.zone_id) if upload.zone_id else None
        result = run_analysis_pipeline(
            db,
            upload_id,
            frames,
            frame_url_by_timestamp,
            provider=request.modelProvider,
            create_events=request.createEvents,
            create_alerts_flag=request.createAlerts,
            zone=zone,
        )
        detections = result["detections"]
        events = result["events"]
        alerts = result["alerts"]
        source = result["source"]
        comparison = (
            _serialize_comparison(upload_id, result["comparison"])
            if result["comparison"] is not None
            else None
        )

        update_upload_status(db, upload_id, "processed")
    except Exception as exc:
        update_upload_status(db, upload_id, "failed")
        raise HTTPException(
            status_code=500,
            detail=_error("INFERENCE_FAILED", f"Vision inference failed: {exc}"),
        ) from exc

    response = {
        "uploadId": upload_id,
        "status": "processed",
        "modelProvider": request.modelProvider,
        "primarySource": source,
        "detections": [serialize_detection(d) for d in detections],
        "events": [serialize_event(e) for e in events],
        "alerts": [serialize_alert(a) for a in alerts],
    }
    if comparison is not None:
        response["comparison"] = comparison
    return response


@router.get("/uploads/{upload_id}/detections")
def get_detections(upload_id: str, db: Session = Depends(get_db)):
    upload = get_upload(db, upload_id)
    if upload is None:
        raise HTTPException(
            status_code=404,
            detail=_error("UPLOAD_NOT_FOUND", f"No upload found for id '{upload_id}'."),
        )
    detections = list_detection_results_for_upload(db, upload_id)
    return {"uploadId": upload_id, "detections": [serialize_detection(d) for d in detections]}
