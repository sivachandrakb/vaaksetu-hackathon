"""
VaakSetu — Dialect Identification Service
Identifies language and Kannada dialect from transcript.

Production: AI4Bharat IndicLID model
Prototype: Rule-based heuristic on vocabulary markers + langdetect
"""

import re
import logging
from typing import Optional

from models.schemas import Language, Dialect, DialectResult

logger = logging.getLogger(__name__)


# ─── Dialect Vocabulary Markers ───────────────────────────────────────────────
# Regional vocabulary patterns for each Kannada dialect.
# In production these are learned by IndicLID from audio features + text.

DIALECT_MARKERS = {
    Dialect.DHARWAD: [
        r"\bhavudaa\b", r"\billaa\b", r"\bhaaNga\b", r"\bmaaDri\b",
        r"\bittu\b", r"\benne\b", r"\bbiDu\b", r"\bnaaDu\b",
        r"dharwad", r"hubli", r"gadag", r"belagavi"
    ],
    Dialect.MYSURU: [
        r"\baagbodu\b", r"\bheLbeku\b", r"\banthidhe\b", r"\bmaaDbeku\b",
        r"\bnoDi\b", r"\bheLi\b", r"\baagtaa\b",
        r"mysuru", r"mysore", r"mandya", r"hassan", r"kodagu"
    ],
    Dialect.MANGALURU: [
        r"\bullaenj\b", r"\bulla\b", r"\baaND\b", r"\bijji\b",
        r"mangalore", r"mangaluru", r"udupi", r"kundapur", r"coastal"
    ],
    Dialect.HAVYAKA: [
        r"\bhavyaka\b", r"\bsirsi\b", r"\bsiddapur\b",
        r"uttara kannada", r"sirsi", r"kumta"
    ],
    Dialect.KODAVA: [
        r"\bkodava\b", r"\bcoorg\b", r"\bkodagu\b",
        r"madikeri", r"virajpet", r"somwarpet"
    ],
    Dialect.BENGALURU: [
        r"\bsaar\b", r"\bmaaDi\b", r"\bheLi\b", r"\bbEku\b",
        r"bengaluru", r"bangalore", r"bang"
    ],
}

# Language detection keyword maps
LANGUAGE_KEYWORDS = {
    Language.KANNADA: [
        "nanna", "naanu", "mane", "illi", "alla", "agide", "maadi", "beku",
        "heLi", "nodri", "kaardi", "rashan", "houdu", "illa", "aagilla",
        "sari", "daya", "tane", "nimma", "avaru", "anta", "aayta"
    ],
    Language.HINDI: [
        "mera", "meri", "hai", "nahi", "karo", "karna", "chahiye",
        "please", "help", "ration", "pension", "card", "naam", "galat",
        "sahi", "theek", "band", "chal", "nahin"
    ],
}


class DialectService:
    """
    Identifies language and dialect from transcript text.
    
    Approach:
    1. Check if OpenAI/LLM identified language from ASR
    2. Run keyword heuristics for Kannada dialect markers
    3. Score each dialect by marker density
    4. Return dialect + confidence
    """

    def identify(self, transcript: str, asr_language: Language) -> DialectResult:
        """
        Identify language and dialect from transcript.
        
        Args:
            transcript: Romanised or native-script transcript
            asr_language: Language as detected by ASR engine
            
        Returns:
            DialectResult with language, dialect, confidence
        """
        text_lower = transcript.lower()
        
        # Step 1: Confirm/refine language
        language = self._confirm_language(text_lower, asr_language)
        
        # Step 2: Only attempt dialect ID for Kannada
        if language != Language.KANNADA:
            return DialectResult(
                language=language,
                dialect=Dialect.STANDARD,
                confidence=0.9 if language != Language.UNKNOWN else 0.3,
                script=self._detect_script(transcript)
            )
        
        # Step 3: Score dialects
        dialect, confidence = self._score_dialects(text_lower)
        
        return DialectResult(
            language=language,
            dialect=dialect,
            confidence=confidence,
            script=self._detect_script(transcript)
        )

    def _confirm_language(self, text: str, asr_lang: Language) -> Language:
        """
        Cross-check ASR language with keyword heuristics.
        If ASR is confident, trust it. Otherwise, run keywords.
        """
        if asr_lang in (Language.ENGLISH, Language.HINDI, Language.KANNADA):
            return asr_lang
        
        # Score each language by keyword hits
        scores = {}
        for lang, keywords in LANGUAGE_KEYWORDS.items():
            hits = sum(1 for kw in keywords if kw in text)
            scores[lang] = hits
        
        if not any(scores.values()):
            return Language.UNKNOWN
        
        return max(scores, key=scores.get)

    def _score_dialects(self, text: str) -> tuple[Dialect, float]:
        """
        Score each dialect by pattern matches. Return best match + confidence.
        """
        scores = {dialect: 0 for dialect in DIALECT_MARKERS}
        
        for dialect, patterns in DIALECT_MARKERS.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    scores[dialect] += 1
        
        total = sum(scores.values())
        if total == 0:
            return Dialect.STANDARD, 0.5
        
        best_dialect = max(scores, key=scores.get)
        best_score = scores[best_dialect]
        
        # Confidence = best score share of total, clamped
        confidence = min(0.95, max(0.5, best_score / total * 1.5))
        
        if best_score == 0:
            return Dialect.STANDARD, 0.5
        
        return best_dialect, confidence

    def _detect_script(self, text: str) -> str:
        """Detect if text is Kannada script, Roman, Devanagari, etc."""
        # Kannada Unicode range: U+0C80–U+0CFF
        kannada_chars = sum(1 for c in text if '\u0C80' <= c <= '\u0CFF')
        # Devanagari Unicode range: U+0900–U+097F
        devanagari_chars = sum(1 for c in text if '\u0900' <= c <= '\u097F')
        
        total = len(text)
        if total == 0:
            return "latin"
        
        if kannada_chars / total > 0.3:
            return "kannada"
        if devanagari_chars / total > 0.3:
            return "devanagari"
        return "latin"

    def format_dialect_label(self, result: DialectResult) -> str:
        """Human-readable label for agent dashboard."""
        lang_labels = {
            Language.KANNADA: "Kannada",
            Language.HINDI: "Hindi",
            Language.ENGLISH: "English",
            Language.UNKNOWN: "Unknown",
        }
        dialect_labels = {
            Dialect.DHARWAD: "Dharwad Kannada",
            Dialect.MYSURU: "Mysuru Kannada",
            Dialect.MANGALURU: "Mangaluru Kannada",
            Dialect.HAVYAKA: "Havyaka",
            Dialect.KODAVA: "Kodava-influenced",
            Dialect.BENGALURU: "Bengaluru Kannada",
            Dialect.STANDARD: "Standard",
            Dialect.UNKNOWN: "Unknown dialect",
        }
        lang = lang_labels.get(result.language, "Unknown")
        dialect = dialect_labels.get(result.dialect, "")
        if result.language == Language.KANNADA and result.dialect != Dialect.STANDARD:
            return f"{dialect} ({lang})"
        return lang


# Module-level singleton
_dialect_service: Optional[DialectService] = None

def get_dialect_service() -> DialectService:
    global _dialect_service
    if _dialect_service is None:
        _dialect_service = DialectService()
    return _dialect_service
