# VaakSetu — Hackathon Submission
## AI for Bharat 2026 | Theme 12 | PAN IIT x Government of Karnataka

---

## ✅ Submission Checklist

### 1. Working Prototype / Demo

| Requirement | Status | Notes |
|---|---|---|
| Voice input (browser mic) | ✅ | `CallInterface.jsx` — MediaRecorder API |
| Demo mode (no mic needed) | ✅ | `/demo` route — 16 realistic scenarios |
| Live ASR transcription | ✅ | Whisper API or local model |
| Dialect identification | ✅ | IndicLID heuristics (6 Kannada dialects) |
| Sentiment classification | ✅ | Dual-channel: acoustic + lexical |
| LLM interpretation + RAG | ✅ | GPT-4o-mini / Gemma 2 + govt API context |
| TTS restatement | ✅ | gTTS (kn/hi/en) |
| Verification loop | ✅ | houdu/illa/partial/uncertain classification |
| Confidence evaluator | ✅ | 5 escalation rules |
| Agent dashboard | ✅ | React + FastAPI WebSocket |
| Human takeover button | ✅ | One-click escalation |
| Agent correction → training | ✅ | Feedback store + training signal |
| Real-time dataset panel | ✅ | Mock Seva Sindhu, BBMP, BWSSB, CRM |
| Docker deployment | ✅ | docker-compose.yml |

### 2. 5-Minute Video Walkthrough

- Script: `docs/VIDEO_WALKTHROUGH_SCRIPT.md`
- Covers: Demo Mode → Call Interface → Agent Dashboard → Dataset Panel → API Docs → Tests
- No live mic needed — Demo Mode shows full pipeline

### 3. Code Repository

- Structure: Clean monorepo with backend/ + frontend/ + docker/ + tests/
- Tests: 30 pytest tests covering all services
- CI: GitHub Actions workflow in `.github/workflows/ci.yml`
- License: MIT

---

## How to Run for Evaluation

```bash
# Option A: Docker (recommended for judges)
cp .env.example .env
# Add OPENAI_API_KEY to .env (optional — demo mode works without it)
docker-compose -f docker/docker-compose.yml up --build

# Option B: Local
cd backend && pip install -r requirements.txt
uvicorn main:app --reload --port 8000 &
cd ../frontend && npm install && npm run dev

# Seed demo data
python scripts/seed_db.py

# Run tests
cd backend && pytest ../tests/ -v
```

Open: **http://localhost:3000/demo** → click any category → Run Demo

---

## Key Differentiators

1. **Verified Understanding Loop** — AI restates, citizen confirms. First-class innovation.
2. **Dual-channel sentiment** — Acoustic (Wav2Vec2) + lexical (MuRIL). Detects distress even when words are calm.
3. **6 Kannada dialects** — Dharwad, Mysuru, Mangaluru, Havyaka, Kodava, Bengaluru.
4. **RAG from live govt APIs** — Seva Sindhu, BBMP, BWSSB, Bhoomi, 1092 CRM.
5. **Human-first design** — Escalation is celebrated, not hidden. Agent always in control.
6. **Continuous learning** — Every correction is a training signal. Agent feedback → model improvement.
7. **On-prem deployable** — No citizen audio leaves the Karnataka State Data Centre.

---

## Team
VaakSetu Team | AI for Bharat Hackathon 2026
