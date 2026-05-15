r"""
Windows Registry startup manager for Trixie.
Manages the HKCU\Software\Microsoft\Windows\CurrentVersion\Run entry.
"""
import sys
import os
import logging

logger = logging.getLogger(__name__)

_APP_NAME = "Trixie"
_REG_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"


def _get_exe_path() -> str:
    """Get the correct path for the startup entry (frozen EXE or dev script)."""
    if getattr(sys, "frozen", False):
        return sys.executable
    else:
        # Dev mode: python main.py
        return f'"{sys.executable}" "{os.path.abspath("main.py")}"'


def enable_startup():
    """Add Trixie to Windows startup via Registry."""
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, _REG_PATH, 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, _APP_NAME, 0, winreg.REG_SZ, _get_exe_path())
        winreg.CloseKey(key)
        logger.info("Startup entry added to Windows Registry")
    except Exception as e:
        logger.error(f"Failed to enable startup: {e}")


def disable_startup():
    """Remove Trixie from Windows startup."""
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, _REG_PATH, 0, winreg.KEY_SET_VALUE)
        try:
            winreg.DeleteValue(key, _APP_NAME)
            logger.info("Startup entry removed from Windows Registry")
        except FileNotFoundError:
            pass  # Already absent
        winreg.CloseKey(key)
    except Exception as e:
        logger.error(f"Failed to disable startup: {e}")


def is_startup_enabled() -> bool:
    """Check if Trixie is set to start at boot."""
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, _REG_PATH, 0, winreg.KEY_READ)
        try:
            winreg.QueryValueEx(key, _APP_NAME)
            winreg.CloseKey(key)
            return True
        except FileNotFoundError:
            winreg.CloseKey(key)
            return False
    except Exception:
        return False
