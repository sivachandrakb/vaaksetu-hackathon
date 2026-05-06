"""
VaakSetu — FastAPI Main Application
AI-Assisted Voice Understanding for the Karnataka 1092 Helpline
"""

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from db.database import init_db
from api.call import router as call_router
from api.dashboard import router as dashboard_router
from api.feedback import router as feedback_router
from api.datasets import router as datasets_router
from api.demo import router as demo_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("VaakSetu starting up...")
    await init_db()
    logger.info("Database initialised.")
    yield
    logger.info("VaakSetu shutting down.")


app = FastAPI(
    title="VaakSetu API",
    description="AI-Assisted Voice Understanding for the Karnataka 1092 Helpline",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(call_router,      prefix="/api/call",      tags=["Call Sessions"])
app.include_router(dashboard_router, prefix="/api/dashboard", tags=["Agent Dashboard"])
app.include_router(feedback_router,  prefix="/api/feedback",  tags=["Feedback"])
app.include_router(datasets_router,  prefix="/api/datasets",  tags=["Real-Time Datasets"])
app.include_router(demo_router,      prefix="/api/demo",      tags=["Demo / Hackathon"])


@app.get("/", tags=["Health"])
async def root():
    return {
        "service": "VaakSetu",
        "tagline": "Bridge of Words",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok"}
