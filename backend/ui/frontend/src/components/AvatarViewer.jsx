import React, { useEffect, useRef, useState } from 'react'
import { useFrame, useLoader } from '@react-three/fiber'
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader'
import { VRMLoaderPlugin } from '@pixiv/three-vrm'
import { Html } from '@react-three/drei'
import * as THREE from 'three'

export default function AvatarViewer({ avatarState }) {
  const [vrm, setVrm] = useState(null)
  const [error, setError] = useState(null)
  const [progress, setProgress] = useState(0)
  const currentVrmRef = useRef(null)

  // Load fallback texture (PNG)
  const texture = useLoader(THREE.TextureLoader, '/avatar.png')

  // Animation variables
  const timeRef = useRef(0)
  const blinkTimerRef = useRef(0)

  useEffect(() => {
    // Load the VRM Avatar
    const loader = new GLTFLoader()
    loader.crossOrigin = 'anonymous'

    loader.register((parser) => {
      return new VRMLoaderPlugin(parser)
    })

    // Load from the public directory. The user must provide this file.
    loader.load(
      '/avatar.vrm',
      (gltf) => {
        const vrmData = gltf.userData.vrm
        if (vrmData) {
          // Center the 1.5m character vertically (head to toe)
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
        setError('Missing /avatar_anime.vrm')
      }
    )

    return () => {
      if (currentVrmRef.current) {
        currentVrmRef.current.scene.parent?.remove(currentVrmRef.current.scene)
        currentVrmRef.current.dispose()
      }
    }
  }, [])

  useFrame((state, delta) => {
    if (!vrm) return

    timeRef.current += delta
    blinkTimerRef.current += delta

    // 1. Core Physics & VRM Updates
    vrm.update(delta)

    // Reset expressions to neutral every frame before applying new ones
    vrm.expressionManager?.setValue('blink', 0)
    vrm.expressionManager?.setValue('aa', 0)
    vrm.expressionManager?.setValue('ih', 0)
    vrm.expressionManager?.setValue('ou', 0)

    // 2. State-Based Animations
    const s = Math.sin(timeRef.current * 2) // Common sine wave for breathing

    // Base Idle / Breathing (always active slightly)
    const chest = vrm.humanoid?.getNormalizedBoneNode('chest')
    if (chest) {
      chest.rotation.x = Math.sin(timeRef.current * 1.5) * 0.02
    }

    // Set a natural A-pose (Arms down)
    const leftUpperArm = vrm.humanoid?.getNormalizedBoneNode('leftUpperArm')
    const rightUpperArm = vrm.humanoid?.getNormalizedBoneNode('rightUpperArm')
    if (leftUpperArm) leftUpperArm.rotation.z = 1.3
    if (rightUpperArm) rightUpperArm.rotation.z = -1.3

    // Blinking logic (Random blink every 3-5 seconds)
    if (blinkTimerRef.current > 4) {
      const blinkValue = Math.sin((blinkTimerRef.current - 4) * Math.PI * 4) // Fast sine wave
      if (blinkValue > 0) {
        vrm.expressionManager?.setValue('blink', blinkValue)
      } else {
        blinkTimerRef.current = Math.random() * 2 // Reset timer with random offset
      }
    }

    // Apply specific states
    if (avatarState === 'listening') {
      // Lean forward slightly
      const spine = vrm.humanoid?.getNormalizedBoneNode('spine')
      if (spine) spine.rotation.x = THREE.MathUtils.lerp(spine.rotation.x, 0.1, 0.1)
      
      // Slight head tilt
      const head = vrm.humanoid?.getNormalizedBoneNode('head')
      if (head) head.rotation.y = Math.sin(timeRef.current * 0.5) * 0.05
    } 
    else if (avatarState === 'thinking') {
      // Look up and tilt head
      const head = vrm.humanoid?.getNormalizedBoneNode('head')
      if (head) {
        head.rotation.x = THREE.MathUtils.lerp(head.rotation.x, -0.1, 0.1)
        head.rotation.z = THREE.MathUtils.lerp(head.rotation.z, 0.05, 0.1)
      }
    } 
    else if (avatarState === 'speaking') {
      // Simulated Lip Sync using amplitude of a sine wave
      const talkSpeed = 15
      const amplitude = Math.abs(Math.sin(timeRef.current * talkSpeed))
      
      // Randomly choose vowel shapes for varied talking
      const vowelShapes = ['aa', 'ih', 'ou']
      const activeVowel = vowelShapes[Math.floor((timeRef.current * 5) % vowelShapes.length)]
      
      vrm.expressionManager?.setValue(activeVowel, amplitude * 0.8)
    }

    // Return bones to neutral if not in specific states
    if (avatarState !== 'listening' && avatarState !== 'thinking') {
      const spine = vrm.humanoid?.getNormalizedBoneNode('spine')
      if (spine) spine.rotation.x = THREE.MathUtils.lerp(spine.rotation.x, 0, 0.1)
      
      const head = vrm.humanoid?.getNormalizedBoneNode('head')
      if (head) {
        head.rotation.x = THREE.MathUtils.lerp(head.rotation.x, 0, 0.1)
        head.rotation.z = THREE.MathUtils.lerp(head.rotation.z, 0, 0.1)
        head.rotation.y = THREE.MathUtils.lerp(head.rotation.y, 0, 0.1)
      }
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
        <div style={{ color: '#00D4FF', fontWeight: 'bold' }}>
          Loading {progress}%
        </div>
      </Html>
    )
  }

  return <primitive object={vrm.scene} />
}
