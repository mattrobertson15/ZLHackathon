from typing import Optional

from sqlalchemy.orm import Session

from app.models.upload import Upload


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
