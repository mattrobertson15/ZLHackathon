from datetime import timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.alert_record import AlertRecord
from app.models.detection_result import DetectionResult
from app.models.safety_event import SafetyEvent
from app.models.upload import Upload
from app.utils.timestamps import now_utc, to_iso

router = APIRouter(prefix="/admin", tags=["admin"])

DEMO_UPLOAD_IDS = [
    "demo_loading_dock",
    "demo_warehouse_aisle",
    "demo_packout_line",
]


def _serialize_upload(upload: Upload) -> dict:
    return {
        "id": upload.id,
        "fileName": upload.file_name,
        "fileType": upload.file_type,
        "fileUrl": upload.file_url,
        "locationLabel": upload.location_label,
        "notes": upload.notes,
        "uploadedAt": to_iso(upload.uploaded_at),
        "status": upload.status,
    }


@router.post("/reset")
def reset_incidents(db: Session = Depends(get_db)):
    """Reset all incidents by clearing SafetyEvents, AlertRecords, and DetectionResults."""
    try:
        db.query(DetectionResult).delete()
        db.query(AlertRecord).delete()
        db.query(SafetyEvent).delete()
        db.commit()
        return {"status": "success", "message": "All incidents reset successfully"}
    except Exception as e:
        db.rollback()
        return {"status": "error", "message": str(e)}, 500


