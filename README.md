# Trixie — Your PC, Your Voice, No Cloud.

A powerful, entirely local desktop AI assistant for Windows. Trixie interprets voice commands, automates tasks, learns from your corrections, and speaks back — all running 100% offline.

> **No cloud. No API keys. No data ever leaves your PC.**

## ✨ Features

- **🎤 Voice Control** — Push-to-talk (`Ctrl + CapsLock`) with local Whisper STT
- **🧠 Intent Classification** — Qwen 3 4B LLM classifies commands into actionable intents
- **⚡ Smart Cache** — Verified commands skip LLM inference on repeat (80% match)
- **🔁 Macro System** — Record action sequences, replay on demand
- **🔊 Voice Response** — Offline TTS speaks results back
- **💬 Feedback Loop** — Asks "was that correct?" and learns from your answers
- **🖥️ Floating Overlay** — Glassmorphic HUD showing status, transcription, and response
- **🔒 Privacy-First** — Every model runs locally. Zero network calls. Ever.

## 🏗️ Architecture

```
main.py                  ← App orchestrator + feedback loop
├── core/
│   ├── audio.py         ← Whisper STT (faster-whisper)
│   ├── llm_engine.py    ← Qwen 3 4B intent classifier (llama.cpp)
│   ├── context.py       ← System prompt + memory
│   ├── executor.py      ← Whitelisted app/command execution
│   ├── macro_manager.py ← Macro recording & replay
│   ├── tts_engine.py    ← Offline text-to-speech (pyttsx3)
│   ├── model_manager.py ← Runtime auto-download from HuggingFace
│   └── db.py            ← SQLite (history + intent cache + macros)
└── ui/
    └── app.py           ← PyQt6 system tray + floating overlay
```

## 🧠 Smart Intent Cache

Trixie learns from your corrections:

1. You say "Open Notepad" → LLM classifies → executes `open_app:notepad`
2. Trixie finishes and shows 👍/👎 buttons in the floating UI.
3. You click **"👍"** → The mapping `"Open Notepad" → open_app:notepad` is cached.
4. Next time you say "Open Notepad":
   - **Cache HIT ⚡** → instant execution, bypassing the 2.5GB LLM inference.
   - *Note: To prevent false positives, commands under 8 words require a 90% similarity match, while longer commands require an 80% match.*

## ⌨️ Typing Commands

If you prefer not to use your voice, Trixie provides a direct typing interface:
- A text input box is located at the bottom of the floating overlay.
- Simply click, type your command (e.g., "open chrome" or "hello"), and press `Enter`.
- Typed commands bypass the Whisper transcription step entirely and flow through the exact same Intent Cache and LLM logic as voice commands.
- *Note: To maintain a clean and distraction-free interface, the on-screen command execution history has been removed.*

## ⚪ Minimal Ball Mode

If you want Trixie out of the way:
- Click the **`-`** (minimize) button in the top right of the overlay to shrink Trixie into a small, floating 'T' ball.
- **Click the ball** once to manually start or stop listening. The ball will pulse with a fast neon green glow while listening.
- **Right-click the ball** to reveal a quick-type text box directly underneath the ball. Type your command and press `Enter`!
- When processing an intent, the ball displays a rapid spinning neon cyan loading arc.
- If Trixie responds to a general query (like "Hello"), a **dynamic speech bubble** will elegantly pop up above the ball, and automatically fade away after 8 seconds.
- When feedback is requested, the 👍/👎 buttons will orbit the left and right sides of the ball.
- **Double-click the ball** to restore the full UI overlay.

## 🔍 Dynamic App Scanning

Instead of relying on a hardcoded whitelist, Trixie scans your system dynamically:
- At startup, she scans `ProgramData`, `AppData`, and the `Desktop` for `.lnk` shortcuts.
- This allows her to automatically discover and launch any installed software (like Chrome, Discord, or Steam) without needing exact file paths.

## 🚀 Setup

### 1. Requirements

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) package manager
- 16GB+ System RAM recommended

### 2. Installation

```bash
uv sync
```

That's it. uv creates the `.venv`, resolves, and installs everything.

### 3. Running

```bash
uv run python main.py
```

On first run, the LLM model (~2.5 GB) downloads automatically from HuggingFace. Whisper downloads automatically on first voice command.

### 4. Pre-download Models (optional)

```bash
uv run python download_models.py
```

### 5. Packaging into `.exe`

```bash
uv sync --extra build
uv run python package.py
```

## 🎯 Supported Commands

| Voice Command | Intent | What It Does |
|---|---|---|
| "Open Notepad" | `open_app` | Launches the application |
| "Close Chrome" | `close_app` | Force-kills the process |
| "Type hello world" | `string_type` | Types the text via keyboard |
| "Press ctrl+alt+delete" | `hotkey` | Sends the key combination |
| "Create a macro called setup" | `macro_creation` | Saves recent actions as a macro |
| "Run the macro setup" | `macro_execution` | Replays the saved macro |
| "What is the capital of France?" | `general_query` | Answers via LLM + TTS |

## 📄 License

MIT
