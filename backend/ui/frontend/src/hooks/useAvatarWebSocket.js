import { useState, useEffect } from 'react'
import useWebSocketDefault from 'react-use-websocket'

const useWebSocket = useWebSocketDefault?.default || useWebSocketDefault

export default function useAvatarWebSocket(url) {
  const [state, setState] = useState('idle')

  const { lastJsonMessage, readyState } = useWebSocket(url, {
    shouldReconnect: (closeEvent) => true,
    reconnectInterval: 3000,
    reconnectAttempts: 100,
  })

  useEffect(() => {
    if (lastJsonMessage && lastJsonMessage.state) {
      setState(lastJsonMessage.state)
    }
  }, [lastJsonMessage])

  return { state, readyState }
}
