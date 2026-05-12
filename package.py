import subprocess
import os

def package_app():
    print("Starting PyInstaller packaging...")
    
    # Check if pyinstaller is available
    try:
        subprocess.run(["uv", "run", "pyinstaller", "--version"], check=True)
    except Exception:
        print("PyInstaller not found in uv environment. Did you run 'uv sync --extra build'?")
        return

    # Basic command
    cmd = [
        "uv",
        "run",
        "pyinstaller",
        "--name=TrixieAssistant",
        "--windowed", # Don't open a console window
        "--onefile",
        # Including core paths and data
        "--add-data=core;core",
        "--add-data=ui;ui",
        # Adding hooks if needed
        "--hidden-import=keyboard",
        "--hidden-import=sounddevice",
        "--hidden-import=llama_cpp",
        "--hidden-import=faster_whisper",
        "--hidden-import=pyttsx3",
        "--clean",
        "-y",
        "main.py"
    ]
    
    print(f"Running: {' '.join(cmd)}")
    subprocess.run(cmd)
    
    print("\nPackaging complete!")
    print("The executable is located in the 'dist' folder.")
    print("Note: You must manually place the 'models' folder next to the generated .exe")

if __name__ == "__main__":
    package_app()
