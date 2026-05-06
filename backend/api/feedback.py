"""VaakSetu — Feedback API"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from db.database import get_db
from db import crud
from models.schemas import FeedbackRecord

router = APIRouter()

@router.post("/submit")
async def submit_feedback(feedback: FeedbackRecord, db: AsyncSession = Depends(get_db)):
    """Submit a feedback record to the learning store."""
    record = await crud.save_feedback(db, feedback)
    return {"status": "saved", "id": record.id, "quality_signal": feedback.quality_signal}

@router.get("/summary")
async def feedback_summary():
    """Placeholder: return feedback quality distribution."""
    return {
        "total_records": 0,
        "positive": 0,
        "corrections": 0,
        "escalations": 0,
        "note": "Connect to DB for live counts"
    }
