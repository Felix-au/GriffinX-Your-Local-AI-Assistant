# Trixie: Your Local AI Assistant - User Guide

Trixie is an AI-powered desktop assistant for Windows. It lives in your tray, listens when you ask it to, and helps operate your computer through voice or typed commands.

The core promise is simple: your command pipeline runs locally. Trixie uses local speech-to-text, a local LLM for intent classification, a local command executor, a local history database, and offline text-to-speech.

## CPU-First Performance Model

Trixie is CPU-first. It is meant to run on ordinary Windows machines without requiring a dedicated GPU.

When CUDA is available, Trixie can use GPU acceleration to make transcription and model inference faster. When CUDA is not available, it uses CPU-friendly quantized settings instead. Any future model or pipeline change should preserve this rule: GPU support may improve speed, but lack of a GPU should not prevent the app from running.

## How It Works

```text
Voice or typed command
        |
        v
Speech-to-text, if voice was used
        |
        v
Intent classification by local LLM
        |
        v
Command execution, answer generation, or macro handling
        |
        v
Feedback cache learns successful mappings
```

## Startup

When `main.py` starts:

1. Trixie loads `config.json`.
2. The SQLite history database opens under `logs/`.
3. The audio engine prepares the microphone and STT model path.
4. The local LLM engine checks whether the Qwen model is available.
5. Piper TTS checks whether its voice files are available.
6. The PyQt6 tray icon and floating overlay appear.

If a required model is missing, Trixie downloads it into `models/`.

## Voice Command Path

### Step 1: Listening

Hold `Ctrl + CapsLock` or click the floating ball. Trixie records microphone audio at 16 kHz mono.

### Step 2: Transcription

When recording stops, Trixie sends the audio to `faster-whisper-medium.en`. The transcription prompt is biased toward common commands and app names such as Chrome, Notepad, shutdown, hotkeys, and typing commands.

### Step 3: Intent Classification

The transcript is sent to the local Qwen intent engine. The model must output JSON, for example:

```json
{"intent": "open_app", "target": "notepad"}
```

Supported intents include:

| Intent | Meaning |
|---|---|
| `open_app` | Open an app, file, or URL |
| `close_app` | Close an app/process |
| `string_type` | Type text into the active window |
| `hotkey` | Press a keyboard shortcut |
| `run_script` | Run an approved script/command |
| `macro_creation` | Save recent actions as a macro |
| `macro_execution` | Replay a saved macro |
| `general_query` | Answer a question |
| `delay` | Wait during macro playback |

### Step 4: Execution

Trixie routes the intent through the command executor. For example:

- `open_app:notepad` opens Notepad.
- `string_type:hello world` types text.
- `hotkey:ctrl+s` presses a shortcut.

### Step 5: Feedback

After an action, Trixie can ask whether it was correct. Positive feedback stores the transcript-to-intent mapping in the local cache. Future similar commands can skip LLM inference and run faster.

## Typed Command Path

Typed commands use the same intent cache, LLM, executor, and feedback system. The only skipped step is speech-to-text.

Use this when:

- Your microphone is unavailable.
- You want to test command parsing.
- You want exact wording for a complex command.

## Macro Workflow

Trixie can record recent successful actions into a named macro and replay them later.

Example:

```text
Create a macro called morning setup
Run the macro morning setup
```

Macros are stored locally in the SQLite database.

## Model Management

Trixie is designed to ship without large model files.

| Model | Download Trigger | Local Path |
|---|---|---|
| STT | First voice command or `download_models.py` | `models/faster-whisper-medium.en/` |
| LLM | First LLM use or `download_models.py` | `models/Qwen_Qwen3-4B-Q4_K_M.gguf` |
| TTS | Startup or `download_models.py` | `models/en_US-lessac-medium.onnx` |

To prepare all models:

```powershell
uv run python download_models.py
```

## Hardware Expectations

| Hardware | Behavior |
|---|---|
| CPU-only Windows PC | Supported baseline; slower inference, especially for voice transcription and first model load |
| NVIDIA CUDA GPU | Optional acceleration path; uses faster compute settings when available |
| No internet | Works only after models are already downloaded or shipped in `models/` |
| 16 GB RAM | Recommended for smoother local model loading |

## Troubleshooting

### Transcription is wrong

- Use a headset or move closer to the microphone.
- Reduce background noise.
- Keep commands short and direct.
- Prefer app names in common form: `Chrome`, `Notepad`, `File Explorer`.

### First command is slow

The model may be downloading or loading. This is expected on first run.

### Trixie opens the wrong app

Use the feedback buttons so the cache learns the correct mapping. You can also type the command once to test whether transcription or intent parsing caused the issue.

### No audio input

Check the Windows default microphone and app microphone permissions. Trixie uses the default input device through `sounddevice`.

## Packaging Notes

Build with:

```powershell
uv sync --extra build
uv run python package.py
```

The generated executable can be shipped without models, but first run will need internet access to download them. For offline distribution, ship the populated `models/` folder beside the executable.

## Privacy

Trixie does not need a cloud API for normal operation. After the initial model downloads, speech transcription, intent classification, action execution, history, macros, and TTS remain local.
