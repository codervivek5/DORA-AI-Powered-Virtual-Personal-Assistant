# config/settings.py
from pyde import BaseSettings
from pydantic import base  

class Settings(BaseSettings):
    USE_LOCAL_STT: bool = True
    USE_LOCAL_TTS: bool = True
    LLM_PROVIDER: str = "openai"  # or "local"
    OPENAI_API_KEY: str | None = None

settings = Settings()
