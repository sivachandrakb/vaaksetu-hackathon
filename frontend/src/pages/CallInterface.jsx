import React, { useState, useEffect, useRef } from 'react'
import { Mic, MicOff, PhoneOff, AlertTriangle } from 'lucide-react'
import { useAudioRecorder } from '../hooks/useAudioRecorder'
import { useWebSocket } from '../hooks/useWebSocket'
import { startCall, processAudio, submitVerification, playBase64Audio } from '../utils/api'
import { TranscriptPanel, VerificationPanel } from '../components/Panels'
import SentimentBadge from '../components/SentimentBadge'
import InterpretationCard from '../components/InterpretationCard'

const PHASE = {
  IDLE: 'idle',
  RECORDING: 'recording',
  PROCESSING: 'processing',
  VERIFICATION: 'verification',
  CONFIRMED: 'confirmed',
  ESCALATED: 'escalated',
}

export default function CallInterface() {
  const [sessionId, setSessionId] = useState(null)
  const [phase, setPhase] = useState(PHASE.IDLE)
  const [transcript, setTranscript] = useState('')
  const [language, setLanguage] = useState(null)
  const [sentiment, setSentiment] = useState(null)
  const [interpretation, setInterpretation] = useState(null)
  const [dialectLabel, setDialectLabel] = useState(null)
  const [verificationOutcome, setVerificationOutcome] = useState(null)
  const [escalationReason, setEscalationReason] = useState(null)
  const [error, setError] = useState(null)
  const [logs, setLogs] = useState([])

  const mainRecorder = useAudioRecorder()
  const verifyRecorder = useAudioRecorder()

  const addLog = (msg) => setLogs(prev => [`[${new Date().toLocaleTimeString()}] ${msg}`, ...prev.slice(0, 19)])

  // WebSocket messages from backend pipeline
  const handleWsMessage = (msg) => {
    switch (msg.type) {
      case 'transcript_update':
        if (msg.payload.transcript) setTranscript(msg.payload.transcript)
        if (msg.payload.language) setLanguage(msg.payload.language)
        addLog(`📝 Transcript received (${msg.payload.language})`)
        break
      case 'sentiment_update':
        setSentiment(msg.payload)
        addLog(`💬 Sentiment: ${msg.payload.label}`)
        break
      case 'interpretation_ready':
        setInterpretation(msg.payload)
        setDialectLabel(msg.payload.dialect)
        addLog(`🤖 Interpretation ready — ${msg.payload.core_issue?.slice(0, 50)}...`)
        if (msg.payload.skip_verification) {
          setPhase(PHASE.ESCALATED)
          addLog('⚠️ High distress — skipping verification, escalating')
        } else {
          setPhase(PHASE.VERIFICATION)
          // Auto-play restatement audio if available
          if (msg.payload.restatement_audio_b64) {
            playBase64Audio(msg.payload.restatement_audio_b64).catch(() => {})
            addLog('🔊 Playing restatement to citizen...')
          }
        }
        break
      case 'verification_result':
        setVerificationOutcome(msg.payload.outcome)
        addLog(`✅ Verification: ${msg.payload.outcome}`)
        break
      case 'confidence_decision':
        addLog(`⚖️ Confidence decision: ${msg.payload.decision} (${Math.round(msg.payload.overall_score * 100)}%)`)
        if (msg.payload.decision === 'proceed') setPhase(PHASE.CONFIRMED)
        break
      case 'escalation':
        setEscalationReason(msg.payload.reason)
        setPhase(PHASE.ESCALATED)
        addLog(`🆘 Escalated: ${msg.payload.reason}`)
        break
    }
  }

  const { connected } = useWebSocket(sessionId, handleWsMessage)

  // ── Start Call ─────────────────────────────────────────────────────────────
  const handleStartCall = async () => {
    try {
      setError(null)
      setLogs([])
      const res = await startCall()
      setSessionId(res.session_id)
      setPhase(PHASE.RECORDING)
      setTranscript('')
      setSentiment(null)
      setInterpretation(null)
      setVerificationOutcome(null)
      setEscalationReason(null)
      addLog(`📞 Call started — session ${res.session_id.slice(0, 8)}...`)
    } catch (e) {
      setError('Failed to start call: ' + e.message)
    }
  }

  // ── Record & Process ───────────────────────────────────────────────────────
  const handleStartRecording = () => {
    mainRecorder.startRecording()
    addLog('🎙️ Recording citizen speech...')
  }

  const handleStopAndProcess = async () => {
    mainRecorder.stopRecording()
    addLog('⏹️ Recording stopped — processing...')
  }

  // When main audio is ready, send to pipeline
  useEffect(() => {
    if (mainRecorder.audioB64 && phase === PHASE.RECORDING) {
      setPhase(PHASE.PROCESSING)
      addLog('🔄 Sending to AI pipeline...')
      processAudio(sessionId, mainRecorder.audioB64)
        .catch(e => {
          setError('Pipeline error: ' + e.message)
          setPhase(PHASE.RECORDING)
        })
    }
  }, [mainRecorder.audioB64])

  // ── Submit Verification Response ───────────────────────────────────────────
  const handleSubmitVerification = async () => {
    if (!verifyRecorder.audioB64) return
    addLog('🔄 Submitting verification response...')
    try {
      await submitVerification(sessionId, verifyRecorder.audioB64)
    } catch (e) {
      setError('Verification error: ' + e.message)
    }
  }

  // ── Demo Mode (no mic) ─────────────────────────────────────────────────────
  const handleDemoProcess = async () => {
    if (!sessionId) return
    setPhase(PHASE.PROCESSING)
    addLog('🎭 Demo mode — using mock audio...')
    // Send a minimal base64 WAV (1 second of silence) — backend will use mock ASR
    const silenceB64 = 'UklGRiQAAABXQVZFZm10IBAAAAABAAEARKwAAIhYAQACABAAZGF0YQAAAAA='
    processAudio(sessionId, silenceB64)
      .catch(e => {
        setError('Pipeline error: ' + e.message)
        setPhase(PHASE.RECORDING)
      })
  }

  // ── Upload Audio File ──────────────────────────────────────────────────────
  const handleFileUpload = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    
    addLog(`📁 Uploaded audio file: ${file.name}`);
    setPhase(PHASE.PROCESSING);
    
    const reader = new FileReader();
    reader.onloadend = () => {
      // reader.result is a data URL
      const base64Data = reader.result.split(',')[1];
      if (base64Data) {
        processAudio(sessionId, base64Data)
          .catch(err => {
            setError('Pipeline error: ' + err.message);
            setPhase(PHASE.RECORDING);
          });
      } else {
        setError('Failed to read audio file properly.');
        setPhase(PHASE.RECORDING);
      }
    };
    reader.readAsDataURL(file);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-brand-900 to-indigo-900 flex flex-col items-center justify-start py-8 px-4">
      {/* Header */}
      <div className="text-center mb-8">
        <h1 className="text-4xl font-bold text-white mb-1">🎙️ VaakSetu</h1>
        <p className="text-indigo-200 text-sm">"Bridge of Words" — 1092 Helpline AI</p>
        <p className="text-indigo-300 text-xs mt-1">AI for Bharat Hackathon 2026 | Theme 12</p>
      </div>

      <div className="w-full max-w-2xl space-y-4">
        {/* Connection status */}
        {sessionId && (
          <div className="flex items-center justify-between text-xs">
            <span className="text-indigo-300">Session: {sessionId.slice(0, 12)}...</span>
            <span className={`flex items-center gap-1 ${connected ? 'text-green-400' : 'text-gray-400'}`}>
              <span className={`w-1.5 h-1.5 rounded-full ${connected ? 'bg-green-400' : 'bg-gray-500'}`} />
              {connected ? 'WS Connected' : 'WS Disconnected'}
            </span>
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="bg-red-900/60 border border-red-500 text-red-200 rounded-xl px-4 py-3 text-sm flex items-center gap-2">
            <AlertTriangle size={16} /> {error}
          </div>
        )}

        {/* Main Controls */}
        <div className="bg-white/10 backdrop-blur rounded-2xl p-6 text-center">
          {phase === PHASE.IDLE && (
            <button
              onClick={handleStartCall}
              className="bg-green-500 hover:bg-green-600 text-white font-bold px-8 py-4 rounded-full text-lg shadow-lg transition-all hover:scale-105"
            >
              📞 Start Call
            </button>
          )}

          {phase === PHASE.RECORDING && (
            <div className="space-y-4">
              <p className="text-white text-sm font-medium">Session active. Speak Kannada, Hindi, or English.</p>
              <div className="flex gap-3 justify-center flex-wrap">
                {!mainRecorder.isRecording ? (
                  <button
                    onClick={handleStartRecording}
                    className="flex items-center gap-2 bg-red-500 hover:bg-red-600 text-white font-bold px-6 py-3 rounded-full shadow-lg transition-all"
                  >
                    <Mic size={20} /> Hold to Record
                  </button>
                ) : (
                  <button
                    onClick={handleStopAndProcess}
                    className="flex items-center gap-2 bg-gray-700 text-white font-bold px-6 py-3 rounded-full pulse-ring"
                  >
                    <MicOff size={20} /> Stop Recording
                  </button>
                )}
                <button
                  onClick={handleDemoProcess}
                  className="flex items-center gap-2 bg-indigo-500 hover:bg-indigo-600 text-white font-semibold px-5 py-3 rounded-full shadow transition-all text-sm"
                >
                  🎭 Demo (mock audio)
                </button>
                <label className="flex items-center gap-2 bg-purple-500 hover:bg-purple-600 text-white font-semibold px-5 py-3 rounded-full shadow transition-all text-sm cursor-pointer">
                  📁 Upload Audio
                  <input
                    type="file"
                    accept="audio/*"
                    className="hidden"
                    onChange={handleFileUpload}
                  />
                </label>
              </div>
            </div>
          )}

          {phase === PHASE.PROCESSING && (
            <div className="text-white space-y-2">
              <div className="flex justify-center gap-1">
                {['ASR', 'Dialect', 'Sentiment', 'LLM', 'TTS'].map((step, i) => (
                  <span key={step} className="text-xs bg-indigo-600 rounded px-2 py-1 animate-pulse" style={{ animationDelay: `${i * 0.15}s` }}>
                    {step}
                  </span>
                ))}
              </div>
              <p className="text-indigo-200 text-sm">Running AI pipeline...</p>
            </div>
          )}

          {phase === PHASE.CONFIRMED && (
            <div className="text-center space-y-3">
              <div className="text-4xl">✅</div>
              <p className="text-white font-bold text-lg">Understanding Verified!</p>
              <p className="text-green-300 text-sm">Interpretation confirmed by citizen. Routing to agent.</p>
              <button
                onClick={handleStartCall}
                className="mt-2 text-indigo-300 text-xs underline hover:text-white"
              >
                Start new call
              </button>
            </div>
          )}

          {phase === PHASE.ESCALATED && (
            <div className="text-center space-y-3">
              <div className="text-4xl">🆘</div>
              <p className="text-white font-bold text-lg">Escalated to Human Agent</p>
              {escalationReason && (
                <p className="text-red-300 text-sm">{escalationReason}</p>
              )}
              <button
                onClick={handleStartCall}
                className="mt-2 text-indigo-300 text-xs underline hover:text-white"
              >
                Start new call
              </button>
            </div>
          )}
        </div>

        {/* Transcript */}
        {transcript && (
          <TranscriptPanel
            transcript={transcript}
            language={language}
            isRecording={mainRecorder.isRecording}
          />
        )}

        {/* Sentiment */}
        {sentiment && (
          <div className="bg-white rounded-xl p-4">
            <p className="text-xs text-gray-500 font-medium mb-2 uppercase tracking-wide">Sentiment Analysis</p>
            <SentimentBadge
              sentiment={sentiment.sentiment}
              label={sentiment.label}
              urgencyFlag={sentiment.urgency_flag}
              confidence={sentiment.confidence}
            />
          </div>
        )}

        {/* Interpretation */}
        {interpretation && (
          <div className="bg-white rounded-xl p-4">
            <InterpretationCard
              interpretation={interpretation}
              dialectLabel={dialectLabel}
              isVerified={verificationOutcome === 'confirmed'}
            />
          </div>
        )}

        {/* Verification Loop */}
        {phase === PHASE.VERIFICATION && interpretation && (
          <div className="bg-white rounded-xl p-4">
            <VerificationPanel
              restatement={interpretation.restatement}
              outcome={verificationOutcome}
              onRecordConfirmation={verifyRecorder.isRecording
                ? verifyRecorder.stopRecording
                : verifyRecorder.startRecording}
              isRecording={verifyRecorder.isRecording}
              audioB64={verifyRecorder.audioB64}
              onSubmit={handleSubmitVerification}
            />
          </div>
        )}

        {/* Pipeline Log */}
        {logs.length > 0 && (
          <div className="bg-gray-900 rounded-xl p-4">
            <p className="text-xs text-gray-400 font-mono mb-2 uppercase tracking-widest">Pipeline Log</p>
            <div className="space-y-0.5 max-h-40 overflow-y-auto">
              {logs.map((log, i) => (
                <p key={i} className="text-xs font-mono text-gray-300">{log}</p>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
