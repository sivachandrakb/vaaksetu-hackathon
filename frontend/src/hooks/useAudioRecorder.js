import { useState, useRef, useCallback } from 'react'
import { blobToBase64 } from '../utils/api'

/**
 * Hook for browser mic recording.
 * Returns { isRecording, startRecording, stopRecording, audioB64, error }
 */
export function useAudioRecorder() {
  const [isRecording, setIsRecording] = useState(false)
  const [audioB64, setAudioB64] = useState(null)
  const [error, setError] = useState(null)
  const mediaRecorderRef = useRef(null)
  const chunksRef = useRef([])

  const startRecording = useCallback(async () => {
    setError(null)
    setAudioB64(null)
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const mr = new MediaRecorder(stream, { mimeType: 'audio/webm;codecs=opus' })
      chunksRef.current = []
      mr.ondataavailable = e => { if (e.data.size > 0) chunksRef.current.push(e.data) }
      mr.onstop = async () => {
        const blob = new Blob(chunksRef.current, { type: 'audio/webm' })
        const b64 = await blobToBase64(blob)
        setAudioB64(b64)
        stream.getTracks().forEach(t => t.stop())
      }
      mr.start(100) // collect every 100ms
      mediaRecorderRef.current = mr
      setIsRecording(true)
    } catch (err) {
      setError(err.message || 'Microphone access denied')
    }
  }, [])

  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop()
      setIsRecording(false)
    }
  }, [isRecording])

  return { isRecording, startRecording, stopRecording, audioB64, error }
}
