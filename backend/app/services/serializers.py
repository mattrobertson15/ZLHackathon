from app.models.alert_record import AlertRecord
from app.models.camera import Camera
from app.models.detection_result import DetectionResult
from app.models.safety_event import SafetyEvent
from app.models.upload import Upload
from app.utils.timestamps import to_iso


def serialize_upload(upload: Upload) -> dict:
    return {
        "id": upload.id,
        "fileName": upload.file_name,
        "fileType": upload.file_type,
        "fileUrl": upload.file_url,
        "locationLabel": upload.location_label,
        "notes": upload.notes,
        "sourceType": getattr(upload, "source_type", None) or "upload",
        "cameraId": getattr(upload, "camera_id", None),
        "uploadedAt": to_iso(upload.uploaded_at),
        "status": upload.status,
    }


def serialize_camera(camera: Camera, recent_event_count: int = 0) -> dict:
    return {
        "id": camera.id,
        "label": camera.label,
        "rtspUrl": camera.rtsp_url,
        "locationLabel": camera.location_label,
        "status": camera.status,
        "monitoring": camera.monitoring,
        "captureIntervalSeconds": camera.capture_interval_seconds,
        "lastCaptureAt": to_iso(camera.last_capture_at) if camera.last_capture_at else None,
        "lastError": camera.last_error,
        "recentEventCount": recent_event_count,
        "createdAt": to_iso(camera.created_at),
    }


def serialize_detection(detection: DetectionResult) -> dict:
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
        "frameUrl": detection.frame_url,
        "source": detection.source,
        "createdAt": to_iso(detection.created_at),
    }


def serialize_event(event: SafetyEvent) -> dict:
    return {
        "id": event.id,
        "uploadId": event.upload_id,
        "eventType": event.event_type,
        "violationType": event.violation_type,
        "severity": event.severity,
        "confidence": event.confidence,
        "status": event.status,
        "statusUpdatedAt": to_iso(event.status_updated_at) if event.status_updated_at else None,
        "reviewNote": event.review_note,
        "suggestedAction": event.suggested_action,
        "createdAt": to_iso(event.created_at),
    }


def serialize_alert(alert: AlertRecord) -> dict:
    return {
        "id": alert.id,
        "safetyEventId": alert.safety_event_id,
        "alertType": alert.alert_type,
        "title": alert.title,
        "message": alert.message,
        "status": alert.status,
        "createdAt": to_iso(alert.created_at),
    }
