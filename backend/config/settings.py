# config/settings.py
from pydantic_settings import BaseSettings
from typing import Optional
import os
from pathlib import Path
from core.prompt import system_prompt


class Settings(BaseSettings):
    # LLM Settings
    LLM_PROVIDER: str = "ollama"  # "ollama" or "openai" (for fallback)
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2"  # or "mistral", "phi3", etc.
    OPENAI_API_KEY: Optional[str] = None

    # Prompt
    SYSTEM_PROMPT:str = system_prompt
    
    # Wake Word Settings
    WAKE_WORD_VARIANTS: list[str] = ["ritu", "रितु", "रीतु"]
    
    # STT Settings
    USE_LOCAL_STT: bool = True
    STT_PROVIDER: str = "whisper"  # Using whisper.cpp for speed
    WHISPER_MODEL: str = "base"  # tiny, base, small, medium, large
    WHISPER_DEVICE: str = "cpu"
    
    # TTS Settings
    USE_LOCAL_TTS: bool = False
    TTS_PROVIDER: str = "sarvam"
    F5_MODEL_ID: str = "SPRINGLab/F5-Hindi-24KHz"
    SARVAM_API_KEY: Optional[str] = None
    SARVAM_MODEL: str = "bulbul:v2" # Options: bulbul:v2, bulbul:v3, ritu (if available)
    SARVAM_VOICE: str = "female"     # Options: male, female, ritu
    
    model_config = {
        "env_file": os.path.join(Path(__file__).parent.parent, ".env"),
        "case_sensitive": False,
        "extra": "ignore"
    }

settings = Settings()
