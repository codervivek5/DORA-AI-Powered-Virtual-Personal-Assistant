try:
    import sounddevice as sd
    SD_AVAILABLE = True
except ImportError:
    SD_AVAILABLE = False
    class DummySD:
        def stop(self):
            pass
    sd = DummySD()
import time
import wave
import tempfile
import os
import requests

# Chunk size for audio streaming
CHUNK = 1024

from typing import Optional
from config.settings import settings

try:
    from sarvamai import SarvamAI
    SARVAM_AVAILABLE = True
except ImportError:
    SARVAM_AVAILABLE = False

try:
    from pywhispercpp.model import Model
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False

import numpy as np

def get_best_mic():
    """Find the best microphone device using sounddevice"""
    try:
        devices = sd.query_devices()
        mic_list = []
        for i, dev in enumerate(devices):
            if dev['max_input_channels'] > 0:
                mic_list.append((i, dev['name']))
        
        if not mic_list:
            return 0

        # Priority: MacBook Pro Microphone or similar
        for idx, name in mic_list:
            if "microphone" in name.lower() or "mic" in name.lower():
                print(f"Auto-selected mic: {name} (index {idx})")
                return idx
        
        return mic_list[0][0]
    except Exception as e:
        print(f"Error listing microphones: {e}")
        return 0


class STTProvider:
    """Speech-to-Text provider using whisper.cpp"""
    
    def __init__(self):
        self.provider = settings.STT_PROVIDER
        self.device_index = get_best_mic()
        
        # Initialize Whisper if needed
        if self.provider == "whisper":
            if not WHISPER_AVAILABLE:
                print("⚠️ pywhispercpp not installed. Falling back to Sarvam if available.")
                self.provider = "sarvam"
            else:
                try:
                    print(f"Loading Whisper model: {settings.WHISPER_MODEL} (whisper.cpp)...")
                    self.model = Model(settings.WHISPER_MODEL, n_threads=4)
                    print("✅ Whisper model loaded successfully!")
                except Exception as e:
                    print(f"❌ Error loading Whisper model: {e}")
                    self.model = None

        # Initialize Sarvam if needed
        if self.provider == "sarvam":
            if SARVAM_AVAILABLE and settings.SARVAM_API_KEY:
                print("🔊 Sarvam AI STT initialized")
                self.sarvam_client = SarvamAI(api_subscription_key=settings.SARVAM_API_KEY)
            else:
                self.sarvam_client = None
    
    def record_audio(self, duration: float = 5.0) -> Optional[str]:
        """Record audio from microphone using sounddevice for maximum stability on macOS"""
        # Ensure any previous audio is stopped
        sd.stop()
        time.sleep(0.3)  # Physical delay for hardware reset
        RATE = 16000  # Whisper works best with 16kHz
        MAX_RETRIES = 3
        
        for attempt in range(MAX_RETRIES):
            try:
                print(f"🎤 Listening from mic {self.device_index} (Attempt {attempt+1})...")
                recording = np.zeros((int(duration * RATE), 1), dtype='int16')
                
                with sd.InputStream(samplerate=RATE, channels=1, dtype='int16', device=self.device_index) as stream:
                    frames_to_read = int(duration * RATE)
                    data, overflowed = stream.read(frames_to_read)
                    recording = data
                
                # If we reach here, it worked!
                break
            except Exception as e:
                if attempt < MAX_RETRIES - 1:
                    print(f"⚠️ Mic busy, retrying in 0.5s... ({e})")
                    sd.stop()
                    time.sleep(0.5)
                else:
                    print(f"❌ Recording error after {MAX_RETRIES} attempts: {e}")
                    return None
        
        try:
            # Save to temporary file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
            temp_file_path = temp_file.name
            temp_file.close()
            
            with wave.open(temp_file_path, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2) # 16-bit
                wf.setframerate(RATE)
                wf.writeframes(recording.tobytes())
            
            return temp_file_path
        except Exception as e:
            print(f"Recording error: {e}")
            return None
    
    def transcribe(self, audio_file_path: str, language: Optional[str] = "hi") -> str:
        """Transcribe audio using the configured provider"""
        if self.provider == "sarvam":
            return self._transcribe_sarvam(audio_file_path, language)
        else:
            return self._transcribe_whisper(audio_file_path, language)

    def _transcribe_sarvam(self, audio_file_path: str, language: Optional[str]) -> str:
        """Transcribe using Sarvam AI (SDK -> REST fallback)"""
        # Try SDK first
        if self.sarvam_client:
            try:
                with open(audio_file_path, 'rb') as f:
                    # Sarvam AI STT SDK usage (transcribe)
                    response = self.sarvam_client.speech_to_text.translate(
                        file=f,
                        prompt=None,
                        model="saaras:v2.5" # Updated from saaras:v1
                    )
                    # The SDK response usually has a 'transcript' field
                    if hasattr(response, 'transcript'):
                        return response.transcript
                    elif isinstance(response, dict) and 'transcript' in response:
                        return response['transcript']
            except Exception as e:
                print(f"Sarvam SDK STT error: {e}. Trying REST fallback...")

        # Fallback to REST API
        if not settings.SARVAM_API_KEY:
            return ""

        try:
            url = "https://api.sarvam.ai/speech-to-text"
            headers = {"api-subscription-key": settings.SARVAM_API_KEY}
            with open(audio_file_path, 'rb') as f:
                data = {"model": "saarika:v2.5"} 
                files = {"file": ("audio.wav", f, "audio/wav")}
                response = requests.post(url, headers=headers, files=files, data=data)
                
                if response.status_code == 200:
                    return response.json().get("transcript", "")
                else:
                    print(f"Sarvam REST STT error {response.status_code}: {response.text}")
                    return ""
        except Exception as e:
            print(f"Sarvam REST STT error: {e}")
            return ""

    def _transcribe_whisper(self, audio_file_path: str, language: Optional[str]) -> str:
        """Transcribe audio using whisper.cpp"""
        if not self.model:
            return ""
        
        try:
            # pywhispercpp transcription
            segments = self.model.transcribe(audio_file_path, language=language)
            text = " ".join([seg.text for seg in segments]).strip()
            return text
        except Exception as e:
            print(f"Whisper transcription error: {e}")
            return ""
    
    def listen_and_transcribe(self, phrase_time_limit: Optional[float] = None, language: Optional[str] = None) -> str:
        """Record from microphone and transcribe"""
        duration = phrase_time_limit or 5.0
        
        # Record audio
        audio_file = self.record_audio(duration=duration)
        if not audio_file:
            return ""
        
        try:
            # Transcribe
            text = self.transcribe(audio_file, language=language)
            return text
        finally:
            # Clean up temporary file
            try:
                os.unlink(audio_file)
            except:
                pass

# Global STT instance
stt_provider = STTProvider()

def transcribe_from_mic(phrase_time_limit: Optional[float] = None, language: Optional[str] = settings.STT_LANGUAGE) -> str:
    """Entry point for speech transcription"""
    return stt_provider.listen_and_transcribe(phrase_time_limit=phrase_time_limit, language=language)

if __name__ == "__main__":
    print("Say something...")
    result = transcribe_from_mic(phrase_time_limit=5, language="en")
    print(f"✅ You said: {result}")