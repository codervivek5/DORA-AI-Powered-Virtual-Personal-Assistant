import time
import os
import wave
import tempfile
import warnings
import asyncio
import sounddevice as sd
import numpy as np
import requests
import edge_tts
import base64
from sarvamai import SarvamAI
from typing import Tuple, Optional, Any
from loguru import logger
from config.settings import settings
from scipy.signal import resample

# Try to import Sarvam AI SDK
try:
    SARVAM_SDK_AVAILABLE = True
except ImportError:
    SARVAM_SDK_AVAILABLE = False

# Try to import Edge TTS
try:
    EDGE_TTS_AVAILABLE = True
except ImportError:
    EDGE_TTS_AVAILABLE = False
    logger.warning("edge-tts not installed. Run: pip install edge-tts")

# Suppress verbose warnings
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)


# =====================================================
# Edge TTS Voice Options (Best Hindi Female Voices):
#
#   "hi-IN-SwaraNeural"    ← Recommended: Most natural Hindi female
#   "hi-IN-AnanyaNeural"   ← Alternative: Slightly softer tone
#
# To test voices, run in terminal:
#   edge-tts --list-voices | grep hi-IN
# =====================================================

EDGE_TTS_VOICE = "hi-IN-SwaraNeural"


class TTSProvider:
    """TTS Provider supporting multiple engines (Edge TTS, Sarvam AI, F5)"""

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

    # --------------------------------------------------
    # EDGE TTS — Primary natural voice engine
    # --------------------------------------------------

    def _get_audio_edge(self, text: str) -> Optional[bytes]:
        """Fetch audio bytes from Microsoft Edge TTS"""
        if not EDGE_TTS_AVAILABLE:
            logger.error("edge-tts not installed. Run: pip install edge-tts")
            return None

        try:
            return asyncio.run(self._edge_tts_generate(text))
        except RuntimeError:
            # If an event loop is already running (e.g. Jupyter), use nest_asyncio approach
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                audio_bytes = loop.run_until_complete(self._edge_tts_generate(text))
                loop.close()
                return audio_bytes
            except Exception as e:
                logger.error(f"Edge TTS async fallback error: {e}")

        return None

    async def _edge_tts_generate(self, text: str) -> Optional[bytes]:
        """Async Edge TTS generation — saves to temp file and reads bytes"""
        try:
            communicate = edge_tts.Communicate(text=text, voice=EDGE_TTS_VOICE)

            # Write to temp file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
                tmp_path = tmp.name

            await communicate.save(tmp_path)

            # Read bytes back
            with open(tmp_path, "rb") as f:
                audio_bytes = f.read()

            os.unlink(tmp_path)
            return audio_bytes

        except Exception as e:
            logger.error(f"Edge TTS generation error: {e}")
            return None

    # --------------------------------------------------
    # SARVAM TTS — Fallback engine
    # --------------------------------------------------

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

        # REST API Fallback
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
            response = requests.post(url, json=payload, headers=headers, timeout=10.0)
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

    # --------------------------------------------------
    # Audio helpers
    # --------------------------------------------------

    def _bytes_to_audio_data(self, audio_bytes: Any) -> Tuple[Optional[np.ndarray], int]:
        """Convert wav/mp3 bytes to numpy float array and detect sample rate"""
        try:
            # Detect format — Edge TTS returns mp3, Sarvam returns wav
            suffix = ".mp3" if audio_bytes[:3] == b'\xff\xfb' or audio_bytes[:2] == b'\xff\xf3' or audio_bytes[:3] == b'ID3' else ".wav"

            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp_file:
                tmp_file.write(audio_bytes)
                tmp_path = tmp_file.name

            try:
                # For mp3, convert to wav using ffmpeg first
                if suffix == ".mp3":
                    wav_path = tmp_path.replace(".mp3", ".wav")
                    import subprocess
                    ffmpeg_bin = "/opt/homebrew/bin/ffmpeg" if os.path.exists("/opt/homebrew/bin/ffmpeg") else "ffmpeg"
                    subprocess.run(
                        [ffmpeg_bin, "-y", "-i", tmp_path, "-ar", "22050", "-ac", "1", wav_path],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        timeout=10
                    )
                    os.unlink(tmp_path)
                    tmp_path = wav_path

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
                logger.error(f"Audio decode error: {inner_e}")
                return None, 16000
            finally:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)

        except Exception as e:
            logger.error(f"Error converting bytes to audio: {e}")
            return None, 16000

    # --------------------------------------------------
    # Main speak method
    # --------------------------------------------------

    def speak(self, text: str, callback: Optional[Any] = None) -> bool:
        if not text or not text.strip():
            return False

        try:
            logger.info(f"🎤 Generating speech: {text[:50]}...")

            if self.provider == "edge":
                # FAST PATH: Play MP3 directly via afplay (No FFMPEG/Numpy overhead)
                audio_bytes = self._get_audio_edge(text)
                if audio_bytes:
                    import subprocess
                    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
                        tmp.write(audio_bytes)
                        tmp_path = tmp.name
                    
                    if callback:
                        try: callback()
                        except: pass
                        
                    subprocess.run(["afplay", tmp_path], check=True)
                    os.unlink(tmp_path)
                    logger.success("✅ Playback completed (Edge Fast Path)")
                    return True
                
                # Auto-fallback to Sarvam if Edge fails
                if self.api_key:
                    logger.warning("Edge TTS failed, falling back to Sarvam...")
                    self.provider = "sarvam" # Temporary fallback for this request

            audio_data = None
            sample_rate = 16000

            if self.provider == "sarvam":
                audio_data, sample_rate = self._get_audio_sarvam(text)

            elif self.provider == "f5":
                logger.warning("F5-TTS local provider not fully implemented.")
                print(f"🔊 AI: {text}")
                return True
            else:
                logger.error(f"Unsupported TTS provider: {self.provider}")
                return False

            if audio_data is None:
                logger.error("Failed to generate audio data from all providers")
                return False

            # Normalize audio
            max_val = np.max(np.abs(audio_data))
            if max_val > 1.0:
                audio_data = audio_data / max_val
            elif max_val == 0:
                return False

            # Stable audio playback using macOS native afplay
            try:
                # Convert float32 to int16 for wave file
                audio_data_int16 = (audio_data * 32767).astype(np.int16)
                
                import subprocess
                import wave
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                    tmp_path = tmp.name
                    with wave.open(tmp_path, 'wb') as wf:
                        wf.setnchannels(1)
                        wf.setsampwidth(2)
                        wf.setframerate(sample_rate)
                        wf.writeframes(audio_data_int16.tobytes())
                
                if callback:
                    try:
                        callback()
                    except:
                        pass

                # afplay is 100% immune to Python GIL and PortAudio deadlocks on macOS
                subprocess.run(["afplay", tmp_path], check=True)
                os.unlink(tmp_path)

                logger.success("✅ Playback completed")
                return True

            except Exception as playback_error:
                logger.error(f"SoundDevice Playback error: {playback_error}")
                return False

        except Exception as e:
            logger.error(f"TTS Error: {e}")
            return False


# Global instance
tts_provider = TTSProvider()

if __name__ == "__main__":
    import sys
    test_text = "हाँ बताओ, क्या हुआ? सुन रही हूँ।" if len(sys.argv) < 2 else sys.argv[1]
    tts_provider.speak(test_text)