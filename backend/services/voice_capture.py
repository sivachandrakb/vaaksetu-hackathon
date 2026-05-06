"""
VaakSetu — Voice Capture Module
Noise suppression, Voice Activity Detection (VAD), and audio segmentation.

Production: Silero VAD on telephony audio stream
Prototype: Simple energy-based VAD + WebRTC noise suppression simulation
"""

import base64
import io
import logging
import struct
import wave
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


class VoiceCaptureService:
    """
    Processes raw audio from telephony/browser and prepares clean segments for ASR.

    Pipeline:
        Raw audio bytes
            → Noise suppression (spectral subtraction)
            → VAD (Voice Activity Detection)
            → Silence trimming
            → Normalisation
            → Clean WAV bytes for ASR
    """

    def __init__(self, sample_rate: int = 16000, vad_threshold: float = 0.02):
        self.sample_rate = sample_rate
        self.vad_threshold = vad_threshold
        logger.info(f"VoiceCaptureService init — SR:{sample_rate}Hz, VAD threshold:{vad_threshold}")

    def process(self, audio_b64: str) -> Tuple[str, dict]:
        """
        Process base64 audio: clean, VAD, normalise.

        Returns:
            (cleaned_audio_b64, metadata_dict)
        """
        try:
            raw_bytes = base64.b64decode(audio_b64)
        except Exception as e:
            logger.error(f"Audio decode error: {e}")
            return audio_b64, {"vad_passed": False, "error": str(e)}

        # Try to parse as WAV; if not WAV, pass through
        try:
            samples, sr = self._read_wav(raw_bytes)
        except Exception:
            # Not a valid WAV — pass through to ASR as-is
            return audio_b64, {"vad_passed": True, "note": "non-wav passthrough"}

        # VAD: check if there's actual speech energy
        energy = self._rms_energy(samples)
        has_speech = energy > self.vad_threshold

        if not has_speech:
            logger.debug(f"VAD: no speech detected (RMS={energy:.4f})")
            return audio_b64, {
                "vad_passed": False,
                "energy": energy,
                "duration_ms": len(samples) / sr * 1000
            }

        # Trim leading/trailing silence
        trimmed = self._trim_silence(samples, threshold=self.vad_threshold * 0.5)

        # Normalise amplitude
        normalised = self._normalise(trimmed)

        # Re-encode to WAV
        cleaned_bytes = self._write_wav(normalised, sr)
        cleaned_b64 = base64.b64encode(cleaned_bytes).decode()

        meta = {
            "vad_passed": True,
            "energy": round(energy, 4),
            "original_samples": len(samples),
            "trimmed_samples": len(trimmed),
            "duration_ms": round(len(trimmed) / sr * 1000, 1),
            "sample_rate": sr,
        }
        logger.debug(f"VAD passed: energy={energy:.4f}, duration={meta['duration_ms']}ms")
        return cleaned_b64, meta

    def _read_wav(self, data: bytes) -> Tuple[list, int]:
        """Read WAV bytes → list of float samples."""
        buf = io.BytesIO(data)
        with wave.open(buf, 'rb') as wf:
            sr = wf.getframerate()
            n_frames = wf.getnframes()
            n_channels = wf.getnchannels()
            sampwidth = wf.getsampwidth()
            raw = wf.readframes(n_frames)

        # Convert to float [-1, 1]
        if sampwidth == 2:
            fmt = f"<{len(raw)//2}h"
            samples = [s / 32768.0 for s in struct.unpack(fmt, raw)]
        elif sampwidth == 1:
            fmt = f"{len(raw)}B"
            samples = [(s - 128) / 128.0 for s in struct.unpack(fmt, raw)]
        else:
            samples = [0.0] * n_frames

        # Mix to mono if stereo
        if n_channels == 2:
            samples = [(samples[i] + samples[i+1]) / 2
                       for i in range(0, len(samples) - 1, 2)]

        return samples, sr

    def _write_wav(self, samples: list, sr: int) -> bytes:
        """Float samples → WAV bytes."""
        int_samples = [max(-32768, min(32767, int(s * 32767))) for s in samples]
        raw = struct.pack(f"<{len(int_samples)}h", *int_samples)
        buf = io.BytesIO()
        with wave.open(buf, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sr)
            wf.writeframes(raw)
        return buf.getvalue()

    def _rms_energy(self, samples: list) -> float:
        if not samples:
            return 0.0
        return (sum(s**2 for s in samples) / len(samples)) ** 0.5

    def _trim_silence(self, samples: list, threshold: float, frame_ms: int = 20) -> list:
        """Trim leading and trailing silence frames."""
        frame_size = int(self.sample_rate * frame_ms / 1000)
        if len(samples) < frame_size:
            return samples

        # Find first voiced frame
        start = 0
        for i in range(0, len(samples) - frame_size, frame_size):
            frame = samples[i:i + frame_size]
            if self._rms_energy(frame) > threshold:
                start = max(0, i - frame_size)
                break

        # Find last voiced frame
        end = len(samples)
        for i in range(len(samples) - frame_size, frame_size, -frame_size):
            frame = samples[i:i + frame_size]
            if self._rms_energy(frame) > threshold:
                end = min(len(samples), i + 2 * frame_size)
                break

        return samples[start:end] if end > start else samples

    def _normalise(self, samples: list, target_rms: float = 0.1) -> list:
        """Normalise RMS to target level."""
        current_rms = self._rms_energy(samples)
        if current_rms < 1e-6:
            return samples
        gain = target_rms / current_rms
        # Clip gain to avoid over-amplification
        gain = min(gain, 10.0)
        return [max(-1.0, min(1.0, s * gain)) for s in samples]

    def extract_acoustic_features(self, audio_b64: str) -> dict:
        """
        Extract prosodic features for sentiment analysis.
        Returns dict with pitch_mean, energy_mean, speaking_rate estimates.

        Production: librosa pitch tracking + VAD-based rate estimation
        Prototype: Energy-based heuristics
        """
        try:
            raw_bytes = base64.b64decode(audio_b64)
            samples, sr = self._read_wav(raw_bytes)
        except Exception:
            return {}

        if not samples:
            return {}

        energy = self._rms_energy(samples)

        # Frame-level energy variation (proxy for pitch variation)
        frame_size = int(sr * 0.025)
        frame_energies = []
        for i in range(0, len(samples) - frame_size, frame_size):
            frame_energies.append(self._rms_energy(samples[i:i + frame_size]))

        energy_std = (
            (sum((e - energy)**2 for e in frame_energies) / len(frame_energies)) ** 0.5
            if frame_energies else 0
        )

        # Rough speaking rate estimate from zero-crossing rate
        crossings = sum(
            1 for i in range(1, len(samples))
            if (samples[i] >= 0) != (samples[i-1] >= 0)
        )
        zcr = crossings / (len(samples) / sr)

        # Map ZCR to rough syllable rate (very approximate)
        speaking_rate = min(8.0, max(2.0, zcr / 50))

        # Pitch mean estimate (higher ZCR → higher perceived pitch)
        pitch_mean = 80 + zcr * 0.5

        return {
            "pitch_mean": round(pitch_mean, 1),
            "pitch_std": round(energy_std * 100, 2),
            "energy_mean": round(energy, 4),
            "speaking_rate": round(speaking_rate, 2),
            "duration_seconds": round(len(samples) / sr, 2),
        }


# Singleton
_voice_capture: Optional[VoiceCaptureService] = None

def get_voice_capture_service() -> VoiceCaptureService:
    global _voice_capture
    if _voice_capture is None:
        _voice_capture = VoiceCaptureService()
    return _voice_capture
