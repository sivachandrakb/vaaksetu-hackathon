import React, { useState, useEffect, useCallback } from 'react'
import { PhoneCall, AlertTriangle, TrendingUp, Database, Edit3, PhoneOff } from 'lucide-react'
import { useWebSocket } from '../hooks/useWebSocket'
import { getDashboardStats, getDatasetFeed, submitCorrection, escalateCall } from '../utils/api'
import SentimentBadge from '../components/SentimentBadge'
import InterpretationCard from '../components/InterpretationCard'
import { DatasetPanel } from '../components/Panels'
import { HourlyTrendsChart, SentimentPieChart } from '../components/CallTrends'
import FeedbackModal from '../components/FeedbackModal'

export default function AgentDashboard() {
  const [stats, setStats] = useState(null)
  const [feeds, setFeeds] = useState([])
  const [activeSession, setActiveSession] = useState(null)
  const [liveInterpretation, setLiveInterpretation] = useState(null)
  const [liveSentiment, setLiveSentiment] = useState(null)
  const [liveTranscript, setLiveTranscript] = useState('')
  const [liveDialect, setLiveDialect] = useState(null)
  const [escalationAlert, setEscalationAlert] = useState(null)
  const [verificationStatus, setVerificationStatus] = useState(null)
  const [confidenceDecision, setConfidenceDecision] = useState(null)
  const [showFeedbackModal, setShowFeedbackModal] = useState(false)
  const [sessionInput, setSessionInput] = useState('')

  // Load dashboard stats
  const loadStats = useCallback(async () => {
    try {
      const data = await getDashboardStats()
      setStats(data)
    } catch (e) { /* backend might not be running */ }
  }, [])

  const loadFeeds = useCallback(async () => {
    try {
      const data = await getDatasetFeed()
      setFeeds(data.feeds || [])
    } catch (e) {}
  }, [])

  useEffect(() => {
    loadStats()
    loadFeeds()
    const interval = setInterval(() => { loadStats(); loadFeeds() }, 15000)
    return () => clearInterval(interval)
  }, [])

  // WebSocket — monitoring a specific call session
  const handleWsMessage = useCallback((msg) => {
    switch (msg.type) {
      case 'transcript_update':
        setLiveTranscript(msg.payload.transcript || '')
        break
      case 'sentiment_update':
        setLiveSentiment(msg.payload)
        break
      case 'interpretation_ready':
        setLiveInterpretation(msg.payload)
        setLiveDialect(msg.payload.dialect)
        setEscalationAlert(null)
        setVerificationStatus(null)
        setConfidenceDecision(null)
        break
      case 'verification_result':
        setVerificationStatus(msg.payload)
        break
      case 'confidence_decision':
        setConfidenceDecision(msg.payload)
        break
      case 'escalation':
        setEscalationAlert(msg.payload)
        break
    }
  }, [])

  useWebSocket(activeSession, handleWsMessage)

  const handleConnectSession = () => {
    if (!sessionInput.trim()) return
    setActiveSession(sessionInput.trim())
    setLiveTranscript('')
    setLiveSentiment(null)
    setLiveInterpretation(null)
    setEscalationAlert(null)
    setVerificationStatus(null)
    setConfidenceDecision(null)
  }

  const handleTakeOver = async () => {
    if (!activeSession) return
    try {
      await escalateCall(activeSession, 'agent_takeover')
      setEscalationAlert({ reason: 'Agent manually took over', triggered_by: 'agent' })
    } catch (e) {}
  }

  const handleSubmitCorrection = async (correction) => {
    if (!activeSession) return
    await submitCorrection(activeSession, correction)
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-brand-900 text-white px-6 py-4 flex items-center justify-between shadow-lg">
        <div>
          <h1 className="font-bold text-xl">🎙️ VaakSetu — Agent Dashboard</h1>
          <p className="text-indigo-200 text-xs mt-0.5">1092 Helpline | Real-Time AI Assistance</p>
        </div>
        <div className="flex items-center gap-3">
          {/* Session connector */}
          <div className="flex gap-2 items-center">
            <input
              className="text-gray-900 text-xs px-3 py-1.5 rounded-lg border border-indigo-300 w-52 focus:outline-none"
              placeholder="Paste session ID to monitor..."
              value={sessionInput}
              onChange={e => setSessionInput(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleConnectSession()}
            />
            <button
              onClick={handleConnectSession}
              className="bg-indigo-500 hover:bg-indigo-600 text-white text-xs px-3 py-1.5 rounded-lg font-medium"
            >
              Monitor
            </button>
          </div>
          {activeSession && (
            <span className="text-xs text-green-300 flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse" />
              Live: {activeSession.slice(0, 8)}...
            </span>
          )}
        </div>
      </div>

      {/* Escalation Alert Banner */}
      {escalationAlert && (
        <div className="bg-red-600 text-white px-6 py-3 flex items-center gap-3">
          <AlertTriangle size={20} className="shrink-0" />
          <div>
            <p className="font-bold">🆘 ESCALATION — Human Takeover Required</p>
            <p className="text-sm text-red-100">{escalationAlert.reason}</p>
          </div>
        </div>
      )}

      <div className="p-6 grid grid-cols-1 xl:grid-cols-3 gap-6 max-w-screen-2xl mx-auto">

        {/* ── Left: Stats & Trends ───────────────────────────────────────── */}
        <div className="space-y-4">
          {/* KPIs */}
          <div className="grid grid-cols-2 gap-3">
            {[
              { label: 'Active Calls', value: stats?.active_calls ?? '—', icon: <PhoneCall size={18} />, color: 'text-brand-600' },
              { label: 'Escalated (1hr)', value: stats?.escalated_last_hour ?? '—', icon: <AlertTriangle size={18} />, color: 'text-red-600' },
              { label: 'Avg Confidence', value: stats?.avg_confidence ? `${Math.round(stats.avg_confidence * 100)}%` : '—', icon: <TrendingUp size={18} />, color: 'text-green-600' },
              { label: 'Escalation Rate', value: stats?.escalation_rate ? `${Math.round(stats.escalation_rate * 100)}%` : '—', icon: <PhoneOff size={18} />, color: 'text-orange-600' },
            ].map(({ label, value, icon, color }) => (
              <div key={label} className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
                <div className={`flex items-center gap-1.5 ${color} mb-1`}>{icon}<span className="text-xs font-medium">{label}</span></div>
                <p className="text-2xl font-bold text-gray-800">{value}</p>
              </div>
            ))}
          </div>

          {/* Hourly trends */}
          <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
            <HourlyTrendsChart data={stats?.hourly_trends} />
          </div>

          {/* Sentiment pie */}
          <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
            <SentimentPieChart data={stats?.sentiment_summary} />
          </div>

          {/* Top issues */}
          <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
            <p className="text-xs text-gray-500 font-medium mb-3 uppercase tracking-wide">Top Issues Today</p>
            <div className="space-y-2">
              {stats?.top_issues?.map((issue, i) => (
                <div key={i} className="flex items-center justify-between">
                  <div className="flex items-center gap-2 flex-1 min-w-0">
                    {issue.spike && <span className="text-xs text-red-500 font-bold shrink-0">SPIKE</span>}
                    <p className="text-sm text-gray-700 truncate">{issue.issue}</p>
                  </div>
                  <span className="text-xs text-gray-400 shrink-0 ml-2">{issue.count}</span>
                </div>
              ))}
              {!stats?.top_issues?.length && (
                <p className="text-sm text-gray-400 italic">Loading...</p>
              )}
            </div>
          </div>
        </div>

        {/* ── Centre: Live Call Monitor ──────────────────────────────────── */}
        <div className="space-y-4">
          <div className="bg-white rounded-2xl shadow-sm border border-gray-200 overflow-hidden">
            <div className="bg-gradient-to-r from-brand-900 to-indigo-800 px-5 py-4 flex items-center justify-between">
              <div>
                <h2 className="text-white font-bold">Live Call Monitor</h2>
                <p className="text-indigo-200 text-xs">
                  {activeSession ? `Monitoring session ${activeSession.slice(0,8)}...` : 'Enter session ID to monitor'}
                </p>
              </div>
              {activeSession && (
                <button
                  onClick={handleTakeOver}
                  className="bg-red-500 hover:bg-red-600 text-white font-bold px-4 py-2 rounded-lg text-sm flex items-center gap-1.5 transition-all"
                >
                  <PhoneOff size={14} /> Take Over
                </button>
              )}
            </div>

            <div className="p-5 space-y-4">
              {/* Live transcript */}
              {liveTranscript && (
                <div>
                  <p className="text-xs text-gray-500 font-medium mb-1.5 uppercase tracking-wide">Citizen Transcript</p>
                  <div className="bg-gray-900 rounded-lg p-3 text-sm text-white font-mono leading-relaxed">
                    {liveTranscript}
                  </div>
                </div>
              )}

              {/* Sentiment */}
              {liveSentiment && (
                <div>
                  <p className="text-xs text-gray-500 font-medium mb-1.5 uppercase tracking-wide">Sentiment</p>
                  <SentimentBadge
                    sentiment={liveSentiment.sentiment}
                    label={liveSentiment.label}
                    urgencyFlag={liveSentiment.urgency_flag}
                    confidence={liveSentiment.confidence}
                  />
                </div>
              )}

              {/* Interpretation */}
              {liveInterpretation && (
                <InterpretationCard
                  interpretation={liveInterpretation}
                  dialectLabel={liveDialect}
                  isVerified={verificationStatus?.outcome === 'confirmed'}
                />
              )}

              {/* Verification status */}
              {verificationStatus && (
                <div className={`rounded-lg px-3 py-2 text-sm font-medium border ${
                  verificationStatus.outcome === 'confirmed' ? 'bg-green-50 border-green-300 text-green-700' :
                  verificationStatus.outcome === 'incorrect' ? 'bg-red-50 border-red-300 text-red-700' :
                  'bg-yellow-50 border-yellow-300 text-yellow-700'
                }`}>
                  🔁 Verification: <strong>{verificationStatus.outcome?.toUpperCase()}</strong>
                  {verificationStatus.citizen_response && (
                    <span className="ml-2 text-xs opacity-70">— "{verificationStatus.citizen_response}"</span>
                  )}
                </div>
              )}

              {/* Confidence decision */}
              {confidenceDecision && (
                <div className={`rounded-lg px-3 py-2 text-xs font-medium border ${
                  confidenceDecision.decision === 'proceed' ? 'bg-green-50 border-green-300 text-green-700' :
                  confidenceDecision.decision === 'escalate' ? 'bg-red-50 border-red-300 text-red-700' :
                  'bg-yellow-50 border-yellow-300 text-yellow-700'
                }`}>
                  ⚖️ Confidence: <strong>{confidenceDecision.decision?.toUpperCase()}</strong>
                  {' '}({Math.round((confidenceDecision.overall_score || 0) * 100)}%)
                </div>
              )}

              {!activeSession && (
                <div className="text-center py-8 text-gray-400">
                  <PhoneCall size={40} className="mx-auto mb-3 opacity-30" />
                  <p className="text-sm">No active session being monitored</p>
                  <p className="text-xs mt-1">Enter a session ID above to watch a live call</p>
                </div>
              )}
            </div>
          </div>

          {/* Agent Actions */}
          {activeSession && liveInterpretation && (
            <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-200">
              <p className="text-xs text-gray-500 font-medium mb-3 uppercase tracking-wide">Agent Actions</p>
              <div className="flex gap-3">
                <button
                  onClick={() => setShowFeedbackModal(true)}
                  className="flex items-center gap-1.5 px-4 py-2 bg-amber-500 hover:bg-amber-600 text-white font-semibold rounded-lg text-sm transition-all"
                >
                  <Edit3 size={14} /> Correct Interpretation
                </button>
                <button
                  onClick={handleTakeOver}
                  className="flex items-center gap-1.5 px-4 py-2 bg-red-500 hover:bg-red-600 text-white font-semibold rounded-lg text-sm transition-all"
                >
                  <PhoneOff size={14} /> Escalate
                </button>
              </div>
            </div>
          )}
        </div>

        {/* ── Right: Dataset Panel ───────────────────────────────────────── */}
        <div className="space-y-4">
          <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-5">
            <div className="flex items-center gap-2 mb-4">
              <Database size={16} className="text-brand-600" />
              <h2 className="font-bold text-gray-800">Real-Time Dataset Panel</h2>
            </div>
            <DatasetPanel feeds={feeds} />
          </div>

          {/* Handle time / avg stats */}
          {stats && (
            <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
              <p className="text-xs text-gray-500 font-medium mb-3 uppercase tracking-wide">Performance Metrics</p>
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Avg handle time</span>
                  <span className="font-semibold text-gray-800">
                    {stats.avg_handle_time_seconds ? `${Math.floor(stats.avg_handle_time_seconds / 60)}m ${stats.avg_handle_time_seconds % 60}s` : '—'}
                  </span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Avg confidence</span>
                  <span className={`font-semibold ${stats.avg_confidence > 0.7 ? 'text-green-600' : 'text-amber-600'}`}>
                    {stats.avg_confidence ? `${Math.round(stats.avg_confidence * 100)}%` : '—'}
                  </span>
                </div>
              </div>
            </div>
          )}

          {/* Feedback queue status */}
          <div className="bg-gradient-to-br from-indigo-900 to-brand-900 rounded-xl p-5 text-white">
            <p className="text-xs text-indigo-300 font-medium mb-2 uppercase tracking-wide">Continuous Learning</p>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-indigo-200">Fine-tune queue</span>
                <span className="font-bold text-green-300">Active</span>
              </div>
              <div className="flex justify-between">
                <span className="text-indigo-200">Last retrain</span>
                <span className="font-bold">Weekly batch</span>
              </div>
              <div className="flex justify-between">
                <span className="text-indigo-200">Agent corrections</span>
                <span className="font-bold text-amber-300">Priority labelled</span>
              </div>
            </div>
            <div className="mt-3 pt-3 border-t border-indigo-700">
              <p className="text-xs text-indigo-300">
                Every confirmed/corrected call is stored as a labelled training example.
                Weekly ASR + semantic model retraining on IndicVoices corpus.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Feedback Modal */}
      {showFeedbackModal && (
        <FeedbackModal
          sessionId={activeSession}
          currentInterpretation={liveInterpretation?.core_issue}
          onSubmit={handleSubmitCorrection}
          onClose={() => setShowFeedbackModal(false)}
        />
      )}
    </div>
  )
}
