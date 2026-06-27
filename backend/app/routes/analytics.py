from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.services.analytics_service import get_overview, get_trends

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/overview")
def analytics_overview(period: str = "all", db: Session = Depends(get_db)):
    return get_overview(db, period)


@router.get("/trends")
def analytics_trends(period: str = "daily", db: Session = Depends(get_db)):
    return get_trends(db, period)
