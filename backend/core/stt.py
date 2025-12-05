# core/stt.py
import speech_recognition as sr
import pyaudio

def get_best_mic():
    p = pyaudio.PyAudio()
    mic_list = []
    for i in range(p.get_device_count()):
        device_info = p.get_device_info_by_index(i)
        if device_info.get('maxInputChannels') > 0:
            mic_list.append((i, device_info.get('name')))

    # 1️⃣ Priority: Bluetooth Hands-Free mic (HFP)
    if not mic_list:
        print("No input device found! Using default mic 0.")
        return 0

    # 2️⃣ Priority: Laptop / USB microphone
    for idx, name in mic_list:
        if "microphone" in name.lower() or "mic" in name.lower():
            print(f"Auto-selected normal mic: {name} (index {idx})")
            return idx

    # 3️⃣ Fallback: first available input device
    idx, name = mic_list[0]
    print(f"Fallback mic selected: {name} (index {idx})")
    return idx


def transcribe_from_mic(phrase_time_limit=None):
    device_index = get_best_mic()
    r = sr.Recognizer()
    r.energy_threshold = 500  # voice sensitivity improve
    r.pause_threshold = 1.2  # allow small gaps in speech
    r.dynamic_energy_threshold = True

    with sr.Microphone(device_index=device_index,chunk_size=2048) as source:
        print(f"Listening from mic {device_index}...")
        r.adjust_for_ambient_noise(source, duration=1)
        audio = r.listen(source, phrase_time_limit=phrase_time_limit)
    try:
        text = r.recognize_google(audio, language="hi-IN")  # change lang as needed
        return text
    except sr.UnknownValueError:
        return ""
    except Exception as e:
        print("STT error:", e)
        return ""
    
if __name__ == "__main__":
    print("Say something in Hindi...")
    result = transcribe_from_mic()
    print("You said:", result)