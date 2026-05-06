"""
VaakSetu — Sentiment & Urgency Classifier
Dual-channel sentiment: acoustic (Wav2Vec2) + lexical (MuRIL/keyword).

Production: Fine-tuned Wav2Vec2 on IEMOCAP + Indic data (acoustic)
            MuRIL fine-tuned on sentiment data (lexical)
Prototype: Keyword-based lexical + pitch/energy heuristics for acoustic simulation
"""

import re
import logging
from typing import Optional

from models.schemas import Sentiment, SentimentResult, Language

logger = logging.getLogger(__name__)


# ─── Lexical Sentiment Markers ────────────────────────────────────────────────

DISTRESS_MARKERS = {
    "en": ["help", "emergency", "urgent", "dying", "sick", "hospital", "please please",
           "crying", "nobody", "alone", "desperate", "no money", "can't"],
    "kn": ["saayi", "tappu", "haani", "yaaro", "tumba", "kashta", "bhaya",
           "help maaDi", "daya", "aagalla", "hegaadre", "beka beka"],
    "hi": ["maro", "madad", "karo", "please", "bimar", "emergency", "hospital",
           "bahut", "mushkil", "pareshan", "takleef", "dard"],
}

ANGER_MARKERS = {
    "en": ["useless", "idiots", "worst", "terrible", "pathetic", "waste", "cheating",
           "fraud", "corrupt", "never", "always fails", "sick of"],
    "kn": ["bekar", "hoda", "ketta", "yaakadru", "haaLu", "gadibidi", "satta",
           "modalE", "sullu", "bekilla"],
    "hi": ["bakwaas", "bekar", "faltu", "cheat", "dhoka", "ganda", "worst",
           "kaam nahi", "pagal", "bewakoof"],
}

URGENCY_MARKERS = {
    "en": ["urgent", "immediately", "right now", "emergency", "today", "deadline",
           "quickly", "asap", "fast", "hurry"],
    "kn": ["turant", "bEga bEga", "jaldi", "urgent", "inda", "ivattu",
           "deadline", "last date", "adE dina"],
    "hi": ["jaldi", "turant", "abhi", "aaj", "deadline", "emergency",
           "karo na", "please jaldi"],
}

CONFUSION_MARKERS = {
    "en": ["don't know", "confused", "understand", "what to do", "which office",
           "not sure", "how to", "lost", "nobody told me"],
    "kn": ["gotilla", "gottilla", "hegaadru", "yaavadu", "hEge", "yaavaaga",
           "yaaru", "enoo gotilla", "hELilla"],
    "hi": ["pata nahi", "samajh nahi", "kya karna", "kaise", "kaun",
           "kahan", "koi nahi bola"],
}

CALM_MARKERS = {
    "en": ["okay", "thank you", "fine", "yes", "no problem", "understood"],
    "kn": ["sari", "houdu", "aaytu", "dhanyavada", "okay", "aaguttade"],
    "hi": ["theek", "haan", "samajh gaya", "dhanyawad", "okay", "sahi"],
}


