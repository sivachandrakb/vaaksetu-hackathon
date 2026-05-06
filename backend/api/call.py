"""
VaakSetu — Call Session API
Endpoints for managing call sessions and the full AI pipeline.
WebSocket: real-time push to agent dashboard.
"""

import uuid
import logging
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_db
from db import crud
from models.schemas import (
    StartCallRequest, StartCallResponse,
    AudioChunkRequest, ProcessAudioResponse,
    VerificationResponseRequest, AgentCorrectionRequest, EscalateRequest,
    CallSession, CallStatus, WSMessage, WSMessageType,
    VerificationOutcome, ConfidenceDecision,
)
from services.asr import get_asr_service
from services.dialect import get_dialect_service
from services.sentiment import get_sentiment_service
from services.interpretation import get_interpretation_service
from services.verification import get_verification_service
from services.confidence import get_confidence_service
from services.tts import get_tts_service

logger = logging.getLogger(__name__)
router = APIRouter()

# In-memory session store (use Redis in production)
_sessions: dict[str, CallSession] = {}

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active: dict[str, list[WebSocket]] = {}

    async def connect(self, session_id: str, ws: WebSocket):
        await ws.accept()
        self.active.setdefault(session_id, []).append(ws)

    def disconnect(self, session_id: str, ws: WebSocket):
        conns = self.active.get(session_id, [])
        if ws in conns:
            conns.remove(ws)

    async def broadcast(self, session_id: str, message: WSMessage):
        conns = self.active.get(session_id, [])
        dead = []
        for ws in conns:
            try:
                await ws.send_text(message.model_dump_json())
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(session_id, ws)

    async def broadcast_all(self, message: WSMessage):
        """Broadcast to all connected sessions (dashboard-wide updates)."""
        for session_id in list(self.active.keys()):
            await self.broadcast(session_id, message)


manager = ConnectionManager()


# ─── REST Endpoints ───────────────────────────────────────────────────────────

@router.post("/start", response_model=StartCallResponse)
async def start_call(
    request: StartCallRequest,
    db: AsyncSession = Depends(get_db)
):
    """Start a new call session. Returns session_id and WebSocket URL."""
    session_id = str(uuid.uuid4())
    session = CallSession(
        session_id=session_id,
        status=CallStatus.ACTIVE,
        started_at=datetime.utcnow()
    )
    _sessions[session_id] = session
    await crud.create_session(db, session, agent_id=request.agent_id)
    
    logger.info(f"Call started: {session_id}")
    return StartCallResponse(
        session_id=session_id,
        websocket_url=f"/api/call/ws/{session_id}"
    )


