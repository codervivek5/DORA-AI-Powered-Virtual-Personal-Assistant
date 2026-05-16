import React from 'react'
import { Canvas } from '@react-three/fiber'
import { OrbitControls, Environment } from '@react-three/drei'
import AvatarViewer from './components/AvatarViewer'
import useAvatarWebSocket from './hooks/useAvatarWebSocket'

function App() {
  const { state } = useAvatarWebSocket('ws://localhost:8000/ws/avatar')
  const isDragging = React.useRef(false)
  const lastPos = React.useRef({ x: 0, y: 0 })

  const handleMouseDown = (e) => {
    isDragging.current = true
    lastPos.current = { x: e.screenX, y: e.screenY }
  }

  const handleMouseMove = (e) => {
    if (!isDragging.current) return
    const deltaX = e.screenX - lastPos.current.x
    const deltaY = e.screenY - lastPos.current.y
    
    if (window.electronAPI) {
      window.electronAPI.moveWindow({ x: deltaX, y: deltaY })
    }
    
    lastPos.current = { x: e.screenX, y: e.screenY }
  }

  const handleMouseUp = () => {
    isDragging.current = false
  }

  return (
    <div 
      style={{ width: '100vw', height: '100vh', background: 'transparent', position: 'relative' }}
      onMouseDown={handleMouseDown}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
      onMouseLeave={handleMouseUp}
    >
      <Canvas
        camera={{ position: [0, 0.8, 6.5], fov: 30 }}
        style={{ background: 'transparent' }}
        gl={{ alpha: true }}
      >
        <ambientLight intensity={1.0} />
        <directionalLight position={[1, 2, 2]} intensity={1.5} />
        
        <Environment preset="city" />

        <AvatarViewer avatarState={state} />
      </Canvas>
    </div>
  )
}

export default App
