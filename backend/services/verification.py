"""
VaakSetu — Verified Understanding Loop Manager
The core innovation: AI restates its interpretation, citizen confirms or corrects.

Response Classification:
  CONFIRMED  → houdu / haan / yes / correct / sari
  INCORRECT  → illa / no / nahin / wrong / aalla
  PARTIAL    → houdu aaadre / yes but / haan lekin (correction follows)
  UNCERTAIN  → silence / unclear / ?
"""

import logging
from typing import Optional

from models.schemas import VerificationOutcome, VerificationResult, Language

logger = logging.getLogger(__name__)

# Confirmation keywords by language
AFFIRMATIONS = {
    "kn": ["houdu", "hodu", "sari", "aaytu", "hauda", "haan", "correct", "yes",
           "adu sari", "ade sari", "exactly", "confirm", "okay", "ok"],
    "hi": ["haan", "ha", "sahi", "theek", "correct", "yes", "bilkul", "ji", "ji haan"],
    "en": ["yes", "correct", "right", "exactly", "that's right", "confirmed", "okay", "ok", "yep"],
}

NEGATIONS = {
    "kn": ["illa", "alla", "beda", "sari alla", "haagu alla", "wrong", "no", "nahi", "nahin",
           "gottilla", "aagilla", "tiliyalla", "tiliyadu"],
    "hi": ["nahi", "nahin", "na", "galat", "sahi nahi", "wrong", "no", "nope", "nahi ji"],
    "en": ["no", "wrong", "incorrect", "not right", "nope", "that's wrong", "no that's not"],
}

PARTIAL_MARKERS = {
    "kn": ["houdu aaadre", "sari aaadre", "aadare", "but", "aaadre", "ondishtu", "partly",
           "haan lekin", "but actually", "not exactly"],
    "hi": ["haan lekin", "sahi hai lekin", "thoda", "but", "par"],
    "en": ["yes but", "correct but", "kind of", "partially", "not exactly", "almost", "sort of"],
}


class VerificationService:
    """
    Manages the verified understanding loop.
    
    The loop:
    1. AI speaks restatement (TTS)
    2. Citizen responds
    3. This service classifies the response
    4. Routes to: proceed / retry / escalate
    """

    def classify_response(
        self,
        response_transcript: str,
        language: Language,
        attempt_number: int = 1
    ) -> VerificationResult:
        """
        Classify citizen's verification response.
        
        Args:
            response_transcript: What citizen said in response to restatement
            language: Citizen's language
            attempt_number: Which verification attempt this is (max 2)
            
        Returns:
            VerificationResult with outcome and signal type
        """
        if not response_transcript or len(response_transcript.strip()) < 2:
            return VerificationResult(
                outcome=VerificationOutcome.UNCERTAIN,
                attempt_number=attempt_number,
                citizen_response=response_transcript,
                signal_type="uncertain"
            )
        
        text = response_transcript.lower().strip()
        lang_key = {Language.KANNADA: "kn", Language.HINDI: "hi"}.get(language, "en")
        
        outcome = self._classify_text(text, lang_key)
        correction = self._extract_correction(text, outcome, response_transcript)
        signal = self._signal_type(outcome)
        
        return VerificationResult(
            outcome=outcome,
            attempt_number=attempt_number,
            citizen_response=response_transcript,
            correction=correction,
            signal_type=signal
        )

    def _classify_text(self, text: str, lang_key: str) -> VerificationOutcome:
        """
        Multi-language response classification.
        Priority: PARTIAL > CONFIRMED > INCORRECT > UNCERTAIN
        """
        # Check partial first (e.g. "houdu aaadre..." = "yes but...")
        partial = PARTIAL_MARKERS.get(lang_key, []) + PARTIAL_MARKERS["en"]
        if any(marker in text for marker in partial):
            return VerificationOutcome.PARTIAL
        
        # Check affirmation
        affirm = AFFIRMATIONS.get(lang_key, []) + AFFIRMATIONS["en"]
        if any(a in text for a in affirm):
            return VerificationOutcome.CONFIRMED
        
        # Check negation
        negate = NEGATIONS.get(lang_key, []) + NEGATIONS["en"]
        if any(n in text for n in negate):
            return VerificationOutcome.INCORRECT
        
        # Too short or unclear
        if len(text) < 4:
            return VerificationOutcome.UNCERTAIN
        
        # If it's a long sentence with no clear marker, treat as partial/correction
        if len(text.split()) > 5:
            return VerificationOutcome.PARTIAL
        
        return VerificationOutcome.UNCERTAIN

    def _extract_correction(
        self,
        text: str,
        outcome: VerificationOutcome,
        original: str
    ) -> Optional[str]:
        """If partial, the correction is the content after the partial marker."""
        if outcome != VerificationOutcome.PARTIAL:
            return None
        
        # Try to extract the correction part (after "but", "aaadre", etc.)
        for marker in ["but", "aaadre", "aadare", "lekin", "par", "actually"]:
            if marker in text:
                parts = text.split(marker, 1)
                if len(parts) > 1 and parts[1].strip():
                    return original.split(marker.capitalize(), 1)[-1].strip()
        
        return original  # Return full response as correction

    def _signal_type(self, outcome: VerificationOutcome) -> str:
        return {
            VerificationOutcome.CONFIRMED: "positive",
            VerificationOutcome.INCORRECT: "negative",
            VerificationOutcome.PARTIAL: "correction",
            VerificationOutcome.UNCERTAIN: "uncertain",
            VerificationOutcome.SKIPPED: "escalation",
        }.get(outcome, "unknown")

    def should_skip_loop(self, urgency_flag: bool, sentiment_label: str) -> bool:
        """
        Guardrail: Skip verification loop if citizen is in high distress.
        High distress → go straight to agent with all context.
        """
        return urgency_flag and any(
            word in sentiment_label.lower()
            for word in ["distress", "anger", "urgent"]
        )

    def build_retry_prompt(self, language: Language) -> str:
        """Build a retry restatement prompt if citizen said 'no'."""
        prompts = {
            Language.KANNADA: "Kshamisii, naanu sari artha maaDalilla. Neevu nimma vishayavannu matte hELuveera?",
            Language.HINDI: "Maafi kijiye, main samajh nahi paya. Kya aap phir se bata sakte hain?",
            Language.ENGLISH: "I'm sorry, I didn't get that right. Could you please tell me again what you need?",
        }
        return prompts.get(language, prompts[Language.ENGLISH])


_verification_service: Optional[VerificationService] = None

def get_verification_service() -> VerificationService:
    global _verification_service
    if _verification_service is None:
        _verification_service = VerificationService()
    return _verification_service
