"""
VaakSetu — Semantic Interpretation Engine
LLM-based structured interpretation of citizen speech.

Production: Gemma 2 9B (quantised, on-prem) or GPT-4o-mini
Prototype: GPT-4o-mini via OpenAI API

Produces: core_issue, intent, entities, department, restatement
"""

import json
import os
import logging
from typing import Optional

from models.schemas import (
    InterpretationResult, Entity, Language, Dialect, SentimentResult
)
from services.rag import get_rag_service

logger = logging.getLogger(__name__)

OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

SYSTEM_PROMPT = """You are VaakSetu, an AI assistant helping interpret citizen calls to the Karnataka 1092 government helpline.

Your role: Given a citizen's speech transcript (possibly in Kannada, Hindi, or English), extract:
1. The core issue they are reporting
2. Their intent (complaint / inquiry / request / emergency)
3. Key entities (departments, locations, service names, ID numbers)
4. Which government department should handle this
5. A natural restatement in the citizen's own language for verification

Karnataka government context:
- SEVA SINDHU: one-stop portal for government services (certificates, applications)
- BBMP: Bruhat Bengaluru Mahanagara Palike (civic body for Bengaluru)
- BWSSB: water supply complaints
- BHOOMI: land records portal
- SANDHYA SURAKSHA: old-age pension scheme
- Ration card: food subsidy identity card

Common Kannada helpline expressions:
- "illa" = not / no
- "agilla/aagilla" = not happening / not done
- "beku" = need / want
- "saayi" = dying / severe distress
- "rashan kaardi" = ration card
- "pinchani" = pension
- "namma ooru" = our village/town
- "houdu/houdu sari" = yes/correct
- "nodi" = please look / check

CRITICAL RULES:
- Be concise — citizens wait for this
- The restatement must be a single, simple sentence in the SAME LANGUAGE the citizen used
- For Kannada, use simple colloquial Kannada (not formal), Roman script for non-Kannada agents
- NEVER invent facts — only use what is in the transcript and the RAG context provided
- If unsure about an entity, mark confidence < 0.7

Respond ONLY with valid JSON — no markdown, no preamble."""

INTERPRETATION_SCHEMA = """{
  "core_issue": "string — one clear sentence describing the problem",
  "intent": "complaint | inquiry | request | emergency",
  "entities": [
    {"type": "department|location|service|id_number|person", "value": "string", "confidence": 0.0-1.0}
  ],
  "department": "string — which govt dept should handle this",
  "restatement": "string — one sentence in citizen's language for verification",
  "confidence": 0.0-1.0
}"""


