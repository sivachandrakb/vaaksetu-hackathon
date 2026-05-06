import React, { useState } from 'react'
import { X, CheckCircle } from 'lucide-react'

export default function FeedbackModal({ sessionId, currentInterpretation, onSubmit, onClose }) {
  const [correction, setCorrection] = useState(currentInterpretation || '')
  const [submitted, setSubmitted] = useState(false)

  const handleSubmit = async () => {
    if (!correction.trim()) return
    await onSubmit(correction)
    setSubmitted(true)
    setTimeout(onClose, 1500)
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg">
        <div className="flex items-center justify-between p-5 border-b">
          <h2 className="font-bold text-gray-800 text-lg">✏️ Agent Correction</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-700 transition-colors">
            <X size={20} />
          </button>
        </div>

        {submitted ? (
          <div className="p-8 text-center">
            <CheckCircle className="text-green-500 mx-auto mb-3" size={40} />
            <p className="text-green-700 font-semibold">Correction saved & queued for training</p>
          </div>
        ) : (
          <div className="p-5 space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Corrected interpretation:
              </label>
              <textarea
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm h-28 resize-none focus:outline-none focus:ring-2 focus:ring-brand-500"
                value={correction}
                onChange={e => setCorrection(e.target.value)}
                placeholder="Describe what the citizen actually meant..."
              />
            </div>
            <div className="bg-amber-50 border border-amber-200 rounded-lg px-3 py-2 text-xs text-amber-700">
              This correction will be stored as a high-quality training example and
              flagged for immediate labelling in the retraining pipeline.
            </div>
            <div className="flex gap-3 justify-end">
              <button
                onClick={onClose}
                className="px-4 py-2 text-sm text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={handleSubmit}
                disabled={!correction.trim()}
                className="px-4 py-2 text-sm font-semibold bg-brand-600 text-white rounded-lg hover:bg-brand-700 disabled:opacity-40 disabled:cursor-not-allowed"
              >
                Save Correction
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
