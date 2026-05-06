# VaakSetu — AI for 1092 Helpline
> "Bridge of Words" | AI for Bharat Hackathon 2026 | Theme 12 | PAN IIT x Government of Karnataka

---

## Overview

VaakSetu is an AI-assisted voice understanding layer for the Karnataka 1092 helpline. It sits between the citizen caller and the agent — transcribing speech, interpreting intent, detecting sentiment, verifying understanding with the citizen, and delivering a confirmed interpretation to the agent dashboard in real time.

---

## Architecture

```
Citizen Voice → ASR (Whisper) → Dialect ID (IndicLID) → Semantic Interpretation (LLM)
     ↓                                                          ↓
Sentiment Analysis (Wav2Vec2 + MuRIL)              RAG from Mock Gov APIs
     ↓                                                          ↓
Verification Loop (TTS Restatement) ←→ Citizen Confirms/Corrects
     ↓
Confidence Evaluator → Agent Dashboard (React + FastAPI WebSocket)
     ↓
Feedback Store (PostgreSQL) → Continuous Learning Pipeline
```

---

## Project Structure

```
vaaksetu/
├── backend/
│   ├── main.py                  # FastAPI app entry point
│   ├── api/
│   │   ├── call.py              # Call session endpoints + WebSocket
│   │   ├── dashboard.py         # Agent dashboard endpoints
│   │   ├── feedback.py          # Feedback & correction endpoints
│   │   └── datasets.py          # Mock real-time dataset feed endpoints
│   ├── services/
│   │   ├── asr.py               # Whisper ASR service
│   │   ├── dialect.py           # Language & dialect identification
│   │   ├── interpretation.py    # LLM semantic interpretation engine
│   │   ├── sentiment.py         # Dual-channel sentiment classifier
│   │   ├── verification.py      # Verified understanding loop manager
│   │   ├── confidence.py        # Confidence evaluator & escalation
│   │   ├── tts.py               # Text-to-speech restatement
│   │   └── rag.py               # RAG context from mock govt APIs
│   ├── models/
│   │   └── schemas.py           # Pydantic data models
│   ├── db/
│   │   ├── database.py          # SQLAlchemy setup
│   │   └── crud.py              # DB operations
│   ├── mock_data/
│   │   ├── seva_sindhu.json     # Mock Seva Sindhu service data
│   │   ├── bbmp.json            # Mock BBMP grievance data
│   │   ├── bwssb.json           # Mock BWSSB outage data
│   │   ├── bhoomi.json          # Mock land records
│   │   ├── ration_card.json     # Mock ration card records
│   │   ├── pension.json         # Mock pension records
│   │   └── crm_logs.json        # Mock 1092 CRM call trends
│   └── requirements.txt
├── frontend/
│   ├── package.json
│   ├── public/
│   └── src/
│       ├── App.jsx
│       ├── components/
│       │   ├── CallInterface.jsx       # Citizen-side voice input widget
│       │   ├── AgentDashboard.jsx      # Agent real-time dashboard
│       │   ├── InterpretationCard.jsx  # Structured interpretation display
│       │   ├── SentimentBadge.jsx      # Sentiment indicator
│       │   ├── VerificationPanel.jsx   # Verification loop UI
│       │   ├── TranscriptPanel.jsx     # Live transcript
│       │   ├── DatasetPanel.jsx        # Real-time dataset feed display
│       │   ├── CallTrends.jsx          # CRM trend charts
│       │   └── FeedbackModal.jsx       # Agent correction UI
│       ├── hooks/
│       │   ├── useWebSocket.js         # WebSocket connection hook
│       │   └── useAudioRecorder.js     # Browser audio capture
│       └── utils/
│           └── api.js                  # API client
├── docker/
│   ├── Dockerfile.backend
│   ├── Dockerfile.frontend
│   └── docker-compose.yml
└── scripts/
    ├── setup.sh                 # Dev environment setup
    └── seed_db.py               # Seed database with mock data
```

---

## Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- Docker + Docker Compose (for full stack)
- OpenAI API key (or local Ollama for Gemma 2)

### Option 1: Docker (recommended)
```bash
cp .env.example .env          # Fill in your API keys
docker-compose -f docker/docker-compose.yml up --build
```

Open: http://localhost:3000 (Frontend) | http://localhost:8000/docs (API)

### Option 2: Local Development
```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

---

## Environment Variables

```
OPENAI_API_KEY=sk-...          # For GPT-4o-mini semantic interpretation
OPENAI_MODEL=gpt-4o-mini       # Or use local Ollama: ollama/gemma2:9b
DATABASE_URL=sqlite:///./vaaksetu.db   # PostgreSQL in production
WHISPER_MODEL=base             # base/small/medium/large-v3
TTS_ENGINE=gtts                # gtts (free) or coqui
```

---

## Demo Flow

1. Open the **Call Interface** tab — click "Start Call"
2. Speak in Kannada, Hindi, or English (browser mic)
3. Watch live transcription appear in real time
4. The AI interprets and restates — citizen confirms
5. Switch to **Agent Dashboard** tab to see the verified interpretation card
6. Use the correction field to fix any misinterpretation
7. Watch the **Dataset Panel** for live mock govt API enrichment

---

## Key Design Principles

- **Verified understanding over speed** — a wrong fast answer is worse than a slower correct one
- **Human takeover is first-class** — escalation is celebrated, never penalised
- **No citizen audio leaves the network** — all processing on-prem
- **Government API data enriches, not decides** — context injection via RAG

---

*VaakSetu Team | AI for Bharat Hackathon 2026*
