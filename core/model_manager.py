import os
import logging
import urllib.request
import sys
from pathlib import Path

logger = logging.getLogger(__name__)


class ModelDownloadSignals:
    """Optional Qt signal emitter for download progress.
    Avoids hard PySide6 dependency at module level — instantiate only when Qt is running.
    """
    def __init__(self):
        try:
            from PySide6.QtCore import QObject, Signal

            class _Emitter(QObject):
                download_started = Signal(str, str)    # (model_key, description)
                download_progress = Signal(str, object, object)  # (model_key, downloaded_bytes, total_bytes)
                download_finished = Signal(str, str)   # (model_key, path)
                download_failed = Signal(str, str)     # (model_key, error)
                model_already_present = Signal(str, str)  # (model_key, path)

            self._emitter = _Emitter()
            self.download_started = self._emitter.download_started
            self.download_progress = self._emitter.download_progress
            self.download_finished = self._emitter.download_finished
            self.download_failed = self._emitter.download_failed
            self.model_already_present = self._emitter.model_already_present
        except ImportError:
            self._emitter = None

# Only the LLM model — vision removed
MODEL_REGISTRY = {
    "stt": {
        "repo_id": "Systran/faster-whisper-medium.en",
        "dirname": "faster-whisper-medium.en",
        "allow_patterns": ["config.json", "model.bin", "tokenizer.json", "vocabulary.*"],
        "size_label": "~1.5 GB",
        "description": "Faster-Whisper Medium English (Speech-to-Text)"
    },
    "llm": {
        "filename": "Qwen_Qwen3-4B-Q4_K_M.gguf",
        "url": "https://huggingface.co/bartowski/Qwen_Qwen3-4B-GGUF/resolve/main/Qwen_Qwen3-4B-Q4_K_M.gguf",
        "size_label": "~2.5 GB",
        "description": "Qwen 3 4B (Intent Classification & Chat)"
    },
    "tts_model": {
        "filename": "en_US-lessac-medium.onnx",
        "url": "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/medium/en_US-lessac-medium.onnx",
        "size_label": "~15 MB",
        "description": "Piper TTS Voice Model (Neural)"
    },
    "tts_config": {
        "filename": "en_US-lessac-medium.onnx.json",
        "url": "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json",
        "size_label": "~1 KB",
        "description": "Piper TTS Voice Config"
    }
}

def _progress_hook(downloaded, total_size):
    if total_size > 0:
        pct = downloaded * 100 / total_size
        filled = int(30 * downloaded / total_size)
        bar = "#" * filled + "-" * (30 - filled)
        sys.stdout.write(f"\r  [{bar}] {pct:.1f}% - {downloaded / (1024**3):.2f} / {total_size / (1024**3):.2f} GB")
        sys.stdout.flush()

def download_model(model_key, models_dir="models", signals=None):
    if model_key not in MODEL_REGISTRY:
        logger.error(f"Unknown model key: {model_key}")
        return None
    info = MODEL_REGISTRY[model_key]
    if "repo_id" in info:
        return download_huggingface_snapshot(model_key, models_dir, signals)

    dest = os.path.join(models_dir, info["filename"])
    if os.path.exists(dest):
        if signals and hasattr(signals, 'model_already_present'):
            signals.model_already_present.emit(model_key, dest)
        return dest
    os.makedirs(models_dir, exist_ok=True)
    print(f"\n{'='*60}")
    print(f"  Downloading: {info['description']}")
    print(f"  Size: {info['size_label']}")
    print(f"{'='*60}")
    if signals and hasattr(signals, 'download_started'):
        signals.download_started.emit(model_key, info['description'])
    req = urllib.request.Request(info["url"], headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req) as resp, open(dest + ".tmp", "wb") as f:
            total = int(resp.info().get("Content-Length", 0))
            downloaded = 0
            while True:
                data = resp.read(1024 * 64)
                if not data:
                    break
                f.write(data)
                downloaded += len(data)
                _progress_hook(downloaded, total)
                if signals and hasattr(signals, 'download_progress'):
                    signals.download_progress.emit(model_key, downloaded, total)
        os.rename(dest + ".tmp", dest)
        print(f"\n  [OK] Downloaded: {dest}\n")
        if signals and hasattr(signals, 'download_finished'):
            signals.download_finished.emit(model_key, dest)
        return dest
    except Exception as e:
        logger.error(f"Download failed: {e}")
        tmp = dest + ".tmp"
        if os.path.exists(tmp):
            os.remove(tmp)
        print(f"\n  [FAILED] Failed: {e}\n")
        if signals and hasattr(signals, 'download_failed'):
            signals.download_failed.emit(model_key, str(e))
        return None

def download_huggingface_snapshot(model_key, models_dir="models", signals=None):
    info = MODEL_REGISTRY[model_key]
    dest = Path(models_dir) / info["dirname"]
    required_files = ["config.json", "model.bin", "tokenizer.json"]

    if dest.exists() and all((dest / filename).exists() for filename in required_files):
        if signals and hasattr(signals, 'model_already_present'):
            signals.model_already_present.emit(model_key, str(dest))
        return str(dest)

    print(f"\n{'='*60}")
    print(f"  Downloading: {info['description']}")
    print(f"  Size: {info['size_label']}")
    print(f"  Destination: {dest}")
    print(f"{'='*60}")
    if signals and hasattr(signals, 'download_started'):
        signals.download_started.emit(model_key, info['description'])

    try:
        from huggingface_hub import snapshot_download

        dest.mkdir(parents=True, exist_ok=True)
        path = snapshot_download(
            repo_id=info["repo_id"],
            local_dir=dest,
            allow_patterns=info.get("allow_patterns"),
            max_workers=4,
        )
        print(f"\n  [OK] Downloaded: {path}\n")
        if signals and hasattr(signals, 'download_finished'):
            signals.download_finished.emit(model_key, str(path))
        return str(path)
    except Exception as e:
        logger.error(f"Hugging Face snapshot download failed: {e}")
        print(f"\n  [FAILED] Failed: {e}\n")
        if signals and hasattr(signals, 'download_failed'):
            signals.download_failed.emit(model_key, str(e))
        return None

def ensure_model(model_key, models_dir="models", signals=None):
    info = MODEL_REGISTRY.get(model_key)
    if not info:
        return None
    if "repo_id" in info:
        return download_huggingface_snapshot(model_key, models_dir, signals)

    dest = os.path.join(models_dir, info["filename"])
    if os.path.exists(dest):
        if signals and hasattr(signals, 'model_already_present'):
            signals.model_already_present.emit(model_key, dest)
        return dest
    return download_model(model_key, models_dir, signals)
