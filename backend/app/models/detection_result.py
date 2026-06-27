from sqlalchemy import Column, DateTime, Float, Integer, String

from app.db.database import Base


class DetectionResult(Base):
    __tablename__ = "detection_results"

    id = Column(String, primary_key=True)
    upload_id = Column(String, nullable=False, index=True)
    frame_timestamp = Column(Float, nullable=True)
    label = Column(String, nullable=False)
    # person | helmet | no_helmet | vest | no_vest
    confidence = Column(Float, nullable=False)
    bbox_x = Column(Integer, nullable=True)
    bbox_y = Column(Integer, nullable=True)
    bbox_width = Column(Integer, nullable=True)
    bbox_height = Column(Integer, nullable=True)
    source = Column(String, nullable=False)
    # qwen_vision | roboflow | manual_mock
    created_at = Column(DateTime, nullable=False)
