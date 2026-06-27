import os

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import UPLOAD_STORAGE_PATH
from app.db.database import get_db
from app.db.repositories import (
    create_alerts,
    create_detection_results,
    create_safety_events,
    get_upload,
    list_detection_results_for_upload,
    update_upload_status,
)
from app.models.alert_record import AlertRecord
from app.models.detection_result import DetectionResult
from app.models.safety_event import SafetyEvent
from app.services import alert_service, rule_engine, vision_service
from app.services.detection_parser import normalize_detections
from app.utils.timestamps import to_iso
from app.utils.video_frames import extract_frames

router = APIRouter(tags=["inference"])


def _error(code: str, message: str):
    return {"error": {"code": code, "message": message}}


class AnalyzeRequest(BaseModel):
    modelProvider: str = "auto"
    createEvents: bool = True
    createAlerts: bool = True


def _serialize_detection(detection: DetectionResult) -> dict:
    bounding_box = None
    if detection.bbox_x is not None:
        bounding_box = {
            "x": detection.bbox_x,
            "y": detection.bbox_y,
            "width": detection.bbox_width,
            "height": detection.bbox_height,
        }
    return {
        "id": detection.id,
        "uploadId": detection.upload_id,
        "frameTimestamp": detection.frame_timestamp,
        "label": detection.label,
        "confidence": detection.confidence,
        "boundingBox": bounding_box,
        "source": detection.source,
        "createdAt": to_iso(detection.created_at),
    }


def _serialize_event(event: SafetyEvent) -> dict:
    return {
        "id": event.id,
        "uploadId": event.upload_id,
        "eventType": event.event_type,
        "violationType": event.violation_type,
        "severity": event.severity,
        "confidence": event.confidence,
        "status": event.status,
        "suggestedAction": event.suggested_action,
        "createdAt": to_iso(event.created_at),
    }


def _serialize_alert(alert: AlertRecord) -> dict:
    return {
        "id": alert.id,
        "safetyEventId": alert.safety_event_id,
        "alertType": alert.alert_type,
        "title": alert.title,
        "message": alert.message,
        "status": alert.status,
        "createdAt": to_iso(alert.created_at),
    }


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
        else:
            frame_dir = os.path.join(UPLOAD_STORAGE_PATH, f"{upload_id}_frames")
            frames = [
                {"path": f["framePath"], "frameTimestamp": f["frameTimestamp"]}
                for f in extract_frames(disk_path, frame_dir)
            ]

        comparison = None
        if request.modelProvider == "compare":
            comparison_result = vision_service.run_comparison(frames)
            primary = comparison_result["primary"]
            raw_detections = primary["detections"]
            source = primary["source"]
            comparison = _serialize_comparison(upload_id, comparison_result["comparison"])
        elif request.modelProvider in {"roboflow", "qwen_vision"}:
            raw_detections, source = vision_service.run_inference_with_fallback(
                frames, request.modelProvider
            )
        else:
            raw_detections, source = vision_service.run_inference(frames, request.modelProvider)

        detections = normalize_detections(raw_detections, upload_id, source)
        detections = create_detection_results(db, detections)

        events: list[SafetyEvent] = []
        if request.createEvents:
            events = rule_engine.evaluate(detections, upload_id)
            events = create_safety_events(db, events)

        alerts: list[AlertRecord] = []
        if request.createAlerts and events:
            alerts = alert_service.generate_alerts(events)
            alerts = create_alerts(db, alerts)

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
        "detections": [_serialize_detection(d) for d in detections],
        "events": [_serialize_event(e) for e in events],
        "alerts": [_serialize_alert(a) for a in alerts],
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
    return {"uploadId": upload_id, "detections": [_serialize_detection(d) for d in detections]}