@router.post("/process-audio", response_model=ProcessAudioResponse)
async def process_audio(
    request: AudioChunkRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Full pipeline: ASR → Dialect → Sentiment → Interpretation → Confidence.
    Pushes intermediate results via WebSocket as they become available.
    """
    session = _sessions.get(request.session_id)
    if not session:
        raise HTTPException(404, "Session not found")

    asr_svc = get_asr_service()
    dialect_svc = get_dialect_service()
    sentiment_svc = get_sentiment_service()
    interp_svc = get_interpretation_service()
    confidence_svc = get_confidence_service()
    tts_svc = get_tts_service()

    # ── Step 1: ASR ───────────────────────────────────────────────────────────
    asr_result = await asr_svc.transcribe(request.audio_b64)
    session.transcript = asr_result.transcript
    session.language = asr_result.language

    await manager.broadcast(request.session_id, WSMessage(
        type=WSMessageType.TRANSCRIPT_UPDATE,
        session_id=request.session_id,
        payload={
            "transcript": asr_result.transcript,
            "language": asr_result.language.value,
            "confidence": asr_result.confidence,
        }
    ))

    # ── Step 2: Dialect ───────────────────────────────────────────────────────
    dialect_result = dialect_svc.identify(asr_result.transcript, asr_result.language)
    session.dialect = dialect_result.dialect

    # ── Step 3: Sentiment ─────────────────────────────────────────────────────
    sentiment_result = sentiment_svc.classify(asr_result.transcript, asr_result.language)
    session.sentiment = sentiment_result

    await manager.broadcast(request.session_id, WSMessage(
        type=WSMessageType.SENTIMENT_UPDATE,
        session_id=request.session_id,
        payload={
            "sentiment": sentiment_result.sentiment.value,
            "label": sentiment_result.label,
            "urgency_flag": sentiment_result.urgency_flag,
            "confidence": sentiment_result.confidence,
        }
    ))

    # ── Step 4: Check if we should skip verification (high distress) ──────────
    verification_svc = get_verification_service()
    skip_verification = verification_svc.should_skip_loop(
        sentiment_result.urgency_flag, sentiment_result.label
    )

    # ── Step 5: Semantic Interpretation ───────────────────────────────────────
    interpretation = await interp_svc.interpret(
        asr_result.transcript,
        asr_result.language,
        dialect_result.dialect,
        sentiment_result,
    )
    session.interpretation = interpretation

    # ── Step 6: TTS restatement audio ─────────────────────────────────────────
    if not skip_verification:
        restatement_audio = await tts_svc.synthesize(
            interpretation.restatement, asr_result.language
        )
        interpretation.restatement_audio_b64 = restatement_audio

    await manager.broadcast(request.session_id, WSMessage(
        type=WSMessageType.INTERPRETATION_READY,
        session_id=request.session_id,
        payload={
            "core_issue": interpretation.core_issue,
            "intent": interpretation.intent,
            "entities": [e.model_dump() for e in interpretation.entities],
            "department": interpretation.department,
            "restatement": interpretation.restatement,
            "restatement_audio_b64": interpretation.restatement_audio_b64,
            "confidence": interpretation.confidence,
            "rag_context_used": interpretation.rag_context_used,
            "skip_verification": skip_verification,
            "dialect": dialect_svc.format_dialect_label(dialect_result),
        }
    ))

    # ── Step 7: Initial confidence evaluation (pre-verification) ──────────────
    confidence_eval = confidence_svc.evaluate(
        asr_result, dialect_result, interpretation, sentiment_result
    )
    session.confidence_eval = confidence_eval

    # If immediate escalation needed
    if skip_verification or confidence_eval.decision == ConfidenceDecision.ESCALATE:
        session.escalated = True
        session.escalation_reason = confidence_eval.escalation_reason or "High distress detected"
        session.status = CallStatus.ESCALATED
        await crud.update_session(db, session)

        await manager.broadcast(request.session_id, WSMessage(
            type=WSMessageType.ESCALATION,
            session_id=request.session_id,
            payload={
                "reason": session.escalation_reason,
                "transcript": asr_result.transcript,
                "interpretation": interpretation.core_issue,
                "sentiment": sentiment_result.label,
                "dialect": dialect_svc.format_dialect_label(dialect_result),
            }
        ))

    await crud.update_session(db, session)

    return ProcessAudioResponse(
        session_id=request.session_id,
        transcript=asr_result.transcript,
        language=asr_result.language,
        dialect=dialect_result.dialect,
        sentiment=sentiment_result,
        interpretation=interpretation,
        verification_needed=not skip_verification and confidence_eval.decision != ConfidenceDecision.ESCALATE,
        confidence_eval=confidence_eval,
    )


@router.post("/verify")
async def submit_verification(
    request: VerificationResponseRequest,
    db: AsyncSession = Depends(get_db)
):
    """Process citizen's verification response (confirmation or correction)."""
    session = _sessions.get(request.session_id)
    if not session:
        raise HTTPException(404, "Session not found")

    asr_svc = get_asr_service()
    verification_svc = get_verification_service()
    confidence_svc = get_confidence_service()

    # Transcribe citizen's verification response
    response_asr = await asr_svc.transcribe(
        request.audio_b64,
        language_hint=session.language.value if session.language else None
    )

    attempt = 1
    if session.verification:
        attempt = session.verification.attempt_number + 1

    verification = verification_svc.classify_response(
        response_asr.transcript,
        session.language,
        attempt_number=attempt
    )
    session.verification = verification

    await manager.broadcast(request.session_id, WSMessage(
        type=WSMessageType.VERIFICATION_RESULT,
        session_id=request.session_id,
        payload={
            "outcome": verification.outcome.value,
            "citizen_response": verification.citizen_response,
            "correction": verification.correction,
            "attempt": attempt,
        }
    ))

    # Re-evaluate confidence with verification outcome
    if session.confidence_eval and session.interpretation and session.sentiment:
        from services.asr import ASRResult
        from services.dialect import DialectResult
        from models.schemas import Language, Dialect

        # Build minimal ASR result for re-evaluation
        asr_stub = type('ASR', (), {
            'confidence': session.confidence_eval.asr_confidence,
            'transcript': session.transcript or "",
            'language': session.language or Language.UNKNOWN,
            'duration_seconds': 0,
            'segments': []
        })()
        dialect_stub = type('D', (), {
            'language': session.language or Language.UNKNOWN,
            'dialect': session.dialect or Dialect.UNKNOWN,
            'confidence': session.confidence_eval.dialect_confidence,
            'script': 'latin'
        })()

        new_eval = confidence_svc.evaluate(
            asr_stub, dialect_stub,
            session.interpretation, session.sentiment,
            verification
        )
        session.confidence_eval = new_eval

        await manager.broadcast(request.session_id, WSMessage(
            type=WSMessageType.CONFIDENCE_DECISION,
            session_id=request.session_id,
            payload={
                "decision": new_eval.decision.value,
                "overall_score": new_eval.overall_score,
                "escalation_reason": new_eval.escalation_reason,
            }
        ))

        if new_eval.decision == ConfidenceDecision.ESCALATE:
            session.escalated = True
            session.escalation_reason = new_eval.escalation_reason
            session.status = CallStatus.ESCALATED

            await manager.broadcast(request.session_id, WSMessage(
                type=WSMessageType.ESCALATION,
                session_id=request.session_id,
                payload={"reason": new_eval.escalation_reason, "attempt": attempt}
            ))

        elif new_eval.decision == ConfidenceDecision.PROCEED:
            session.status = CallStatus.VERIFIED

        # If CLARIFY + max attempts reached → escalate
        if attempt >= 2 and new_eval.decision == ConfidenceDecision.CLARIFY:
            session.escalated = True
            session.escalation_reason = "Max verification attempts reached"
            session.status = CallStatus.ESCALATED
            await manager.broadcast(request.session_id, WSMessage(
                type=WSMessageType.ESCALATION,
                session_id=request.session_id,
                payload={"reason": session.escalation_reason, "attempt": attempt}
            ))

    await crud.update_session(db, session)
    return {"status": "ok", "outcome": verification.outcome.value}


@router.post("/escalate")
async def escalate_call(
    request: EscalateRequest,
    db: AsyncSession = Depends(get_db)
):
    """Agent manually triggers human takeover."""
    session = _sessions.get(request.session_id)
    if not session:
        raise HTTPException(404, "Session not found")

    session.escalated = True
    session.escalation_reason = request.reason
    session.status = CallStatus.ESCALATED
    await crud.update_session(db, session)

    await manager.broadcast(request.session_id, WSMessage(
        type=WSMessageType.ESCALATION,
        session_id=request.session_id,
        payload={
            "reason": request.reason,
            "triggered_by": "agent",
            "agent_id": request.agent_id,
        }
    ))
    return {"status": "escalated"}


@router.post("/correct")
async def agent_correction(
    request: AgentCorrectionRequest,
    db: AsyncSession = Depends(get_db)
):
    """Agent submits a correction to AI's interpretation."""
    session = _sessions.get(request.session_id)
    if not session:
        raise HTTPException(404, "Session not found")

    session.agent_correction = request.corrected_interpretation
    session.status = CallStatus.COMPLETED
    await crud.update_session(db, session)

    # Store as high-quality feedback
    from models.schemas import FeedbackRecord, Language, Dialect, Sentiment, VerificationOutcome
    feedback = FeedbackRecord(
        session_id=request.session_id,
        transcript=session.transcript or "",
        ai_interpretation=session.interpretation.core_issue if session.interpretation else "",
        verified_interpretation=request.corrected_interpretation,
        sentiment=session.sentiment.sentiment if session.sentiment else Sentiment.UNKNOWN,
        language=session.language or Language.UNKNOWN,
        dialect=session.dialect or Dialect.UNKNOWN,
        outcome=session.verification.outcome if session.verification else VerificationOutcome.UNCERTAIN,
        agent_correction=request.corrected_interpretation,
        quality_signal="correction",
    )
    await crud.save_feedback(db, feedback)

    return {"status": "correction saved", "queued_for_training": True}


@router.get("/session/{session_id}")
async def get_session(session_id: str):
    """Get current session state."""
    session = _sessions.get(session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    return session


# ─── WebSocket ────────────────────────────────────────────────────────────────

@router.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for real-time updates to the agent dashboard.
    Stays open for the duration of the call session.
    """
    await manager.connect(session_id, websocket)
    logger.info(f"WebSocket connected: {session_id}")
    try:
        # Send current session state immediately on connect
        session = _sessions.get(session_id)
        if session:
            await websocket.send_text(WSMessage(
                type=WSMessageType.TRANSCRIPT_UPDATE,
                session_id=session_id,
                payload={"status": session.status.value, "connected": True}
            ).model_dump_json())

        while True:
            # Keep connection alive; client can also send messages
            data = await websocket.receive_text()
            # Handle ping/pong or client-initiated messages
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(session_id, websocket)
        logger.info(f"WebSocket disconnected: {session_id}")