class InterpretationService:
    """
    LLM-powered semantic interpretation of citizen speech.
    
    Uses RAG context from government APIs to ground interpretation
    in real service status and prevent hallucination.
    """

    def __init__(self):
        self._client = None
        self._has_api = bool(os.getenv("OPENAI_API_KEY"))
        self._rag = get_rag_service()
        logger.info(f"Interpretation Service — LLM: {'OpenAI ' + OPENAI_MODEL if self._has_api else 'mock'}")

    def _get_client(self):
        if self._client is None and self._has_api:
            from openai import OpenAI
            self._client = OpenAI()
        return self._client

    async def interpret(
        self,
        transcript: str,
        language: Language,
        dialect: Dialect,
        sentiment: SentimentResult,
    ) -> InterpretationResult:
        """
        Generate structured interpretation from transcript.
        
        Args:
            transcript: Citizen's transcribed speech
            language: Detected language
            dialect: Detected Kannada dialect (if applicable)
            sentiment: Sentiment classification result
            
        Returns:
            InterpretationResult with all fields populated
        """
        # Get RAG context from government APIs
        rag_context, sources_used = self._rag.get_context(transcript)

        if self._has_api:
            return await self._interpret_via_llm(transcript, language, dialect, sentiment, rag_context, sources_used)
        else:
            return self._interpret_mock(transcript, language, sources_used)

    async def _interpret_via_llm(
        self,
        transcript: str,
        language: Language,
        dialect: Dialect,
        sentiment: SentimentResult,
        rag_context: str,
        sources_used: list[str]
    ) -> InterpretationResult:
        """Call OpenAI API for interpretation."""
        from openai import AsyncOpenAI
        client = AsyncOpenAI()

        dialect_note = f"Dialect: {dialect.value}" if dialect else ""
        sentiment_note = f"Citizen sentiment: {sentiment.sentiment.value} (urgency: {sentiment.urgency_flag})"
        
        user_prompt = f"""TRANSCRIPT (Language: {language.value}, {dialect_note}):
{transcript}

{sentiment_note}

GOVERNMENT SERVICE CONTEXT (from live APIs):
{rag_context}

Respond with JSON matching this schema:
{INTERPRETATION_SCHEMA}"""

        try:
            response = await client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.2,
                max_tokens=600,
                response_format={"type": "json_object"}
            )
            
            raw = response.choices[0].message.content
            data = json.loads(raw)
            
            entities = [
                Entity(
                    type=e.get("type", "unknown"),
                    value=e.get("value", ""),
                    confidence=float(e.get("confidence", 0.7))
                )
                for e in data.get("entities", [])
            ]
            
            return InterpretationResult(
                core_issue=data.get("core_issue", transcript[:80]),
                intent=data.get("intent", "inquiry"),
                entities=entities,
                department=data.get("department", "General Helpline"),
                restatement=data.get("restatement", self._build_fallback_restatement(transcript, language)),
                confidence=float(data.get("confidence", 0.75)),
                rag_context_used=sources_used
            )
            
        except Exception as e:
            logger.error(f"LLM interpretation error: {e}")
            return self._interpret_mock(transcript, language, sources_used)

    def _interpret_mock(
        self,
        transcript: str,
        language: Language,
        sources_used: list[str]
    ) -> InterpretationResult:
        """
        Rule-based mock interpretation for demo without API key.
        Covers the most common 1092 helpline scenarios.
        """
        text = transcript.lower()
        
        # Issue detection rules
        issue_map = [
            (["ration", "rashan", "ration card", "rashan kaardi", "aadhaar link"],
             "Citizen's ration card is not linked with Aadhaar",
             "Food & Civil Supplies",
             "ration_link"),
            (["pension", "pinchani", "sandhya", "amount", "haana", "paisa"],
             "Citizen has not received pension payment",
             "Social Welfare Department",
             "pension"),
            (["water", "bwssb", "neeru", "supply", "nali", "bandu illa"],
             "Citizen is reporting a water supply issue",
             "BWSSB",
             "water"),
            (["road", "pothole", "bbmp", "garbage", "dustbin", "light"],
             "Citizen is filing a civic complaint (BBMP)",
             "BBMP",
             "civic"),
            (["land", "mutation", "bhoomi", "survey", "khata", "record"],
             "Citizen needs help with land record or mutation",
             "Revenue / Bhoomi",
             "land"),
            (["certificate", "income", "caste", "birth", "domicile"],
             "Citizen is requesting a government certificate",
             "Revenue Department (Seva Sindhu)",
             "certificate"),
        ]
        
        core_issue = "Citizen is seeking government assistance"
        department = "General Helpline"
        intent = "inquiry"
        issue_type = "general"
        
        for keywords, issue, dept, itype in issue_map:
            if any(kw in text for kw in keywords):
                core_issue = issue
                department = dept
                issue_type = itype
                intent = "complaint" if any(w in text for w in ["complaint", "problem", "illa", "aagilla", "nahi", "not"]) else "inquiry"
                break
        
        entities = self._extract_entities_mock(text)
        restatement = self._build_fallback_restatement(transcript, language)
        
        return InterpretationResult(
            core_issue=core_issue,
            intent=intent,
            entities=entities,
            department=department,
            restatement=restatement,
            confidence=0.72,
            rag_context_used=sources_used
        )

    def _extract_entities_mock(self, text: str) -> list[Entity]:
        """Extract entities with simple keyword matching."""
        entities = []
        
        # Departments
        dept_map = {
            "bwssb": "BWSSB", "ration": "Food & Civil Supplies", "pension": "Social Welfare",
            "bbmp": "BBMP", "bhoomi": "Revenue / Bhoomi", "seva sindhu": "Seva Sindhu"
        }
        for kw, dept in dept_map.items():
            if kw in text:
                entities.append(Entity(type="department", value=dept, confidence=0.88))
                break
        
        # Locations
        locations = ["bengaluru", "mysuru", "dharwad", "mangaluru", "yelahanka",
                     "koramangala", "rajajinagar", "hubli", "belgaum", "davangere"]
        for loc in locations:
            if loc in text:
                entities.append(Entity(type="location", value=loc.title(), confidence=0.85))
                break
        
        # Services
        services = {
            "ration card": "Ration Card", "pension": "Sandhya Suraksha Pension",
            "water": "BWSSB Water Supply", "mutation": "Bhoomi Mutation"
        }
        for kw, svc in services.items():
            if kw in text:
                entities.append(Entity(type="service", value=svc, confidence=0.80))
                break
        
        return entities

    def _build_fallback_restatement(self, transcript: str, language: Language) -> str:
        """Build a simple restatement when LLM is not available."""
        text = transcript.lower()
        
        # Kannada restatements
        if language == Language.KANNADA:
            if any(w in text for w in ["ration", "rashan"]):
                return "Neevu heLidantu, nimage ration card update aagilla antha — ide sari tane?"
            if any(w in text for w in ["pension", "pinchani"]):
                return "Neevu heLidantu, nimage pension haNA bandilla antha — ide sari tane?"
            if any(w in text for w in ["water", "neeru"]):
                return "Neevu heLidantu, nimage neeru supply aagutilla antha — ide sari tane?"
            return "Neevu heLidantu, nimage sarkaari sEveyalli tondare aagide antha — ide sari tane?"
        
        # Hindi restatements
        if language == Language.HINDI:
            if any(w in text for w in ["ration", "rashan"]):
                return "Aapne kaha ki aapka ration card update nahi hua — kya yeh sahi hai?"
            if any(w in text for w in ["pension"]):
                return "Aapne kaha ki aapki pension nahi aayi — kya yeh sahi hai?"
            return "Aapne kaha ki aapko sarkari seva mein pareshani ho rahi hai — kya yeh sahi hai?"
        
        # English
        truncated = transcript[:60] + "..." if len(transcript) > 60 else transcript
        return f"You said: \"{truncated}\" — is that correct?"


# Module-level singleton
_interpretation_service: Optional[InterpretationService] = None

def get_interpretation_service() -> InterpretationService:
    global _interpretation_service
    if _interpretation_service is None:
        _interpretation_service = InterpretationService()
    return _interpretation_service
