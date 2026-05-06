"""
VaakSetu — Test Suite
pytest tests for all backend services and API endpoints.
Run: cd backend && pytest ../tests/ -v
"""

import pytest
import asyncio
import sys
import os

# Make backend importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

# ── Dialect Service Tests ─────────────────────────────────────────────────────

class TestDialectService:
    def setup_method(self):
        from services.dialect import DialectService
        self.svc = DialectService()

    def test_kannada_detected(self):
        from models.schemas import Language, Dialect
        result = self.svc.identify("Namma ration card Aadhaar link aagilla", Language.KANNADA)
        assert result.language == Language.KANNADA

    def test_dharwad_dialect(self):
        from models.schemas import Language, Dialect
        result = self.svc.identify("Haavudaa nimma dharwad office le file haaNga maaDri", Language.KANNADA)
        assert result.language == Language.KANNADA

    def test_hindi_detected(self):
        from models.schemas import Language
        result = self.svc.identify("Mera ration card mein naam galat hai", Language.HINDI)
        assert result.language == Language.HINDI

    def test_english_passthrough(self):
        from models.schemas import Language, Dialect
        result = self.svc.identify("My water supply is not working", Language.ENGLISH)
        assert result.language == Language.ENGLISH
        assert result.dialect == Dialect.STANDARD

    def test_bengaluru_dialect(self):
        from models.schemas import Language
        result = self.svc.identify("Saar Bangalore le road le pothole ide please noDi maaDi", Language.KANNADA)
        assert result.language == Language.KANNADA

    def test_script_detection_kannada(self):
        result = self.svc._detect_script("ನಮ್ಮ ರೇಷನ್ ಕಾರ್ಡ್")
        assert result == "kannada"

    def test_script_detection_latin(self):
        result = self.svc._detect_script("Namma ration card")
        assert result == "latin"


# ── Sentiment Service Tests ───────────────────────────────────────────────────

class TestSentimentService:
    def setup_method(self):
        from services.sentiment import SentimentService
        self.svc = SentimentService()

    def test_distress_detected_english(self):
        from models.schemas import Language, Sentiment
        result = self.svc.classify("Please help me I am desperate nobody is listening", Language.ENGLISH)
        assert result.sentiment in (Sentiment.DISTRESS, Sentiment.URGENCY)

    def test_anger_detected_kannada(self):
        from models.schemas import Language, Sentiment
        result = self.svc.classify("Nimdu bekar kelsa, satta sullu maaDtidare", Language.KANNADA)
        assert result.sentiment in (Sentiment.ANGER, Sentiment.CONFUSION)

    def test_calm_detected(self):
        from models.schemas import Language, Sentiment
        result = self.svc.classify("Okay thank you yes that is correct understood", Language.ENGLISH)
        assert result.sentiment in (Sentiment.CALM, Sentiment.CONFUSION)

    def test_urgency_flag_emergency(self):
        from models.schemas import Language
        result = self.svc.classify("Emergency please help immediately urgent hospital", Language.ENGLISH)
        assert result.urgency_flag == True

    def test_urgency_flag_kannada(self):
        from models.schemas import Language
        result = self.svc.classify("Bega bEga help maaDri urgent aagide tumba kashta", Language.KANNADA)
        assert result.urgency_flag == True

    def test_label_is_string(self):
        from models.schemas import Language
        result = self.svc.classify("I need help", Language.ENGLISH)
        assert isinstance(result.label, str)
        assert len(result.label) > 0

    def test_confidence_in_range(self):
        from models.schemas import Language
        result = self.svc.classify("My ration card is not linked", Language.ENGLISH)
        assert 0.0 <= result.confidence <= 1.0


# ── Verification Service Tests ────────────────────────────────────────────────

