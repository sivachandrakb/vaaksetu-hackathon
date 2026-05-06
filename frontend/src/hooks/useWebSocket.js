import { useEffect, useRef, useCallback, useState } from 'react'

/**
 * WebSocket hook for real-time pipeline updates.
 * @param {string|null} sessionId
 * @param {function} onMessage  callback(parsedMessage)
 */
export function useWebSocket(sessionId, onMessage) {
  const wsRef = useRef(null)
  const [connected, setConnected] = useState(false)

  useEffect(() => {
    if (!sessionId) return

    const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws'
    const host = window.location.host
    const url = `${protocol}://${host}/api/call/ws/${sessionId}`

    const ws = new WebSocket(url)
    wsRef.current = ws

    ws.onopen = () => {
      setConnected(true)
    }
    ws.onmessage = (evt) => {
      try {
        const msg = JSON.parse(evt.data)
        onMessage(msg)
      } catch (e) {
        // pong or non-JSON
      }
    }
    ws.onclose = () => setConnected(false)
    ws.onerror = () => setConnected(false)

    // Keepalive ping every 20s
    const pingInterval = setInterval(() => {
      if (ws.readyState === WebSocket.OPEN) ws.send('ping')
    }, 20000)

    return () => {
      clearInterval(pingInterval)
      ws.close()
    }
  }, [sessionId])

  const send = useCallback((data) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(typeof data === 'string' ? data : JSON.stringify(data))
    }
  }, [])

  return { connected, send }
}
