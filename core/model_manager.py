import os
import logging
import urllib.request
import sys

logger = logging.getLogger(__name__)

# Only the LLM model — vision removed
MODEL_REGISTRY = {
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

def download_model(model_key, models_dir="models"):
    if model_key not in MODEL_REGISTRY:
        logger.error(f"Unknown model key: {model_key}")
        return None
    info = MODEL_REGISTRY[model_key]
    dest = os.path.join(models_dir, info["filename"])
    if os.path.exists(dest):
        return dest
    os.makedirs(models_dir, exist_ok=True)
    print(f"\n{'='*60}")
    print(f"  Downloading: {info['description']}")
    print(f"  Size: {info['size_label']}")
    print(f"{'='*60}")
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
        os.rename(dest + ".tmp", dest)
        print(f"\n  [OK] Downloaded: {dest}\n")
        return dest
    except Exception as e:
        logger.error(f"Download failed: {e}")
        tmp = dest + ".tmp"
        if os.path.exists(tmp):
            os.remove(tmp)
        print(f"\n  [FAILED] Failed: {e}\n")
        return None

def ensure_model(model_key, models_dir="models"):
    info = MODEL_REGISTRY.get(model_key)
    if not info:
        return None
    dest = os.path.join(models_dir, info["filename"])
    if os.path.exists(dest):
        return dest
    return download_model(model_key, models_dir)