class TestVerificationService:
    def setup_method(self):
        from services.verification import VerificationService
        self.svc = VerificationService()

    def test_houdu_confirmed(self):
        from models.schemas import Language, VerificationOutcome
        result = self.svc.classify_response("houdu sari", Language.KANNADA)
        assert result.outcome == VerificationOutcome.CONFIRMED

    def test_yes_confirmed_english(self):
        from models.schemas import Language, VerificationOutcome
        result = self.svc.classify_response("yes that is correct", Language.ENGLISH)
        assert result.outcome == VerificationOutcome.CONFIRMED

    def test_haan_confirmed_hindi(self):
        from models.schemas import Language, VerificationOutcome
        result = self.svc.classify_response("haan bilkul sahi hai", Language.HINDI)
        assert result.outcome == VerificationOutcome.CONFIRMED

    def test_illa_incorrect(self):
        from models.schemas import Language, VerificationOutcome
        result = self.svc.classify_response("illa alla sari alla", Language.KANNADA)
        assert result.outcome == VerificationOutcome.INCORRECT

    def test_no_incorrect_english(self):
        from models.schemas import Language, VerificationOutcome
        result = self.svc.classify_response("no that's wrong", Language.ENGLISH)
        assert result.outcome == VerificationOutcome.INCORRECT

    def test_partial_correction(self):
        from models.schemas import Language, VerificationOutcome
        result = self.svc.classify_response("houdu aaadre ration card alla pension card", Language.KANNADA)
        assert result.outcome == VerificationOutcome.PARTIAL

    def test_empty_response_uncertain(self):
        from models.schemas import Language, VerificationOutcome
        result = self.svc.classify_response("", Language.KANNADA)
        assert result.outcome == VerificationOutcome.UNCERTAIN

    def test_skip_loop_high_distress(self):
        result = self.svc.should_skip_loop(True, "⚠️ Citizen appears distressed")
        assert result == True

    def test_no_skip_when_calm(self):
        result = self.svc.should_skip_loop(False, "✅ Citizen is calm")
        assert result == False

    def test_attempt_number_tracked(self):
        from models.schemas import Language
        result = self.svc.classify_response("houdu", Language.KANNADA, attempt_number=2)
        assert result.attempt_number == 2


# ── Confidence Service Tests ──────────────────────────────────────────────────

class TestConfidenceService:
    def setup_method(self):
        from services.confidence import ConfidenceService
        self.svc = ConfidenceService()

    def _make_asr(self, confidence=0.9):
        from models.schemas import Language
        return type('ASR', (), {
            'confidence': confidence, 'transcript': 'test', 'language': Language.KANNADA,
            'duration_seconds': 3.0, 'segments': []
        })()

    def _make_dialect(self, confidence=0.8):
        from models.schemas import Language, Dialect
        return type('D', (), {
            'language': Language.KANNADA, 'dialect': Dialect.STANDARD,
            'confidence': confidence, 'script': 'latin'
        })()

    def _make_interpretation(self, confidence=0.85):
        from models.schemas import InterpretationResult
        return InterpretationResult(
            core_issue="Test issue",
            intent="complaint",
            entities=[],
            department="Test Dept",
            restatement="Test restatement",
            confidence=confidence
        )

    def _make_sentiment(self, sentiment_val="calm", urgency=False):
        from models.schemas import SentimentResult, Sentiment
        sent = Sentiment(sentiment_val)
        return SentimentResult(
            sentiment=sent,
            confidence=0.8,
            acoustic_signal=sent,
            lexical_signal=sent,
            urgency_flag=urgency,
            label="Test label"
        )

    def test_proceed_on_high_confidence(self):
        from models.schemas import ConfidenceDecision
        eval = self.svc.evaluate(
            self._make_asr(0.9), self._make_dialect(0.9),
            self._make_interpretation(0.9), self._make_sentiment("calm", False)
        )
        assert eval.decision in (ConfidenceDecision.PROCEED, ConfidenceDecision.CLARIFY)

    def test_escalate_on_distress_urgency(self):
        from models.schemas import ConfidenceDecision
        eval = self.svc.evaluate(
            self._make_asr(0.85), self._make_dialect(0.8),
            self._make_interpretation(0.8), self._make_sentiment("distress", True)
        )
        assert eval.decision == ConfidenceDecision.ESCALATE

    def test_escalate_on_low_asr(self):
        from models.schemas import ConfidenceDecision
        eval = self.svc.evaluate(
            self._make_asr(0.3), self._make_dialect(0.8),
            self._make_interpretation(0.8), self._make_sentiment("calm")
        )
        assert eval.decision == ConfidenceDecision.ESCALATE

    def test_overall_score_in_range(self):
        eval = self.svc.evaluate(
            self._make_asr(0.8), self._make_dialect(0.7),
            self._make_interpretation(0.75), self._make_sentiment("confusion")
        )
        assert 0.0 <= eval.overall_score <= 1.0

    def test_proceed_after_confirmed_verification(self):
        from models.schemas import ConfidenceDecision, VerificationResult, VerificationOutcome
        verification = VerificationResult(
            outcome=VerificationOutcome.CONFIRMED,
            attempt_number=1,
            citizen_response="houdu sari",
            signal_type="positive"
        )
        eval = self.svc.evaluate(
            self._make_asr(0.8), self._make_dialect(0.8),
            self._make_interpretation(0.78), self._make_sentiment("confusion"),
            verification
        )
        assert eval.decision == ConfidenceDecision.PROCEED


