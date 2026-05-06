import React, { useState } from 'react'
import { Play, ChevronRight, CheckCircle, XCircle, AlertTriangle, Mic, Building2, MapPin, Zap } from 'lucide-react'
import axios from 'axios'

const CATEGORIES = [
  { key: 'ration',      label: '🍚 Ration Card',       color: 'bg-orange-100 border-orange-300 text-orange-800' },
  { key: 'pension',     label: '👴 Pension',            color: 'bg-purple-100 border-purple-300 text-purple-800' },
  { key: 'water',       label: '💧 BWSSB Water',        color: 'bg-blue-100 border-blue-300 text-blue-800' },
  { key: 'bbmp',        label: '🏙️ BBMP Civic',        color: 'bg-gray-100 border-gray-300 text-gray-800' },
  { key: 'land',        label: '🌾 Land Records',       color: 'bg-green-100 border-green-300 text-green-800' },
  { key: 'certificate', label: '📄 Certificates',       color: 'bg-yellow-100 border-yellow-300 text-yellow-800' },
  { key: 'emergency',   label: '🆘 Emergency',          color: 'bg-red-100 border-red-400 text-red-800' },
  { key: 'mixed',       label: '🔀 Code-Switch',        color: 'bg-indigo-100 border-indigo-300 text-indigo-800' },
]

const SENTIMENT_COLORS = {
  distress:  'bg-red-100 text-red-800 border-red-300',
  anger:     'bg-orange-100 text-orange-800 border-orange-300',
  confusion: 'bg-yellow-100 text-yellow-800 border-yellow-300',
  urgency:   'bg-red-200 text-red-900 border-red-500',
  calm:      'bg-green-100 text-green-800 border-green-300',
  fear:      'bg-purple-100 text-purple-800 border-purple-300',
}

const SENTIMENT_ICONS = {
  distress: '😰', anger: '😠', confusion: '😕',
  urgency: '🔴', calm: '😌', fear: '😨',
}

const LANG_LABELS = { kn: 'Kannada', hi: 'Hindi', en: 'English' }

function PipelineStep({ step, title, children, done }) {
  return (
    <div className={`rounded-xl border-2 p-4 transition-all ${done ? 'border-green-400 bg-green-50' : 'border-gray-200 bg-white'}`}>
      <div className="flex items-center gap-2 mb-3">
        <span className={`w-7 h-7 rounded-full flex items-center justify-center text-sm font-bold ${done ? 'bg-green-500 text-white' : 'bg-gray-200 text-gray-600'}`}>
          {done ? '✓' : step}
        </span>
        <h3 className="font-bold text-gray-800">{title}</h3>
      </div>
      {children}
    </div>
  )
}

