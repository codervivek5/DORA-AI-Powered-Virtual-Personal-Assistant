import pyrootutils

# Establish project root and capture it
ROOT = pyrootutils.setup_root(__file__, indicator="requirements.txt")

import time
import customtkinter as ctk
import threading
from typing import Optional

# Import Ritu core modules
from core.stt import transcribe_from_mic
from core.tts import tts_provider
from core.wakeword import wake_word_detector
from core.graph import ritu_app  # New LangGraph engine integration
from config.settings import settings
from loguru import logger


class RituUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.wake_word = settings.WAKE_WORD_VARIANTS[0].title()

        # 1. Window Configuration
        self.title("Ritu AI")
        self.geometry("400x150+500+50")  # Set window size and position
        self.overrideredirect(True)  # Remove standard macOS title bar
        self.attributes("-topmost", True)  # Keep window always on top
        self.attributes("-alpha", 0.85)  # Glassmorphism transparency effect
        self.wm_attributes("-transparent", True)  # Specific transparency for macOS
        self.config(bg='systemTransparent')

        # 2. Glassmorphism UI Frame
        self.main_frame = ctk.CTkFrame(
            self,
            corner_radius=25,
            fg_color=("#2B2B2B", "#1A1A1A"),  # Dark glass appearance
            border_width=2,
            border_color="#4A4A4A"
        )
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # 3. Widgets (Labels and Status Indicators)
        self.label = ctk.CTkLabel(
            self.main_frame,
            text=f"Say '{self.wake_word}'...",
            font=("System", 16, "bold"),
            text_color="#00D4FF",
            wraplength=350
        )
        self.label.pack(pady=(15, 0))

        self.response_label = ctk.CTkLabel(
            self.main_frame,
            text="",
            font=("System", 12),
            text_color="white",
            wraplength=350
        )
        self.response_label.pack(pady=5)

        self.status_ball = ctk.CTkLabel(
            self.main_frame,
            text="●",
            text_color="gray",
            font=("System", 24)
        )
        self.status_ball.pack()

        # 4. Draggable Window Logic
        self.main_frame.bind("<B1-Motion>", self.move_window)
        self.main_frame.bind("<Button-1>", self.get_pos)

    def get_pos(self, event):
        """Capture window position when clicked"""
        self.xwin = event.x
        self.ywin = event.y

    def move_window(self, event):
        """Move window following the mouse cursor"""
        self.geometry(f'+{event.x_root - self.xwin}+{event.y_root - self.ywin}')

    def update_status(self, text: str, color: str, response_text: Optional[str] = ""):
        """Update UI text and status ball color safely"""
        self.label.configure(text=text)
        self.status_ball.configure(text_color=color)
        if response_text is not None:
            self.response_label.configure(text=response_text)

        # Map UI status to Avatar state
        avatar_state = "idle"
        if "listening" in text.lower() or "say" in text.lower():
            avatar_state = "idle" if "say" in text.lower() else "listening"
        elif "thinking" in text.lower():
            avatar_state = "thinking"
        elif "speaking" in text.lower():
            avatar_state = "speaking"

        # Silently ping the FastAPI backend so the Avatar UI reacts
        def ping_avatar():
            try:
                import requests
                requests.post("http://localhost:8000/api/avatar/event", json={"state": avatar_state}, timeout=0.5)
            except:
                pass
        
        threading.Thread(target=ping_avatar, daemon=True).start()

    def start_listening_thread(self):
        """Launch the voice loop in a background thread to prevent UI freezing"""
        thread = threading.Thread(target=self.voice_loop, daemon=True)
        thread.start()

    def voice_loop(self):
        """Main interaction loop: Wake word detection -> STT -> LangGraph -> TTS"""
        detector = wake_word_detector
        active_session = False
        last_interaction_time = 0
        SESSION_TIMEOUT = 12  # Time in seconds to keep mic open for follow-up

        # Tracking ghost transcriptions to prevent infinite short loop anomalies
        last_processed_text = ""
        repeat_count = 0

        # Set initial UI state
        self.update_status(f"Say '{self.wake_word}'...", "gray")

        while True:
            current_time = time.time()

            # Check if we are in an active follow-up session
            if active_session and (current_time - last_interaction_time < SESSION_TIMEOUT):
                self.update_status("Listening (Active)...", "#00D4FF")
                user_text = transcribe_from_mic(phrase_time_limit=5)
            else:
                if active_session:
                    logger.info("💤 Session timed out. Returning to wake word mode.")

                active_session = False
                # Re-verify UI update state gracefully on sleep resets
                self.update_status(f"Say '{self.wake_word}'...", "gray")

                # Block here until wake word is detected
                if detector.listen():
                    active_session = True
                    self.update_status("I'm listening...", "#00D4FF")
                    user_text = transcribe_from_mic(phrase_time_limit=4)
                else:
                    user_text = None

            # Process transcribed text if available
            if user_text and user_text.strip():
                clean_input = user_text.strip().strip('.').strip()

                # =========================================================================
                # SAFELY OPTIMIZED FILTER BLOCK: Prevent ghost loops while keeping wake-word active
                # =========================================================================
                if clean_input.lower() in ["okay", "yes", "야", "हाँ", "ठीक है", "ok", "sure", "ritu"]:
                    # If it captures just the wake-word or a filler phrase by mistake, don't trigger brain logic
                    if clean_input.lower() == last_processed_text.lower() or clean_input.lower() == "ritu":
                        repeat_count += 1
                    else:
                        repeat_count = 1

                    last_processed_text = clean_input

                    # If the mic keeps repeating short words or captures empty wake prompt, drop execution and reset
                    if repeat_count >= 2 or clean_input.lower() == "ritu":
                        logger.warning(f"Bypassing empty transcription or continuous loop context ('{clean_input}').")
                        active_session = False  # Instantly release active lock to let wake word engine listen again
                        self.update_status(f"Say '{self.wake_word}'...", "gray")
                        time.sleep(0.5)
                        continue
                else:
                    repeat_count = 0
                    last_processed_text = clean_input
                # =========================================================================

                logger.info(f"🧠 Processing query via LangGraph: '{user_text}'")
                self.update_status("Thinking...", "#FFCC00")

                try:
                    # Initialize LangGraph State
                    initial_state = {
                        "input": user_text,
                        "chat_history": [],  # Can be populated from brain.conversation_history
                        "action": None,
                        "param": None,
                        "response": "",
                        "raw_ai_response": {},
                        "final_output": ""
                    }

                    # Execute LangGraph Workflow (Brain Node -> Action Node -> End)
                    final_state = ritu_app.invoke(initial_state)
                    spoken_response = final_state.get("final_output", "मुझे समझ नहीं आया.")

                    # Update UI status to 'Speaking'
                    self.after(0, lambda: self.update_status("Speaking...", "#00FF7F", ""))

                    # Audio Playback
                    tts_provider.speak(spoken_response)

                    # Keep session active for follow-up conversation
                    active_session = True
                    last_interaction_time = time.time()

                except Exception as e:
                    logger.error(f"❌ Error in voice loop: {e}")
                    self.update_status("Error occurred.", "red")
                    time.sleep(2)

            time.sleep(0.1)  # Minimal delay to prevent high CPU usage


if __name__ == "__main__":
    # Create and run the Ritu UI Application
    app = RituUI()
    app.start_listening_thread()
    app.mainloop()