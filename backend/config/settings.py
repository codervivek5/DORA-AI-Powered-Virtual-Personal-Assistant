# config/settings.py
from pydantic import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # LLM Settings
    LLM_PROVIDER: str = "ollama"  # "ollama" or "openai" (for fallback)
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2"  # or "mistral", "phi3", etc.
    OPENAI_API_KEY: Optional[str] = None
    
    # STT Settings
    USE_LOCAL_STT: bool = True
    STT_PROVIDER: str = "whisper"  # "whisper" or "google" (fallback)
    WHISPER_MODEL: str = "base"  # "tiny", "base", "small", "medium", "large"
    WHISPER_DEVICE: str = "cpu"  # "cpu" or "cuda"
    
    # TTS Settings
    USE_LOCAL_TTS: bool = True
    TTS_PROVIDER: str = "piper"  # "piper" or "pyttsx3" (fallback)
    PIPER_VOICE: str = "en_US-lessac-medium"  # Default voice
    PIPER_MODEL_PATH: Optional[str] = None  # Auto-download if None
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
