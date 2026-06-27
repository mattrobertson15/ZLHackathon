from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.models.alert_record import AlertRecord
from app.models.camera import Camera
from app.models.detection_result import DetectionResult
from app.models.safety_event import SafetyEvent
from app.models.upload import Upload


# --- Cameras ---------------------------------------------------------------

def create_camera(db: Session, camera: Camera) -> Camera:
    db.add(camera)
    db.commit()
    db.refresh(camera)
    return camera


def list_cameras(db: Session) -> list[Camera]:
    return db.query(Camera).order_by(Camera.created_at.desc()).all()


def list_monitoring_cameras(db: Session) -> list[Camera]:
    return db.query(Camera).filter(Camera.monitoring.is_(True)).all()


def get_camera(db: Session, camera_id: str) -> Optional[Camera]:
    return db.query(Camera).filter(Camera.id == camera_id).first()


def update_camera(db: Session, camera: Camera) -> Camera:
    db.commit()
    db.refresh(camera)
    return camera


def delete_camera(db: Session, camera_id: str) -> bool:
    camera = get_camera(db, camera_id)
    if camera is None:
        return False
    db.delete(camera)
    db.commit()
    return True


def list_uploads_for_camera(db: Session, camera_id: str, limit: Optional[int] = None) -> list[Upload]:
    query = (
        db.query(Upload)
        .filter(Upload.camera_id == camera_id)
        .order_by(Upload.uploaded_at.desc())
    )
    if limit:
        query = query.limit(limit)
    return query.all()


def count_events_for_camera(db: Session, camera_id: str) -> int:
    return (
        db.query(SafetyEvent)
        .join(Upload, SafetyEvent.upload_id == Upload.id)
        .filter(Upload.camera_id == camera_id)
        .count()
    )


def list_events_for_camera(db: Session, camera_id: str, limit: Optional[int] = None) -> list[SafetyEvent]:
    query = (
        db.query(SafetyEvent)
        .join(Upload, SafetyEvent.upload_id == Upload.id)
        .filter(Upload.camera_id == camera_id)
        .order_by(SafetyEvent.created_at.desc())
    )
    if limit:
        query = query.limit(limit)
    return query.all()


# --- Uploads ---------------------------------------------------------------

def create_upload(db: Session, upload: Upload) -> Upload:
    db.add(upload)
    db.commit()
    db.refresh(upload)
    return upload


def list_uploads(db: Session, limit: Optional[int] = None):
    query = db.query(Upload).order_by(Upload.uploaded_at.desc())
    if limit:
        query = query.limit(limit)
    return query.all()


def get_upload(db: Session, upload_id: str) -> Optional[Upload]:
    return db.query(Upload).filter(Upload.id == upload_id).first()


def update_upload_status(db: Session, upload_id: str, status: str) -> Optional[Upload]:
    upload = get_upload(db, upload_id)
    if upload is None:
        return None
    upload.status = status
    db.commit()
    db.refresh(upload)
    return upload


def create_detection_results(db: Session, detections: list[DetectionResult]) -> list[DetectionResult]:
    db.add_all(detections)
    db.commit()
    for detection in detections:
        db.refresh(detection)
    return detections


def list_detection_results_for_upload(db: Session, upload_id: str) -> list[DetectionResult]:
    return (
        db.query(DetectionResult)
        .filter(DetectionResult.upload_id == upload_id)
        .order_by(DetectionResult.frame_timestamp, DetectionResult.created_at)
        .all()
    )


def create_safety_events(db: Session, events: list[SafetyEvent]) -> list[SafetyEvent]:
    db.add_all(events)
    db.commit()
    for event in events:
        db.refresh(event)
    return events


def list_safety_events(
    db: Session,
    status: Optional[str] = None,
    event_type: Optional[str] = None,
    violation_type: Optional[str] = None,
    severity: Optional[str] = None,
    limit: Optional[int] = None,
) -> list[SafetyEvent]:
    query = db.query(SafetyEvent)
    if status:
        query = query.filter(SafetyEvent.status == status)
    if event_type:
        query = query.filter(SafetyEvent.event_type == event_type)
    if violation_type:
        query = query.filter(SafetyEvent.violation_type == violation_type)
    if severity:
        query = query.filter(SafetyEvent.severity == severity)
    query = query.order_by(SafetyEvent.created_at.desc())
    if limit:
        query = query.limit(limit)
    return query.all()


def list_safety_events_since(db: Session, since: Optional[datetime] = None) -> list[SafetyEvent]:
    query = db.query(SafetyEvent)
    if since:
        query = query.filter(SafetyEvent.created_at >= since)
    return query.order_by(SafetyEvent.created_at.asc()).all()


def list_safety_events_in_range(
    db: Session, start_date: datetime, end_date: datetime
) -> list[SafetyEvent]:
    return (
        db.query(SafetyEvent)
        .filter(SafetyEvent.created_at >= start_date)
        .filter(SafetyEvent.created_at <= end_date)
        .order_by(SafetyEvent.created_at.asc())
        .all()
    )


def get_safety_event(db: Session, event_id: str) -> Optional[SafetyEvent]:
    return db.query(SafetyEvent).filter(SafetyEvent.id == event_id).first()


def update_safety_event_status(
    db: Session, event_id: str, status: str, note: Optional[str] = None
) -> Optional[SafetyEvent]:
    event = get_safety_event(db, event_id)
    if event is None:
        return None
    event.status = status
    event.status_updated_at = datetime.now(timezone.utc)
    if note is not None:
        event.review_note = note
    db.commit()
    db.refresh(event)
    return event


def list_safety_events_for_upload(db: Session, upload_id: str) -> list[SafetyEvent]:
    return (
        db.query(SafetyEvent)
        .filter(SafetyEvent.upload_id == upload_id)
        .order_by(SafetyEvent.created_at.asc())
        .all()
    )


def list_alerts_for_upload(db: Session, upload_id: str) -> list[AlertRecord]:
    return (
        db.query(AlertRecord)
        .join(SafetyEvent, AlertRecord.safety_event_id == SafetyEvent.id)
        .filter(SafetyEvent.upload_id == upload_id)
        .order_by(AlertRecord.created_at.asc())
        .all()
    )


def create_alerts(db: Session, alerts: list[AlertRecord]) -> list[AlertRecord]:
    db.add_all(alerts)
    db.commit()
    for alert in alerts:
        db.refresh(alert)
    return alerts


def list_alerts(
    db: Session,
    status: Optional[str] = None,
    alert_type: Optional[str] = None,
    limit: Optional[int] = None,
) -> list[AlertRecord]:
    query = db.query(AlertRecord)
    if status:
        query = query.filter(AlertRecord.status == status)
    if alert_type:
        query = query.filter(AlertRecord.alert_type == alert_type)
    query = query.order_by(AlertRecord.created_at.desc())
    if limit:
        query = query.limit(limit)
    return query.all()


def get_alert(db: Session, alert_id: str) -> Optional[AlertRecord]:
    return db.query(AlertRecord).filter(AlertRecord.id == alert_id).first()


def update_alert_status(db: Session, alert_id: str, status: str) -> Optional[AlertRecord]:
    alert = get_alert(db, alert_id)
    if alert is None:
        return None
    alert.status = status
    db.commit()
    db.refresh(alert)
    return alert
