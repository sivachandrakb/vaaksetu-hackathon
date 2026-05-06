"""
VaakSetu — ASR Service
Whisper-based speech-to-text with confidence scoring.
In production: Whisper Large-v3 fine-tuned on AI4Bharat IndicSUPERB.
For hackathon prototype: uses OpenAI Whisper API or local whisper model.
"""

import base64
import io
import os
import tempfile
import time
import logging
from typing import Optional

import numpy as np

from models.schemas import ASRResult, Language

logger = logging.getLogger(__name__)

# Whisper model size — configurable via env
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "base")


class ASRService:
    """
    Automatic Speech Recognition using OpenAI Whisper.
    
    Production: Fine-tuned Whisper Large-v3 on IndicSUPERB Kannada corpus.
    Prototype: Base Whisper model with language detection.
    """

    def __init__(self):
        self._model = None
        self._use_api = bool(os.getenv("OPENAI_API_KEY"))
        logger.info(f"ASR Service init — mode: {'OpenAI API' if self._use_api else 'local whisper'}, model: {WHISPER_MODEL}")

    def _load_local_model(self):
        """Lazy-load local Whisper model (avoids slow startup)."""
        if self._model is None:
            try:
                import whisper
                logger.info(f"Loading Whisper model: {WHISPER_MODEL}")
                self._model = whisper.load_model(WHISPER_MODEL)
                logger.info("Whisper model loaded.")
            except ImportError:
                logger.warning("openai-whisper not installed. Using mock ASR.")
                self._model = "mock"
        return self._model

    async def transcribe(self, audio_b64: str, language_hint: Optional[str] = None) -> ASRResult:
        """
        Transcribe base64-encoded audio.
        
        Args:
            audio_b64: Base64-encoded WAV audio bytes
            language_hint: Optional ISO language code hint
            
        Returns:
            ASRResult with transcript, language, confidence
        """
        try:
            audio_bytes = base64.b64decode(audio_b64)
        except Exception as e:
            logger.error(f"Audio decode error: {e}")
            return self._mock_asr_result("(audio decode error)")

        if self._use_api:
            return await self._transcribe_via_api(audio_bytes, language_hint)
        else:
            return self._transcribe_local(audio_bytes, language_hint)

    async def _transcribe_via_api(self, audio_bytes: bytes, language_hint: Optional[str]) -> ASRResult:
        """Use OpenAI Whisper API."""
        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI()
            
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                f.write(audio_bytes)
                tmp_path = f.name

            with open(tmp_path, "rb") as audio_file:
                kwargs = {"model": "whisper-1", "file": audio_file, "response_format": "verbose_json"}
                if language_hint:
                    kwargs["language"] = language_hint
                result = await client.audio.transcriptions.create(**kwargs)

            os.unlink(tmp_path)

            lang = self._map_language(result.language if hasattr(result, 'language') else 'unknown')
            transcript = result.text.strip() if hasattr(result, 'text') else ""
            
            # Whisper API doesn't return per-token confidence; estimate from result quality
            confidence = self._estimate_confidence(transcript, audio_bytes)
            
            return ASRResult(
                transcript=transcript,
                language=lang,
                confidence=confidence,
                duration_seconds=len(audio_bytes) / (16000 * 2),  # estimate
                segments=[]
            )
        except Exception as e:
            logger.error(f"Whisper API error: {e}")
            return self._mock_asr_result("(API transcription failed — using mock)")

    def _transcribe_local(self, audio_bytes: bytes, language_hint: Optional[str]) -> ASRResult:
        """Use local Whisper model."""
        model = self._load_local_model()
        
        if model == "mock":
            return self._mock_asr_result()

        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                f.write(audio_bytes)
                tmp_path = f.name

            options = {}
            if language_hint:
                options["language"] = language_hint
            
            start = time.time()
            result = model.transcribe(tmp_path, **options)
            elapsed = time.time() - start
            
            os.unlink(tmp_path)
            
            transcript = result["text"].strip()
            lang = self._map_language(result.get("language", "unknown"))
            
            # Compute average segment confidence
            segments = result.get("segments", [])
            if segments:
                avg_logprob = sum(s.get("avg_logprob", -1.0) for s in segments) / len(segments)
                # logprob → probability (roughly): exp(logprob), clamped to [0,1]
                confidence = min(1.0, max(0.0, float(np.exp(avg_logprob))))
            else:
                confidence = 0.7

            return ASRResult(
                transcript=transcript,
                language=lang,
                confidence=confidence,
                duration_seconds=elapsed,
                segments=segments
            )
        except Exception as e:
            logger.error(f"Local Whisper error: {e}")
            return self._mock_asr_result("(local transcription error)")

    def _map_language(self, whisper_lang: str) -> Language:
        mapping = {
            "kannada": Language.KANNADA,
            "kn": Language.KANNADA,
            "hindi": Language.HINDI,
            "hi": Language.HINDI,
            "english": Language.ENGLISH,
            "en": Language.ENGLISH,
        }
        return mapping.get(whisper_lang.lower(), Language.UNKNOWN)

    def _estimate_confidence(self, transcript: str, audio_bytes: bytes) -> float:
        """Heuristic confidence from transcript quality."""
        if not transcript or len(transcript) < 3:
            return 0.3
        if len(transcript) > 10:
            return 0.85
        return 0.6

    def _mock_asr_result(self, override_text: str = None) -> ASRResult:
        """
        Mock ASR for demo/testing when no audio device or model available.
        Returns realistic Kannada helpline transcripts.
        """
        import random
        mock_transcripts = [
            ("ನನ್ನ ರೇಷನ್ ಕಾರ್ಡ್ ಆಧಾರ್ ಜೊತೆ ಲಿಂಕ್ ಆಗಿಲ್ಲ, ದಯವಿಟ್ಟು ಸಹಾಯ ಮಾಡಿ", Language.KANNADA, 0.88),
            ("Nanna pension haNA ee tumhiN bandilla, tumhiN maaDu help", Language.KANNADA, 0.82),
            ("मेरे राशन कार्ड में नाम गलत है, सुधार करना है", Language.HINDI, 0.91),
            ("My BWSSB water connection is not working since yesterday please help", Language.ENGLISH, 0.95),
            ("ನಮ್ಮ ಊರಿನಲ್ಲಿ ನೀರು ಬರ್ತಾ ಇಲ್ಲ, ಯಲಹಂಕದಲ್ಲಿ", Language.KANNADA, 0.87),
            ("Nanna land record mutation pending aagide, Bhoomi portal le status check maaDabeku", Language.KANNADA, 0.79),
        ]
        
        if override_text:
            return ASRResult(
                transcript=override_text,
                language=Language.UNKNOWN,
                confidence=0.0,
                duration_seconds=0.0
            )
        
        text, lang, conf = random.choice(mock_transcripts)
        return ASRResult(
            transcript=text,
            language=lang,
            confidence=conf,
            duration_seconds=3.5
        )


# Module-level singleton
_asr_service: Optional[ASRService] = None

def get_asr_service() -> ASRService:
    global _asr_service
    if _asr_service is None:
        _asr_service = ASRService()
    return _asr_service
