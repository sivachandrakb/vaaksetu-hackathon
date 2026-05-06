import axios from 'axios'

const BASE = import.meta.env.VITE_API_URL || ''

const api = axios.create({ baseURL: BASE })

export const startCall = (agentId = 'agent_001') =>
  api.post('/api/call/start', { agent_id: agentId }).then(r => r.data)

export const processAudio = (sessionId, audioB64, isFinal = true) =>
  api.post('/api/call/process-audio', {
    session_id: sessionId,
    audio_b64: audioB64,
    is_final: isFinal,
  }).then(r => r.data)

export const submitVerification = (sessionId, audioB64) =>
  api.post('/api/call/verify', {
    session_id: sessionId,
    audio_b64: audioB64,
  }).then(r => r.data)

export const submitCorrection = (sessionId, correctedInterpretation, agentId = 'agent_001') =>
  api.post('/api/call/correct', {
    session_id: sessionId,
    corrected_interpretation: correctedInterpretation,
    agent_id: agentId,
  }).then(r => r.data)

export const escalateCall = (sessionId, reason = 'agent_takeover', agentId = 'agent_001') =>
  api.post('/api/call/escalate', {
    session_id: sessionId,
    agent_id: agentId,
    reason,
  }).then(r => r.data)

export const getDashboardStats = () =>
  api.get('/api/dashboard/stats').then(r => r.data)

export const getDatasetFeed = () =>
  api.get('/api/dashboard/dataset-feed').then(r => r.data)

export const getDataset = (source) =>
  api.get(`/api/datasets/${source}`).then(r => r.data)

// ── Audio Helpers ──────────────────────────────────────────────────────────

/** Convert a Blob to base64 string */
export const blobToBase64 = (blob) =>
  new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(reader.result.split(',')[1])
    reader.onerror = reject
    reader.readAsDataURL(blob)
  })

/** Play base64-encoded MP3 audio */
export const playBase64Audio = (b64) => {
  const audio = new Audio(`data:audio/mp3;base64,${b64}`)
  return audio.play()
}

export default api