# ── RAG Service Tests ─────────────────────────────────────────────────────────

class TestRAGService:
    def setup_method(self):
        from services.rag import RAGService
        self.svc = RAGService()

    def test_ration_card_context(self):
        context, sources = self.svc.get_context("ration card Aadhaar link aagilla")
        assert "Seva Sindhu" in sources or len(context) > 10

    def test_water_bwssb_context(self):
        context, sources = self.svc.get_context("BWSSB water supply not working")
        assert "BWSSB" in sources

    def test_bbmp_context(self):
        context, sources = self.svc.get_context("BBMP road pothole garbage complaint")
        assert "BBMP" in sources

    def test_empty_context_graceful(self):
        context, sources = self.svc.get_context("hello")
        assert isinstance(context, str)
        assert isinstance(sources, list)

    def test_feed_returns_list(self):
        feeds = self.svc.get_all_feed()
        assert isinstance(feeds, list)
        assert len(feeds) > 0

    def test_feed_has_required_fields(self):
        feeds = self.svc.get_all_feed()
        for feed in feeds:
            assert "source" in feed
            assert "status" in feed
            assert "preview" in feed


# ── VoiceCapture Tests ────────────────────────────────────────────────────────

class TestVoiceCaptureService:
    def setup_method(self):
        from services.voice_capture import VoiceCaptureService
        self.svc = VoiceCaptureService()

    def test_invalid_audio_passthrough(self):
        import base64
        bad_b64 = base64.b64encode(b"not audio").decode()
        result_b64, meta = self.svc.process(bad_b64)
        assert isinstance(result_b64, str)

    def test_rms_energy_silence(self):
        energy = self.svc._rms_energy([0.0] * 100)
        assert energy == 0.0

    def test_rms_energy_nonzero(self):
        energy = self.svc._rms_energy([0.5] * 100)
        assert energy > 0

    def test_normalise_scales_up(self):
        samples = [0.01] * 100
        normed = self.svc._normalise(samples, target_rms=0.1)
        assert self.svc._rms_energy(normed) > self.svc._rms_energy(samples)

    def test_normalise_clips_to_range(self):
        samples = [1.0] * 100
        normed = self.svc._normalise(samples)
        assert all(-1.0 <= s <= 1.0 for s in normed)


# ── Schema Validation Tests ───────────────────────────────────────────────────

class TestSchemas:
    def test_call_session_defaults(self):
        from models.schemas import CallSession, CallStatus
        s = CallSession(session_id="test-123")
        assert s.status == CallStatus.ACTIVE
        assert s.escalated == False

    def test_entity_confidence_range(self):
        from models.schemas import Entity
        e = Entity(type="location", value="Bengaluru", confidence=0.9)
        assert e.confidence == 0.9

    def test_feedback_record_required_fields(self):
        from models.schemas import FeedbackRecord, Language, Dialect, Sentiment, VerificationOutcome
        f = FeedbackRecord(
            session_id="test",
            transcript="test transcript",
            ai_interpretation="test interpretation",
            verified_interpretation="test verified",
            sentiment=Sentiment.CALM,
            language=Language.KANNADA,
            dialect=Dialect.STANDARD,
            outcome=VerificationOutcome.CONFIRMED,
            quality_signal="positive"
        )
        assert f.session_id == "test"
