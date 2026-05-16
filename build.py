"""
GriffinX — Professional Build Pipeline
Produces a single-file Windows EXE via PyInstaller.
The output EXE always supports both CPU-only and NVIDIA GPU environments.
"""
import subprocess
import sys
import os
import shutil


def _banner():
    print()
    print("╔══════════════════════════════════════════════════╗")
    print("║       GriffinX — Build Pipeline  v1.0            ║")
    print("╚══════════════════════════════════════════════════╝")
    print()


def _step(num, label):
    print(f"🔍 Step {num}: {label}")


def _ok(msg):
    print(f"  ✅ {msg}")


def _fail(msg):
    print(f"  ❌ {msg}")
    sys.exit(1)


def main():
    _banner()

    # ── Step 1: Check PyInstaller ────────────────────────────
    _step(1, "Checking PyInstaller …")
    try:
        result = subprocess.run(
            ["uv", "run", "pyinstaller", "--version"],
            capture_output=True, text=True, check=True
        )
        version = result.stdout.strip()
        _ok(f"PyInstaller {version} found")
    except Exception:
        _fail("PyInstaller not found. Run: uv sync --extra build")

    # ── Step 2: Verify assets ────────────────────────────────
    _step(2, "Verifying assets …")
    required_assets = [
        "assets/trixie.ico",
        "assets/trixie.jpeg",
        "assets/trixie-circular.jpeg",
    ]
    for asset in required_assets:
        if os.path.exists(asset):
            _ok(asset)
        else:
            _fail(f"Missing: {asset}")

    # ── Step 3: Clean previous build ─────────────────────────
    _step(3, "Cleaning previous build artifacts …")
    for d in ["build", "dist"]:
        if os.path.exists(d):
            shutil.rmtree(d)
            _ok(f"Removed {d}/")
        else:
            _ok(f"{d}/ already clean")

    # ── Step 4: Build ────────────────────────────────────────
    _step(4, "Building single-file EXE …")
    print("  This may take several minutes …")

    cmd = [
        "uv", "run", "pyinstaller",
        "--clean", "-y",
        "build.spec"
    ]

    result = subprocess.run(cmd)
    if result.returncode != 0:
        _fail("PyInstaller build failed")
    _ok("PyInstaller build complete")

    # ── Summary ──────────────────────────────────────────────
    exe_path = os.path.join("dist", "GriffinX.exe")
    if not os.path.exists(exe_path):
        _fail(f"Expected {exe_path} not found")

    size_mb = os.path.getsize(exe_path) / (1024 * 1024)

    print()
    print("=" * 55)
    print("  🎉 Build complete!")
    print("=" * 55)
    print(f"  EXE:      {exe_path}")
    print(f"  Size:     {size_mb:.1f} MB")
    print(f"  Target:   CPU + NVIDIA GPU (universal)")
    print()
    print("  To run:")
    print("    dist\\GriffinX.exe")
    print()
    print("  Notes:")
    print("    • All Python dependencies are bundled (including pynvml)")
    print("    • The EXE runs on BOTH CPU-only and NVIDIA GPU systems")
    print("    • GPU gauges show real-time stats on NVIDIA, N/A otherwise")
    print("    • AI models (~4 GB) download from HuggingFace on first launch")
    print("    • Models cached at: models/ (next to the EXE)")
    print("    • Settings stored at: %LOCALAPPDATA%/GriffinX/settings.json")
    print("=" * 55)
    print()


if __name__ == "__main__":
    main()
