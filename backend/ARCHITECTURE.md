DORA/
│── core/
│   ├── stt.py               # audio → text
│   ├── tts.py               # text → voice
│   ├── brain.py             # logic + intent + LLM
│   ├── actions/
│   │     ├── system.py      # shutdown, restart, sleep
│   │     ├── apps.py        # open/close apps
│   │     ├── browser.py     # google search, youtube
│   │     ├── media.py       # music control
│   │     ├── files.py       # file operations
│   │     ├── keyboard.py    # automate typing
│── server/
│   ├── api.py               # FastAPI local server
│── ui/
│   ├── desktop.py           # UI (Tkinter or Electron)
│── config/
│   ├── settings.py
│── main.py                  # entry point
