from datetime import timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.repositories import get_zone
from app.models.alert_record import AlertRecord
from app.models.detection_result import DetectionResult
from app.models.safety_event import SafetyEvent
from app.models.upload import Upload
from app.utils.timestamps import now_utc, to_iso

router = APIRouter(prefix="/admin", tags=["admin"])

# Current demo uploads plus legacy ids from earlier scenarios, so re-running the
# loader cleans up both. See ZONE_CAMERA_PLAN.md#7-sample-dataset.
DEMO_UPLOAD_IDS = [
    "demo_dock_mon",
    "demo_dock_wed",
    "demo_dock_fri",
    "demo_dock_obscured",
    "demo_floor_entry",
    "demo_welding_bay",
    "demo_packout_legacy",
    # legacy ids
    "demo_loading_dock",
    "demo_warehouse_aisle",
    "demo_packout_line",
]

DEMO_EVENT_IDS = [
    "demo_evt_dock_mon_vest",
    "demo_evt_dock_wed_vest",
    "demo_evt_dock_fri_vest",
    "demo_evt_floor_helmet",
    "demo_evt_weld_helmet",
    "demo_evt_weld_vest",
    "demo_evt_packout_vest",
    "demo_evt_dock_obscured",
    # legacy ids
    "demo_evt_loading_helmet",
    "demo_evt_loading_vest",
    "demo_evt_aisle_positive",
    "demo_evt_aisle_uncertain",
    "demo_evt_packout_vest_legacy",
    "demo_evt_packout_positive",
]


