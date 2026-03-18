# ui/desktop.py
import pyrootutils
from pathlib import Path

# Establish project root and capture it
ROOT = pyrootutils.setup_root(__file__, indicator="requirements.txt")

import time
import random
import customtkinter as ctk
import threading
from core.brain import brain
from core.stt import transcribe_from_mic
from core.tts import tts_provider
from core.wakeword import wake_word_detector
from core.actions.manager import action_manager

from config.settings import settings

class RituUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.wake_word = settings.WAKE_WORD_VARIANTS[0].title()

        # 1. Window Configuration
        self.title("Ritu AI")
        self.geometry("400x150+500+50")  # Width x Height + X_offset + Y_offset
        self.overrideredirect(True)      # Removes standard Mac title bar
        self.attributes("-topmost", True) # Always on top
        self.attributes("-alpha", 0.85)   # The "Glass" transparency effect
        self.wm_attributes("-transparent", True) # macOS specific transparency
        self.config(bg='systemTransparent')

        # 2. Glassmorphism Design
        self.main_frame = ctk.CTkFrame(
            self, 
            corner_radius=25, 
            fg_color=("#2B2B2B", "#1A1A1A"), # Dark glass look
            border_width=2,
            border_color="#4A4A4A"
        )
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # 3. Widgets
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

        # 4. Make it Draggable
        self.main_frame.bind("<B1-Motion>", self.move_window)
        self.main_frame.bind("<Button-1>", self.get_pos)

    def get_pos(self, event):
        self.xwin = event.x
        self.ywin = event.y

    def move_window(self, event):
        self.geometry(f'+{event.x_root - self.xwin}+{event.y_root - self.ywin}')

    def update_status(self, text, color, response_text=""):
        self.label.configure(text=text)
        self.status_ball.configure(text_color=color)
        if response_text is not None:
            self.response_label.configure(text=response_text)

    def start_listening_thread(self):
        """Runs the voice loop without freezing the UI"""
        thread = threading.Thread(target=self.voice_loop, daemon=True)
        thread.start()

    def voice_loop(self):
        detector = wake_word_detector
        active_session = False
        last_interaction_time = 0
        SESSION_TIMEOUT = 12

        # Initialize TTS (Samrvadam AI - no model loading required)
        self.update_status(f"Say '{self.wake_word}'...", "gray")

        while True:
            current_time = time.time()
            
            if active_session and (current_time - last_interaction_time < SESSION_TIMEOUT):
                self.update_status("Listening (Active)...", "#00D4FF")
                user_text = transcribe_from_mic(phrase_time_limit=5)
            else:
                if active_session:
                    print("💤 Session timed out.")
                active_session = False
                self.update_status(f"Say '{self.wake_word}'...", "gray", response_text="")

                if detector.listen():
                    active_session = True
                    self.update_status("I'm listening...", "#00D4FF")
                    # Quick audio ack
                    # tts_provider.speak("Yes?") # Removed to make it "direct" as per user request
                    user_text = transcribe_from_mic(phrase_time_limit=4)
                else:
                    user_text = None

            if user_text and user_text.strip():
                print(f"🧠 Brain: Processing query: '{user_text}'")
                self.update_status("Thinking...", "#FFCC00")
                
                try:
                    ai_raw_response = brain.chat(user_text)
                    spoken_response = action_manager.parse_and_execute(ai_raw_response)
                    
                    # Update UI status without showing full response text
                    self.after(0, lambda: self.update_status("Speaking...", "#00FF7F", ""))
                    
                    # Speak
                    tts_provider.speak(spoken_response)
                    
                    active_session = True
                    last_interaction_time = time.time()
                except Exception as e:
                    print(f"❌ Error in voice loop: {e}")
                    self.update_status("Error occurred.", "red")
                    time.sleep(2)
            
            time.sleep(0.1)
                
if __name__ == "__main__":
    app = RituUI()        
    app.start_listening_thread()
    app.mainloop()