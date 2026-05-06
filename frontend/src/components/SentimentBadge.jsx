import React from 'react'

const CONFIG = {
  distress:  { bg: 'bg-red-100',    border: 'border-red-400',    text: 'text-red-800',    icon: '⚠️' },
  anger:     { bg: 'bg-orange-100', border: 'border-orange-400', text: 'text-orange-800', icon: '⚠️' },
  fear:      { bg: 'bg-purple-100', border: 'border-purple-400', text: 'text-purple-800', icon: '😰' },
  confusion: { bg: 'bg-yellow-100', border: 'border-yellow-400', text: 'text-yellow-800', icon: 'ℹ️' },
  urgency:   { bg: 'bg-red-100',    border: 'border-red-500',    text: 'text-red-900',    icon: '🔴' },
  calm:      { bg: 'bg-green-100',  border: 'border-green-400',  text: 'text-green-800',  icon: '✅' },
  unknown:   { bg: 'bg-gray-100',   border: 'border-gray-300',   text: 'text-gray-600',   icon: '❓' },
}

export default function SentimentBadge({ sentiment, label, urgencyFlag, confidence }) {
  const cfg = CONFIG[sentiment] || CONFIG.unknown
  return (
    <div className={`flex items-center gap-2 px-3 py-2 rounded-lg border ${cfg.bg} ${cfg.border}`}>
      <span className="text-xl">{cfg.icon}</span>
      <div>
        <p className={`font-semibold text-sm ${cfg.text}`}>{label || sentiment}</p>
        {urgencyFlag && (
          <p className="text-xs text-red-700 font-medium mt-0.5">🔴 URGENCY FLAGGED</p>
        )}
        {confidence != null && (
          <p className="text-xs text-gray-500 mt-0.5">Confidence: {Math.round(confidence * 100)}%</p>
        )}
      </div>
    </div>
  )
}