def _serialize_upload(upload: Upload, zone_display_name: str = None) -> dict:
    return {
        "id": upload.id,
        "fileName": upload.file_name,
        "fileType": upload.file_type,
        "fileUrl": upload.file_url,
        "locationLabel": upload.location_label,
        "zoneId": upload.zone_id,
        "cameraId": upload.camera_id,
        "zoneDisplayName": zone_display_name,
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


def _det(det_id, upload_id, label, confidence, created_at):
    return DetectionResult(
        id=det_id,
        upload_id=upload_id,
        frame_timestamp=None,
        label=label,
        confidence=confidence,
        bbox_x=120,
        bbox_y=80,
        bbox_width=140,
        bbox_height=320,
        source="manual_mock",
        created_at=created_at,
    )


@router.post("/demo-scenario")
def load_demo_scenario(db: Session = Depends(get_db)):
    """Seed a repeatable hackathon demo scenario into the real app tables.

    The dataset exercises both the zone-aware rule engine and repeated-zone
    violation detection, and stays consistent with what the rule engine would
    produce per zone (suppressed detections create no event).
    """
    try:
        db.query(AlertRecord).filter(
            AlertRecord.safety_event_id.in_(DEMO_EVENT_IDS)
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

        base = now_utc()

        uploads = [
            Upload(
                id="demo_dock_mon",
                file_name="Loading Dock Inbound AM.jpg",
                file_type="image",
                file_url="/media/002823.jpg",
                location_label="Loading Dock",
                zone_id="loading-dock",
                camera_id="cam-02",
                notes="Demo: vest required at the dock; worker without a vest.",
                status="processed",
                uploaded_at=base - timedelta(days=5, hours=2),
            ),
            Upload(
                id="demo_dock_wed",
                file_name="Loading Dock Midweek Check.jpg",
                file_type="image",
                file_url="/media/006956.jpg",
                location_label="Loading Dock",
                zone_id="loading-dock",
                camera_id="cam-02",
                notes="Demo: second no-vest observation at the dock this week.",
                status="processed",
                uploaded_at=base - timedelta(days=3),
            ),
            Upload(
                id="demo_dock_fri",
                file_name="Loading Dock Friday Spot Check.jpg",
                file_type="image",
                file_url="/media/helmet9991192.jpg",
                location_label="Loading Dock",
                zone_id="loading-dock",
                camera_id="cam-02",
                notes="Demo: third no-vest crosses the repeated-violation threshold; a no-helmet here is suppressed (helmet not required at the dock).",
                status="processed",
                uploaded_at=base - timedelta(hours=18),
            ),
            Upload(
                id="demo_floor_entry",
                file_name="General Floor Entry Check.jpg",
                file_type="image",
                file_url="/media/002883.jpg",
                location_label="General Floor",
                zone_id="general-floor",
                camera_id="cam-01",
                notes="Demo: helmet present (required) is a positive; no-vest here is suppressed (vest not required on the floor).",
                status="processed",
                uploaded_at=base - timedelta(days=2),
            ),
            Upload(
                id="demo_welding_bay",
                file_name="Welding Bay Compliance.jpg",
                file_type="image",
                file_url="/media/005763.jpg",
                location_label="Welding Station",
                zone_id="welding-station",
                camera_id="cam-03",
                notes="Demo: helmet and vest both required and present — fully compliant.",
                status="processed",
                uploaded_at=base - timedelta(hours=6),
            ),
            Upload(
                id="demo_packout_legacy",
                file_name="Packout Line Manual Upload.jpg",
                file_type="image",
                file_url="/media/002823.jpg",
                location_label="Packout Line",
                zone_id=None,
                camera_id=None,
                notes="Demo: legacy manual upload with no zone; falls back to global rules and location label.",
                status="processed",
                uploaded_at=base - timedelta(days=1),
            ),
            Upload(
                id="demo_dock_obscured",
                file_name="Loading Dock Obscured View.jpg",
                file_type="image",
                file_url="/media/006956.jpg",
                location_label="Loading Dock",
                zone_id="loading-dock",
                camera_id="cam-02",
                notes="Demo: person visible but PPE state unclear — routes to manual review.",
                status="processed",
                uploaded_at=base - timedelta(hours=10),
            ),
        ]

        detections = [
            _det("demo_det_dock_mon_person", "demo_dock_mon", "person", 0.95, base - timedelta(days=5, hours=1, minutes=59)),
            _det("demo_det_dock_mon_no_vest", "demo_dock_mon", "no_vest", 0.88, base - timedelta(days=5, hours=1, minutes=59)),
            _det("demo_det_dock_wed_person", "demo_dock_wed", "person", 0.94, base - timedelta(days=2, hours=23, minutes=59)),
            _det("demo_det_dock_wed_no_vest", "demo_dock_wed", "no_vest", 0.86, base - timedelta(days=2, hours=23, minutes=59)),
            _det("demo_det_dock_fri_person", "demo_dock_fri", "person", 0.96, base - timedelta(hours=17, minutes=59)),
            _det("demo_det_dock_fri_no_vest", "demo_dock_fri", "no_vest", 0.90, base - timedelta(hours=17, minutes=59)),
            # no_helmet at the dock is suppressed by the rule engine (helmet not required there)
            _det("demo_det_dock_fri_no_helmet", "demo_dock_fri", "no_helmet", 0.84, base - timedelta(hours=17, minutes=59)),
            _det("demo_det_floor_person", "demo_floor_entry", "person", 0.93, base - timedelta(days=1, hours=23, minutes=59)),
            _det("demo_det_floor_helmet", "demo_floor_entry", "helmet", 0.92, base - timedelta(days=1, hours=23, minutes=59)),
            # no_vest on the general floor is suppressed (vest not required there)
            _det("demo_det_floor_no_vest", "demo_floor_entry", "no_vest", 0.80, base - timedelta(days=1, hours=23, minutes=59)),
            _det("demo_det_weld_person", "demo_welding_bay", "person", 0.97, base - timedelta(hours=5, minutes=59)),
            _det("demo_det_weld_helmet", "demo_welding_bay", "helmet", 0.94, base - timedelta(hours=5, minutes=59)),
            _det("demo_det_weld_vest", "demo_welding_bay", "vest", 0.90, base - timedelta(hours=5, minutes=59)),
            _det("demo_det_packout_person", "demo_packout_legacy", "person", 0.90, base - timedelta(hours=23, minutes=59)),
            _det("demo_det_packout_no_vest", "demo_packout_legacy", "no_vest", 0.78, base - timedelta(hours=23, minutes=59)),
            _det("demo_det_obscured_person", "demo_dock_obscured", "person", 0.70, base - timedelta(hours=9, minutes=59)),
        ]

        events = [
            SafetyEvent(
                id="demo_evt_dock_mon_vest",
                upload_id="demo_dock_mon",
                event_type="ppe_violation",
                violation_type="no_vest",
                severity="high",
                confidence=0.88,
                status="open",
                suggested_action="Supervisor review recommended. Safety vest required in Loading Dock. Safety vest appears missing.",
                created_at=base - timedelta(days=5, hours=1, minutes=58),
            ),
            SafetyEvent(
                id="demo_evt_dock_wed_vest",
                upload_id="demo_dock_wed",
                event_type="ppe_violation",
                violation_type="no_vest",
                severity="high",
                confidence=0.86,
                status="reviewed",
                suggested_action="Supervisor review recommended. Safety vest required in Loading Dock. Safety vest appears missing.",
                created_at=base - timedelta(days=2, hours=23, minutes=58),
            ),
            SafetyEvent(
                id="demo_evt_dock_fri_vest",
                upload_id="demo_dock_fri",
                event_type="ppe_violation",
                violation_type="no_vest",
                severity="high",
                confidence=0.90,
                status="open",
                suggested_action="Supervisor review recommended. Safety vest required in Loading Dock. Safety vest appears missing.",
                created_at=base - timedelta(hours=17, minutes=58),
            ),
            SafetyEvent(
                id="demo_evt_floor_helmet",
                upload_id="demo_floor_entry",
                event_type="positive_observation",
                violation_type=None,
                severity="low",
                confidence=0.92,
                status="reviewed",
                suggested_action="Helmet compliance observed in General Floor.",
                created_at=base - timedelta(days=1, hours=23, minutes=57),
            ),
            SafetyEvent(
                id="demo_evt_weld_helmet",
                upload_id="demo_welding_bay",
                event_type="positive_observation",
                violation_type=None,
                severity="low",
                confidence=0.94,
                status="reviewed",
                suggested_action="Helmet compliance observed in Welding Station.",
                created_at=base - timedelta(hours=5, minutes=58),
            ),
            SafetyEvent(
                id="demo_evt_weld_vest",
                upload_id="demo_welding_bay",
                event_type="positive_observation",
                violation_type=None,
                severity="low",
                confidence=0.90,
                status="reviewed",
                suggested_action="Safety vest compliance observed in Welding Station.",
                created_at=base - timedelta(hours=5, minutes=57),
            ),
            SafetyEvent(
                id="demo_evt_packout_vest",
                upload_id="demo_packout_legacy",
                event_type="ppe_violation",
                violation_type="no_vest",
                severity="medium",
                confidence=0.78,
                status="open",
                suggested_action="Coaching reminder recommended. Safety vest appears missing.",
                created_at=base - timedelta(hours=23, minutes=57),
            ),
            SafetyEvent(
                id="demo_evt_dock_obscured",
                upload_id="demo_dock_obscured",
                event_type="uncertain_review",
                violation_type=None,
                severity="medium",
                confidence=0.70,
                status="open",
                suggested_action="PPE status unclear. Manual review recommended.",
                created_at=base - timedelta(hours=9, minutes=58),
            ),
        ]

        alerts = [
            AlertRecord(
                id="demo_alrt_dock_mon",
                safety_event_id="demo_evt_dock_mon_vest",
                alert_type="supervisor_review",
                title="Missing Vest Detected",
                message="A high-severity PPE violation was detected at the Loading Dock. Supervisor review is recommended.",
                status="draft",
                created_at=base - timedelta(days=5, hours=1, minutes=57),
            ),
            AlertRecord(
                id="demo_alrt_dock_wed",
                safety_event_id="demo_evt_dock_wed_vest",
                alert_type="supervisor_review",
                title="Missing Vest Detected",
                message="A high-severity PPE violation was detected at the Loading Dock. Supervisor review is recommended.",
                status="sent_mock",
                created_at=base - timedelta(days=2, hours=23, minutes=57),
            ),
            AlertRecord(
                id="demo_alrt_dock_fri",
                safety_event_id="demo_evt_dock_fri_vest",
                alert_type="supervisor_review",
                title="Missing Vest Detected",
                message="A high-severity PPE violation was detected at the Loading Dock. Supervisor review is recommended.",
                status="draft",
                created_at=base - timedelta(hours=17, minutes=57),
            ),
            AlertRecord(
                id="demo_alrt_packout",
                safety_event_id="demo_evt_packout_vest",
                alert_type="coaching_reminder",
                title="Missing Vest Detected",
                message="A medium-severity PPE violation was detected on the Packout Line. A coaching reminder is recommended.",
                status="draft",
                created_at=base - timedelta(hours=23, minutes=56),
            ),
            AlertRecord(
                id="demo_alrt_obscured",
                safety_event_id="demo_evt_dock_obscured",
                alert_type="manual_review",
                title="PPE Status Unclear",
                message="Detection confidence was low or PPE status was unclear. Manual review is recommended.",
                status="queued",
                created_at=base - timedelta(hours=9, minutes=57),
            ),
            AlertRecord(
                id="demo_alrt_repeated_dock_vest",
                safety_event_id="demo_evt_dock_fri_vest",
                alert_type="repeated_violation",
                title="Repeated Vest Issue",
                message="Loading Dock has 3 no-vest violations in the past week. Supervisor coaching review is recommended.",
                status="draft",
                created_at=base - timedelta(hours=17, minutes=56),
            ),
        ]

        db.add_all(uploads)
        db.add_all(detections)
        db.add_all(events)
        db.add_all(alerts)
        db.commit()

        zone_names = {
            upload.id: (get_zone(db, upload.zone_id).display_name if upload.zone_id else None)
            for upload in uploads
        }

        return {
            "status": "success",
            "scenario": "zone_aware_shift_review",
            "message": "Zone-aware warehouse shift demo scenario loaded.",
            "uploads": [_serialize_upload(u, zone_names.get(u.id)) for u in uploads],
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
