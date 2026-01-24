# ui/desktop.py
import customtkinter as ctk
import threading
from core.brain import brain
from core.stt import transcribe_from_mic
from core.tts import tts_provider

class MuskanUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        # 1. Window Configuration
        self.title("Muskan AI")
        self.geometry("400x150+500+50")  # Width x Height + X_offset + Y_offset
        self.overrideredirect(True)      # Removes standard Mac title bar
        self.attributes("-topmost", True) # Always on top
        self.attributes("-alpha", 0.85)   # The "Glass" transparency effect
        self.wm_attributes("-transparent", True) # MacOS specific transparency
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
            text="Muskan is listening...", 
            font=("System", 16, "bold"),
            text_color="#00D4FF" # Cyberpunk Blue
        )
        self.label.pack(pady=(20, 0))

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

    def update_status(self, text, color):
        self.label.configure(text=text)
        self.status_ball.configure(text_color=color)

    def start_listening_thread(self):
        """Runs the voice loop without freezing the UI"""
        thread = threading.Thread(target=self.voice_loop, daemon=True)
        thread.start()

    def voice_loop(self):
        while True:
            self.update_status("Say 'Muskan'...", "#505050")
            # Logic: Here you would call your STT wake-word logic
            # For now, let's trigger a chat manually
            user_text = transcribe_from_mic(phrase_time_limit=5)
            
            if user_text:
                self.update_status("Thinking...", "#FFCC00")
                response = brain.chat(user_text)
                
                self.update_status("Speaking...", "#00FF7F")
                tts_provider.speak(response)

if __name__ == "__main__":
    app = MuskanUI()
    app.start_listening_thread()
    app.mainloop()