import React from 'react'
import { MapPin, Building2, Zap, Tag } from 'lucide-react'

const INTENT_COLORS = {
  complaint: 'bg-red-100 text-red-700 border-red-300',
  inquiry:   'bg-blue-100 text-blue-700 border-blue-300',
  request:   'bg-yellow-100 text-yellow-700 border-yellow-300',
  emergency: 'bg-red-200 text-red-900 border-red-500 font-bold',
}

const ENTITY_ICONS = {
  department: <Building2 size={12} />,
  location:   <MapPin size={12} />,
  service:    <Zap size={12} />,
  id_number:  <Tag size={12} />,
  person:     <Tag size={12} />,
}

export default function InterpretationCard({ interpretation, dialectLabel, isVerified }) {
  if (!interpretation) return null
  const { core_issue, intent, entities, department, restatement, confidence, rag_context_used } = interpretation

  return (
    <div className={`rounded-xl border-2 p-4 ${isVerified ? 'border-green-400 bg-green-50' : 'border-brand-500 bg-white'}`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-bold text-gray-800 text-sm uppercase tracking-wide">
          {isVerified ? '✅ Verified Interpretation' : '🤖 AI Interpretation'}
        </h3>
        <div className="flex items-center gap-2">
          {dialectLabel && (
            <span className="text-xs bg-indigo-100 text-indigo-700 px-2 py-0.5 rounded-full border border-indigo-200">
              {dialectLabel}
            </span>
          )}
          <span className={`text-xs px-2 py-0.5 rounded-full border ${INTENT_COLORS[intent] || INTENT_COLORS.inquiry}`}>
            {intent}
          </span>
        </div>
      </div>

      {/* Core Issue */}
      <div className="mb-3">
        <p className="text-xs text-gray-500 mb-1 font-medium">CORE ISSUE</p>
        <p className="text-gray-900 font-semibold text-base leading-snug">{core_issue}</p>
      </div>

      {/* Department */}
      <div className="flex items-center gap-1.5 mb-3">
        <Building2 size={14} className="text-gray-400" />
        <span className="text-sm text-gray-600">Route to:</span>
        <span className="text-sm font-semibold text-brand-700">{department}</span>
      </div>

      {/* Entities */}
      {entities?.length > 0 && (
        <div className="mb-3">
          <p className="text-xs text-gray-500 mb-1.5 font-medium">ENTITIES DETECTED</p>
          <div className="flex flex-wrap gap-1.5">
            {entities.map((e, i) => (
              <span key={i} className="flex items-center gap-1 text-xs bg-gray-100 border border-gray-200 text-gray-700 px-2 py-0.5 rounded-full">
                {ENTITY_ICONS[e.type] || <Tag size={12} />}
                <span className="text-gray-500">{e.type}:</span> {e.value}
                {e.confidence < 0.7 && <span className="text-amber-500">*</span>}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Restatement */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mb-3">
        <p className="text-xs text-blue-600 font-medium mb-1">RESTATEMENT (spoken to citizen)</p>
        <p className="text-sm text-blue-900 italic">"{restatement}"</p>
      </div>

      {/* Footer */}
      <div className="flex items-center justify-between text-xs text-gray-400">
        <span>Confidence: <strong className={confidence > 0.7 ? 'text-green-600' : 'text-amber-600'}>{Math.round(confidence * 100)}%</strong></span>
        {rag_context_used?.length > 0 && (
          <span className="text-indigo-500">
            📡 {rag_context_used.join(', ')}
          </span>
        )}
      </div>
    </div>
  )
}
