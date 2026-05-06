"""
VaakSetu — Confidence Evaluator
Aggregates signals and decides: PROCEED / CLARIFY / ESCALATE.

Policy (rule-based):
- Escalate if: urgency_flag AND distress/anger, OR any signal < hard threshold
- Clarify if: medium uncertainty — try verification loop
- Proceed if: high confidence across all signals
"""

import logging
from typing import Optional

from models.schemas import (
    ASRResult, DialectResult, InterpretationResult,
    SentimentResult, VerificationOutcome, VerificationResult,
    ConfidenceEvaluation, ConfidenceDecision
)

logger = logging.getLogger(__name__)

# Configurable thresholds
ESCALATE_ASR_THRESHOLD = 0.45       # Below this ASR confidence → escalate
ESCALATE_INTERP_THRESHOLD = 0.50    # Below this interpretation confidence → escalate
CLARIFY_ASR_THRESHOLD = 0.70        # Below this → request clarification
CLARIFY_INTERP_THRESHOLD = 0.65


class ConfidenceService:
    """
    Aggregates all pipeline signals and decides routing.
    
    In production this also reads per-call Whisper telemetry fed back
    via Kafka to dynamically calibrate thresholds.
    """

    def evaluate(
        self,
        asr: ASRResult,
        dialect: DialectResult,
        interpretation: InterpretationResult,
        sentiment: SentimentResult,
        verification: Optional[VerificationResult] = None
    ) -> ConfidenceEvaluation:
        """
        Evaluate all signals and return a routing decision.
        """
        overall = self._compute_overall(
            asr.confidence, dialect.confidence,
            interpretation.confidence,
            verification.outcome if verification else None
        )

        decision, reason = self._apply_policy(
            asr.confidence,
            interpretation.confidence,
            sentiment,
            verification,
            overall
        )

        return ConfidenceEvaluation(
            decision=decision,
            asr_confidence=asr.confidence,
            interpretation_confidence=interpretation.confidence,
            dialect_confidence=dialect.confidence,
            verification_outcome=verification.outcome if verification else None,
            overall_score=overall,
            escalation_reason=reason
        )

    def _compute_overall(
        self,
        asr_conf: float,
        dialect_conf: float,
        interp_conf: float,
        verification: Optional[VerificationOutcome]
    ) -> float:
        """Weighted average of all confidence signals."""
        weights = {
            "asr": 0.30,
            "dialect": 0.10,
            "interpretation": 0.35,
            "verification": 0.25,
        }
        
        verification_score = {
            VerificationOutcome.CONFIRMED: 1.0,
            VerificationOutcome.PARTIAL: 0.7,
            VerificationOutcome.INCORRECT: 0.2,
            VerificationOutcome.UNCERTAIN: 0.3,
            VerificationOutcome.SKIPPED: 0.6,
            None: 0.5,  # no verification yet
        }.get(verification, 0.5)
        
        overall = (
            asr_conf * weights["asr"] +
            dialect_conf * weights["dialect"] +
            interp_conf * weights["interpretation"] +
            verification_score * weights["verification"]
        )
        return round(min(1.0, overall), 3)

    def _apply_policy(
        self,
        asr_conf: float,
        interp_conf: float,
        sentiment: SentimentResult,
        verification: Optional[VerificationResult],
        overall: float
    ) -> tuple[ConfidenceDecision, Optional[str]]:
        """
        Rule-based routing policy.
        
        Escalation rules (in priority order):
        1. High distress/anger + urgency flag → immediate escalation
        2. ASR confidence below hard threshold → can't proceed safely
        3. Interpretation confidence below hard threshold
        4. Verification rejected/uncertain after max attempts
        5. Overall score too low
        """
        from models.schemas import Sentiment
        
        # Rule 1: High distress/anger + urgency → skip loop, escalate immediately
        if sentiment.urgency_flag and sentiment.sentiment in (Sentiment.DISTRESS, Sentiment.ANGER):
            return ConfidenceDecision.ESCALATE, "High distress/anger with urgency flag — immediate human takeover"
        
        # Rule 2: ASR too low
        if asr_conf < ESCALATE_ASR_THRESHOLD:
            return ConfidenceDecision.ESCALATE, f"ASR confidence too low ({asr_conf:.0%}) — cannot reliably transcribe"
        
        # Rule 3: Interpretation too low
        if interp_conf < ESCALATE_INTERP_THRESHOLD:
            return ConfidenceDecision.ESCALATE, f"Interpretation confidence too low ({interp_conf:.0%})"
        
        # Rule 4: Verification failed after attempt
        if verification:
            if verification.outcome == VerificationOutcome.INCORRECT and verification.attempt_number >= 2:
                return ConfidenceDecision.ESCALATE, "Citizen rejected interpretation twice — human takeover"
            if verification.outcome == VerificationOutcome.UNCERTAIN:
                return ConfidenceDecision.ESCALATE, "Citizen could not confirm — escalating"
            if verification.outcome == VerificationOutcome.CONFIRMED:
                return ConfidenceDecision.PROCEED, None
            if verification.outcome == VerificationOutcome.PARTIAL:
                return ConfidenceDecision.CLARIFY, None
        
        # Rule 5: Score-based routing
        if overall >= 0.75:
            return ConfidenceDecision.PROCEED, None
        if overall >= 0.55:
            return ConfidenceDecision.CLARIFY, None
        
        return ConfidenceDecision.ESCALATE, f"Overall confidence too low ({overall:.0%})"


_confidence_service: Optional[ConfidenceService] = None

def get_confidence_service() -> ConfidenceService:
    global _confidence_service
    if _confidence_service is None:
        _confidence_service = ConfidenceService()
    return _confidence_service
