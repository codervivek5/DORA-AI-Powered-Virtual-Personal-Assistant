import pyrootutils

# Establish project root and capture it
ROOT = pyrootutils.setup_root(__file__, indicator="requirements.txt")

import time

# Import Shalu core modules
from core.stt import transcribe_from_mic
from core.tts import tts_provider
from core.wakeword import wake_word_detector
from core.graph import shalu_app
from config.settings import settings
from loguru import logger
import requests

class ShaluAssistant:
    def __init__(self):
        self.wake_word = settings.WAKE_WORD_VARIANTS[0].title()
        self.session = requests.Session() # Persistent session for faster pings
        logger.info(f"🚀 Shalu Assistant started. Wake Word: {self.wake_word}")

    def update_status(self, text: str):
        """Map status text to Avatar state and notify backend rapidly"""
        avatar_state = "idle"
        lower_text = text.lower()
        
        if "listening" in lower_text or "सुन रही" in lower_text:
            avatar_state = "listening"
        elif "thinking" in lower_text or "सोच रही" in lower_text:
            avatar_state = "thinking"
        elif "speaking" in lower_text or "बोल रही" in lower_text:
            avatar_state = "speaking"
        elif "say" in lower_text or "idle" in lower_text:
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
                    
                    # Acknowledge the wake word
                    import random
                    ack_word = random.choice(["हाँ सर?", "जी सर?", "बताइए सर?"])
                    
                    def ack_sync():
                        self.update_status("बोल रही हूँ...")
                        
                    tts_provider.speak(ack_word, callback=ack_sync)
                    
                    self.update_status("सुन रही हूँ...")
                    user_text = transcribe_from_mic(phrase_time_limit=10.0) # Using 10.0 as it dynamically stops via VAD now
                else:
                    user_text = None

            if user_text and user_text.strip():
                clean_input = user_text.strip().strip('.').strip()

                lower_input = clean_input.lower()

                # Explicitly enter Standby Mode on "bye"
                if lower_input in ["bye", "goodbye", "by", "tata", "alvida", "stop", "exit", "chalo bye"]:
                    logger.info("👋 User said bye. Going to standby mode.")
                    active_session = False
                    self.update_status(f"Say '{self.wake_word}'...")
                    tts_provider.speak("बाय! जब ज़रूरत हो, शालू बोलकर बुला लेना.", callback=lambda: self.update_status("idle"))
                    continue

                # Handle repetitive simple affirmatives to prevent loop lock
                if lower_input in ["okay", "yes", "ok", "haan", "ha", "hm", "hmm"]:
                    if lower_input == last_processed_text.lower():
                        repeat_count += 1
                    else:
                        repeat_count = 1
                    last_processed_text = clean_input

                    if repeat_count >= 2:
                        active_session = False
                        self.update_status(f"Say '{self.wake_word}'...")
                        continue
                else:
                    repeat_count = 0
                    last_processed_text = clean_input

                logger.info(f"🧠 Query: '{user_text}'")
                self.update_status("सोच रही हूँ...")

                try:
                    from core.brain import brain
                    import queue
                    import threading

                    sentence_queue = queue.Queue()
                    
                    def tts_worker():
                        while True:
                            sentence = sentence_queue.get()
                            if sentence is None:  # Sentinel to stop thread
                                break
                            
                            def trigger_sync():
                                self.update_status("बोल रही हूँ...")
                            
                            # Speak the chunk
                            tts_provider.speak(sentence, callback=trigger_sync)
                            sentence_queue.task_done()
                            
                    tts_thread = threading.Thread(target=tts_worker, daemon=True)
                    tts_thread.start()
                    
                    final_state = None
                    streamed_any = False
                    for chunk in brain.chat_stream(user_text):
                        if chunk["type"] == "sentence":
                            sentence_queue.put(chunk["text"])
                            streamed_any = True
                        elif chunk["type"] == "final":
                            final_state = chunk["state"]
                            
                    # Once stream is done
                    if final_state:
                        # Fallback: if streaming parser failed to find RESPONSE: tag, speak the parsed response now
                        if not streamed_any and final_state.get("response"):
                            sentence_queue.put(final_state.get("response"))
                            
                        # Execute action if any
                        if final_state.get("action"):
                            from core.actions.manager import action_manager
                            action_result = action_manager.parse_and_execute(final_state)
                            # If LLM didn't provide a response, but action generated a fallback response, speak it
                            if not final_state.get("response") and action_result and action_result != "ठीक है 😊":
                                sentence_queue.put(action_result)
                            
                    # Stop the TTS thread after all sentences are spoken
                    sentence_queue.put(None)
                    tts_thread.join()

                    active_session = True
                    last_interaction_time = time.time()

                except Exception as e:
                    logger.error(f"❌ Error: {e}")
                    self.update_status("कुछ गड़बड़ हो गई।")
                    time.sleep(1)

            time.sleep(0.01) # Reduced delay for faster loop

if __name__ == "__main__":
    assistant = ShaluAssistant()
    assistant.start()   