@router.post("/demo-scenario")
def load_demo_scenario(db: Session = Depends(get_db)):
    """Seed a repeatable hackathon demo scenario into the real app tables."""
    try:
        db.query(AlertRecord).filter(
            AlertRecord.safety_event_id.in_(
                [
                    "demo_evt_loading_helmet",
                    "demo_evt_loading_vest",
                    "demo_evt_aisle_positive",
                    "demo_evt_aisle_uncertain",
                    "demo_evt_packout_vest",
                    "demo_evt_packout_positive",
                ]
            )
        ).delete(synchronize_session=False)
        db.query(SafetyEvent).filter(SafetyEvent.upload_id.in_(DEMO_UPLOAD_IDS)).delete(
            synchronize_session=False
        )
        db.query(DetectionResult).filter(
            DetectionResult.upload_id.in_(DEMO_UPLOAD_IDS)
        ).delete(synchronize_session=False)
        db.query(Upload).filter(Upload.id.in_(DEMO_UPLOAD_IDS)).delete(
            synchronize_session=False
        )

        base_time = now_utc()
        uploads = [
            Upload(
                id="demo_loading_dock",
                file_name="Loading Dock PPE Review.jpg",
                file_type="image",
                file_url="/media/002823.jpg",
                location_label="Loading Dock",
                notes="Demo scenario: morning inbound freight with missing helmet and vest observations.",
                status="processed",
                uploaded_at=base_time - timedelta(days=4, hours=2),
            ),
            Upload(
                id="demo_warehouse_aisle",
                file_name="Warehouse Aisle Shift Check.jpg",
                file_type="image",
                file_url="/media/006956.jpg",
                location_label="Warehouse Aisle 3",
                notes="Demo scenario: mixed compliant observations and one manual review item.",
                status="processed",
                uploaded_at=base_time - timedelta(days=2, hours=5),
            ),
            Upload(
                id="demo_packout_line",
                file_name="Packout Line PPE Spot Check.jpg",
                file_type="image",
                file_url="/media/helmet9991192.jpg",
                location_label="Packout Line",
                notes="Demo scenario: recent spot check used for dashboard and alert walkthrough.",
                status="processed",
                uploaded_at=base_time - timedelta(hours=4),
            ),
        ]

        detections = [
            DetectionResult(
                id="demo_det_loading_person",
                upload_id="demo_loading_dock",
                frame_timestamp=None,
                label="person",
                confidence=0.95,
                bbox_x=118,
                bbox_y=70,
                bbox_width=210,
                bbox_height=500,
                source="manual_mock",
                created_at=base_time - timedelta(days=4, hours=1, minutes=59),
            ),
            DetectionResult(
                id="demo_det_loading_no_helmet",
                upload_id="demo_loading_dock",
                frame_timestamp=None,
                label="no_helmet",
                confidence=0.89,
                bbox_x=152,
                bbox_y=78,
                bbox_width=72,
                bbox_height=66,
                source="manual_mock",
                created_at=base_time - timedelta(days=4, hours=1, minutes=59),
            ),
            DetectionResult(
                id="demo_det_loading_no_vest",
                upload_id="demo_loading_dock",
                frame_timestamp=None,
                label="no_vest",
                confidence=0.82,
                bbox_x=138,
                bbox_y=160,
                bbox_width=142,
                bbox_height=230,
                source="manual_mock",
                created_at=base_time - timedelta(days=4, hours=1, minutes=59),
            ),
            DetectionResult(
                id="demo_det_aisle_person",
                upload_id="demo_warehouse_aisle",
                frame_timestamp=None,
                label="person",
                confidence=0.93,
                bbox_x=90,
                bbox_y=82,
                bbox_width=190,
                bbox_height=455,
                source="manual_mock",
                created_at=base_time - timedelta(days=2, hours=4, minutes=59),
            ),
            DetectionResult(
                id="demo_det_aisle_helmet",
                upload_id="demo_warehouse_aisle",
                frame_timestamp=None,
                label="helmet",
                confidence=0.91,
                bbox_x=126,
                bbox_y=88,
                bbox_width=78,
                bbox_height=58,
                source="manual_mock",
                created_at=base_time - timedelta(days=2, hours=4, minutes=59),
            ),
            DetectionResult(
                id="demo_det_aisle_vest",
                upload_id="demo_warehouse_aisle",
                frame_timestamp=None,
                label="vest",
                confidence=0.88,
                bbox_x=110,
                bbox_y=165,
                bbox_width=130,
                bbox_height=220,
                source="manual_mock",
                created_at=base_time - timedelta(days=2, hours=4, minutes=59),
            ),
            DetectionResult(
                id="demo_det_packout_person",
                upload_id="demo_packout_line",
                frame_timestamp=None,
                label="person",
                confidence=0.97,
                bbox_x=170,
                bbox_y=60,
                bbox_width=235,
                bbox_height=520,
                source="manual_mock",
                created_at=base_time - timedelta(hours=3, minutes=59),
            ),
            DetectionResult(
                id="demo_det_packout_helmet",
                upload_id="demo_packout_line",
                frame_timestamp=None,
                label="helmet",
                confidence=0.94,
                bbox_x=206,
                bbox_y=68,
                bbox_width=84,
                bbox_height=62,
                source="manual_mock",
                created_at=base_time - timedelta(hours=3, minutes=59),
            ),
            DetectionResult(
                id="demo_det_packout_no_vest",
                upload_id="demo_packout_line",
                frame_timestamp=None,
                label="no_vest",
                confidence=0.79,
                bbox_x=190,
                bbox_y=154,
                bbox_width=150,
                bbox_height=240,
                source="manual_mock",
                created_at=base_time - timedelta(hours=3, minutes=59),
            ),
        ]

        events = [
            SafetyEvent(
                id="demo_evt_loading_helmet",
                upload_id="demo_loading_dock",
                event_type="ppe_violation",
                violation_type="no_helmet",
                severity="high",
                confidence=0.89,
                status="open",
                status_updated_at=base_time - timedelta(days=4, hours=1, minutes=58),
                suggested_action="Supervisor review recommended. Helmet appears missing near the loading dock.",
                created_at=base_time - timedelta(days=4, hours=1, minutes=58),
            ),
            SafetyEvent(
                id="demo_evt_loading_vest",
                upload_id="demo_loading_dock",
                event_type="ppe_violation",
                violation_type="no_vest",
                severity="medium",
                confidence=0.82,
                status="reviewed",
                status_updated_at=base_time - timedelta(days=4, hours=1, minutes=10),
                suggested_action="Coaching reminder recommended. Safety vest appears missing during freight handling.",
                created_at=base_time - timedelta(days=4, hours=1, minutes=57),
            ),
            SafetyEvent(
                id="demo_evt_aisle_positive",
                upload_id="demo_warehouse_aisle",
                event_type="positive_observation",
                violation_type=None,
                severity="low",
                confidence=0.9,
                status="reviewed",
                status_updated_at=base_time - timedelta(days=2, hours=4, minutes=20),
                suggested_action="No action required. Helmet and vest appear present.",
                created_at=base_time - timedelta(days=2, hours=4, minutes=55),
            ),
            SafetyEvent(
                id="demo_evt_aisle_uncertain",
                upload_id="demo_warehouse_aisle",
                event_type="uncertain_review",
                violation_type=None,
                severity="low",
                confidence=0.68,
                status="open",
                status_updated_at=base_time - timedelta(days=2, hours=4, minutes=54),
                suggested_action="Manual review recommended. PPE state is partially obscured.",
                created_at=base_time - timedelta(days=2, hours=4, minutes=54),
            ),
            SafetyEvent(
                id="demo_evt_packout_vest",
                upload_id="demo_packout_line",
                event_type="ppe_violation",
                violation_type="no_vest",
                severity="medium",
                confidence=0.79,
                status="open",
                status_updated_at=base_time - timedelta(hours=3, minutes=55),
                suggested_action="Coaching reminder recommended. Vest appears missing on the packout line.",
                created_at=base_time - timedelta(hours=3, minutes=55),
            ),
            SafetyEvent(
                id="demo_evt_packout_positive",
                upload_id="demo_packout_line",
                event_type="positive_observation",
                violation_type=None,
                severity="low",
                confidence=0.94,
                status="reviewed",
                status_updated_at=base_time - timedelta(hours=3, minutes=20),
                suggested_action="No action required. Helmet appears present.",
                created_at=base_time - timedelta(hours=3, minutes=54),
            ),
        ]

        alerts = [
            AlertRecord(
                id="demo_alrt_loading_helmet",
                safety_event_id="demo_evt_loading_helmet",
                alert_type="supervisor_review",
                title="Missing Helmet Detected",
                message="A high-severity PPE violation was detected at the loading dock. Supervisor review is recommended.",
                status="draft",
                created_at=base_time - timedelta(days=4, hours=1, minutes=56),
            ),
            AlertRecord(
                id="demo_alrt_loading_vest",
                safety_event_id="demo_evt_loading_vest",
                alert_type="coaching_reminder",
                title="Missing Vest Detected",
                message="A medium-severity PPE violation was detected during freight handling. A coaching reminder is recommended.",
                status="sent_mock",
                created_at=base_time - timedelta(days=4, hours=1, minutes=56),
            ),
            AlertRecord(
                id="demo_alrt_aisle_manual",
                safety_event_id="demo_evt_aisle_uncertain",
                alert_type="manual_review",
                title="PPE Status Unclear",
                message="Detection confidence was low or PPE status was unclear. Manual review is recommended.",
                status="queued",
                created_at=base_time - timedelta(days=2, hours=4, minutes=53),
            ),
            AlertRecord(
                id="demo_alrt_packout_vest",
                safety_event_id="demo_evt_packout_vest",
                alert_type="coaching_reminder",
                title="Missing Vest Detected",
                message="A medium-severity PPE violation was detected on the packout line. A coaching reminder is recommended.",
                status="draft",
                created_at=base_time - timedelta(hours=3, minutes=53),
            ),
        ]

        db.add_all(uploads)
        db.add_all(detections)
        db.add_all(events)
        db.add_all(alerts)
        db.commit()

        return {
            "status": "success",
            "scenario": "warehouse_shift_review",
            "message": "Warehouse shift demo scenario loaded.",
            "uploads": [_serialize_upload(upload) for upload in uploads],
            "counts": {
                "uploads": len(uploads),
                "detections": len(detections),
                "events": len(events),
                "alerts": len(alerts),
            },
        }
    except Exception as e:
        db.rollback()
        return {"status": "error", "message": str(e)}, 500
