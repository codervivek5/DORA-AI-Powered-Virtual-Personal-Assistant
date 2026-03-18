# core/stt.py
import pyaudio
import wave
import tempfile
import os
import requests
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

def get_best_mic():
    """Find the best microphone device"""
    p = pyaudio.PyAudio()
    mic_list = []
    
    try:
        for i in range(p.get_device_count()):
            device_info = p.get_device_info_by_index(i)
            if device_info.get('maxInputChannels') > 0:
                mic_list.append((i, device_info.get('name')))
    except Exception as e:
        print(f"Error listing microphones: {e}")
        return 0

    if not mic_list:
        print("No input device found! Using default mic 0.")
        return 0

    # Priority: Laptop / USB microphone
    for idx, name in mic_list:
        if "microphone" in name.lower() or "mic" in name.lower():
            print(f"Auto-selected normal mic: {name} (index {idx})")
            return idx

    # Fallback: first available input device
    idx, name = mic_list[0]
    print(f"Fallback mic selected: {name} (index {idx})")
    return idx


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
        """Record audio from microphone and save to temporary file"""
        CHUNK = 1024
        FORMAT = pyaudio.paInt16
        CHANNELS = 1
        RATE = 16000  # Whisper works best with 16kHz
        
        p = pyaudio.PyAudio()
        
        try:
            stream = p.open(
                format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                input_device_index=self.device_index,
                frames_per_buffer=CHUNK
            )
            
            print(f"🎤 Listening from mic {self.device_index}...")
            
            frames = []
            max_frames = int(RATE / CHUNK * duration)
            
            for _ in range(max_frames):
                data = stream.read(CHUNK, exception_on_overflow=False)
                frames.append(data)
            
            stream.stop_stream()
            stream.close()
            
            # Save to temporary file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
            temp_file_path = temp_file.name
            temp_file.close()
            
            wf = wave.open(temp_file_path, 'wb')
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(p.get_sample_size(FORMAT))
            wf.setframerate(RATE)
            wf.writeframes(b''.join(frames))
            wf.close()
            
            return temp_file_path
            
        except Exception as e:
            print(f"Recording error: {e}")
            return None
        finally:
            p.terminate()
    
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