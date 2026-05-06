"""
VaakSetu — Agent Dashboard API
Endpoints for the agent dashboard: stats, trends, active calls.
"""

import logging
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_db
from db import crud
from services.rag import get_rag_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/stats")
async def get_dashboard_stats(db: AsyncSession = Depends(get_db)):
    """Aggregate stats: active calls, escalation rate, confidence, top issues."""
    stats = await crud.get_dashboard_stats(db)
    
    rag = get_rag_service()
    crm = rag._cache.get("crm", {})
    
    return {
        **stats,
        "top_issues": crm.get("top_issues_today", [])[:5],
        "hourly_trends": crm.get("hourly_trends", []),
        "sentiment_summary": crm.get("sentiment_summary", {}),
        "escalation_rate": crm.get("escalation_rate", 0),
        "avg_handle_time_seconds": crm.get("avg_handle_time_seconds", 0),
    }


@router.get("/dataset-feed")
async def get_dataset_feed():
    """Return all real-time dataset feeds for the dashboard panel."""
    rag = get_rag_service()
    return {"feeds": rag.get_all_feed()}
