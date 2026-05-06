"""
VaakSetu — Text-to-Speech Service
Converts restatement text to audio for citizen playback.

Production: Coqui TTS / IndicTTS (supports Kannada)
Prototype: gTTS (Google TTS, free, supports Kannada/Hindi/English)
"""

import base64
import io
import logging
import os
from typing import Optional

from models.schemas import Language

logger = logging.getLogger(__name__)

TTS_ENGINE = os.getenv("TTS_ENGINE", "gtts")


class TTSService:
    async def synthesize(self, text: str, language: Language) -> Optional[str]:
        """
        Convert text to speech. Returns base64-encoded MP3 or None.
        """
        lang_code = {
            Language.KANNADA: "kn",
            Language.HINDI: "hi",
            Language.ENGLISH: "en",
        }.get(language, "en")
        
        try:
            from gtts import gTTS
            tts = gTTS(text=text, lang=lang_code, slow=False)
            buf = io.BytesIO()
            tts.write_to_fp(buf)
            buf.seek(0)
            return base64.b64encode(buf.read()).decode("utf-8")
        except Exception as e:
            logger.warning(f"TTS synthesis failed: {e} — skipping audio")
            return None


_tts_service: Optional[TTSService] = None

def get_tts_service() -> TTSService:
    global _tts_service
    if _tts_service is None:
        _tts_service = TTSService()
    return _tts_service
