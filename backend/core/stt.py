# core/stt.py
"""
Speech-to-Text using whisper.cpp (pywhispercpp) for ultra-fast local transcription.
Optimized for Hindi/English mixed speech.
"""
import pyaudio
import wave
import tempfile
import os
from typing import Optional
from config.settings import settings

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
        if not WHISPER_AVAILABLE:
            print("⚠️ pywhispercpp not installed. Install with: pip install pywhispercpp")
            self.model = None
            return
        
        self.model_name = settings.WHISPER_MODEL
        self.device_index = get_best_mic()
        
        try:
            print(f"Loading Whisper model: {self.model_name} (whisper.cpp)...")
            # pywhispercpp will auto-download model if not present
            self.model = Model(self.model_name, n_threads=4)
            print("✅ Whisper model loaded successfully!")
        except Exception as e:
            print(f"❌ Error loading Whisper model: {e}")
            self.model = None
    
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
    
    def transcribe(self, audio_file_path: str, language: str = "en") -> str:
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
    
    def listen_and_transcribe(self, phrase_time_limit: Optional[float] = None, language: str = "en") -> str:
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

def transcribe_from_mic(phrase_time_limit: Optional[float] = None, language: str = "en") -> str:
    """Entry point for speech transcription"""
    return stt_provider.listen_and_transcribe(phrase_time_limit=phrase_time_limit, language=language)

if __name__ == "__main__":
    print("Testing whisper.cpp STT...")
    print("Say something...")
    result = transcribe_from_mic(phrase_time_limit=5, language="en")
    print(f"✅ You said: {result}")