import { useRef } from 'react';
import * as THREE from 'three';

export const useAvatarAnimations = (vrm, avatarState) => {
  const timeRef = useRef(0);
  const blinkTimerRef = useRef(0);
  const gazeTimerRef = useRef(0);
  const moodTimerRef = useRef(0);
  const thinkTiltRef = useRef(0);    // tracks which direction she tilts while thinking
  const thinkTiltTimer = useRef(0);  // timer to switch tilt direction

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
      states.current.mood = moods[Math.floor(Math.random() * moods.length)];
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
      // Never look away while speaking — maintain direct eye contact
      const lookAway = avatarState !== 'speaking' && Math.random() > 0.75;

      states.current.gazeTarget.set(
        lookAway ? (Math.random() - 0.5) * 0.35 : (Math.random() - 0.5) * 0.02,
        1.42 + (Math.random() - 0.5) * 0.02,
        lookAway ? 2 : 4
      );

      gazeTimerRef.current = 0;
    }

    // Soft eye follow
    states.current.currentGaze.lerp(states.current.gazeTarget, delta * 0.65);

    // Micro saccades (ultra subtle)
    states.current.currentGaze.x += Math.sin(t * 7.5) * 0.002;
    states.current.currentGaze.y += Math.cos(t * 5.2) * 0.001;

    vrm.lookAt?.lookAt(states.current.currentGaze);

    // =========================================================
    // 4. NATURAL BREATHING & POSTURE
    // =========================================================

    const breathingCycle = Math.sin(t * 0.75);   // ~0.75 Hz - natural resting breath rate
    const breathingSlow  = Math.sin(t * 0.35);   // very slow full-body sway

    const chest      = vrm.humanoid?.getNormalizedBoneNode('chest');
    const upperChest = vrm.humanoid?.getNormalizedBoneNode('upperChest');
    const spine      = vrm.humanoid?.getNormalizedBoneNode('spine');
    const hips       = vrm.humanoid?.getNormalizedBoneNode('hips');
    const head       = vrm.humanoid?.getNormalizedBoneNode('head');
    const neck       = vrm.humanoid?.getNormalizedBoneNode('neck');

    const leftShoulder  = vrm.humanoid?.getNormalizedBoneNode('leftShoulder');
    const rightShoulder = vrm.humanoid?.getNormalizedBoneNode('rightShoulder');

    // Legs & Feet
    const leftUpperLeg  = vrm.humanoid?.getNormalizedBoneNode('leftUpperLeg');
    const rightUpperLeg = vrm.humanoid?.getNormalizedBoneNode('rightUpperLeg');
    const leftLowerLeg  = vrm.humanoid?.getNormalizedBoneNode('leftLowerLeg');
    const rightLowerLeg = vrm.humanoid?.getNormalizedBoneNode('rightLowerLeg');
    const leftFoot      = vrm.humanoid?.getNormalizedBoneNode('leftFoot');
    const rightFoot     = vrm.humanoid?.getNormalizedBoneNode('rightFoot');

    // Arms
    const rightUpperArm = vrm.humanoid?.getNormalizedBoneNode('rightUpperArm');
    const rightLowerArm = vrm.humanoid?.getNormalizedBoneNode('rightLowerArm');
    const rightHand     = vrm.humanoid?.getNormalizedBoneNode('rightHand');
    const leftUpperArm  = vrm.humanoid?.getNormalizedBoneNode('leftUpperArm');
    const leftLowerArm  = vrm.humanoid?.getNormalizedBoneNode('leftLowerArm');
    const leftHand      = vrm.humanoid?.getNormalizedBoneNode('leftHand');

    const isThinking = states.current.thinking;
    const isListening = states.current.listening;
    const isSpeaking  = states.current.speaking;

    // =========================================================
    // HIPS — weight shift, the root of all natural movement
    // =========================================================
    if (hips) {
      // subtle weight shift side to side (idle body sway)
      hips.rotation.z = THREE.MathUtils.lerp(
        hips.rotation.z,
        Math.sin(t * 0.38) * 0.018,
        delta * 1.5
      );
      // slight front/back balance
      hips.rotation.x = THREE.MathUtils.lerp(
        hips.rotation.x,
        Math.cos(t * 0.45) * 0.005,
        delta * 1.0
      );
    }

    // =========================================================
    // SPINE — breathing and gentle idle sway
    // =========================================================
    if (spine) {
      spine.rotation.x = THREE.MathUtils.lerp(
        spine.rotation.x,
        breathingCycle * 0.012 - isListening * 0.015,
        delta * 2.5
      );
      spine.rotation.y = THREE.MathUtils.lerp(
        spine.rotation.y,
        Math.sin(t * 0.22) * 0.008,
        delta * 1.5
      );
      spine.rotation.z = THREE.MathUtils.lerp(
        spine.rotation.z,
        -Math.sin(t * 0.38) * 0.012, // counter the hip sway slightly
        delta * 1.5
      );
    }

    // =========================================================
    // CHEST — breathing is most visible here
    // =========================================================
    if (chest) {
      chest.rotation.x = THREE.MathUtils.lerp(
        chest.rotation.x,
        breathingCycle * 0.018 - isListening * 0.01,
        delta * 3.0
      );
      chest.rotation.y = THREE.MathUtils.lerp(
        chest.rotation.y,
        Math.sin(t * 0.25) * 0.007,
        delta * 1.5
      );
      chest.rotation.z = THREE.MathUtils.lerp(
        chest.rotation.z,
        Math.sin(t * 2.0) * 0.008 * isSpeaking,
        delta * 3.0
      );
    }

    // =========================================================
    // UPPER CHEST / NECK
    // =========================================================
    if (upperChest) {
      upperChest.rotation.x = breathingCycle * 0.008;
    }

    if (neck) {
      neck.rotation.y = Math.sin(t * 0.45) * 0.008;
      neck.rotation.x = Math.cos(t * 0.35) * 0.004;
    }

    // =========================================================
    // SHOULDERS — subtle breathing shrug
    // =========================================================
    if (leftShoulder) {
      leftShoulder.rotation.z  = Math.sin(t * 0.75) * 0.007;
      leftShoulder.rotation.x  = breathingCycle * 0.005;
    }
    if (rightShoulder) {
      rightShoulder.rotation.z = -Math.sin(t * 0.75) * 0.007;
      rightShoulder.rotation.x = breathingCycle * 0.005;
    }

    // =========================================================
    // 5. NATURAL BLINK SYSTEM
    // =========================================================

    blinkTimerRef.current += delta;

    if (blinkTimerRef.current > 5) {
      const blinkCycle = (blinkTimerRef.current - 5) * 12;
      const blinkVal = Math.max(0, Math.sin(blinkCycle));
      vrm.expressionManager?.setValue('blink', blinkVal);

      if (blinkCycle > Math.PI) {
        blinkTimerRef.current = Math.random() * 2;
      }
    }

    // =========================================================
    // 6. HEAD BEHAVIOR
    // =========================================================

    if (head) {
      // Smooth decay — prevents accumulation drift
      head.rotation.y *= 0.92;
      head.rotation.x *= 0.92;
      head.rotation.z *= 0.92;

      // Idle micro movement — alive, breathing feel
      head.rotation.y += Math.sin(t * 0.28) * 0.005;
      head.rotation.x += Math.cos(t * 0.20) * 0.003;

      // LISTENING — very slight forward nod attention
      head.rotation.x -= isListening * 0.012;

      // THINKING — slow pendulum tilt left/right (no up/down)
      if (avatarState === 'thinking') {
        thinkTiltTimer.current += delta;
        if (thinkTiltTimer.current > 3.5) {
          thinkTiltRef.current = -thinkTiltRef.current || 1;
          thinkTiltTimer.current = 0;
        }
      } else {
        thinkTiltTimer.current = 0;
        thinkTiltRef.current = 0;
      }
      // Apply smooth tilt toward the current direction
      const tiltTarget = thinkTiltRef.current * 0.12 * isThinking;
      head.rotation.z = THREE.MathUtils.lerp(head.rotation.z, tiltTarget, delta * 1.2);

      // SPEAKING — very subtle alive head movement, eyes forward
      if (avatarState === 'speaking') {
        head.rotation.y += Math.sin(t * 1.4) * 0.003;
        head.rotation.x += Math.cos(t * 1.1) * 0.005;
      }

      // Caring mood — gentle tilt
      if (states.current.mood === 'caring') {
        head.rotation.z += Math.sin(t * 0.5) * 0.008;
      }
    }

    // =========================================================
    // 7. ARMS — idle only, no gestures
    // =========================================================

    // Left arm — gently hanging, breathing sway
    if (leftUpperArm) {
      leftUpperArm.rotation.z = THREE.MathUtils.lerp(
        leftUpperArm.rotation.z,
        1.35 + breathingCycle * 0.012,
        delta * 2.5
      );
      leftUpperArm.rotation.x = THREE.MathUtils.lerp(
        leftUpperArm.rotation.x,
        Math.sin(t * 0.38) * 0.008,
        delta * 2.0
      );
      leftUpperArm.rotation.y = THREE.MathUtils.lerp(
        leftUpperArm.rotation.y,
        Math.sin(t * 0.3) * 0.005,
        delta * 2.0
      );
    }

    if (leftLowerArm) {
      leftLowerArm.rotation.x = THREE.MathUtils.lerp(
        leftLowerArm.rotation.x,
        Math.sin(t * 0.42) * 0.01,
        delta * 2.0
      );
      leftLowerArm.rotation.y = 0;
      leftLowerArm.rotation.z = 0;
    }

    if (leftHand) {
      leftHand.rotation.x = THREE.MathUtils.lerp(
        leftHand.rotation.x,
        Math.cos(t * 0.5) * 0.007,
        delta * 2.0
      );
      leftHand.rotation.y = 0;
      leftHand.rotation.z = 0;
    }

    // Right arm — mirror of left arm, opposite phase
    if (rightUpperArm) {
      rightUpperArm.rotation.z = THREE.MathUtils.lerp(
        rightUpperArm.rotation.z,
        -1.35 - breathingCycle * 0.012,
        delta * 2.5
      );
      rightUpperArm.rotation.x = THREE.MathUtils.lerp(
        rightUpperArm.rotation.x,
        -Math.sin(t * 0.38) * 0.008,
        delta * 2.0
      );
      rightUpperArm.rotation.y = THREE.MathUtils.lerp(
        rightUpperArm.rotation.y,
        -Math.sin(t * 0.3) * 0.005,
        delta * 2.0
      );
    }

    if (rightLowerArm) {
      rightLowerArm.rotation.x = THREE.MathUtils.lerp(
        rightLowerArm.rotation.x,
        -Math.sin(t * 0.42) * 0.01,
        delta * 2.0
      );
      rightLowerArm.rotation.y = 0;
      rightLowerArm.rotation.z = 0;
    }

    if (rightHand) {
      rightHand.rotation.x = THREE.MathUtils.lerp(
        rightHand.rotation.x,
        -Math.cos(t * 0.5) * 0.007,
        delta * 2.0
      );
      rightHand.rotation.y = 0;
      rightHand.rotation.z = 0;
    }

    // =========================================================
    // 8. LEGS & FEET — natural micro weight shift
    // =========================================================

    // Weight-bearing foot micro-rotation (left foot carries more weight half the time)
    const weightPhase = Math.sin(t * 0.35);  // very slow ~0.35Hz shift

    if (leftUpperLeg) {
      leftUpperLeg.rotation.x = THREE.MathUtils.lerp(
        leftUpperLeg.rotation.x,
        weightPhase * 0.012,   // slight forward/back tilt
        delta * 1.0
      );
      leftUpperLeg.rotation.z = THREE.MathUtils.lerp(
        leftUpperLeg.rotation.z,
        weightPhase * 0.01,    // slight adduction
        delta * 1.0
      );
    }

    if (rightUpperLeg) {
      rightUpperLeg.rotation.x = THREE.MathUtils.lerp(
        rightUpperLeg.rotation.x,
        -weightPhase * 0.012,  // opposite phase
        delta * 1.0
      );
      rightUpperLeg.rotation.z = THREE.MathUtils.lerp(
        rightUpperLeg.rotation.z,
        -weightPhase * 0.01,
        delta * 1.0
      );
    }

    if (leftLowerLeg) {
      leftLowerLeg.rotation.x = THREE.MathUtils.lerp(
        leftLowerLeg.rotation.x,
        Math.max(0, weightPhase) * 0.008,  // slight knee bend when bearing weight
        delta * 1.0
      );
    }

    if (rightLowerLeg) {
      rightLowerLeg.rotation.x = THREE.MathUtils.lerp(
        rightLowerLeg.rotation.x,
        Math.max(0, -weightPhase) * 0.008,
        delta * 1.0
      );
    }

    // Foot micro rock — toes rise very slightly on the non-weight side
    if (leftFoot) {
      leftFoot.rotation.x = THREE.MathUtils.lerp(
        leftFoot.rotation.x,
        -Math.max(0, -weightPhase) * 0.025, // slight toe-up on off-weight foot
        delta * 1.5
      );
    }

    if (rightFoot) {
      rightFoot.rotation.x = THREE.MathUtils.lerp(
        rightFoot.rotation.x,
        -Math.max(0, weightPhase) * 0.025,
        delta * 1.5
      );
    }

    // =========================================================
    // 9. EXPRESSIONS
    // =========================================================

    vrm.expressionManager?.setValue('happy', 0);
    vrm.expressionManager?.setValue('relaxed', 0);
    vrm.expressionManager?.setValue('surprised', 0);

    const moodIntensity = states.current.moodIntensity;

    if (states.current.mood === 'happy') {
      vrm.expressionManager?.setValue('happy', 0.12 * moodIntensity);
    }

    if (avatarState === 'listening') {
      vrm.expressionManager?.setValue('surprised', 0.05);
    }

    if (avatarState === 'speaking') {
      vrm.expressionManager?.setValue('happy', 0.08);
    }

    // =========================================================
    // 10. NATURAL LIP SYNC
    // =========================================================

    if (avatarState === 'speaking') {
      const speechPattern =
        Math.sin(t * 5.0) * 0.4 +
        Math.sin(t * 8.0) * 0.2 +
        Math.sin(t * 11.0) * 0.15;

      const mouthOpen = THREE.MathUtils.clamp(Math.abs(speechPattern), 0, 0.65);

      vrm.expressionManager?.setValue('aa', mouthOpen);
      vrm.expressionManager?.setValue('oh', mouthOpen * 0.4);
      vrm.expressionManager?.setValue('ee', mouthOpen * 0.25);
    } else {
      vrm.expressionManager?.setValue('aa', 0);
      vrm.expressionManager?.setValue('oh', 0);
      vrm.expressionManager?.setValue('ee', 0);
    }

    // =========================================================
    // 11. SCENE POSITION & ROTATION (Root transform)
    // =========================================================

    // Very slight idle breathing bob on scene root
    vrm.scene.position.y = -0.8 + Math.sin(t * 0.75) * 0.003;

    // Tiny weight shift along X
    vrm.scene.position.x = Math.sin(t * 0.35) * 0.005;

    // Base rotation — Math.PI makes her face the camera
    vrm.scene.rotation.y = Math.PI;

    // =========================================================
    // FINAL VRM UPDATE
    // =========================================================

    vrm.update(delta);
  };

  return { update };
};