export default function DemoMode() {
  const [selectedCategory, setSelectedCategory] = useState(null)
  const [running, setRunning] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const [animStep, setAnimStep] = useState(0)

  const runDemo = async (category = null, random = false) => {
    setRunning(true)
    setResult(null)
    setError(null)
    setAnimStep(0)

    // Animate steps
    const steps = [1, 2, 3, 4, 5]
    for (const s of steps) {
      await new Promise(r => setTimeout(r, 350))
      setAnimStep(s)
    }

    try {
      const body = random
        ? { random_pick: true }
        : category
          ? { category }
          : { random_pick: true }

      const res = await axios.post('/api/demo/run', body)
      setResult(res.data)
    } catch (e) {
      setError(e.response?.data?.detail || e.message)
    } finally {
      setRunning(false)
    }
  }

  const pipeline = result?.pipeline
  const scenario = result?.scenario

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 to-indigo-950 py-8 px-4">
      {/* Header */}
      <div className="text-center mb-8">
        <div className="inline-flex items-center gap-2 bg-white/10 text-white text-xs font-semibold px-4 py-1.5 rounded-full mb-4 border border-white/20">
          🏆 AI for Bharat 2026 · Theme 12 · Hackathon Demo Mode
        </div>
        <h1 className="text-5xl font-black text-white mb-2">VaakSetu <span className="text-indigo-400">Demo</span></h1>
        <p className="text-indigo-300 text-lg">"Bridge of Words" — AI Pipeline for 1092 Helpline</p>
        <p className="text-indigo-400 text-sm mt-1">No microphone needed · Uses realistic Kannada/Hindi/English call transcripts</p>
      </div>

      <div className="max-w-6xl mx-auto space-y-6">

        {/* Scenario Picker */}
        <div className="bg-white/10 backdrop-blur rounded-2xl p-6 border border-white/20">
          <h2 className="text-white font-bold text-lg mb-4">🎬 Choose a Call Scenario</h2>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-5">
            {CATEGORIES.map(cat => (
              <button
                key={cat.key}
                onClick={() => setSelectedCategory(cat.key)}
                className={`px-3 py-2.5 rounded-xl border-2 text-sm font-semibold text-left transition-all hover:scale-105 ${
                  selectedCategory === cat.key
                    ? cat.color + ' ring-2 ring-offset-1 ring-indigo-400 scale-105'
                    : 'bg-white/10 border-white/20 text-white hover:bg-white/20'
                }`}
              >
                {cat.label}
              </button>
            ))}
          </div>

          <div className="flex gap-3 flex-wrap">
            <button
              onClick={() => runDemo(selectedCategory)}
              disabled={running}
              className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white font-bold px-6 py-3 rounded-xl shadow-lg transition-all hover:scale-105 disabled:scale-100"
            >
              <Play size={18} />
              {running ? 'Running Pipeline...' : selectedCategory ? `Run ${selectedCategory} scenario` : 'Run Demo'}
            </button>
            <button
              onClick={() => runDemo(null, true)}
              disabled={running}
              className="flex items-center gap-2 bg-white/20 hover:bg-white/30 disabled:opacity-50 text-white font-semibold px-5 py-3 rounded-xl transition-all"
            >
              🎲 Random Scenario
            </button>
          </div>
        </div>

        {/* Pipeline Animation */}
        {running && (
          <div className="bg-white/10 backdrop-blur rounded-2xl p-6 border border-white/20">
            <h3 className="text-white font-bold mb-4 text-center">⚡ Running AI Pipeline...</h3>
            <div className="flex items-center justify-center gap-2 flex-wrap">
              {[
                { n: 1, label: 'ASR', icon: '🎙️' },
                { n: 2, label: 'Dialect ID', icon: '🗺️' },
                { n: 3, label: 'Sentiment', icon: '💬' },
                { n: 4, label: 'LLM+RAG', icon: '🤖' },
                { n: 5, label: 'TTS', icon: '🔊' },
              ].map(({ n, label, icon }) => (
                <React.Fragment key={n}>
                  <div className={`flex flex-col items-center gap-1 px-4 py-3 rounded-xl border-2 transition-all ${
                    animStep >= n
                      ? 'bg-indigo-600 border-indigo-400 text-white scale-105'
                      : 'bg-white/10 border-white/20 text-indigo-300'
                  }`}>
                    <span className="text-xl">{icon}</span>
                    <span className="text-xs font-bold">{label}</span>
                  </div>
                  {n < 5 && <ChevronRight className="text-indigo-400" size={16} />}
                </React.Fragment>
              ))}
            </div>
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="bg-red-900/60 border border-red-500 text-red-200 rounded-xl p-4 flex items-center gap-3">
            <AlertTriangle size={20} /> {error}
            <span className="text-xs ml-auto opacity-70">Make sure the backend is running on :8000</span>
          </div>
        )}

        {/* Results */}
        {result && !running && (
          <div className="space-y-5">

            {/* Scenario Info */}
            <div className="bg-gradient-to-r from-indigo-900 to-blue-900 rounded-2xl p-5 border border-indigo-500">
              <div className="flex items-start justify-between flex-wrap gap-3">
                <div>
                  <div className="text-indigo-300 text-xs font-semibold mb-1 uppercase tracking-widest">Scenario {scenario.id}</div>
                  <h2 className="text-white font-bold text-xl">{scenario.title}</h2>
                </div>
                <div className="flex gap-2 flex-wrap">
                  <span className="bg-white/20 text-white text-xs px-3 py-1 rounded-full font-medium">
                    {LANG_LABELS[result.pipeline?.language] || pipeline?.language}
                  </span>
                  <span className={`text-xs px-3 py-1 rounded-full font-semibold border ${SENTIMENT_COLORS[pipeline?.sentiment?.sentiment] || 'bg-gray-100 border-gray-300 text-gray-700'}`}>
                    {SENTIMENT_ICONS[pipeline?.sentiment?.sentiment]} {pipeline?.sentiment?.sentiment}
                  </span>
                </div>
              </div>
            </div>

            {/* 5 Pipeline Steps */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">

              {/* Step 1: Transcript */}
              <PipelineStep step={1} title="ASR — Transcription" done={true}>
                <div className="bg-gray-900 rounded-lg p-3 font-mono text-sm text-green-300 leading-relaxed">
                  {pipeline?.transcript}
                </div>
                <div className="flex gap-2 mt-2 text-xs text-gray-500">
                  <span>Language: <strong className="text-gray-700">{LANG_LABELS[pipeline?.language] || pipeline?.language}</strong></span>
                  <span>·</span>
                  <span>Dialect: <strong className="text-gray-700">{pipeline?.dialect}</strong></span>
                  <span>·</span>
                  <span>ASR conf: <strong className="text-gray-700">{Math.round((pipeline?.confidence_eval?.asr_confidence || 0.87) * 100)}%</strong></span>
                </div>
              </PipelineStep>

              {/* Step 2: Sentiment */}
              <PipelineStep step={2} title="Sentiment & Urgency Classifier" done={true}>
                <div className={`rounded-lg px-4 py-3 border ${SENTIMENT_COLORS[pipeline?.sentiment?.sentiment] || 'bg-gray-100 border-gray-200 text-gray-700'}`}>
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-2xl">{SENTIMENT_ICONS[pipeline?.sentiment?.sentiment]}</span>
                    <span className="font-bold text-base">{pipeline?.sentiment?.label}</span>
                  </div>
                  {pipeline?.sentiment?.urgency_flag && (
                    <div className="text-red-700 text-xs font-bold mt-1">🔴 URGENCY FLAGGED</div>
                  )}
                </div>
                <div className="flex gap-3 mt-2 text-xs text-gray-500">
                  <span>Acoustic: <strong>{pipeline?.sentiment?.acoustic_signal}</strong></span>
                  <span>·</span>
                  <span>Lexical: <strong>{pipeline?.sentiment?.lexical_signal}</strong></span>
                  <span>·</span>
                  <span>Conf: <strong>{Math.round((pipeline?.sentiment?.confidence || 0) * 100)}%</strong></span>
                </div>
              </PipelineStep>

              {/* Step 3: Interpretation */}
              <PipelineStep step={3} title="Semantic Interpretation (LLM + RAG)" done={true}>
                <div className="space-y-3">
                  <div>
                    <p className="text-xs text-gray-400 uppercase tracking-wide mb-1">Core Issue</p>
                    <p className="font-semibold text-gray-800">{pipeline?.interpretation?.core_issue}</p>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <Building2 size={13} className="text-gray-400" />
                    <span className="text-sm text-gray-500">Route to:</span>
                    <span className="text-sm font-bold text-indigo-700">{pipeline?.interpretation?.department}</span>
                  </div>
                  <div className="flex flex-wrap gap-1.5">
                    {pipeline?.interpretation?.entities?.map((e, i) => (
                      <span key={i} className="text-xs bg-indigo-50 border border-indigo-200 text-indigo-700 px-2 py-0.5 rounded-full">
                        {e.type}: {e.value}
                      </span>
                    ))}
                  </div>
                  {pipeline?.interpretation?.rag_context_used?.length > 0 && (
                    <div className="text-xs text-indigo-500">
                      📡 RAG enriched from: {pipeline.interpretation.rag_context_used.join(', ')}
                    </div>
                  )}
                  <div className="text-xs text-gray-400">
                    Confidence: <strong className={pipeline?.interpretation?.confidence > 0.7 ? 'text-green-600' : 'text-amber-600'}>
                      {Math.round((pipeline?.interpretation?.confidence || 0) * 100)}%
                    </strong>
                  </div>
                </div>
              </PipelineStep>

              {/* Step 4: Verification Loop */}
              <PipelineStep step={4} title="Verification Loop — Restatement" done={true}>
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mb-3">
                  <p className="text-xs text-blue-500 font-semibold mb-1">🔊 Spoken to citizen in their language:</p>
                  <p className="text-blue-900 italic text-sm leading-relaxed">
                    "{pipeline?.verification_restatement || pipeline?.interpretation?.restatement}"
                  </p>
                  {pipeline?.interpretation?.has_audio && (
                    <p className="text-xs text-blue-400 mt-1.5">✅ TTS audio generated (plays on citizen's phone)</p>
                  )}
                </div>
                {pipeline?.skip_verification ? (
                  <div className="bg-red-50 border border-red-300 rounded-lg px-3 py-2 text-sm text-red-700 font-semibold">
                    ⚠️ High distress detected — verification loop SKIPPED → immediate escalation
                  </div>
                ) : (
                  <div className="bg-green-50 border border-green-300 rounded-lg px-3 py-2 text-sm text-green-700">
                    Awaiting citizen confirmation → houdu / illa / partial correction
                  </div>
                )}
              </PipelineStep>
            </div>

            {/* Step 5: Confidence Decision */}
            <div className={`rounded-2xl border-2 p-5 ${
              pipeline?.confidence_eval?.decision === 'proceed'
                ? 'border-green-400 bg-green-50'
                : pipeline?.confidence_eval?.decision === 'escalate'
                  ? 'border-red-400 bg-red-50'
                  : 'border-yellow-400 bg-yellow-50'
            }`}>
              <div className="flex items-center gap-3 mb-3">
                <span className="text-3xl">
                  {pipeline?.confidence_eval?.decision === 'proceed' ? '✅' :
                   pipeline?.confidence_eval?.decision === 'escalate' ? '🆘' : '⚠️'}
                </span>
                <div>
                  <h3 className="font-black text-xl text-gray-800">
                    Step 5: Confidence Evaluator → {pipeline?.confidence_eval?.decision?.toUpperCase()}
                  </h3>
                  <p className="text-sm text-gray-500">
                    Overall score: <strong>{Math.round((pipeline?.confidence_eval?.overall_score || 0) * 100)}%</strong>
                    {pipeline?.confidence_eval?.escalation_reason && (
                      <span className="ml-2 text-red-600">— {pipeline.confidence_eval.escalation_reason}</span>
                    )}
                  </p>
                </div>
              </div>

              {/* Agent card preview */}
              <div className="bg-white rounded-xl border border-gray-200 p-4">
                <p className="text-xs text-gray-400 font-semibold mb-2 uppercase tracking-widest">Agent Dashboard Card</p>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                  <div>
                    <p className="text-xs text-gray-400 mb-1">Issue</p>
                    <p className="font-semibold text-gray-800 text-sm">{pipeline?.interpretation?.core_issue}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-400 mb-1">Route To</p>
                    <p className="font-bold text-indigo-700 text-sm">{pipeline?.interpretation?.department}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-400 mb-1">Sentiment</p>
                    <span className={`text-xs px-2 py-0.5 rounded-full border font-semibold ${SENTIMENT_COLORS[pipeline?.sentiment?.sentiment]}`}>
                      {pipeline?.sentiment?.label}
                    </span>
                  </div>
                </div>
              </div>
            </div>

            {/* AI vs Expected accuracy check */}
            <div className="bg-white rounded-2xl border border-gray-200 p-5">
              <h3 className="font-bold text-gray-700 mb-3">🎯 Pipeline Accuracy Check</h3>
              <div className="grid grid-cols-2 gap-4">
                <div className="flex items-center gap-2">
                  {result.ai_vs_expected?.issue_match
                    ? <CheckCircle className="text-green-500" size={20} />
                    : <XCircle className="text-amber-500" size={20} />}
                  <div>
                    <p className="text-sm font-semibold text-gray-700">Issue Detection</p>
                    <p className="text-xs text-gray-400">Expected: {scenario.expected_issue}</p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {result.ai_vs_expected?.dept_match
                    ? <CheckCircle className="text-green-500" size={20} />
                    : <XCircle className="text-amber-500" size={20} />}
                  <div>
                    <p className="text-sm font-semibold text-gray-700">Department Routing</p>
                    <p className="text-xs text-gray-400">Expected: {scenario.expected_dept}</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Run another */}
            <div className="text-center">
              <button
                onClick={() => runDemo(null, true)}
                className="bg-indigo-600 hover:bg-indigo-700 text-white font-bold px-8 py-3 rounded-xl shadow-lg transition-all hover:scale-105"
              >
                🎲 Try Another Random Scenario
              </button>
            </div>

          </div>
        )}
      </div>
    </div>
  )
}
