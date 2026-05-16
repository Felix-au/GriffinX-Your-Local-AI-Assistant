# GriffinX v1.0 Release Notes 🚀

Welcome to the first official release of **GriffinX: Your Local AI Assistant**! 

GriffinX is a voice-controlled Windows desktop assistant that runs entirely on your machine. GriffinX v1.0 release brings a complete offline pipeline—transcription, intent classification, desktop execution, and text-to-speech—ensuring your privacy without any cloud dependency.

## 🌟 Key Features

### 🧠 Local AI Pipeline
*   **Speech-to-Text (STT):** Integrated **Faster-Whisper Medium English** for fast and accurate voice transcription. It runs seamlessly on your GPU (float16) or CPU (int8) with VAD filtering for silence.
*   **Intent Classification:** Powered by **Qwen 3 4B** (4-bit quantized GGUF via `llama.cpp`). It accurately translates natural language into structured desktop actions, smartly stripping reasoning blocks for faster response times.
*   **Text-to-Speech (TTS):** Features offline **Piper Neural TTS** (Lessac Medium voice) for natural-sounding, asynchronous speech playback that never blocks the UI.

### 🖥️ Desktop Control & Automation
*   **App Management:** Dynamically opens applications by scanning Start Menu and Desktop shortcuts, and seamlessly closes apps.
*   **Keyboard & Text:** Type text directly into active windows or execute complex keyboard shortcuts via voice.
*   **Smart Macro System:** Say "Create a macro" to save your recent actions. Bind them to hotkeys or run them via voice commands for automated workflows.

### ⚡ Smart Intent Cache (Learning System)
*   **Feedback-Driven:** Click 👍 on successful commands to cache the action mapping.
*   **Instant Execution:** Cached commands use fuzzy matching (≥80% similarity) to skip the LLM inference entirely, providing **instant execution** for your most-used commands.

### 🎨 Premium UI & Dashboard
*   **Dashboard Command Centre:** Features a beautiful golden-brown theme with real-time system resource gauges (CPU, RAM, GPU, VRAM) and live model download progress bars.
*   **Floating Ball & Overlay:** A compact, draggable desktop avatar with neon state animations (green pulse for listening, cyan arc for thinking). Expand it to a translucent glassmorphic overlay for text input and history.
*   **System Tray Integration:** Always runs quietly in the background.

### 📦 Standalone Executable
*   **Plug and Play:** The `GriffinX.exe` is a fully self-contained application. 
*   **Cross-Hardware Compatibility:** The exact same executable runs out-of-the-box on **both CPU-only and NVIDIA GPU** systems without any manual modification.
*   **Smart Model Management:** To keep the executable size lightweight, the ~4GB AI models are not bundled. They will automatically download on your first launch and cache permanently in a local `models/` directory.

---

### 📝 Getting Started
Simply run `GriffinX.exe`. The Dashboard will open and begin downloading the necessary models. Once finished, hold `Ctrl + CapsLock` (default) and speak your first command!

*Thank you for using GriffinX — built for users who want AI desktop control without the cloud.*
