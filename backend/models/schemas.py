"""
VaakSetu — Data Models (Pydantic Schemas)
All request/response models for the API and internal services.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import datetime
from enum import Enum


# ─── Enums ───────────────────────────────────────────────────────────────────

class Language(str, Enum):
    KANNADA = "kn"
    HINDI = "hi"
    ENGLISH = "en"
    UNKNOWN = "unknown"


class Dialect(str, Enum):
    DHARWAD = "dharwad"
    MYSURU = "mysuru"
    MANGALURU = "mangaluru"
    HAVYAKA = "havyaka"
    KODAVA = "kodava"
    BENGALURU = "bengaluru"
    STANDARD = "standard"
    UNKNOWN = "unknown"


class Sentiment(str, Enum):
    DISTRESS = "distress"
    ANGER = "anger"
    FEAR = "fear"
    CONFUSION = "confusion"
    URGENCY = "urgency"
    CALM = "calm"
    UNKNOWN = "unknown"


class VerificationOutcome(str, Enum):
    CONFIRMED = "confirmed"
    INCORRECT = "incorrect"
    PARTIAL = "partial"
    UNCERTAIN = "uncertain"
    SKIPPED = "skipped"      # high distress — skip loop


class CallStatus(str, Enum):
    ACTIVE = "active"
    VERIFIED = "verified"
    ESCALATED = "escalated"
    COMPLETED = "completed"


class ConfidenceDecision(str, Enum):
    PROCEED = "proceed"
    CLARIFY = "clarify"
    ESCALATE = "escalate"


# ─── ASR ─────────────────────────────────────────────────────────────────────

class ASRResult(BaseModel):
    transcript: str
    language: Language
    confidence: float = Field(ge=0.0, le=1.0)
    duration_seconds: float
    segments: List[dict] = []


# ─── Dialect ─────────────────────────────────────────────────────────────────

class DialectResult(BaseModel):
    language: Language
    dialect: Dialect
    confidence: float = Field(ge=0.0, le=1.0)
    script: str = "latin"


# ─── Sentiment ───────────────────────────────────────────────────────────────

class SentimentResult(BaseModel):
    sentiment: Sentiment
    confidence: float = Field(ge=0.0, le=1.0)
    acoustic_signal: Sentiment     # from Wav2Vec2 channel
    lexical_signal: Sentiment      # from MuRIL channel
    urgency_flag: bool
    label: str                     # human-readable for dashboard


# ─── Semantic Interpretation ─────────────────────────────────────────────────

class Entity(BaseModel):
    type: str       # location | department | person | service | id_number
    value: str
    confidence: float = Field(ge=0.0, le=1.0)


class InterpretationResult(BaseModel):
    core_issue: str
    intent: str
    entities: List[Entity]
    department: str
    restatement: str               # natural-language restatement in citizen's language
    restatement_audio_b64: Optional[str] = None   # base64 TTS audio
    confidence: float = Field(ge=0.0, le=1.0)
    rag_context_used: List[str] = []   # which govt APIs enriched this


# ─── Verification Loop ───────────────────────────────────────────────────────

class VerificationResult(BaseModel):
    outcome: VerificationOutcome
    attempt_number: int
    citizen_response: Optional[str] = None
    correction: Optional[str] = None     # if partial correction given
    signal_type: str                     # for fine-tune queue


# ─── Confidence Evaluation ───────────────────────────────────────────────────

class ConfidenceEvaluation(BaseModel):
    decision: ConfidenceDecision
    asr_confidence: float
    interpretation_confidence: float
    dialect_confidence: float
    verification_outcome: Optional[VerificationOutcome] = None
    overall_score: float
    escalation_reason: Optional[str] = None


# ─── Call Session ─────────────────────────────────────────────────────────────

class CallSession(BaseModel):
    session_id: str
    status: CallStatus = CallStatus.ACTIVE
    started_at: datetime = Field(default_factory=datetime.utcnow)
    language: Optional[Language] = None
    dialect: Optional[Dialect] = None
    transcript: Optional[str] = None
    interpretation: Optional[InterpretationResult] = None
    sentiment: Optional[SentimentResult] = None
    verification: Optional[VerificationResult] = None
    confidence_eval: Optional[ConfidenceEvaluation] = None
    agent_correction: Optional[str] = None
    escalated: bool = False
    escalation_reason: Optional[str] = None


# ─── API Request / Response Bodies ───────────────────────────────────────────

class StartCallRequest(BaseModel):
    agent_id: Optional[str] = "agent_001"


class StartCallResponse(BaseModel):
    session_id: str
    websocket_url: str


class AudioChunkRequest(BaseModel):
    session_id: str
    audio_b64: str          # base64-encoded WAV chunk
    is_final: bool = False


class ProcessAudioResponse(BaseModel):
    session_id: str
    transcript: str
    language: Language
    dialect: Dialect
    sentiment: SentimentResult
    interpretation: InterpretationResult
    verification_needed: bool
    confidence_eval: ConfidenceEvaluation


class VerificationResponseRequest(BaseModel):
    session_id: str
    audio_b64: str          # citizen's confirmation audio


class AgentCorrectionRequest(BaseModel):
    session_id: str
    corrected_interpretation: str
    agent_id: str


class EscalateRequest(BaseModel):
    session_id: str
    agent_id: str
    reason: str = "agent_takeover"


# ─── WebSocket Messages ───────────────────────────────────────────────────────

class WSMessageType(str, Enum):
    TRANSCRIPT_UPDATE = "transcript_update"
    INTERPRETATION_READY = "interpretation_ready"
    SENTIMENT_UPDATE = "sentiment_update"
    VERIFICATION_RESTATEMENT = "verification_restatement"
    VERIFICATION_RESULT = "verification_result"
    CONFIDENCE_DECISION = "confidence_decision"
    ESCALATION = "escalation"
    CALL_COMPLETE = "call_complete"
    DATASET_UPDATE = "dataset_update"
    ERROR = "error"


class WSMessage(BaseModel):
    type: WSMessageType
    session_id: str
    payload: dict
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ─── Dashboard ────────────────────────────────────────────────────────────────

class CallTrend(BaseModel):
    hour: str
    count: int
    top_issue: str


class DashboardState(BaseModel):
    active_calls: int
    escalated_last_hour: int
    avg_confidence: float
    top_issues: List[dict]
    recent_trends: List[CallTrend]
    dataset_feed: List[dict]


# ─── Feedback Store ───────────────────────────────────────────────────────────

class FeedbackRecord(BaseModel):
    session_id: str
    transcript: str
    ai_interpretation: str
    verified_interpretation: str
    sentiment: Sentiment
    language: Language
    dialect: Dialect
    outcome: VerificationOutcome
    agent_correction: Optional[str]
    quality_signal: Literal["positive", "negative", "correction", "escalation"]
    recorded_at: datetime = Field(default_factory=datetime.utcnow)
