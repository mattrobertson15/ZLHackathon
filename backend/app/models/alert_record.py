from sqlalchemy import Column, DateTime, String

from app.db.database import Base


class AlertRecord(Base):
    __tablename__ = "alert_records"

    id = Column(String, primary_key=True)
    safety_event_id = Column(String, nullable=False, index=True)
    alert_type = Column(String, nullable=False)
    # supervisor_review | coaching_reminder | manual_review
    title = Column(String, nullable=False)
    message = Column(String, nullable=False)
    status = Column(String, nullable=False, default="draft")
    # draft | queued | sent_mock | dismissed
    created_at = Column(DateTime, nullable=False)