class SentimentService:
    """
    Dual-channel sentiment classifier.
    
    Channel 1 (Acoustic): In production uses Wav2Vec2 prosodic features.
                          In prototype: mock based on text heuristics.
    Channel 2 (Lexical):  Keyword-based scoring across Kannada, Hindi, English.
    
    Fusion: If channels agree, high confidence. If disagree, acoustic wins for
            distress/anger (vocal cues are harder to mask than words).
    """

    def classify(
        self,
        transcript: str,
        language: Language,
        audio_features: Optional[dict] = None
    ) -> SentimentResult:
        """
        Classify sentiment from transcript (and optionally audio features).
        
        Args:
            transcript: Transcribed text
            language: Detected language
            audio_features: Optional dict with pitch_mean, energy, speaking_rate
            
        Returns:
            SentimentResult with fused sentiment, urgency flag, dashboard label
        """
        text = transcript.lower()
        
        # Channel 2: Lexical scoring
        lexical_sentiment, lexical_conf = self._lexical_classify(text, language)
        
        # Channel 1: Acoustic (mock in prototype; real in production)
        acoustic_sentiment, acoustic_conf = self._acoustic_classify(
            audio_features or {}, lexical_sentiment
        )
        
        # Fusion: acoustic wins on high-arousal states
        fused, confidence = self._fuse(
            acoustic_sentiment, acoustic_conf,
            lexical_sentiment, lexical_conf
        )
        
        urgency = self._check_urgency(text, language, fused)
        label = self._generate_label(fused, urgency)
        
        return SentimentResult(
            sentiment=fused,
            confidence=confidence,
            acoustic_signal=acoustic_sentiment,
            lexical_signal=lexical_sentiment,
            urgency_flag=urgency,
            label=label
        )

    def _lexical_classify(self, text: str, language: Language) -> tuple[Sentiment, float]:
        """Score text against keyword banks for each sentiment."""
        lang_key = {
            Language.KANNADA: "kn",
            Language.HINDI: "hi",
            Language.ENGLISH: "en",
        }.get(language, "en")

        scores = {
            Sentiment.DISTRESS: self._score(text, DISTRESS_MARKERS.get(lang_key, []) + DISTRESS_MARKERS["en"]),
            Sentiment.ANGER: self._score(text, ANGER_MARKERS.get(lang_key, []) + ANGER_MARKERS["en"]),
            Sentiment.URGENCY: self._score(text, URGENCY_MARKERS.get(lang_key, []) + URGENCY_MARKERS["en"]),
            Sentiment.CONFUSION: self._score(text, CONFUSION_MARKERS.get(lang_key, []) + CONFUSION_MARKERS["en"]),
            Sentiment.CALM: self._score(text, CALM_MARKERS.get(lang_key, []) + CALM_MARKERS["en"]),
        }
        
        total = sum(scores.values())
        if total == 0:
            return Sentiment.CONFUSION, 0.5
        
        best = max(scores, key=scores.get)
        confidence = min(0.92, scores[best] / max(total, 1) * 1.8)
        return best, max(0.4, confidence)

    def _acoustic_classify(
        self,
        features: dict,
        lexical_fallback: Sentiment
    ) -> tuple[Sentiment, float]:
        """
        Acoustic sentiment from prosodic features.
        
        Production: Wav2Vec2 embeddings → classifier head.
        Prototype: Rule-based on pitch, energy, speaking_rate heuristics.
        
        Feature dict keys: pitch_mean, pitch_std, energy_mean, speaking_rate
        """
        if not features:
            # No audio features available — use lexical as acoustic proxy with lower confidence
            return lexical_fallback, 0.55
        
        pitch_mean = features.get("pitch_mean", 150)
        energy = features.get("energy_mean", 0.1)
        speaking_rate = features.get("speaking_rate", 4.0)  # syllables/second
        
        # High pitch + high energy → distress or anger
        if pitch_mean > 250 and energy > 0.3:
            if speaking_rate > 5.5:
                return Sentiment.ANGER, 0.78
            return Sentiment.DISTRESS, 0.75
        
        # High energy, faster speech → urgency
        if energy > 0.25 and speaking_rate > 5.0:
            return Sentiment.URGENCY, 0.70
        
        # Low energy, slow speech → calm or confusion
        if energy < 0.08 and speaking_rate < 3.5:
            return Sentiment.CALM, 0.72
        
        # Mid features → confusion
        return Sentiment.CONFUSION, 0.60

    def _fuse(
        self,
        acoustic: Sentiment, a_conf: float,
        lexical: Sentiment, l_conf: float
    ) -> tuple[Sentiment, float]:
        """
        Fuse acoustic and lexical channels.
        
        Rules:
        - If both agree → high confidence
        - Acoustic wins for distress/anger (arousal states)
        - Lexical wins for confusion/calm (cognitive states)
        - Disagreement on urgency → take higher-confidence signal
        """
        if acoustic == lexical:
            return acoustic, min(0.97, (a_conf + l_conf) / 2 + 0.1)
        
        # Acoustic priority for high-arousal states
        if acoustic in (Sentiment.DISTRESS, Sentiment.ANGER):
            return acoustic, a_conf * 0.9
        
        # Lexical priority for cognitive states
        if lexical in (Sentiment.CONFUSION, Sentiment.CALM):
            return lexical, l_conf * 0.85
        
        # Default: higher confidence wins
        if a_conf >= l_conf:
            return acoustic, a_conf * 0.8
        return lexical, l_conf * 0.8

    def _check_urgency(self, text: str, language: Language, sentiment: Sentiment) -> bool:
        """Urgency = URGENCY/DISTRESS sentiment OR explicit urgency keywords."""
        if sentiment in (Sentiment.URGENCY, Sentiment.DISTRESS):
            return True
        
        lang_key = {Language.KANNADA: "kn", Language.HINDI: "hi"}.get(language, "en")
        urgency_hits = self._score(text, URGENCY_MARKERS.get(lang_key, []) + URGENCY_MARKERS["en"])
        return urgency_hits >= 1

    def _score(self, text: str, markers: list) -> int:
        return sum(1 for m in markers if m.lower() in text)

    def _generate_label(self, sentiment: Sentiment, urgency: bool) -> str:
        """Human-readable label for agent dashboard."""
        labels = {
            Sentiment.DISTRESS: "⚠️ Citizen appears distressed",
            Sentiment.ANGER: "⚠️ Citizen sounds frustrated/angry",
            Sentiment.FEAR: "⚠️ Citizen appears fearful",
            Sentiment.CONFUSION: "ℹ️ Citizen sounds confused",
            Sentiment.URGENCY: "🔴 Citizen has an urgent matter",
            Sentiment.CALM: "✅ Citizen is calm",
            Sentiment.UNKNOWN: "❓ Sentiment unclear",
        }
        label = labels.get(sentiment, "❓ Sentiment unclear")
        if urgency and sentiment not in (Sentiment.URGENCY, Sentiment.DISTRESS):
            label += " — Urgency flagged"
        return label


# Module-level singleton
_sentiment_service: Optional[SentimentService] = None

def get_sentiment_service() -> SentimentService:
    global _sentiment_service
    if _sentiment_service is None:
        _sentiment_service = SentimentService()
    return _sentiment_service
