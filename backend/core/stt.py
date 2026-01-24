# core/stt.py
"""
Speech-to-Text module using free, local STT providers
Primary: Whisper (via faster-whisper)
Fallback: Google Speech Recognition (requires internet)
"""
import pyaudio
import wave
import tempfile
import os
from typing import Optional
from config.settings import settings

# Try to import faster-whisper (primary)
try:
    from faster_whisper import WhisperModel
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False

# Try to import speech_recognition (fallback)
try:
    import speech_recognition as sr
    SPEECH_RECOGNITION_AVAILABLE = True
except ImportError:
    SPEECH_RECOGNITION_AVAILABLE = False


def get_best_mic():
    """Find the best microphone device"""
    p = pyaudio.PyAudio()
    mic_list = []
    for i in range(p.get_device_count()):
        device_info = p.get_device_info_by_index(i)
        if device_info.get('maxInputChannels') > 0:
            mic_list.append((i, device_info.get('name')))

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
    """Speech-to-Text provider with Whisper and fallback support"""
    
    def __init__(self):
        self.provider = settings.STT_PROVIDER
        self.model_name = settings.WHISPER_MODEL
        self.device = settings.WHISPER_DEVICE
        self.whisper_model = None
        self.language = "en"  # Default language, can be changed
        
        # Initialize Whisper if available
        if WHISPER_AVAILABLE and self.provider == "whisper":
            try:
                print(f"Loading Whisper model: {self.model_name} ({self.device})...")
                self.whisper_model = WhisperModel(
                    self.model_name,
                    device=self.device,
                    compute_type="int8" if self.device == "cpu" else "float16"
                )
                print("✅ Whisper model loaded successfully!")
            except Exception as e:
                print(f"Warning: Could not load Whisper model: {e}")
                self.whisper_model = None
    
    def transcribe_with_whisper(self, audio_file_path: str) -> str:
        """Transcribe audio using Whisper"""
        if not WHISPER_AVAILABLE or not self.whisper_model:
            return ""
        
        try:
            segments, info = self.whisper_model.transcribe(
                audio_file_path,
                language=self.language if self.language != "auto" else None,
                beam_size=5
            )
            
            # Combine all segments
            text_parts = []
            for segment in segments:
                text_parts.append(segment.text)
            
            return " ".join(text_parts).strip()
            
        except Exception as e:
            print(f"Whisper transcription error: {e}")
            return ""
    
    def transcribe_with_google(self, audio_file_path: str, language: str = "en-US") -> str:
        """Transcribe audio using Google Speech Recognition (fallback)"""
        if not SPEECH_RECOGNITION_AVAILABLE:
            return ""
        
        try:
            r = sr.Recognizer()
            with sr.AudioFile(audio_file_path) as source:
                audio = r.record(source)
            
            text = r.recognize_google(audio, language=language)
            return text
            
        except sr.UnknownValueError:
            return ""
        except Exception as e:
            print(f"Google STT error: {e}")
            return ""
    
    def record_audio(self, duration: Optional[float] = None, phrase_time_limit: Optional[float] = None) -> Optional[str]:
        """
        Record audio from microphone and save to temporary file
        
        Args:
            duration: Maximum recording duration in seconds
            phrase_time_limit: Maximum phrase duration in seconds
            
        Returns:
            Path to temporary audio file, or None if error
        """
        device_index = get_best_mic()
        
        # Audio parameters
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
                input_device_index=device_index,
                frames_per_buffer=CHUNK
            )
            
            print(f"🎤 Listening from mic {device_index}...")
            
            frames = []
            max_frames = int(RATE / CHUNK * (duration or phrase_time_limit or 5))
            
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
    
    def transcribe_from_mic(self, duration: Optional[float] = None, language: str = "en") -> str:
        """
        Record from microphone and transcribe
        
        Args:
            duration: Maximum recording duration in seconds
            language: Language code (e.g., "en", "hi", "es")
            
        Returns:
            Transcribed text
        """
        self.language = language
        
        # Record audio
        audio_file = self.record_audio(duration=duration)
        if not audio_file:
            return ""
        
        try:
            # Try primary provider
            if self.provider == "whisper":
                text = self.transcribe_with_whisper(audio_file)
                if text:
                    return text
                # Fallback to Google if Whisper fails
                print("Falling back to Google STT...")
                return self.transcribe_with_google(audio_file, language=f"{language}-{language.upper()}")
            
            elif self.provider == "google":
                text = self.transcribe_with_google(audio_file, language=f"{language}-{language.upper()}")
                if text:
                    return text
                # Fallback to Whisper if Google fails
                print("Falling back to Whisper...")
                return self.transcribe_with_whisper(audio_file)
            
            return ""
            
        finally:
            # Clean up temporary file
            try:
                os.unlink(audio_file)
            except:
                pass


# Global STT instance
stt_provider = STTProvider()


def transcribe_from_mic(phrase_time_limit: Optional[float] = None, language: str = "en") -> str:
    """
    Transcribe from microphone (maintains compatibility with old API)
    
    Args:
        phrase_time_limit: Maximum phrase duration in seconds
        language: Language code (e.g., "en", "hi")
        
    Returns:
        Transcribed text
    """
    return stt_provider.transcribe_from_mic(duration=phrase_time_limit, language=language)


if __name__ == "__main__":
    print("Testing STT providers...")
    print("Say something...")
    
    result = transcribe_from_mic(language="en")
    
    if result:
        print(f"✅ You said: {result}")
    else:
        print("❌ Could not transcribe audio. Please check your STT setup.")