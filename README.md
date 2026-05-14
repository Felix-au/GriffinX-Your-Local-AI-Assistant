<h1 align="center">Trixie: Your Local AI Assistant</h1>
<p align="center">
  <strong>Voice-controlled desktop assistant that runs entirely on your machine</strong><br/>
  <em>Hold a hotkey → speak naturally → Trixie transcribes, thinks, acts, and speaks back — all offline</em>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/platform-Windows-0078D6?style=flat-square&logo=windows&logoColor=white" alt="Windows" />
  <img src="https://img.shields.io/badge/STT-Faster--Whisper-FF6F00?style=flat-square&logo=huggingface&logoColor=white" alt="Whisper" />
  <img src="https://img.shields.io/badge/LLM-Qwen3--4B--GGUF-blueviolet?style=flat-square" alt="Qwen" />
  <img src="https://img.shields.io/badge/TTS-Piper_Neural-41CD52?style=flat-square" alt="Piper" />
  <img src="https://img.shields.io/badge/ui-PyQt6-41CD52?style=flat-square&logo=qt&logoColor=white" alt="PyQt6" />
  <img src="https://img.shields.io/badge/license-MIT-green?style=flat-square" alt="License" />
</p>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Why Trixie?](#-why-trixie)
- [Features](#-features)
- [Architecture](#-architecture)
- [Pipeline Flow](#-pipeline-flow)
- [Model Pipeline](#-model-pipeline)
- [Quick Start](#-quick-start)
- [Hardware-Accelerated LLM Setup](#-hardware-accelerated-llm-setup)
- [Build Standalone EXE](#-build-standalone-exe)
- [Project Structure](#-project-structure)
- [Dependencies](#-dependencies)
- [Configuration](#-configuration)
- [Improvement Ideas](#-improvement-ideas)
- [Author](#-author)

---

## 🔍 Overview

**Trixie** is a Windows desktop assistant that lets you control your PC with your voice while keeping all inference local. It listens through push-to-talk, transcribes speech with a local Whisper model, classifies your intent with a local Qwen 3 4B LLM running via `llama.cpp`, executes desktop actions (open/close apps, type text, press hotkeys, run macros), learns from your feedback, and speaks back using offline Piper neural text-to-speech.

No cloud is required for normal use. Model files (~4 GB total) are downloaded on first run and then loaded from the local `models/` folder.

> Trixie is **CPU-first by design**. A GPU is optional — it accelerates inference but is never required. The app runs on any Windows 10/11 machine with 16 GB RAM.

---

## 🎯 Why Trixie?

> **Most AI assistants either live in a browser or depend on cloud APIs. Trixie gives you direct desktop control — offline.**

| | Cloud AI Assistants | Trixie |
|---|---|---|
| **Workflow** | Open browser → type prompt → wait → copy result | Hold hotkey → speak → Trixie acts immediately |
| **Privacy** | Voice and commands sent to cloud servers | Everything stays on your machine — STT, LLM, TTS, history |
| **Desktop Control** | Text-only responses, no system actions | Opens/closes apps, types text, presses hotkeys, runs macros |
| **Learning** | Stateless — no memory of your habits | Intent cache learns from feedback — repeated commands skip LLM |
| **Offline** | Requires constant internet | Works fully offline after one-time model download |
| **Latency** | Network round-trip per request | Direct local inference — sub-second for cached commands |
| **Voice Output** | Browser-based TTS or none | Offline neural TTS via Piper — natural-sounding speech |

---

## ✨ Features

### 🎙️ Voice Input
| Feature | Description |
|---|---|
| **Push-to-Talk** | Hold `Ctrl + CapsLock` to record; release to transcribe and process |
| **Local STT** | Faster-Whisper Medium English — runs on GPU (float16) or CPU (int8) |
| **Command Priming** | Transcription prompt biased toward common commands and app names for better accuracy |
| **VAD Filtering** | Voice Activity Detection filters silence — min 500ms silence threshold |

### 🧠 Intent Classification
| Feature | Description |
|---|---|
| **Local LLM** | Qwen 3 4B (Q4_K_M GGUF) via `llama-cpp-python` — 4-bit quantized, ~2.5 GB |
| **Structured Output** | LLM outputs JSON with `intent` and `target` fields |
| **Think-Block Stripping** | Automatically removes Qwen 3's `<think>` reasoning blocks |
| **Robust JSON Parsing** | Handles code fences, nested objects, and partial outputs |
| **GPU Auto-Offload** | `n_gpu_layers=-1` offloads all layers to GPU when available |

### ⚡ Smart Intent Cache
| Feature | Description |
|---|---|
| **Feedback-Driven** | Only verified-correct commands are cached |
| **Fuzzy Matching** | SequenceMatcher-based similarity (80% threshold, 90% for short commands) |
| **Cache-First Pipeline** | Cached commands skip LLM inference entirely — instant execution |
| **Use Counting** | Tracks how often each cached mapping is used |

### 🖥️ Desktop Actions
| Feature | Description |
|---|---|
| **App Launch** | Opens any app via whitelist + dynamic Start Menu/Desktop shortcut scanning |
| **App Close** | Kills processes by executable name via `taskkill` |
| **Text Typing** | Types text into the active window via `pyautogui` |
| **Hotkeys** | Presses keyboard shortcuts (e.g., `ctrl+s`, `alt+f4`) |
| **Script Execution** | Runs `.py` scripts (safety-restricted to Python files only) |
| **Delay** | Timed pauses during macro playback (max 30 seconds) |

### 🔁 Macro System
| Feature | Description |
|---|---|
| **Voice-Created** | Say "Create a macro called morning setup" to save recent actions |
| **Voice-Triggered** | Say "Run the macro morning setup" to replay |
| **Hotkey-Bound** | Macros can be assigned global hotkeys for instant trigger |
| **History-Derived** | Macros are built from the last N successful actions in the interaction log |
| **SQLite-Persisted** | Stored in the local database — survive restarts |

### 🔊 Text-to-Speech
| Feature | Description |
|---|---|
| **Piper Neural TTS** | Offline neural synthesis — Lessac Medium voice (22050 Hz, 16-bit mono) |
| **Async Playback** | Speech runs in a background thread — never blocks the UI |
| **WAV Pipeline** | Synthesizes to in-memory WAV buffer → PCM16 → float32 → `sounddevice` |

### 🖥️ Desktop UI
| Feature | Description |
|---|---|
| **Floating Overlay** | Translucent glassmorphic panel — shows status, transcript, and response |
| **Minimal Ball Mode** | Shrinks to a floating "T" ball with speech bubble responses |
| **Neon Animations** | Green pulse ring when listening; cyan arc spinner when thinking |
| **System Tray** | Purple gradient tray icon with show/hide/quit context menu |
| **Text Input** | Type commands directly via the input box — bypasses STT |
| **Feedback Buttons** | 👍/👎 buttons for training the intent cache |
| **Dynamic Resize** | Overlay grows upward to fit long transcripts and responses |
| **Draggable** | Click and drag to reposition anywhere on screen |

---

## 🏗 Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                      Trixie Desktop App                             │
│                                                                     │
│  ┌────────────────┐    ┌─────────────────────────────────────────┐  │
│  │   Keyboard     │    │          UI Layer (PyQt6)               │  │
│  │   Listener     │    │                                         │  │
│  │                │    │  ┌──────────────┐  ┌─────────────────┐  │  │
│  │ Ctrl+CapsLock  ├───►│  │   Floating   │  │   System Tray   │  │  │
│  │ push-to-talk   │    │  │   Overlay    │  │   Icon + Menu   │  │  │
│  │ hook           │    │  │   (expanded  │  └─────────────────┘  │  │
│  └────────────────┘    │  │    + ball)   │                       │  │
│                        │  └──────┬───────┘                       │  │
│                        │         │ text input / voice trigger    │  │
│                        └─────────┼───────────────────────────────┘  │
│                                  │                                  │
│  ┌───────────────────────────────┼───────────────────────────────┐  │
│  │                     Core Engine                               │  │
│  │                                                               │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌────────────────────┐   │  │
│  │  │ Audio Engine │  │ LLM Engine   │  │ Command Executor   │   │  │
│  │  │              │  │              │  │                    │   │  │
│  │  │ Microphone   │  │ Qwen 3 4B    │  │ open/close apps    │   │  │
│  │  │ capture at   │  │ GGUF via     │  │ type text          │   │  │
│  │  │ 16kHz mono   │  │ llama.cpp    │  │ press hotkeys      │   │  │
│  │  │      ↓       │  │      ↓       │  │ run scripts        │   │  │
│  │  │ Faster-      │  │ JSON intent  │  │ macro playback     │   │  │
│  │  │ Whisper STT  │  │ extraction   │  └────────────────────┘   │  │
│  │  └──────────────┘  └──────────────┘                           │  │
│  │                                                               │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌────────────────────┐   │  │
│  │  │ Context      │  │ DB Manager   │  │ Macro Manager      │   │  │
│  │  │ Manager      │  │              │  │                    │   │  │
│  │  │ System       │  │ SQLite:      │  │ Create from        │   │  │
│  │  │ prompt +     │  │ history,     │  │ history, bind      │   │  │
│  │  │ short-term   │  │ intent cache │  │ hotkeys, replay    │   │  │
│  │  │ memory       │  │ macros       │  └────────────────────┘   │  │
│  │  └──────────────┘  └──────────────┘                           │  │
│  │                                                               │  │
│  │  ┌──────────────┐  ┌──────────────┐                           │  │
│  │  │ TTS Engine   │  │ Model        │                           │  │
│  │  │ Piper neural │  │ Manager      │                           │  │
│  │  │ offline      │  │ Auto-download│                           │  │
│  │  │ synthesis    │  │ from HF      │                           │  │
│  │  └──────────────┘  └──────────────┘                           │  │
│  └───────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Pipeline Flow

```
Hold Ctrl+CapsLock → Microphone captures 16kHz mono audio
     │
     ▼
Release key → Audio sent to Faster-Whisper (GPU float16 / CPU int8)
     │            Transcription prompt primes for command vocabulary
     ▼
Transcript: "Open Chrome"
     │
     ├──► Intent Cache Check (SequenceMatcher ≥ 80% similarity)
     │         │
     │    ┌────┴─────┐
     │    │ HIT      │ → Execute immediately (skip LLM) → ⚡ instant
     │    │ MISS     │ → Continue to LLM ↓
     │    └──────────┘
     │
     ▼
Context Manager assembles system prompt + last 5 interactions
     │
     ▼
Qwen 3 4B (llama.cpp) → JSON output: {"intent":"open_app","target":"chrome"}
     │                    Think-blocks stripped, robust JSON extraction
     ▼
Command Executor routes intent:
  → open_app: resolve target → subprocess.Popen via cmd.exe start
  → close_app: taskkill /IM target.exe /F
  → string_type: pyautogui.write(target)
  → hotkey: pyautogui.hotkey(*keys)
  → macro_creation: save last N actions to SQLite
  → macro_execution: replay saved action sequence
  → general_query: return LLM's text response
     │
     ▼
TTS Engine speaks response (Piper neural, async thread)
     │
     ▼
Feedback buttons appear (👍/👎) → positive = cache the mapping
     │
     ▼
Interaction logged to SQLite (timestamp, input, intent, status, feedback)
```

---

## 🧪 Model Pipeline

Trixie ships without large model files. On first use it downloads three models:

| Model | Engine | Size | Purpose | Local Path |
|---|---|---|---|---|
| Faster-Whisper Medium English | CTranslate2 | ~1.5 GB | Speech-to-text | `models/faster-whisper-medium.en/` |
| Qwen 3 4B (Q4_K_M GGUF) | llama.cpp | ~2.5 GB | Intent classification & chat | `models/Qwen_Qwen3-4B-Q4_K_M.gguf` |
| Piper Lessac Medium | ONNX Runtime | ~15 MB | Text-to-speech | `models/en_US-lessac-medium.onnx` |

### Hardware Adaptation

| Hardware | Whisper | LLM | TTS |
|---|---|---|---|
| **NVIDIA GPU** | CUDA, float16 | All layers on GPU (`n_gpu_layers=-1`) | CPU (ONNX) |
| **AMD GPU** | CPU, int8 | Vulkan backend (via install.py) | CPU (ONNX) |
| **CPU only** | CPU, int8 | CPU inference | CPU (ONNX) |

Pre-download all models before first use:

```powershell
uv run python download_models.py
```

---

## 🚀 Quick Start

### Prerequisites

- Windows 10/11
- Python 3.10+
- [`uv`](https://docs.astral.sh/uv/) package manager
- 16 GB RAM recommended
- GPU optional (NVIDIA CUDA or AMD Vulkan); CPU mode is the default baseline

### Install & Run

```powershell
# 1. Clone the repository
git clone https://github.com/Felix-au/Trixie-Your-Local-AI-Assistant.git
cd Trixie-Your-Local-AI-Assistant

# 2. Install dependencies
uv sync

# 3. (Optional) Pre-download models
uv run python download_models.py

# 4. Run Trixie
uv run python main.py
```

On first launch:
- Missing models auto-download from HuggingFace (~4 GB total)
- GPU is auto-detected for Whisper (CUDA float16 / CPU int8)
- The floating overlay and system tray icon appear
- The first voice command triggers model loading

### Use It

1. **Hold `Ctrl + CapsLock`** — Trixie starts listening (green pulse)
2. **Speak a command** — e.g., "Open Chrome", "Type hello world", "Press ctrl+s"
3. **Release the hotkey** — Trixie transcribes, classifies intent, and executes
4. **Confirm with 👍/👎** — positive feedback caches the command for instant future use
5. **Or type** — use the text input box for exact-wording commands

---

## 🔧 Hardware-Accelerated LLM Setup

By default, `llama-cpp-python` installs with CPU-only support. For GPU acceleration, run the included installer:

```powershell
python install.py
```

This script:
1. Installs base dependencies from `requirements.txt`
2. Detects your GPU vendor via WMIC (NVIDIA / AMD / Intel)
3. Rebuilds `llama-cpp-python` with the appropriate backend:
   - **NVIDIA** → `CMAKE_ARGS="-DGGML_CUDA=on"`
   - **AMD/Intel** → `CMAKE_ARGS="-DGGML_VULKAN=on"`
4. Falls back to CPU-only if the build fails

> **Requires:** Visual Studio C++ Build Tools for compilation.

---

## 📦 Build Standalone EXE

```powershell
uv sync --extra build
uv run python package.py
```

Output:

```
dist/
└── Trixie.exe      # Single-file executable (windowed, no console)
                     # Python runtime + all deps bundled via PyInstaller
```

### What's Bundled Inside the EXE
- Python runtime + all dependencies (llama-cpp-python, faster-whisper, PyQt6, piper-tts, etc.)
- All `core/` and `ui/` modules
- Hidden imports for keyboard, sounddevice, llama_cpp, faster_whisper

### What Downloads on First Run
- **STT model**: Faster-Whisper Medium English (~1.5 GB) → `models/faster-whisper-medium.en/`
- **LLM model**: Qwen 3 4B GGUF (~2.5 GB) → `models/Qwen_Qwen3-4B-Q4_K_M.gguf`
- **TTS model**: Piper Lessac voice + config (~15 MB) → `models/en_US-lessac-medium.onnx`

> **Why not bundle the models?** The models total ~4 GB — bundling would create an impractically large executable. Instead, they download once on first launch and are cached permanently in `models/`.

For offline distribution, ship the populated `models/` folder beside `Trixie.exe`.

---

## 📁 Project Structure

```
Trixie/
├── main.py                      # App entry point — orchestrator + feedback loop (233 lines)
├── config.json                  # Runtime configuration (model paths, Whisper settings)
├── install.py                   # GPU-aware dependency installer (71 lines)
├── package.py                   # PyInstaller build script (45 lines)
├── download_models.py           # Pre-downloads all runtime models (28 lines)
├── pyproject.toml               # Project metadata + dependencies (uv/pip)
│
├── core/                        # Backend engine
│   ├── __init__.py
│   ├── audio.py                 # Microphone capture + Faster-Whisper STT (139 lines)
│   ├── llm_engine.py            # Qwen 3 4B intent classifier via llama.cpp (107 lines)
│   ├── context.py               # System prompt + short-term memory (31 lines)
│   ├── executor.py              # Desktop action execution + app resolution (185 lines)
│   ├── macro_manager.py         # Macro creation, storage, and hotkey binding (69 lines)
│   ├── tts_engine.py            # Piper neural TTS with async playback (70 lines)
│   ├── model_manager.py         # HuggingFace model download + caching (127 lines)
│   └── db.py                    # SQLite: history, intent cache, macros (147 lines)
│
├── ui/                          # PyQt6 GUI
│   ├── __init__.py
│   └── app.py                   # Floating overlay + system tray + UIEngine (546 lines)
│
├── models/                      # Runtime model storage (auto-populated, gitignored)
├── logs/                        # SQLite database storage (gitignored)
│
├── Trixie.md                    # Detailed user guide with worked examples
├── guide.md                     # Quick-start guide
├── README.md                    # This file
├── LICENSE                      # MIT License
└── .gitignore                   # Ignores models, logs, venv, build artifacts
```

---

## 📚 Dependencies

| Package | Purpose |
|---|---|
| `faster-whisper` | Local speech-to-text (CTranslate2 backend) |
| `huggingface-hub` | Model downloading from HuggingFace |
| `llama-cpp-python` | Local LLM inference for Qwen 3 4B GGUF |
| `PyQt6` | Desktop UI framework (overlay, tray, dialogs) |
| `piper-tts` | Offline neural text-to-speech |
| `onnxruntime` | ONNX model runtime for Piper TTS |
| `keyboard` | Global hotkey hooks (push-to-talk) |
| `sounddevice` | Audio capture and playback |
| `numpy` | Audio array processing |
| `scipy` | Signal processing utilities |
| `pyautogui` | Desktop automation (typing, hotkeys) |
| `mss` | Screen capture utilities |
| `Pillow` | Image processing |
| `pyinstaller` | Standalone EXE packaging (optional build dependency) |

---

## ⚙️ Configuration

All runtime configuration lives in [`config.json`](config.json):

| Key | Default | Description |
|---|---|---|
| `db_path` | `logs/history.db` | SQLite database location |
| `model_paths.whisper` | `models/faster-whisper-medium.en` | Path to Whisper model directory |
| `model_paths.llm` | `models/Qwen_Qwen3-4B-Q4_K_M.gguf` | Path to GGUF model file |
| `whisper_device` | `auto` | STT device: `auto`, `cuda`, or `cpu` |
| `whisper_compute_type` | `default` | STT precision: `default`, `float16`, or `int8` |
| `cache_threshold` | `0.80` | Fuzzy-match threshold for intent cache (0.0–1.0) |

### Auto-Detected Settings

| Hardware | `whisper_device` resolves to | `whisper_compute_type` resolves to |
|---|---|---|
| NVIDIA CUDA GPU detected | `cuda` | `float16` |
| No CUDA GPU | `cpu` | `int8` |

---

## 💡 Improvement Ideas

### High Impact
- **Conversation Mode** — Multi-turn dialogue for complex queries instead of single-shot intent classification
- **Custom Wake Word** — Always-on listening with a wake word (e.g., "Hey Trixie") instead of push-to-talk
- **Plugin System** — Let users add custom intents and executors without modifying core code
- **Cross-Platform** — Port to macOS (Core Audio) and Linux (PulseAudio) for microphone and app control

### Medium Impact
- **Streaming TTS** — Stream Piper output as it generates for reduced perceived latency
- **Multiple Voices** — Let users choose from different Piper voice models
- **Macro Editor** — Visual UI for editing, reordering, and testing macro steps
- **Command Suggestions** — Auto-suggest likely commands based on history patterns

### Polish
- **Overlay Themes** — Light/dark/custom theme options for the floating overlay
- **Accessibility** — Screen reader support and keyboard-only navigation
- **Auto-Update** — Check GitHub releases for new versions on startup
- **Telemetry Dashboard** — Show inference latency, cache hit rate, and model memory usage

---

## 👤 Author

**Felix-au** (Harshit Soni)

- 🔗 GitHub: [github.com/Felix-au](https://github.com/Felix-au)
- 📧 Email: [harshit.soni.23cse@bmu.edu.in](mailto:harshit.soni.23cse@bmu.edu.in)

---

<p align="center">
  <sub>Built for users who want AI desktop control without the cloud.</sub>
</p>
