import { useRef } from 'react';
import * as THREE from 'three';

export const useAvatarAnimations = (vrm, avatarState) => {
  const timeRef = useRef(0);
  const blinkTimerRef = useRef(0);
  const gazeTimerRef = useRef(0);
  const moodTimerRef = useRef(0);
  const speakingGestureTimerRef = useRef(0);

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

    // =========================================================
    // 1. STATE TRANSITIONS
    // =========================================================

    const lerpSpeed = 1.5;

    states.current.thinking = THREE.MathUtils.lerp(
      states.current.thinking,
      avatarState === 'thinking' ? 1 : 0,
      delta * lerpSpeed
    );

    states.current.listening = THREE.MathUtils.lerp(
      states.current.listening,
      avatarState === 'listening' ? 1 : 0,
      delta * 2.5
    );

    states.current.speaking = THREE.MathUtils.lerp(
      states.current.speaking,
      avatarState === 'speaking' ? 1 : 0,
      delta * 3.0
    );

    // =========================================================
    // 2. MOOD & EMOTION ENGINE
    // =========================================================

    moodTimerRef.current += delta;

    if (moodTimerRef.current > 12) {
      const moods = ['calm', 'happy', 'thoughtful', 'caring'];
      states.current.mood =
        moods[Math.floor(Math.random() * moods.length)];

      moodTimerRef.current = 0;
    }

    states.current.moodIntensity = THREE.MathUtils.lerp(
      states.current.moodIntensity,
      1.0,
      delta * 0.2
    );

    // =========================================================
    // 3. NATURAL HUMAN EYE GAZE SYSTEM
    // =========================================================

    gazeTimerRef.current += delta;

    if (gazeTimerRef.current > (Math.random() * 4 + 4)) {

      // Never look away if speaking, maintain direct eye contact
      const lookAway = avatarState !== 'speaking' && Math.random() > 0.75;

      states.current.gazeTarget.set(
        lookAway
          ? (Math.random() - 0.5) * 0.4
          : (Math.random() - 0.5) * 0.02,

        1.42 + (Math.random() - 0.5) * 0.02,

        lookAway ? 2 : 4
      );

      gazeTimerRef.current = 0;
    }

    // SOFT EYE FOLLOW
    states.current.currentGaze.lerp(
      states.current.gazeTarget,
      delta * 0.65
    );

    // MICRO SACCADES
    const microX = Math.sin(t * 7.5) * 0.003;
    const microY = Math.cos(t * 5.2) * 0.001;

    states.current.currentGaze.x += microX;
    states.current.currentGaze.y += microY;

    vrm.lookAt?.lookAt(states.current.currentGaze);

    // =========================================================
    // 4. NATURAL BREATHING & POSTURE
    // =========================================================

    const breathingCycle = Math.sin(t * 0.8);

    const chest = vrm.humanoid?.getNormalizedBoneNode('chest');
    const spine = vrm.humanoid?.getNormalizedBoneNode('spine');
    const head = vrm.humanoid?.getNormalizedBoneNode('head');

    const leftShoulder =
      vrm.humanoid?.getNormalizedBoneNode('leftShoulder');

    const rightShoulder =
      vrm.humanoid?.getNormalizedBoneNode('rightShoulder');

    const neck =
      vrm.humanoid?.getNormalizedBoneNode('neck');

    if (chest) {

      chest.rotation.x =
        breathingCycle * 0.015 -
        (states.current.listening * 0.2);

      chest.rotation.y =
        Math.sin(t * 0.25) * 0.01;

      // talking chest movement
      chest.rotation.z =
        Math.sin(t * 2.0) *
        0.01 *
        states.current.speaking;
    }

    if (spine) {

      // idle sway
      spine.rotation.y =
        Math.sin(t * 0.2) * 0.01;

      spine.rotation.x = THREE.MathUtils.lerp(
        spine.rotation.x,
        -states.current.listening * 0.02,
        delta * 2
      );

      // talking body movement
      spine.rotation.z =
        Math.sin(t * 1.5) *
        0.01 *
        states.current.speaking;
    }

    if (neck) {

      neck.rotation.y =
        Math.sin(t * 0.5) * 0.01;

      neck.rotation.x =
        Math.cos(t * 0.4) * 0.005;
    }

    if (leftShoulder) {
      leftShoulder.rotation.z =
        Math.sin(t * 0.7) * 0.008;
    }

    if (rightShoulder) {
      rightShoulder.rotation.z =
        -Math.sin(t * 0.7) * 0.008;
    }

    // =========================================================
    // 5. NATURAL BLINK SYSTEM
    // =========================================================

    blinkTimerRef.current += delta;

    if (blinkTimerRef.current > 5) {

      const blinkCycle =
        (blinkTimerRef.current - 5) * 12;

      const blinkVal =
        Math.max(0, Math.sin(blinkCycle));

      vrm.expressionManager?.setValue(
        'blink',
        blinkVal
      );

      if (blinkCycle > Math.PI) {
        blinkTimerRef.current =
          Math.random() * 2;
      }
    }

    // =========================================================
    // 6. HEAD BEHAVIOR
    // =========================================================

    if (head) {

      // smooth damping
      head.rotation.y *= 0.94;
      head.rotation.x *= 0.94;
      head.rotation.z *= 0.94;

      // idle movement
      head.rotation.y +=
        Math.sin(t * 0.25) * 0.006;

      head.rotation.x +=
        Math.cos(t * 0.18) * 0.003;

      const isThinking = states.current.thinking;
      const isListening = states.current.listening;
      const isSpeaking = states.current.speaking;

      // THINKING (Slight side tilt only, no up/down)
      head.rotation.y -= isThinking * 0.005; // slight horizontal turn
      head.rotation.z += isThinking * 0.015; // slight lateral tilt

      // LISTENING
      head.rotation.x -= isListening * 0.02;

      // TALKING HUMAN MOTION (Look Straight)
      if (avatarState === 'speaking') {

        // VERY subtle head bop, but keep head looking straight (No side-to-side shaking)
        head.rotation.y +=
          Math.sin(t * 1.5) *
          0.003;

        head.rotation.x +=
          Math.cos(t * 1.2) *
          0.008;

        head.rotation.z +=
          Math.sin(t * 1.8) *
          0.002;
      }

      // caring emotion
      if (states.current.mood === 'caring') {

        head.rotation.z +=
          Math.sin(t * 0.5) * 0.01;
      }
    }

    // =========================================================
    // 7. ARMS & GESTURES
    // =========================================================

    const rightUpperArm =
      vrm.humanoid?.getNormalizedBoneNode('rightUpperArm');

    const rightLowerArm =
      vrm.humanoid?.getNormalizedBoneNode('rightLowerArm');

    const rightHand =
      vrm.humanoid?.getNormalizedBoneNode('rightHand');

    const leftUpperArm =
      vrm.humanoid?.getNormalizedBoneNode('leftUpperArm');

    const leftLowerArm =
      vrm.humanoid?.getNormalizedBoneNode('leftLowerArm');

    const leftHand =
      vrm.humanoid?.getNormalizedBoneNode('leftHand');

    // =========================================================
    // LEFT ARM IDLE
    // =========================================================

    if (leftUpperArm) {

      leftUpperArm.rotation.z =
        1.4 +
        Math.sin(t * 0.5) * 0.01;

      leftUpperArm.rotation.x =
        Math.sin(t * 0.3) * 0.01;

      leftUpperArm.rotation.y = 0;
    }

    // =========================================================
    // RIGHT ARM IDLE
    // =========================================================

    if (rightUpperArm) {

      rightUpperArm.rotation.z =
        -1.4 -
        Math.sin(t * 0.5) * 0.01;

      rightUpperArm.rotation.x =
        Math.sin(t * 0.3) * 0.01;

      rightUpperArm.rotation.y = 0;
    }


    // =========================================================
    // 8. EXPRESSIONS
    // =========================================================

    vrm.expressionManager?.setValue('happy', 0);
    vrm.expressionManager?.setValue('relaxed', 0);
    vrm.expressionManager?.setValue('surprised', 0);

    const moodIntensity =
      states.current.moodIntensity;

    if (states.current.mood === 'happy') {

      vrm.expressionManager?.setValue(
        'happy',
        0.12 * moodIntensity
      );
    }

    if (avatarState === 'listening') {

      vrm.expressionManager?.setValue(
        'surprised',
        0.05
      );
    }

    // subtle smile during talking
    if (avatarState === 'speaking') {

      vrm.expressionManager?.setValue(
        'happy',
        0.08
      );
    }

    // =========================================================
    // 9. NATURAL LIP SYNC
    // =========================================================

    if (avatarState === 'speaking') {

      const speechPattern =
        Math.sin(t * 5.0) * 0.4 +
        Math.sin(t * 8.0) * 0.2 +
        Math.sin(t * 11.0) * 0.15;

      const mouthOpen =
        THREE.MathUtils.clamp(
          Math.abs(speechPattern),
          0,
          0.65
        );

      vrm.expressionManager?.setValue(
        'aa',
        mouthOpen
      );

      vrm.expressionManager?.setValue(
        'oh',
        mouthOpen * 0.4
      );

      vrm.expressionManager?.setValue(
        'ee',
        mouthOpen * 0.25
      );

    } else {

      vrm.expressionManager?.setValue('aa', 0);
      vrm.expressionManager?.setValue('oh', 0);
      vrm.expressionManager?.setValue('ee', 0);
    }

    // =========================================================
    // 10. BODY WEIGHT SHIFTING
    // =========================================================

    vrm.scene.position.y =
      -0.8 +
      Math.sin(t * 0.5) * 0.004;

    vrm.scene.position.x =
      Math.sin(t * 0.2) * 0.008;

    // subtle speaking bounce
    if (avatarState === 'speaking') {

      vrm.scene.position.y +=
        Math.sin(t * 3.0) * 0.003;
    }

    // Base rotation (Math.PI faces the camera)
    vrm.scene.rotation.y = Math.PI;

    // listening lean
    if (avatarState === 'listening') {
      vrm.scene.rotation.y +=
        Math.sin(t * 0.5) * 0.02;
    }

    // =========================================================
    // FINAL VRM UPDATE
    // =========================================================

    vrm.update(delta);
  };

  return { update };
};