# Trixie: Your Local AI Assistant

Trixie is a Windows desktop assistant that lets you control your PC with your voice while keeping inference local. It listens through push-to-talk, transcribes speech with a local Whisper model, classifies your intent with a local LLM, executes desktop actions, learns from feedback, and speaks back using offline neural text-to-speech.

No cloud is required for normal use. Model files are downloaded on first run and then loaded from the local `models/` folder.

## Why Trixie?

Most AI assistants either live in a browser or depend on cloud APIs. Trixie is built for direct desktop control:

| Need | Trixie |
|---|---|
| Voice control | Push-to-talk command capture with local speech-to-text |
| Privacy | Speech, intent parsing, history, and TTS stay on your machine |
| Desktop actions | Open/close apps, type text, press hotkeys, run scripts, and replay macros |
| Learning | Verified commands are cached so repeated actions get faster |
| Offline use | Runtime models are local after the first download |

## Features

- Voice control with `Ctrl + CapsLock`
- Local speech-to-text using `faster-whisper-medium.en`
- Command vocabulary priming for better accented recognition of app names and actions
- Local Qwen 3 4B intent classification through `llama.cpp`
- Smart intent cache for repeated commands
- Macro recording and replay
- Offline Piper neural text-to-speech
- Floating PyQt6 overlay with minimal ball mode
- Dynamic app discovery from Windows shortcuts and app paths
- First-run model downloader for STT, LLM, and TTS assets

## Architecture

```text
main.py                  App orchestrator and feedback loop
core/
  audio.py               Microphone capture and faster-whisper STT
  llm_engine.py          Local Qwen intent classifier
  context.py             Prompt and short-term command memory
  executor.py            Desktop action execution
  macro_manager.py       Macro creation and replay
  tts_engine.py          Offline Piper speech output
  model_manager.py       Runtime model downloads
  db.py                  SQLite history and intent cache
ui/
  app.py                 PyQt6 tray icon and floating overlay
```

## Model Downloads

Trixie is intended to ship without large model files. On first use it downloads:

| Model | Purpose | Destination |
|---|---|---|
| Faster-Whisper Medium English | Speech-to-text | `models/faster-whisper-medium.en/` |
| Qwen 3 4B GGUF | Intent classification and chat | `models/Qwen_Qwen3-4B-Q4_K_M.gguf` |
| Piper Lessac voice | Text-to-speech | `models/en_US-lessac-medium.onnx` |

You can pre-download everything with:

```powershell
uv run python download_models.py
```

## Quick Start

Requirements:

- Windows 10/11
- Python 3.10+
- `uv`
- 16 GB RAM recommended

Install dependencies:

```powershell
uv sync
```

Run Trixie:

```powershell
uv run python main.py
```

The first voice command may take time because the STT model downloads and loads. Later launches use the local copy.

## Usage

Hold `Ctrl + CapsLock` and say a command:

```text
Open Chrome
Open Notepad
Type hello world
Press ctrl alt delete
Create a macro called setup
Run the macro setup
What is the capital of France?
```

You can also type directly into the floating overlay and press `Enter`. Typed commands go through the same intent cache and LLM path as voice commands.

## Build Standalone EXE

```powershell
uv sync --extra build
uv run python package.py
```

The executable is written to `dist/`. Large models are not bundled; first run downloads them into the local `models/` folder unless you ship that folder beside the app.

## Configuration

Runtime settings live in [config.json](config.json):

```json
{
  "model_paths": {
    "whisper": "models/faster-whisper-medium.en",
    "llm": "models/Qwen_Qwen3-4B-Q4_K_M.gguf"
  },
  "whisper_device": "auto",
  "whisper_compute_type": "default"
}
```

On CUDA systems, Trixie uses `float16`. On CPU, it uses `int8`.

## Privacy

Trixie stores command history and feedback in a local SQLite database under `logs/`. Speech recognition, intent parsing, macro handling, and speech output run locally after model download.

## License

MIT. See [LICENSE](LICENSE).
