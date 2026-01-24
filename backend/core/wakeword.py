# core/wakeword.py
import time
from core.stt import transcribe_from_mic

class MuskanWakeWord:
    def __init__(self, wake_word="muskan"):
        """
        Initializes the STT-based wake word detector.
        Handles common phonetic variations since "Muskan" can be mis-transcribed.
        """
        self.wake_word = wake_word.lower()
        # Common ways STT might hear "Muskan"
        self.variations = ["muskan", "muscon", "ms. kahn", "muskon", "ms kahn", "ms. khan", "muscon", "muskan"]
        print(f"🎤 Muskan Wake Word initialized. Support variations: {self.variations}")

    def listen(self):
        """
        Continuously listens in short bursts and checks for the wake word.
        Returns True when the wake word or its variations are detected.
        """
        print(f"👂 Muskan is waiting (Say '{self.wake_word}')...")
        
        while True:
            # We use a slightly shorter limit to reduce the "dead zone" time
            # Note: While processing (transcribing), the mic is OFF. 
            # This is why it 'skips' if you speak during that 1-2 sec window.
            try:
                text = transcribe_from_mic(phrase_time_limit=2.5)
                
                if text:
                    text_lower = text.lower()
                    print(f"🔍 Heard: '{text_lower}'")
                    
                    # Check for wake word or any of its phonetic variations
                    if any(variant in text_lower for variant in self.variations):
                        print(f"✨ Wake word activation triggered!")
                        return True
            except Exception as e:
                print(f"⚠️ Error during wake word detection: {e}")
                time.sleep(0.2)

# Simple test
if __name__ == "__main__":
    detector = MuskanWakeWord()
    if detector.listen():
        print("Success: Muskan is now awake!")