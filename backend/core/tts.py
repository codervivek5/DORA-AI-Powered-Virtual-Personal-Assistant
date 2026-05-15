import os
import wave
import tempfile
import warnings
import sounddevice as sd
import numpy as np
import requests
import base64
from sarvamai import SarvamAI
from typing import Tuple, Optional, Any
from loguru import logger
from config.settings import settings

# Try to import Sarvam AI SDK
try:
    SARVAM_SDK_AVAILABLE = True
except ImportError:
    SARVAM_SDK_AVAILABLE = False

# Suppress verbose warnings
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)


class TTSProvider:
    """TTS Provider supporting multiple engines (Sarvam AI, F5, etc.)"""

    def __init__(self):
        self.provider = settings.TTS_PROVIDER.lower()
        self.api_key = settings.SARVAM_API_KEY or os.getenv("SARVAM_API_KEY")

        # Initialize Sarvam Client if available
        self.sarvam_client: Any = None
        if self.provider == "sarvam" and SARVAM_SDK_AVAILABLE and self.api_key:
            try:
                self.sarvam_client = SarvamAI(api_subscription_key=self.api_key)
                logger.info("Sarvam SDK initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Sarvam SDK: {e}. Will use REST API fallback.")

        logger.info(f"🔊 TTS Provider initialized: {self.provider.upper()}")

    def _get_audio_sarvam(self, text: str) -> Tuple[Optional[np.ndarray], int]:
        """Fetch audio from Sarvam AI TTS (v1 or v2/SDK)"""
        if not self.api_key:
            logger.error("SARVAM_API_KEY not set")
            return None, 16000

        # Try SDK first if available
        if self.sarvam_client is not None:
            try:
                response = self.sarvam_client.text_to_speech.convert(
                    text=text,
                    target_language_code="hi-IN"
                )

                audio_bytes = None
                if isinstance(response, dict):
                    audio_base64 = response.get("audios", [None])[0] or response.get("audio")
                    if audio_base64:
                        audio_bytes = base64.b64decode(audio_base64)
                elif hasattr(response, "audios") and response.audios:
                    audio_val = response.audios[0]
                    audio_bytes = base64.b64decode(audio_val) if isinstance(audio_val, str) else audio_val
                elif hasattr(response, "audio"):
                    audio_val = response.audio
                    audio_bytes = base64.b64decode(audio_val) if isinstance(audio_val, str) else audio_val

                if audio_bytes and isinstance(audio_bytes, (bytes, bytearray)):
                    return self._bytes_to_audio_data(audio_bytes)
                else:
                    logger.warning(f"Unexpected SDK response type: {type(response)}. Trying REST API...")
            except Exception as e:
                logger.warning(f"Sarvam SDK call failed: {e}. Trying REST API fallback...")

        # REST API Fallback (v3/v2)
        url = "https://api.sarvam.ai/text-to-speech"
        payload = {
            "inputs": [text],
            "target_language_code": "hi-IN",
            "speaker_gender": settings.SARVAM_VOICE,
            "model": settings.SARVAM_MODEL
        }
        headers = {
            "api-subscription-key": self.api_key,
            "Content-Type": "application/json"
        }

        try:
            response = requests.post(url, json=payload, headers=headers)
            if response.status_code == 200:
                data = response.json()
                audio_base64 = data.get("audios", [None])[0] or data.get("audio")
                if audio_base64:
                    audio_bytes = base64.b64decode(audio_base64)
                    return self._bytes_to_audio_data(audio_bytes)
            else:
                logger.error(f"Sarvam API error {response.status_code}: {response.text}")
        except Exception as e:
            logger.error(f"Sarvam REST API error: {e}")

        return None, 16000

    def _bytes_to_audio_data(self, audio_bytes: Any) -> Tuple[Optional[np.ndarray], int]:
        """Convert wav bytes to numpy float array and detect sample rate"""
        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
                tmp_file.write(audio_bytes)
                tmp_path = tmp_file.name

            try:
                with wave.open(tmp_path, 'rb') as wav_file:
                    n_channels = wav_file.getnchannels()
                    sample_width = wav_file.getsampwidth()
                    sample_rate = wav_file.getframerate()
                    frames = wav_file.readframes(wav_file.getnframes())

                    if sample_width == 2:
                        audio_data = np.frombuffer(frames, dtype=np.int16).astype('float32') / 32768.0
                    else:
                        audio_data = np.frombuffer(frames, dtype=np.uint8).astype('float32') / 255.0

                    if n_channels > 1:
                        audio_data = audio_data.reshape(-1, n_channels).mean(axis=1)

                    return audio_data, sample_rate
            except Exception as inner_e:
                logger.error(f"Wave opening error: {inner_e}")
                return None, 16000
            finally:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)

        except Exception as e:
            logger.error(f"Error converting bytes to audio: {e}")
            return None, 16000

    def speak(self, text: str) -> bool:
        if not text or not text.strip():
            return False

        try:
            logger.info(f"🎤 Generating speech: {text[:50]}...")

            audio_data = None
            sample_rate = 16000  # Default fallback

            if self.provider == "sarvam":
                audio_data, sample_rate = self._get_audio_sarvam(text)
            elif self.provider == "f5":
                logger.warning("F5-TTS local provider not fully implemented. Falling back to simple console print.")
                print(f"🔊 AI: {text}")
                return True
            else:
                logger.error(f"Unsupported TTS provider: {self.provider}")
                return False

            if audio_data is None:
                logger.error("Failed to generate audio data")
                return False

            # Normalize
            max_val = np.max(np.abs(audio_data))
            if max_val > 1.0:
                audio_data = audio_data / max_val
            elif max_val == 0:
                return False

            # ==========================================
            # HIGHLIGHT: FIXED STABLE AUDIO PLAYBACK
            # ==========================================
            try:
                # 1. Stop any currently active or hanging audio channels before starting a new one
                sd.stop()

                # 2. Make sure the numpy array structure is continuous in memory (Crucial for macOS CoreAudio wrappers)
                audio_data = np.ascontiguousarray(audio_data)

                # 3. Stream data into sounddevice
                sd.play(audio_data, samplerate=sample_rate)
                sd.wait()  # Block until the text playback finishes safely

                logger.success("Playback completed")
                return True
            except Exception as playback_error:
                logger.error(f"SoundDevice Playback error: {playback_error}")
                return False
            # ==========================================

        except Exception as e:
            logger.error(f"TTS Error: {e}")
            return False


# Global instance
tts_provider = TTSProvider()

if __name__ == "__main__":
    import sys

    test_text = "नमस्ते, मैं आपकी कैसे मदद कर सकता हूँ?" if len(sys.argv) < 2 else sys.argv[1]
    tts_provider.speak(test_text)