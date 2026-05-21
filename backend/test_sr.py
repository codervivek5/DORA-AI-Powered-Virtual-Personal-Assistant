import speech_recognition as sr
import time

r = sr.Recognizer()
# Increase pause threshold to avoid cutting off early
r.pause_threshold = 0.8
r.energy_threshold = 300

try:
    with sr.Microphone() as source:
        print("Adjusting for ambient noise...")
        r.adjust_for_ambient_noise(source, duration=0.5)
        print("Listening (Speak now!)...")
        start_time = time.time()
        audio = r.listen(source, timeout=5, phrase_time_limit=10)
        end_time = time.time()
        print(f"Finished listening. Took {end_time - start_time:.2f} seconds.")
        
        with open("test_vad.wav", "wb") as f:
            f.write(audio.get_wav_data())
        print("Saved to test_vad.wav")
except Exception as e:
    print(f"Error: {e}")
