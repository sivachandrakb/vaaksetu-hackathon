# VaakSetu — 5-Minute Video Walkthrough Script
## AI for Bharat Hackathon 2026 | Theme 12

---

### Suggested Screen Recording Order

**Tools:** OBS Studio or Loom | Resolution: 1920×1080 | Duration: 4:45 – 5:00 min

---

## [0:00 – 0:30] Title Slide + Problem Statement

**On screen:** Title card with VaakSetu logo

**Narration:**
> "Welcome. This is VaakSetu — Bridge of Words.
>
> Karnataka's 1092 helpline receives thousands of calls daily from citizens speaking
> Kannada, Hindi, and English across dozens of dialects. The problem isn't speed.
> The problem is comprehension. A wrong response built on misunderstanding
> is worse than no response at all.
>
> VaakSetu is an AI-assisted voice understanding layer that ensures every citizen
> is correctly understood before any action is taken."

---

## [0:30 – 1:00] Architecture Overview

**On screen:** Architecture diagram from the proposal document

**Narration:**
> "Here is the complete VaakSetu pipeline.
>
> A citizen's voice travels through ASR transcription using Whisper,
> dialect identification via IndicLID, dual-channel sentiment analysis
> using Wav2Vec2 acoustics and MuRIL lexical processing,
> semantic interpretation via an LLM enriched with live government API context,
> and a verified understanding loop that speaks back what the AI understood —
> and waits for citizen confirmation before routing to the agent."

---

## [1:00 – 1:45] Demo Mode — Pick a Scenario

**On screen:** Browser → http://localhost:3000/demo

**Actions:**
1. Click "🏆 Demo Mode" in the nav
2. Show the category grid
3. Click "🆘 Emergency"
4. Click "Run emergency scenario"
5. Watch pipeline animate: ASR → Dialect → Sentiment → LLM+RAG → TTS

**Narration:**
> "In the Demo Mode, we can run the full AI pipeline on realistic call transcripts
> without needing a live phone call.
>
> Let's pick an emergency scenario — an 80-year-old citizen who hasn't received
> their pension for months and cannot afford medicine.
>
> Watch the pipeline run: ASR transcription, dialect identification,
> sentiment analysis, LLM interpretation enriched with Seva Sindhu and
> pension portal data, and TTS restatement generation."

**Pause on result — point out:**
- Transcript (Kannada)
- Sentiment badge: 😰 DISTRESS + URGENCY FLAG
- Core issue extracted
- Department routed correctly
- Verification SKIPPED (high distress — immediate escalation)
- Confidence Evaluator: ESCALATE

---

## [1:45 – 2:30] Live Call Interface

**On screen:** Browser → http://localhost:3000

**Actions:**
1. Click "📞 Call Interface"
2. Click "Start Call" — show session ID
3. Click "🎭 Demo (mock audio)"
4. Watch transcript appear live
5. Watch sentiment badge update
6. Watch interpretation card appear
7. Show verification restatement spoken to citizen

**Narration:**
> "Now let's see the live call interface — what a citizen would experience.
>
> When a call starts, the pipeline runs in real time.
> Here's the transcript appearing as the citizen speaks.
> Sentiment is classified immediately — confusion detected.
>
> The AI generates a structured interpretation, enriched with live context
> from Seva Sindhu. And then — the key innovation — it speaks back
> a restatement in the citizen's own language:
>
> 'Neevu heLidantu, nimage ration card Aadhaar link aagilla antha — ide sari tane?'
>
> 'You said your ration card is not linked with Aadhaar — is that correct?'
>
> The citizen says yes or no. That response drives routing."

---

## [2:30 – 3:30] Agent Dashboard

**On screen:** Browser → http://localhost:3000/dashboard (open in second tab)

**Actions:**
1. Open dashboard tab
2. Paste session ID from call interface into monitor box
3. Click Monitor
4. Switch back to call interface tab, run another demo scenario
5. Switch to dashboard — show live update arriving via WebSocket
6. Point to: interpretation card, sentiment badge, confidence score
7. Click "Correct Interpretation" → fill in correction → Save
8. Show "Queued for training" confirmation

**Narration:**
> "This is the agent dashboard — what the helpline operator sees in real time.
>
> The interpretation card shows exactly what the citizen said,
> structured and verified. The sentiment badge gives the agent
> immediate emotional context without the agent needing to interpret tone themselves.
>
> The agent can take over at any point with one click.
> And critically — if the AI got something wrong, the agent can correct it here.
> That correction is immediately stored as a labelled training example
> and queued for the retraining pipeline."

---

## [3:30 – 4:00] Real-Time Dataset Panel

**On screen:** Dashboard — right panel

**Actions:**
1. Scroll to Dataset Panel on dashboard right side
2. Show Seva Sindhu, BWSSB, BBMP, CRM feeds
3. Open browser → http://localhost:8000/api/datasets/crm_logs
4. Show raw JSON — spike issues, hourly trends

**Narration:**
> "VaakSetu is enriched by real-time data from Karnataka government APIs.
>
> Seva Sindhu tells the AI what services are currently active.
> BWSSB outage data means if a citizen calls about Yelahanka water,
> the AI already knows there's an active outage and routes appropriately.
> The 1092 CRM logs surface trending issues — if 300 calls mention
> the same BWSSB outage this hour, the agent sees that context immediately."

---

## [4:00 – 4:30] API Documentation + Tests

**On screen:** http://localhost:8000/docs

**Actions:**
1. Show Swagger UI
2. Expand /api/demo/run
3. Show /api/demo/scenarios
4. Run a quick test in terminal: `pytest tests/ -v --tb=short`

**Narration:**
> "Every pipeline stage is accessible via a clean REST API with full documentation.
>
> The test suite covers dialect detection, sentiment classification,
> verification response parsing, confidence evaluation, and RAG context retrieval —
> 30 tests across all services.
>
> The codebase is fully Dockerised and deployable on Karnataka State Data Centre
> infrastructure with no external API calls on citizen audio."

---

## [4:30 – 5:00] Closing

**On screen:** VaakSetu architecture diagram + title card

**Narration:**
> "For 6 crore Kannada speakers across Karnataka —
> from a farmer in Dharwad filing a land record complaint
> to a senior citizen in Mysuru confused about a pension payment —
>
> VaakSetu ensures that when they call 1092, they are heard.
> Not just heard — understood. Correctly. Verifiably. Respectfully.
>
> That is the innovation. That is the impact.
>
> VaakSetu — Bridge of Words."

---

## Recording Tips

- Use a dark background browser theme for contrast
- Chrome DevTools → Device toolbar off (full desktop view)
- Font size: increase browser font to 110% for readability
- Demo Mode is the fastest path to showing the full pipeline
- Run `scripts/seed_db.py` before recording to pre-populate dashboard stats
- Keep the backend terminal visible in a small side panel to show logs
