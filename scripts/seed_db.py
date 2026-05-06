"""
VaakSetu — Seed Database with mock call sessions for demo.
Run: python scripts/seed_db.py
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from db.database import init_db, AsyncSessionLocal
from db.database import CallSessionDB, FeedbackDB
from datetime import datetime, timedelta
import uuid
import random

MOCK_SESSIONS = [
    dict(core_issue="Ration card not linked with Aadhaar", dept="Food & Civil Supplies",
         lang="kn", sent="confusion", escalated=False, confidence=0.83),
    dict(core_issue="Pension payment not received this month", dept="Social Welfare",
         lang="kn", sent="distress", escalated=True, confidence=0.72),
    dict(core_issue="BWSSB water supply interrupted in Yelahanka", dept="BWSSB",
         lang="en", sent="anger", escalated=False, confidence=0.91),
    dict(core_issue="Land mutation pending at Bhoomi portal", dept="Revenue / Bhoomi",
         lang="kn", sent="confusion", escalated=False, confidence=0.78),
    dict(core_issue="Caste certificate status inquiry", dept="Revenue",
         lang="hi", sent="calm", escalated=False, confidence=0.88),
]

async def seed():
    await init_db()
    async with AsyncSessionLocal() as db:
        for i, m in enumerate(MOCK_SESSIONS):
            s = CallSessionDB(
                session_id=str(uuid.uuid4()),
                status="completed" if not m["escalated"] else "escalated",
                started_at=datetime.utcnow() - timedelta(hours=random.randint(1, 8)),
                language=m["lang"],
                dialect="standard",
                transcript="[Mock transcript]",
                core_issue=m["core_issue"],
                intent="complaint",
                department=m["dept"],
                restatement="[Mock restatement]",
                sentiment=m["sent"],
                urgency_flag=m["sent"] in ("distress", "urgency"),
                verification_outcome="confirmed" if not m["escalated"] else "uncertain",
                overall_confidence=m["confidence"],
                escalated=m["escalated"],
                agent_id="agent_001",
            )
            db.add(s)
        await db.commit()
    print(f"✅ Seeded {len(MOCK_SESSIONS)} mock call sessions.")

if __name__ == "__main__":
    asyncio.run(seed())
