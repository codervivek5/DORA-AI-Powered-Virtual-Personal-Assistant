import React, { useEffect, useRef, useState } from 'react'
import { useFrame, useLoader } from '@react-three/fiber'
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader'
import { VRMLoaderPlugin } from '@pixiv/three-vrm'
import { Html } from '@react-three/drei'
import * as THREE from 'three'
import { useAvatarAnimations } from '../hooks/useAvatarAnimations'

export default function AvatarViewer({ avatarState }) {
  const [vrm, setVrm] = useState(null)
  const [error, setError] = useState(null)
  const [progress, setProgress] = useState(0)
  const currentVrmRef = useRef(null)

  // Initialize enhanced animation hook
  const { update } = useAvatarAnimations(vrm, avatarState)

  useEffect(() => {
    // Load the VRM Avatar
    const loader = new GLTFLoader()
    loader.crossOrigin = 'anonymous'

    loader.register((parser) => {
      return new VRMLoaderPlugin(parser)
    })

    loader.load(
      '/avatar.vrm',
      (gltf) => {
        const vrmData = gltf.userData.vrm
        if (vrmData) {
          vrmData.scene.rotation.y = Math.PI
          vrmData.scene.position.y = -0.8 
          setVrm(vrmData)
          currentVrmRef.current = vrmData
        }
      },
      (progressEvent) => {
        const p = Math.floor(100.0 * (progressEvent.loaded / progressEvent.total))
        setProgress(p)
      },
      (error) => {
        console.error('Error loading VRM:', error)
        setError('Missing /avatar.vrm')
      }
    )

    return () => {
      if (currentVrmRef.current) {
        currentVrmRef.current.scene.parent?.remove(currentVrmRef.current.scene)
        currentVrmRef.current.dispose()
      }
    }
  }, [])

  // Use the animation hook inside the Three.js render loop
  useFrame((state, delta) => {
    if (vrm) {
      update(delta)
      
      // 11. CINEMATIC CAMERA (Fluid Drift)
      const t = state.clock.getElapsedTime()
      state.camera.position.x = Math.sin(t * 0.22) * 0.015
      state.camera.position.y = Math.cos(t * 0.18) * 0.008
      state.camera.position.z = 3.17 + Math.sin(t * 0.12) * 0.015
      state.camera.lookAt(0, 0, 0)
    }
  })

  if (error) {
    return (
      <mesh position={[0, 1.4, 0]}>
        <boxGeometry args={[0.3, 0.3, 0.3]} />
        <meshStandardMaterial color="red" />
      </mesh>
    )
  }

  if (!vrm) {
    return (
      <Html center>
        <div style={{ 
          color: '#00D4FF', 
          fontWeight: 'bold', 
          background: 'rgba(0,0,0,0.5)', 
          padding: '10px 20px', 
          borderRadius: '20px',
          backdropFilter: 'blur(5px)'
        }}>
          Loading Jenny {progress}%
        </div>
      </Html>
    )
  }

  return <primitive object={vrm.scene} />
}
