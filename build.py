"""
Trixie — Professional Build Pipeline
Produces a single-file Windows EXE via PyInstaller.
"""
import subprocess
import sys
import os
import shutil


def _banner():
    print()
    print("╔══════════════════════════════════════════╗")
    print("║        Trixie — Build Pipeline           ║")
    print("╚══════════════════════════════════════════╝")
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
    exe_path = os.path.join("dist", "Trixie.exe")
    if not os.path.exists(exe_path):
        _fail(f"Expected {exe_path} not found")

    size_mb = os.path.getsize(exe_path) / (1024 * 1024)

    print()
    print("=" * 50)
    print("  🎉 Build complete!")
    print("=" * 50)
    print(f"  EXE:   {exe_path}")
    print(f"  Size:  {size_mb:.1f} MB")
    print()
    print("  To run:")
    print("    dist\\Trixie.exe")
    print()
    print("  Notes:")
    print("    • All Python dependencies are bundled inside the EXE")
    print("    • AI models (~4 GB) download from HuggingFace on first launch")
    print("    • Models cached at: models/ (next to the EXE)")
    print("    • Settings stored at: %LOCALAPPDATA%/Trixie/settings.json")
    print("=" * 50)
    print()


if __name__ == "__main__":
    main()
