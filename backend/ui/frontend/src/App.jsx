import React from 'react'
import { Canvas } from '@react-three/fiber'
import { OrbitControls, Environment } from '@react-three/drei'
import AvatarViewer from './components/AvatarViewer'
import useAvatarWebSocket from './hooks/useAvatarWebSocket'

function App() {
  const { state } = useAvatarWebSocket('ws://localhost:8000/ws/avatar')

  return (
    <div style={{ width: '100vw', height: '100vh', background: 'transparent', position: 'relative' }}>
      {/* Invisible layer to allow dragging the window */}
      <div className="draggable-area"></div>

      <Canvas
        camera={{ position: [0, 1.3, 3.0], fov: 35 }}
        style={{ background: 'transparent' }}
        gl={{ alpha: true }}
      >
        <ambientLight intensity={0.8} />
        <directionalLight position={[1, 2, 2]} intensity={1.2} />
        
        <Environment preset="city" />

        <AvatarViewer avatarState={state} />
        
        <OrbitControls
          enablePan={false}
          minDistance={1}
          maxDistance={5}
          minPolarAngle={Math.PI / 3}
          maxPolarAngle={Math.PI / 1.5}
          target={[0, 1.4, 0]}
        />
      </Canvas>
    </div>
  )
}

export default App
