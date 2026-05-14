# Trixie: Your Local AI Assistant - Quick Guide

Trixie is a local Windows voice assistant for controlling your PC. Hold a hotkey, speak naturally, and Trixie transcribes your command, figures out the intent, executes the action, and learns from your feedback.

## CPU-First Promise

Trixie is built to work without a GPU. CPU mode is the compatibility baseline.

If your machine has a compatible NVIDIA GPU, Trixie can use it to run faster. If no GPU is available, the app should continue on CPU with quantized local models. Expect CPU inference to be slower, especially on first load, but it should not break just because the machine has no GPU.

## Run From Source

Prerequisites:

- Windows 10/11
- Python 3.10+
- `uv`
- GPU optional

```powershell
uv sync
uv run python main.py
```

On first use, Trixie downloads its runtime models into `models/`. This can take a while, but later launches load from disk.

## Pre-Download Models

```powershell
uv run python download_models.py
```

This downloads the speech-to-text, LLM, and text-to-speech models before launching the app.

## Build The EXE

```powershell
uv sync --extra build
uv run python package.py
```

The output appears in `dist/`. Models are not bundled into the single-file executable; they download on first run or can be shipped beside the app in `models/`.

## How To Use

1. Launch Trixie.
2. Wait for the floating overlay or tray icon.
3. Hold `Ctrl + CapsLock`.
4. Speak a command.
5. Release the hotkey and let Trixie transcribe.
6. Confirm whether the action was correct when feedback buttons appear.

Example commands:

```text
Open Chrome
Open Notepad
Close Chrome
Type hello world
Press enter
Create a macro called setup
Run the macro setup
```

## Typing Instead Of Speaking

Use the text box in the floating overlay. Type a command and press `Enter`. This bypasses speech-to-text but still uses the same intent engine and cache.

## Minimal Ball Mode

Click the minimize button on the overlay to shrink Trixie into a floating `T` ball.

- Single-click the ball to start or stop listening.
- Right-click the ball to show the quick text input.
- Double-click the ball to restore the full overlay.

## First-Run Notes

- The first voice command can be slow because the STT model downloads and loads.
- CPU-only machines are supported; GPU acceleration is only a speed upgrade.
- Internet is needed only for downloading missing models.
- Runtime command processing is local after the models are present.
- If transcription accuracy feels off, test the microphone level and background noise first.

## Important Files

| File | Purpose |
|---|---|
| `main.py` | App entry point |
| `config.json` | Runtime model and Whisper settings |
| `download_models.py` | Pre-downloads runtime models |
| `core/audio.py` | Microphone capture and transcription |
| `core/model_manager.py` | Model download logic |
| `ui/app.py` | Floating overlay and tray UI |
