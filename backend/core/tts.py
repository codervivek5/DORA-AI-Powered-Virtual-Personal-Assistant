# core/tts.py
import pyaudio
from murf import Murf
import os
from dotenv import load_dotenv
from stt import transcribe_from_mic

load_dotenv()

api_key = os.getenv("MURF_API_KEY")
client = Murf(api_key=api_key)

SAMPLE_RATE = 24000     # Murf Hindi voice output default
CHANNELS = 1
FORMAT = pyaudio.paInt16


def play_streaming_audio(text=None):
    if not text or not isinstance(text, str):
        print("Error: text parameter must be a non-empty string")
        return

    # Get streaming PCM chunks directly
    audio_stream = client.text_to_speech.stream(
        voice_id="hi-IN-ayushi",
        style="Conversational",
        text=text,
        rate=0,
        multi_native_locale="hi-IN",
    )

    pa = pyaudio.PyAudio()
    stream = pa.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=SAMPLE_RATE,
        output=True
    )

    print("Starting audio playback...")

    try:
        for chunk in audio_stream:
            if not chunk:
                continue

            # 🔥 No base64 decode — Murf sends raw PCM in streaming mode
            stream.write(chunk)

    except Exception as e:
        print(f"Error during streaming: {e}")

    finally:
        stream.stop_stream()
        stream.close()
        pa.terminate()
        print("Audio streaming and playback complete!")


if __name__ == "__main__":
    while True:
        text = transcribe_from_mic()

        if text == "" or text is None:
            print("Didn't catch that. Say again...")
            continue

        if "ruk ja" in text.lower() or "stop" in text.lower():
            print("Stopping conversation...")
            break

        play_streaming_audio(text)


