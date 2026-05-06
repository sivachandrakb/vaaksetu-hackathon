import React from 'react'

// ── TranscriptPanel ──────────────────────────────────────────────────────────
export function TranscriptPanel({ transcript, language, isRecording }) {
  return (
    <div className="bg-gray-900 rounded-xl p-4 min-h-[120px] relative">
      <div className="flex items-center gap-2 mb-2">
        <span className="text-xs text-gray-400 uppercase tracking-widest font-mono">Live Transcript</span>
        {isRecording && (
          <span className="flex gap-0.5 items-end h-4">
            {[...Array(5)].map((_, i) => (
              <span
                key={i}
                className="waveform-bar w-0.5 bg-red-400 rounded-full inline-block"
                style={{ height: '100%', animationDelay: `${i * 0.1}s` }}
              />
            ))}
          </span>
        )}
        {language && (
          <span className="ml-auto text-xs bg-gray-700 text-gray-300 px-2 py-0.5 rounded-full">
            {{kn:'Kannada', hi:'Hindi', en:'English'}[language] || language}
          </span>
        )}
      </div>
      <p className="text-white font-mono text-sm leading-relaxed">
        {transcript || <span className="text-gray-500 italic">Waiting for speech...</span>}
      </p>
    </div>
  )
}

// ── VerificationPanel ────────────────────────────────────────────────────────
export function VerificationPanel({ restatement, outcome, onRecordConfirmation, isRecording, audioB64, onSubmit }) {
  const OUTCOME_STYLES = {
    confirmed: 'bg-green-100 border-green-400 text-green-800',
    incorrect: 'bg-red-100 border-red-400 text-red-800',
    partial:   'bg-yellow-100 border-yellow-400 text-yellow-800',
    uncertain: 'bg-gray-100 border-gray-300 text-gray-600',
  }

  return (
    <div className="border-2 border-indigo-300 rounded-xl p-4 bg-indigo-50">
      <h4 className="font-bold text-indigo-800 text-sm mb-2">🔁 Verification Loop</h4>
      {restatement && (
        <div className="bg-white border border-indigo-200 rounded-lg p-3 mb-3">
          <p className="text-xs text-indigo-500 font-medium mb-1">Spoken to citizen:</p>
          <p className="text-sm text-indigo-900 italic">"{restatement}"</p>
        </div>
      )}
      {!outcome && (
        <div className="flex gap-2">
          <button
            onMouseDown={onRecordConfirmation}
            onMouseUp={() => { if (isRecording) onRecordConfirmation() }}
            className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium transition-all ${
              isRecording
                ? 'bg-red-500 text-white pulse-ring'
                : 'bg-indigo-600 text-white hover:bg-indigo-700'
            }`}
          >
            🎙️ {isRecording ? 'Recording...' : 'Record citizen response'}
          </button>
          {audioB64 && !isRecording && (
            <button
              onClick={onSubmit}
              className="px-3 py-2 bg-green-600 text-white rounded-lg text-sm font-medium hover:bg-green-700"
            >
              Submit →
            </button>
          )}
        </div>
      )}
      {outcome && (
        <div className={`px-3 py-2 rounded-lg border text-sm font-semibold ${OUTCOME_STYLES[outcome] || OUTCOME_STYLES.uncertain}`}>
          Outcome: {outcome.toUpperCase()}
        </div>
      )}
    </div>
  )
}

// ── DatasetPanel ─────────────────────────────────────────────────────────────
export function DatasetPanel({ feeds }) {
  const STATUS_COLORS = {
    live:      'text-green-600',
    streaming: 'text-blue-600',
    normal:    'text-gray-400',
  }
  return (
    <div className="bg-gray-900 rounded-xl p-4">
      <h4 className="text-xs text-gray-400 uppercase tracking-widest font-mono mb-3">
        📡 Real-Time Dataset Feed
      </h4>
      {!feeds?.length && (
        <p className="text-gray-500 text-sm italic">Loading feeds...</p>
      )}
      <div className="space-y-2">
        {feeds?.map((feed, i) => (
          <div key={i} className="flex items-start justify-between bg-gray-800 rounded-lg px-3 py-2">
            <div>
              <div className="flex items-center gap-1.5">
                <span className={`text-xs font-semibold ${STATUS_COLORS[feed.status] || 'text-gray-400'}`}>
                  ● {feed.source}
                </span>
                <span className="text-xs text-gray-500">{feed.type}</span>
              </div>
              <p className="text-xs text-gray-400 mt-0.5">{feed.preview}</p>
            </div>
            <span className="text-xs text-gray-600 shrink-0 ml-2">
              {feed.last_updated ? new Date(feed.last_updated).toLocaleTimeString() : ''}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}
