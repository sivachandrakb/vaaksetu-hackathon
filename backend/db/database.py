"""
VaakSetu — Database Setup
SQLite for prototype / PostgreSQL for production.
"""

import os
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy import Column, String, Float, Boolean, DateTime, Text, Integer
from datetime import datetime

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./vaaksetu.db")

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class CallSessionDB(Base):
    __tablename__ = "call_sessions"
    
    session_id = Column(String, primary_key=True, index=True)
    status = Column(String, default="active")
    started_at = Column(DateTime, default=datetime.utcnow)
    language = Column(String, nullable=True)
    dialect = Column(String, nullable=True)
    transcript = Column(Text, nullable=True)
    core_issue = Column(Text, nullable=True)
    intent = Column(String, nullable=True)
    department = Column(String, nullable=True)
    restatement = Column(Text, nullable=True)
    sentiment = Column(String, nullable=True)
    urgency_flag = Column(Boolean, default=False)
    verification_outcome = Column(String, nullable=True)
    overall_confidence = Column(Float, nullable=True)
    escalated = Column(Boolean, default=False)
    escalation_reason = Column(Text, nullable=True)
    agent_correction = Column(Text, nullable=True)
    agent_id = Column(String, nullable=True)


class FeedbackDB(Base):
    __tablename__ = "feedback_records"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, index=True)
    transcript = Column(Text)
    ai_interpretation = Column(Text)
    verified_interpretation = Column(Text)
    sentiment = Column(String)
    language = Column(String)
    dialect = Column(String)
    outcome = Column(String)
    agent_correction = Column(Text, nullable=True)
    quality_signal = Column(String)
    recorded_at = Column(DateTime, default=datetime.utcnow)


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
