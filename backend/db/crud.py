"""
VaakSetu — CRUD Operations
Database operations for call sessions and feedback records.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from datetime import datetime, timedelta
from typing import Optional

from db.database import CallSessionDB, FeedbackDB
from models.schemas import CallSession, FeedbackRecord


async def create_session(db: AsyncSession, session: CallSession, agent_id: str = None) -> CallSessionDB:
    db_session = CallSessionDB(
        session_id=session.session_id,
        status=session.status.value,
        started_at=session.started_at,
        agent_id=agent_id
    )
    db.add(db_session)
    await db.commit()
    await db.refresh(db_session)
    return db_session


async def update_session(db: AsyncSession, session: CallSession) -> None:
    result = await db.execute(
        select(CallSessionDB).where(CallSessionDB.session_id == session.session_id)
    )
    db_session = result.scalar_one_or_none()
    if not db_session:
        return
    
    db_session.status = session.status.value
    if session.language:
        db_session.language = session.language.value
    if session.dialect:
        db_session.dialect = session.dialect.value
    if session.transcript:
        db_session.transcript = session.transcript
    if session.interpretation:
        db_session.core_issue = session.interpretation.core_issue
        db_session.intent = session.interpretation.intent
        db_session.department = session.interpretation.department
        db_session.restatement = session.interpretation.restatement
    if session.sentiment:
        db_session.sentiment = session.sentiment.sentiment.value
        db_session.urgency_flag = session.sentiment.urgency_flag
    if session.verification:
        db_session.verification_outcome = session.verification.outcome.value
    if session.confidence_eval:
        db_session.overall_confidence = session.confidence_eval.overall_score
    db_session.escalated = session.escalated
    db_session.escalation_reason = session.escalation_reason
    db_session.agent_correction = session.agent_correction
    
    await db.commit()


async def save_feedback(db: AsyncSession, feedback: FeedbackRecord) -> FeedbackDB:
    db_feedback = FeedbackDB(
        session_id=feedback.session_id,
        transcript=feedback.transcript,
        ai_interpretation=feedback.ai_interpretation,
        verified_interpretation=feedback.verified_interpretation,
        sentiment=feedback.sentiment.value,
        language=feedback.language.value,
        dialect=feedback.dialect.value,
        outcome=feedback.outcome.value,
        agent_correction=feedback.agent_correction,
        quality_signal=feedback.quality_signal,
        recorded_at=feedback.recorded_at,
    )
    db.add(db_feedback)
    await db.commit()
    await db.refresh(db_feedback)
    return db_feedback


async def get_dashboard_stats(db: AsyncSession) -> dict:
    """Aggregate stats for agent dashboard."""
    # Active calls
    active_result = await db.execute(
        select(func.count()).where(CallSessionDB.status == "active")
    )
    active_count = active_result.scalar() or 0
    
    # Escalated in last hour
    one_hour_ago = datetime.utcnow() - timedelta(hours=1)
    escalated_result = await db.execute(
        select(func.count()).where(
            CallSessionDB.escalated == True,
            CallSessionDB.started_at >= one_hour_ago
        )
    )
    escalated_count = escalated_result.scalar() or 0
    
    # Average confidence
    avg_result = await db.execute(
        select(func.avg(CallSessionDB.overall_confidence)).where(
            CallSessionDB.overall_confidence.isnot(None)
        )
    )
    avg_conf = avg_result.scalar() or 0.0
    
    return {
        "active_calls": active_count,
        "escalated_last_hour": escalated_count,
        "avg_confidence": round(float(avg_conf), 3),
    }
