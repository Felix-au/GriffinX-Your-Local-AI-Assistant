"""
Trixie Model Downloader
Downloads runtime models from Hugging Face.
Models also auto-download at runtime if missing.
"""
from core.model_manager import MODEL_REGISTRY, ensure_model


def main():
    print("=" * 60)
    print("  Trixie: Your Local AI Assistant")
    print("  Model Downloader")
    print("=" * 60)
    print()

    for key, info in MODEL_REGISTRY.items():
        print(f"  - {info['description']} ({info['size_label']})")

    print()
    for key in ("stt", "llm", "tts_model", "tts_config"):
        path = ensure_model(key)
        status = "OK" if path else "FAILED"
        print(f"\n  [{status}] {MODEL_REGISTRY[key]['description']}: {path or 'FAILED'}")


if __name__ == "__main__":
    main()
