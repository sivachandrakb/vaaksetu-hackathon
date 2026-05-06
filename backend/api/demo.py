"""
VaakSetu — Demo API Router
Endpoints that drive the hackathon demo without needing a real microphone.
Simulates the full pipeline using pre-written realistic call transcripts.
"""

import logging
import random
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional

from db.database import get_db
from demo.scenarios import DEMO_SCENARIOS, SCENARIOS_BY_ID, SCENARIOS_BY_CATEGORY
from services.sentiment import get_sentiment_service
from services.dialect import get_dialect_service
from services.interpretation import get_interpretation_service
from services.confidence import get_confidence_service
from services.tts import get_tts_service
from models.schemas import Language, Dialect

logger = logging.getLogger(__name__)
router = APIRouter()


class RunScenarioRequest(BaseModel):
    scenario_id: Optional[str] = None      # specific ID e.g. "RC001"
    category: Optional[str] = None         # or category: "ration", "pension", etc.
    random_pick: bool = False


@router.get("/scenarios")
async def list_scenarios():
    """List all available demo scenarios."""
    return {
        "total": len(DEMO_SCENARIOS),
        "categories": list(SCENARIOS_BY_CATEGORY.keys()),
        "scenarios": [
            {
                "id": s["id"],
                "title": s["title"],
                "language": s["language"],
                "dialect": s["dialect"],
                "sentiment": s["sentiment"],
            }
            for s in DEMO_SCENARIOS
        ]
    }


@router.post("/run")
async def run_demo_scenario(request: RunScenarioRequest):
    """
    Run the full AI pipeline on a pre-written demo scenario.
    Returns all pipeline outputs without needing audio input.
    Perfect for demo/presentation mode.
    """
    # Pick scenario
    if request.scenario_id:
        scenario = SCENARIOS_BY_ID.get(request.scenario_id)
        if not scenario:
            raise HTTPException(404, f"Scenario {request.scenario_id} not found")
    elif request.category:
        pool = SCENARIOS_BY_CATEGORY.get(request.category, [])
        if not pool:
            raise HTTPException(404, f"Category '{request.category}' not found")
        scenario = random.choice(pool)
    elif request.random_pick:
        scenario = random.choice(DEMO_SCENARIOS)
    else:
        # Default: first scenario
        scenario = DEMO_SCENARIOS[0]

    transcript = scenario["transcript"]
    lang_map = {"kn": Language.KANNADA, "hi": Language.HINDI, "en": Language.ENGLISH}
    language = lang_map.get(scenario["language"], Language.UNKNOWN)

    # ── Run pipeline ──────────────────────────────────────────────────────────
    dialect_svc = get_dialect_service()
    sentiment_svc = get_sentiment_service()
    interp_svc = get_interpretation_service()
    confidence_svc = get_confidence_service()
    tts_svc = get_tts_service()

    # Dialect
    dialect_result = dialect_svc.identify(transcript, language)

    # Sentiment
    sentiment_result = sentiment_svc.classify(transcript, language)

    # Interpretation
    interpretation = await interp_svc.interpret(
        transcript, language, dialect_result.dialect, sentiment_result
    )

    # TTS restatement
    restatement_audio = await tts_svc.synthesize(interpretation.restatement, language)
    interpretation.restatement_audio_b64 = restatement_audio

    # Confidence (simulated as confirmed for demo)
    from models.schemas import VerificationResult, VerificationOutcome
    from services.asr import ASRResult
    mock_asr = type('ASR', (), {
        'confidence': 0.87,
        'transcript': transcript,
        'language': language,
        'duration_seconds': 4.2,
        'segments': []
    })()
    confidence_eval = confidence_svc.evaluate(
        mock_asr, dialect_result, interpretation, sentiment_result
    )

    skip_verification = sentiment_svc.classify(transcript, language).urgency_flag and \
                        sentiment_result.sentiment.value in ("distress", "anger")

    return {
        "scenario": {
            "id": scenario["id"],
            "title": scenario["title"],
            "expected_issue": scenario["expected_issue"],
            "expected_dept": scenario["expected_dept"],
        },
        "pipeline": {
            "transcript": transcript,
            "language": language.value,
            "dialect": dialect_svc.format_dialect_label(dialect_result),
            "dialect_confidence": round(dialect_result.confidence, 2),
            "sentiment": {
                "sentiment": sentiment_result.sentiment.value,
                "label": sentiment_result.label,
                "urgency_flag": sentiment_result.urgency_flag,
                "confidence": round(sentiment_result.confidence, 2),
                "acoustic_signal": sentiment_result.acoustic_signal.value,
                "lexical_signal": sentiment_result.lexical_signal.value,
            },
            "interpretation": {
                "core_issue": interpretation.core_issue,
                "intent": interpretation.intent,
                "entities": [e.model_dump() for e in interpretation.entities],
                "department": interpretation.department,
                "restatement": interpretation.restatement,
                "has_audio": restatement_audio is not None,
                "confidence": round(interpretation.confidence, 2),
                "rag_context_used": interpretation.rag_context_used,
            },
            "confidence_eval": {
                "decision": confidence_eval.decision.value,
                "overall_score": round(confidence_eval.overall_score, 2),
                "asr_confidence": round(confidence_eval.asr_confidence, 2),
                "escalation_reason": confidence_eval.escalation_reason,
            },
            "skip_verification": skip_verification,
            "verification_restatement": scenario.get("restatement"),
        },
        "ai_vs_expected": {
            "issue_match": _fuzzy_match(interpretation.core_issue, scenario["expected_issue"]),
            "dept_match": interpretation.department.lower() in scenario["expected_dept"].lower()
                         or scenario["expected_dept"].lower() in interpretation.department.lower(),
        }
    }


@router.get("/random")
async def get_random_scenario(category: Optional[str] = None):
    """Get a random scenario (with optional category filter)."""
    if category:
        pool = SCENARIOS_BY_CATEGORY.get(category, [])
        if not pool:
            raise HTTPException(404, f"Category '{category}' not found")
        return random.choice(pool)
    return random.choice(DEMO_SCENARIOS)


@router.get("/pipeline-health")
async def pipeline_health():
    """Check that all pipeline services are initialised."""
    checks = {}
    try:
        get_dialect_service()
        checks["dialect"] = "ok"
    except Exception as e:
        checks["dialect"] = f"error: {e}"
    try:
        get_sentiment_service()
        checks["sentiment"] = "ok"
    except Exception as e:
        checks["sentiment"] = f"error: {e}"
    try:
        get_interpretation_service()
        checks["interpretation"] = "ok"
    except Exception as e:
        checks["interpretation"] = f"error: {e}"
    try:
        get_confidence_service()
        checks["confidence"] = "ok"
    except Exception as e:
        checks["confidence"] = f"error: {e}"

    all_ok = all(v == "ok" for v in checks.values())
    return {"healthy": all_ok, "services": checks}


def _fuzzy_match(a: str, b: str) -> bool:
    """Very rough keyword overlap check for demo accuracy display."""
    a_words = set(a.lower().split())
    b_words = set(b.lower().split())
    stopwords = {"the", "a", "an", "is", "are", "has", "not", "in", "of", "for", "and", "to"}
    a_kw = a_words - stopwords
    b_kw = b_words - stopwords
    if not a_kw or not b_kw:
        return False
    overlap = len(a_kw & b_kw) / min(len(a_kw), len(b_kw))
    return overlap > 0.3
