import { useRef } from 'react';
import * as THREE from 'three';

export const useAvatarAnimations = (vrm, avatarState) => {
  const timeRef = useRef(0);
  const blinkTimerRef = useRef(0);
  const gazeTimerRef = useRef(0);
  const moodTimerRef = useRef(0);

  // Refs for smooth state management
  const states = useRef({
    thinking: 0,
    listening: 0,
    speaking: 0,
    mood: 'calm',
    moodIntensity: 0,
    gazeTarget: new THREE.Vector3(0, 1.42, 4),
    currentGaze: new THREE.Vector3(0, 1.42, 4),
  });

  const update = (delta) => {
    if (!vrm) return;

    timeRef.current += delta;
    const t = timeRef.current;

    // 1. STATE TRANSITIONS
    const lerpSpeed = 1.5;
    states.current.thinking = THREE.MathUtils.lerp(states.current.thinking, avatarState === 'thinking' ? 1 : 0, delta * lerpSpeed);
    states.current.listening = THREE.MathUtils.lerp(states.current.listening, avatarState === 'listening' ? 1 : 0, delta * 2.5);
    states.current.speaking = THREE.MathUtils.lerp(states.current.speaking, avatarState === 'speaking' ? 1 : 0, delta * 3.0);

    // 2. MOOD & EMOTION ENGINE
    moodTimerRef.current += delta;
    if (moodTimerRef.current > 12) {
      const moods = ['calm', 'happy', 'thoughtful', 'caring'];
      states.current.mood = moods[Math.floor(Math.random() * moods.length)];
      moodTimerRef.current = 0;
    }
    states.current.moodIntensity = THREE.MathUtils.lerp(states.current.moodIntensity, 1.0, delta * 0.2);

    // =========================================================
    // NATURAL HUMAN EYE GAZE SYSTEM
    // =========================================================
    gazeTimerRef.current += delta;
    if (gazeTimerRef.current > (Math.random() * 4 + 4)) {
      const lookAway = Math.random() > 0.75;
      states.current.gazeTarget.set(
        lookAway ? (Math.random() - 0.5) * 0.4 : (Math.random() - 0.5) * 0.02,
        1.42 + (Math.random() - 0.5) * 0.02,
        lookAway ? 2 : 4
      );
      gazeTimerRef.current = 0;
    }

    // SOFT EYE FOLLOW
    states.current.currentGaze.lerp(states.current.gazeTarget, delta * 0.65);

    // MICRO SACCADES (Ultra-subtle for stability)
    const microX = Math.sin(t * 7.5) * 0.003;
    const microY = Math.cos(t * 5.2) * 0.001;
    states.current.currentGaze.x += microX;
    states.current.currentGaze.y += microY;

    vrm.lookAt?.lookAt(states.current.currentGaze);

    // 4. NATURAL BREATHING & POSTURE
    const breathingCycle = Math.sin(t * 0.8);
    const chest = vrm.humanoid?.getNormalizedBoneNode('chest');
    const spine = vrm.humanoid?.getNormalizedBoneNode('spine');
    const head = vrm.humanoid?.getNormalizedBoneNode('head');
    const leftShoulder = vrm.humanoid?.getNormalizedBoneNode('leftShoulder');
    const rightShoulder = vrm.humanoid?.getNormalizedBoneNode('rightShoulder');

    if (chest) chest.rotation.x = breathingCycle * 0.015 + (states.current.listening * 0.04);
    if (spine) {
        spine.rotation.y = Math.sin(t * 0.2) * 0.01;
        spine.rotation.x = THREE.MathUtils.lerp(spine.rotation.x, states.current.listening * 0.04, delta * 2);
    }
    if (leftShoulder) leftShoulder.rotation.z = Math.sin(t * 0.7) * 0.008;
    if (rightShoulder) rightShoulder.rotation.z = -Math.sin(t * 0.7) * 0.008;

    // =========================================================
    // NATURAL BLINK SYSTEM (Fixed Fast Blinking)
    // =========================================================
    blinkTimerRef.current += delta;
    // Longer interval between blinks (3-7 seconds)
    if (blinkTimerRef.current > 5) {
      const blinkCycle = (blinkTimerRef.current - 5) * 12; // Controlled speed
      const blinkVal = Math.max(0, Math.sin(blinkCycle));
      
      vrm.expressionManager?.setValue('blink', blinkVal);
      
      if (blinkCycle > Math.PI) {
        blinkTimerRef.current = Math.random() * 2; // Reset with random offset to prevent mechanical feel
      }
    }

    // =========================================================
    // HEAD BEHAVIOR
    // =========================================================
    if (head) {
      // reset slight drift
      head.rotation.y *= 0.94;
      head.rotation.x *= 0.94;
      head.rotation.z *= 0.94;

      // idle micro movement
      head.rotation.y += Math.sin(t * 0.25) * 0.006;
      head.rotation.x += Math.cos(t * 0.18) * 0.003;

      // thinking tilt
      head.rotation.x += states.current.thinking * 0.06;

      // caring emotional tilt
      if (states.current.mood === 'caring') {
        head.rotation.z += Math.sin(t * 0.5) * 0.01;
      }

      // speaking movement
      if (avatarState === 'speaking') {
        head.rotation.y += Math.sin(t * 1.5) * 0.01;
        head.rotation.x += Math.cos(t * 1.2) * 0.005;
      }
    }

    // 7. ARMS & GESTURES
    const rightUpperArm = vrm.humanoid?.getNormalizedBoneNode('rightUpperArm');
    const rightLowerArm = vrm.humanoid?.getNormalizedBoneNode('rightLowerArm');
    const leftUpperArm = vrm.humanoid?.getNormalizedBoneNode('leftUpperArm');
    
    if (leftUpperArm) leftUpperArm.rotation.z = 1.4 + Math.sin(t * 0.5) * 0.01;
    if (rightUpperArm && rightLowerArm) {
        const isThinking = states.current.thinking;
        rightUpperArm.rotation.z = THREE.MathUtils.lerp(-1.4, -1.1, isThinking);
        rightUpperArm.rotation.x = THREE.MathUtils.lerp(Math.sin(t * 0.5) * 0.01, -0.4, isThinking);
        rightLowerArm.rotation.x = THREE.MathUtils.lerp(0, -1.0, isThinking);
    }

    // 8. EXPRESSIONS (Brightness Fix)
    vrm.expressionManager?.setValue('happy', 0);
    vrm.expressionManager?.setValue('relaxed', 0);
    vrm.expressionManager?.setValue('surprised', 0);

    const moodIntensity = states.current.moodIntensity;
    if (states.current.mood === 'happy') vrm.expressionManager?.setValue('happy', 0.1 * moodIntensity);
    // Removed 'relaxed' from caring to keep eyes open
    if (avatarState === 'listening') vrm.expressionManager?.setValue('surprised', 0.05);

    // =========================================================
    // NATURAL LIP SYNC
    // =========================================================
    if (avatarState === 'speaking') {
      const speechPattern = Math.sin(t * 5.0) * 0.4 + Math.sin(t * 8.0) * 0.2;
      const mouthOpen = THREE.MathUtils.clamp(Math.abs(speechPattern), 0, 0.6);
      vrm.expressionManager?.setValue('aa', mouthOpen);
      // Keep eyes bright even when talking
      vrm.expressionManager?.setValue('relaxed', 0); 
    } else {
      vrm.expressionManager?.setValue('aa', 0);
    }

    // 10. BODY WEIGHT SHIFTING
    vrm.scene.position.y = -0.8 + Math.sin(t * 0.5) * 0.004;
    vrm.scene.position.x = Math.sin(t * 0.2) * 0.008;
    
    vrm.update(delta);
  };

  return { update };
};