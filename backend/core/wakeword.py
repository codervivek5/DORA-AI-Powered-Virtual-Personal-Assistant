# core/wakeword.py
"""
Wake word detection using Whisper.
Multilingual support for "Muse" and its variants.
"""
import time
import os
import pyrootutils
from pathlib import Path

# Establish project root
ROOT = pyrootutils.setup_root(__file__, indicator="requirements.txt")

from config.settings import settings
from core.stt import transcribe_from_mic
from loguru import logger

class WakeWordDetector:
    def __init__(self):
        """
        Initialize Whisper-based wake word detector.
        """
        self.variants = [v.lower() for v in settings.WAKE_WORD_VARIANTS]
        logger.info(f"🎤 Wake Word Engine: Whisper (Variants: {self.variants})")

    def listen(self):
        """
        Continuously listen for wake word using Whisper.
        Returns True when any variant is detected in the transcription.
        """
        logger.info(f"👂 Standing by for keyword...")
        
        while True:
            try:
                # Auto-detect language or use settings to support "Ritu" in Hindi/English
                text = transcribe_from_mic(phrase_time_limit=2.5, language=None).strip().lower()
                
                if not text:
                    continue
                
                logger.debug(f"Wake check: '{text}'")
                
                # Check for any variant in the transcribed text
                # We look for exact matches or if the variant is part of the text
                for variant in self.variants:
                    if variant in text:
                        logger.info(f"✨ Wake word '{variant}' detected in: '{text}'")
                        return True
                        
            except KeyboardInterrupt:
                return False
            except Exception as e:
                logger.error(f"❌ Wake word error: {e}")
                time.sleep(1) # Back off on error
                
    def __del__(self):
        """Cleanup resources if any"""
        pass

# Global wake word detector
wake_word_detector = WakeWordDetector()

if __name__ == "__main__":
    print("Testing Whisper wake word detection...")
    print(f"Say one of {settings.WAKE_WORD_VARIANTS} to trigger...")
    detected = wake_word_detector.listen()
    if detected:
        print("✅ Wake word detected successfully!")