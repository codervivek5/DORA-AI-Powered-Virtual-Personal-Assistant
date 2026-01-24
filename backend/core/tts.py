# core/tts.py
"""
Text-to-Speech module using free, local TTS providers
Primary: Piper (fast, high-quality)
Fallback: pyttsx3 (system TTS)
"""
import pyaudio
import subprocess
import os
import tempfile
from pathlib import Path
from typing import Optional
from config.settings import settings

# Try to import pyttsx3 for fallback
try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False

SAMPLE_RATE = 22050  # Piper default sample rate
CHANNELS = 1
FORMAT = pyaudio.paInt16


class TTSProvider:
    """Text-to-Speech provider with Piper and fallback support"""
    
    def __init__(self):
        self.provider = settings.TTS_PROVIDER
        self.voice = settings.PIPER_VOICE
        self.model_path = settings.PIPER_MODEL_PATH
        self.pyttsx3_engine = None
        
        if PYTTSX3_AVAILABLE:
            try:
                self.pyttsx3_engine = pyttsx3.init()
                # Set properties for better quality
                self.pyttsx3_engine.setProperty('rate', 150)
                self.pyttsx3_engine.setProperty('volume', 0.9)
            except Exception as e:
                print(f"Warning: Could not initialize pyttsx3: {e}")
    
    def _get_piper_path(self) -> Optional[str]:
        """Try to find piper executable"""
        # Check common locations
        possible_paths = [
            "piper",
            "/usr/local/bin/piper",
            os.path.expanduser("~/.local/bin/piper"),
        ]
        
        for path in possible_paths:
            if os.path.exists(path) or self._check_command_exists(path):
                return path
        
        return None
    
    def _check_command_exists(self, cmd: str) -> bool:
        """Check if command exists in PATH"""
        try:
            subprocess.run(
                [cmd, "--version"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=2
            )
            return True
        except:
            return False
    
    def _get_piper_model_path(self) -> str:
        """Get or download Piper model path"""
        if self.model_path and os.path.exists(self.model_path):
            return self.model_path
        
        # Default model path in user's home directory
        home = Path.home()
        model_dir = home / ".local" / "share" / "piper" / "voices"
        model_dir.mkdir(parents=True, exist_ok=True)
        
        # Default voice: en_US-lessac-medium
        model_file = model_dir / f"{self.voice}.onnx"
        
        if not model_file.exists():
            print(f"⚠️  Piper model not found at {model_file}")
            print(f"Please download it manually or install piper-tts:")
            print(f"  pip install piper-tts")
            print(f"  python -m piper.download {self.voice}")
            return None
        
        return str(model_file)
    
    def speak_with_piper(self, text: str) -> bool:
        """Use Piper TTS to speak text"""
        piper_path = self._get_piper_path()
        if not piper_path:
            print("⚠️  Piper not found. Install from: https://github.com/rhasspy/piper")
            return False
        
        model_path = self._get_piper_model_path()
        if not model_path:
            return False
        
        try:
            # Use piper to generate audio
            process = subprocess.Popen(
                [
                    piper_path,
                    "--model", model_path,
                    "--output_file", "-",  # Output to stdout
                ],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Send text and get audio
            stdout, stderr = process.communicate(input=text.encode(), timeout=10)
            
            if process.returncode != 0:
                print(f"Piper error: {stderr.decode()}")
                return False
            
            # Play audio using pyaudio
            self._play_audio_data(stdout)
            return True
            
        except subprocess.TimeoutExpired:
            print("Piper TTS timeout")
            return False
        except Exception as e:
            print(f"Piper TTS error: {e}")
            return False
    
    def speak_with_pyttsx3(self, text: str) -> bool:
        """Use pyttsx3 (system TTS) as fallback"""
        if not PYTTSX3_AVAILABLE or not self.pyttsx3_engine:
            return False
        
        try:
            self.pyttsx3_engine.say(text)
            self.pyttsx3_engine.runAndWait()
            return True
        except Exception as e:
            print(f"pyttsx3 error: {e}")
            return False
    
    def _play_audio_data(self, audio_data: bytes):
        """Play raw audio data using pyaudio"""
        pa = pyaudio.PyAudio()
        
        try:
            stream = pa.open(
                format=FORMAT,
                channels=CHANNELS,
                rate=SAMPLE_RATE,
                output=True
            )
            
            # Write audio data in chunks
            chunk_size = 1024
            for i in range(0, len(audio_data), chunk_size):
                chunk = audio_data[i:i + chunk_size]
                stream.write(chunk)
            
            stream.stop_stream()
            stream.close()
            
        except Exception as e:
            print(f"Audio playback error: {e}")
        finally:
            pa.terminate()
    
    def speak(self, text: str) -> bool:
        """
        Main method to speak text using available TTS provider
        
        Args:
            text: Text to speak
            
        Returns:
            True if successful, False otherwise
        """
        if not text or not isinstance(text, str) or not text.strip():
            print("Error: text parameter must be a non-empty string")
            return False
        
        # Try primary provider first
        if self.provider == "piper":
            if self.speak_with_piper(text):
                return True
            # Fallback to pyttsx3 if piper fails
            print("Falling back to pyttsx3...")
            return self.speak_with_pyttsx3(text)
        
        elif self.provider == "pyttsx3":
            if self.speak_with_pyttsx3(text):
                return True
            # Fallback to piper if pyttsx3 fails
            print("Falling back to Piper...")
            return self.speak_with_piper(text)
        
        return False


# Global TTS instance
tts_provider = TTSProvider()


def play_streaming_audio(text: Optional[str] = None):
    """
    Play audio from text (maintains compatibility with old API)
    
    Args:
        text: Text to convert to speech
    """
    if text:
        tts_provider.speak(text)
    else:
        print("Error: text parameter is required")


if __name__ == "__main__":
    # Test TTS
    print("Testing TTS providers...")
    
    test_text = "Hello! I am Muskan, your AI-powered virtual personal assistant."
    
    print(f"\nSpeaking: '{test_text}'")
    success = tts_provider.speak(test_text)
    
    if success:
        print("✅ TTS test successful!")
    else:
        print("❌ TTS test failed. Please check your TTS setup.")


