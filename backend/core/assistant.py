import pyrootutils

# Establish project root and capture it
ROOT = pyrootutils.setup_root(__file__, indicator="requirements.txt")

import time

# Import Ritu core modules
from core.stt import transcribe_from_mic
from core.tts import tts_provider
from core.wakeword import wake_word_detector
from core.graph import ritu_app
from config.settings import settings
from loguru import logger
import requests

class RituAssistant:
    def __init__(self):
        self.wake_word = settings.WAKE_WORD_VARIANTS[0].title()
        self.session = requests.Session() # Persistent session for faster pings
        logger.info(f"🚀 Ritu Assistant started. Wake Word: {self.wake_word}")

    def update_status(self, text: str):
        """Map status text to Avatar state and notify backend rapidly"""
        avatar_state = "idle"
        lower_text = text.lower()
        
        if "listening" in lower_text:
            avatar_state = "listening"
        elif "thinking" in lower_text:
            avatar_state = "thinking"
        elif "speaking" in lower_text:
            avatar_state = "speaking"
        elif "say" in lower_text:
            avatar_state = "idle"

        try:
            # Using persistent session is much faster than requests.post
            self.session.post("http://localhost:8000/api/avatar/event", json={"state": avatar_state}, timeout=0.2)
        except:
            pass

    def start(self):
        detector = wake_word_detector
        active_session = False
        last_interaction_time = 0
        SESSION_TIMEOUT = 20 

        last_processed_text = ""
        repeat_count = 0

        self.update_status(f"Say '{self.wake_word}'...")

        while True:
            current_time = time.time()

            if active_session and (current_time - last_interaction_time < SESSION_TIMEOUT):
                self.update_status("Listening...")
                user_text = transcribe_from_mic(phrase_time_limit=4)
            else:
                if active_session:
                    logger.info("💤 Session timed out.")
                
                active_session = False
                self.update_status(f"Say '{self.wake_word}'...")

                if detector.listen():
                    active_session = True
                    last_interaction_time = current_time # Start session timer immediately
                    self.update_status("I'm listening...")
                    user_text = transcribe_from_mic(phrase_time_limit=4)
                else:
                    user_text = None

            if user_text and user_text.strip():
                clean_input = user_text.strip().strip('.').strip()

                if clean_input.lower() in ["okay", "yes", "ok", "ritu"]:
                    if clean_input.lower() == last_processed_text.lower() or clean_input.lower() == "ritu":
                        repeat_count += 1
                    else:
                        repeat_count = 1
                    last_processed_text = clean_input

                    if repeat_count >= 2 or clean_input.lower() == "ritu":
                        active_session = False
                        self.update_status(f"Say '{self.wake_word}'...")
                        continue
                else:
                    repeat_count = 0
                    last_processed_text = clean_input

                logger.info(f"🧠 Query: '{user_text}'")
                self.update_status("Thinking...")

                try:
                    initial_state = {
                        "input": user_text,
                        "chat_history": [],
                        "action": None,
                        "param": None,
                        "response": "",
                        "raw_ai_response": {},
                        "final_output": ""
                    }

                    final_state = ritu_app.invoke(initial_state)
                    spoken_response = final_state.get("final_output", "मुझे समझ नहीं आया.")

                    # SYNC FIX: Only trigger "Speaking" when audio playback actually starts
                    def trigger_sync():
                        self.update_status("Speaking...")

                    tts_provider.speak(spoken_response, callback=trigger_sync)

                    active_session = True
                    last_interaction_time = time.time()

                except Exception as e:
                    logger.error(f"❌ Error: {e}")
                    self.update_status("Error occurred.")
                    time.sleep(1)

            time.sleep(0.01) # Reduced delay for faster loop

if __name__ == "__main__":
    assistant = RituAssistant()
    assistant.start()