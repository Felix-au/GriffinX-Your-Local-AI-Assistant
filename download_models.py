"""
Trixie Model Downloader
Downloads the LLM model from HuggingFace.
Models also auto-download at runtime if missing.
"""
from core.model_manager import ensure_model, MODEL_REGISTRY

def main():
    print("=" * 60)
    print("  Trixie — Model Downloader")
    print("  Your PC, Your Voice, No Cloud.")
    print("=" * 60)
    print()
    for key, info in MODEL_REGISTRY.items():
        print(f"  • {info['description']} ({info['size_label']})")
    print("\n  Whisper STT downloads automatically on first boot.\n")
    
    path = ensure_model("llm")
    status = "✅" if path else "❌"
    print(f"\n  {status} {MODEL_REGISTRY['llm']['description']}: {path or 'FAILED'}\n")

if __name__ == "__main__":
    main()
