from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.services.summary_service import generate_summary, get_summaries, get_summary_by_id

router = APIRouter(prefix="/summaries", tags=["summaries"])


class GenerateSummaryRequest(BaseModel):
    period: str  # daily | weekly | monthly
    startDate: datetime
    endDate: datetime


@router.post("/generate")
def create_summary(request: GenerateSummaryRequest, db: Session = Depends(get_db)):
    try:
        summary = generate_summary(db, request.period, request.startDate, request.endDate)
        return {"summary": summary}
    except ValueError as e:
        raise HTTPException(status_code=500, detail={"error": {"code": "CONFIG_ERROR", "message": str(e)}})
    except Exception as e:
        raise HTTPException(
            status_code=500, detail={"error": {"code": "SUMMARY_GENERATION_ERROR", "message": str(e)}}
        )


@router.get("")
def list_summaries(db: Session = Depends(get_db)):
    summaries = get_summaries(db)
    return {"summaries": summaries}


@router.get("/{summary_id}")
def fetch_summary(summary_id: str, db: Session = Depends(get_db)):
    summary = get_summary_by_id(db, summary_id)
    if not summary:
        raise HTTPException(status_code=404, detail={"error": {"code": "NOT_FOUND", "message": "Summary not found"}})
    return {"summary": summary}
