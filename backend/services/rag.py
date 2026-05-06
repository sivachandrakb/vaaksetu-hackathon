"""
VaakSetu — RAG Context Service
Retrieval-Augmented Generation from mock government service APIs.

Injects live context from Seva Sindhu, BBMP, BWSSB, Bhoomi, Pension, CRM
into the semantic interpretation prompt to reduce hallucination and improve
entity resolution.

Production: Apache Kafka streams + REST API connectors + JDBC
Prototype: Mock JSON files simulating real-time API responses
"""

import json
import os
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

MOCK_DATA_DIR = Path(__file__).parent.parent / "mock_data"


class RAGService:
    """
    Retrieves relevant government service context for a given transcript.
    
    Keyword-based retrieval maps transcript terms to relevant data sources.
    In production, this would use vector embeddings + Kafka-streamed documents.
    """

    def __init__(self):
        self._cache = {}
        self._load_all()

    def _load_all(self):
        """Load all mock data files at startup."""
        files = {
            "seva_sindhu": "seva_sindhu.json",
            "bbmp": "bbmp.json",
            "bwssb": "bwssb.json",
            "bhoomi": "bhoomi.json",
            "crm": "crm_logs.json",
        }
        for key, filename in files.items():
            path = MOCK_DATA_DIR / filename
            try:
                with open(path, encoding='utf-8') as f:
                    self._cache[key] = json.load(f)
                logger.info(f"Loaded mock data: {filename}")
            except FileNotFoundError:
                logger.warning(f"Mock data file not found: {path}")
                self._cache[key] = {}

    def get_context(self, transcript: str) -> tuple[str, list[str]]:
        """
        Build RAG context string for the LLM prompt.
        
        Args:
            transcript: Citizen's transcribed speech
            
        Returns:
            (context_string, list_of_sources_used)
        """
        text = transcript.lower()
        context_parts = []
        sources_used = []

        # ── Seva Sindhu Services ──────────────────────────────────────────────
        seva = self._cache.get("seva_sindhu", {})
        matched_services = []
        for svc in seva.get("services", []):
            for kw in svc.get("keywords", []):
                if kw.lower() in text:
                    matched_services.append(svc)
                    break
        
        if matched_services:
            svc_lines = []
            for s in matched_services[:2]:
                svc_lines.append(
                    f"  - {s['name']} (Dept: {s['department']}, "
                    f"Status: {s['status']}, "
                    f"Avg processing: {s['avg_processing_days']} days, "
                    f"Common issues: {', '.join(s['common_issues'])})"
                )
            context_parts.append("SEVA SINDHU SERVICES:\n" + "\n".join(svc_lines))
            sources_used.append("Seva Sindhu API")

        # Trending issues
        trending = seva.get("trending_issues", [])
        last_hour = [t for t in trending if t.get("last_hour")]
        if last_hour:
            issues = "; ".join(f"{t['issue']} ({t['count']} calls)" for t in last_hour)
            context_parts.append(f"TRENDING ISSUES (LAST HOUR): {issues}")

        # ── BWSSB Outages ─────────────────────────────────────────────────────
        bwssb_keywords = ["water", "bwssb", "neeru", "neer", "nali", "supply", "pipe", "drinking"]
        if any(kw in text for kw in bwssb_keywords):
            bwssb = self._cache.get("bwssb", {})
            active_outages = [o for o in bwssb.get("outages", []) if o["status"] == "active"]
            if active_outages:
                outage_lines = [
                    f"  - {o['area']}: {o['type']} (until {o['end']}, "
                    f"{o['affected_households']:,} households affected)"
                    for o in active_outages
                ]
                context_parts.append("BWSSB ACTIVE OUTAGES:\n" + "\n".join(outage_lines))
                sources_used.append("BWSSB Status API")

        # ── BBMP Grievances ───────────────────────────────────────────────────
        bbmp_keywords = ["road", "garbage", "bbmp", "light", "pothole", "drain", "dustbin", "sweeping"]
        if any(kw in text for kw in bbmp_keywords):
            bbmp = self._cache.get("bbmp", {})
            trending_complaints = bbmp.get("trending_complaints", [])
            if trending_complaints:
                comp_lines = [
                    f"  - {c['category']}: {c['count']} recent complaints ({c['ward']})"
                    for c in trending_complaints[:3]
                ]
                context_parts.append("BBMP TRENDING COMPLAINTS:\n" + "\n".join(comp_lines))
                sources_used.append("BBMP Grievance Feed")

        # ── Bhoomi / Land Records ─────────────────────────────────────────────
        bhoomi_keywords = ["land", "survey", "mutation", "khata", "bhoomi", "record", "property", "acres", "pahani"]
        if any(kw in text for kw in bhoomi_keywords):
            bhoomi = self._cache.get("bhoomi", {})
            issues = bhoomi.get("common_issues", [])
            if issues:
                context_parts.append(f"BHOOMI COMMON ISSUES: {', '.join(issues)}")
                sources_used.append("Bhoomi Land Records")

        # ── CRM Call Trends ───────────────────────────────────────────────────
        crm = self._cache.get("crm", {})
        top_issues = crm.get("top_issues_today", [])
        spike_issues = [i for i in top_issues if i.get("spike")]
        if spike_issues:
            spike_lines = [f"  - {i['issue']} ({i['count']} calls today, SPIKE)" for i in spike_issues[:2]]
            context_parts.append("CRM SPIKE ISSUES TODAY:\n" + "\n".join(spike_lines))
            sources_used.append("1092 CRM Logs")

        if not context_parts:
            return "No specific government service context found for this query.", []
        
        context = "\n\n".join(context_parts)
        return context, sources_used

    def get_all_feed(self) -> list[dict]:
        """Return all data feeds for the real-time dataset panel in the dashboard."""
        feeds = []
        
        seva = self._cache.get("seva_sindhu", {})
        if seva:
            feeds.append({
                "source": "Seva Sindhu",
                "type": "Government Services",
                "status": "live",
                "last_updated": seva.get("last_updated", ""),
                "preview": f"{len(seva.get('services', []))} services, "
                           f"{len(seva.get('trending_issues', []))} trending issues"
            })
        
        bwssb = self._cache.get("bwssb", {})
        if bwssb:
            active = [o for o in bwssb.get("outages", []) if o["status"] == "active"]
            feeds.append({
                "source": "BWSSB",
                "type": "Utility Status",
                "status": "live" if active else "normal",
                "last_updated": bwssb.get("last_updated", ""),
                "preview": f"{len(active)} active outage(s)"
            })
        
        bbmp = self._cache.get("bbmp", {})
        if bbmp:
            feeds.append({
                "source": "BBMP",
                "type": "Civic Complaints",
                "status": "live",
                "last_updated": bbmp.get("last_updated", ""),
                "preview": f"{len(bbmp.get('active_grievances', []))} active grievances"
            })
        
        crm = self._cache.get("crm", {})
        if crm:
            feeds.append({
                "source": "1092 CRM",
                "type": "Call Trends",
                "status": "streaming",
                "last_updated": crm.get("last_updated", ""),
                "preview": f"Top issue: {crm['top_issues_today'][0]['issue'] if crm.get('top_issues_today') else 'N/A'}"
            })
        
        return feeds


# Module-level singleton
_rag_service: Optional[RAGService] = None

def get_rag_service() -> RAGService:
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service
