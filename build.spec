# -*- mode: python ; coding: utf-8 -*-
"""
Trixie — PyInstaller Spec File
Single-file EXE build with all dependencies bundled.
Models are NOT bundled — downloaded on first run.
Supports both CPU-only and NVIDIA GPU environments.
"""
from PyInstaller.utils.hooks import collect_all

block_cipher = None

# ── Collect all files for packages with native internals ─────
# These packages have .pyd/.dll internals that hiddenimports alone won't pick up
keyboard_datas, keyboard_binaries, keyboard_hiddenimports = collect_all("keyboard")
sounddevice_datas, sounddevice_binaries, sounddevice_hiddenimports = collect_all("sounddevice")
# llama_cpp needs its lib/ directory (native GGUF DLLs) bundled
llama_datas, llama_binaries, llama_hiddenimports = collect_all("llama_cpp")

# ── Hidden imports for runtime-imported packages ─────────────
hiddenimports = [
    "keyboard",
    "sounddevice",
    "llama_cpp",
    "faster_whisper",
    "piper",
    "onnxruntime",
    "numpy",
    "scipy",
    "psutil",
    "pynvml",
    "PySide6.QtCore",
    "PySide6.QtGui",
    "PySide6.QtWidgets",
    "platformdirs",
    *keyboard_hiddenimports,
    *sounddevice_hiddenimports,
    *llama_hiddenimports,
]

# ── Analysis ─────────────────────────────────────────────────
a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=[
        *keyboard_binaries,
        *sounddevice_binaries,
        *llama_binaries,
    ],
    datas=[
        ("assets", "assets"),
        *keyboard_datas,
        *sounddevice_datas,
        *llama_datas,
    ],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["matplotlib", "notebook", "jupyter", "IPython", "tkinter", "test"],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# ── Single-file EXE (--onefile mode) ─────────────────────────
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="Trixie",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon="assets/trixie.ico",
)
