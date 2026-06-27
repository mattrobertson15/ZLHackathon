from sqlalchemy import Column, DateTime, Float, String

from app.db.database import Base


class SafetyEvent(Base):
    __tablename__ = "safety_events"

    id = Column(String, primary_key=True)
    upload_id = Column(String, nullable=False, index=True)
    event_type = Column(String, nullable=False)
    # positive_observation | ppe_violation | uncertain_review
    violation_type = Column(String, nullable=True)
    # no_helmet | no_vest
    severity = Column(String, nullable=False)
    # low | medium | high
    confidence = Column(Float, nullable=False)
    status = Column(String, nullable=False, default="open")
    # open | reviewed | dismissed | resolved
    suggested_action = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False)
