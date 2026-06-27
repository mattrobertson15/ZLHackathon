from sqlalchemy import Column, String, DateTime

from app.db.database import Base


class Upload(Base):
    __tablename__ = "uploads"

    id = Column(String, primary_key=True)
    file_name = Column(String, nullable=False)
    file_type = Column(String, nullable=False)  # "image" | "video"
    file_url = Column(String, nullable=False)
    location_label = Column(String, nullable=True)
    notes = Column(String, nullable=True)
    status = Column(String, nullable=False, default="uploaded")
    # uploaded -> processing -> processed -> failed
    source_type = Column(String, nullable=False, default="upload")
    # upload | camera  (camera captures reuse the upload pipeline)
    camera_id = Column(String, nullable=True, index=True)
    uploaded_at = Column(DateTime, nullable=False)
