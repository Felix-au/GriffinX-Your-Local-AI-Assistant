"""
Settings persistence — stores user preferences in %LOCALAPPDATA%/GriffinX/settings.json.
Atomic writes via .tmp + os.rename.
"""
import os
import json
import logging
from pathlib import Path

import platformdirs

logger = logging.getLogger(__name__)

SETTINGS_DIR = Path(platformdirs.user_data_dir("GriffinX", appauthor=False))
SETTINGS_FILE = SETTINGS_DIR / "settings.json"

DEFAULT_SETTINGS = {
    "start_at_startup": True,
    "hotkey": "ctrl+caps lock",
}


def load_settings() -> dict:
    """Load settings from disk, returning defaults if file doesn't exist."""
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            # Merge with defaults (in case new keys were added)
            merged = {**DEFAULT_SETTINGS, **data}
            return merged
        except Exception as e:
            logger.warning(f"Failed to load settings, using defaults: {e}")
    return dict(DEFAULT_SETTINGS)


def save_settings(data: dict):
    """Atomically write the full settings dict to disk."""
    SETTINGS_DIR.mkdir(parents=True, exist_ok=True)
    tmp_path = SETTINGS_FILE.with_suffix(".tmp")
    try:
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        # Atomic rename (Windows: need to remove target first)
        if SETTINGS_FILE.exists():
            os.remove(SETTINGS_FILE)
        os.rename(tmp_path, SETTINGS_FILE)
        logger.info(f"Settings saved to {SETTINGS_FILE}")
    except Exception as e:
        logger.error(f"Failed to save settings: {e}")
        if tmp_path.exists():
            os.remove(tmp_path)


def update_setting(key: str, value):
    """Load, update a single key, and save."""
    data = load_settings()
    data[key] = value
    save_settings(data)
