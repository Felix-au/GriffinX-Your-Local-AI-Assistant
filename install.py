import subprocess
import sys
import platform
import os

def get_gpu_vendor_windows():
    print("Detecting hardware...")
    try:
        # Use WMIC to get GPU names
        output = subprocess.check_output(
            ["wmic", "path", "win32_VideoController", "get", "name"], 
            text=True
        )
        output = output.lower()
        if "nvidia" in output:
            return "nvidia"
        elif "amd" in output or "radeon" in output:
            return "amd"
        elif "intel" in output:
            return "intel"
    except Exception as e:
        print(f"Warning: Failed to detect GPU: {e}")
    return "unknown"

def main():
    print("Starting GriffinX: Your Local AI Assistant setup...")
    
    print("\n--- Step 1: Installing base dependencies ---")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    
    print("\n--- Step 2: Configuring Hardware Acceleration ---")
    if platform.system() == "Windows":
        vendor = get_gpu_vendor_windows()
        print(f"Detected GPU Vendor: {vendor.upper()}")
        
        env = None
        if vendor == "nvidia":
            print("Configuring LLM engine for NVIDIA (CUDA)...")
            env = {"CMAKE_ARGS": "-DGGML_CUDA=on"}
        elif vendor in ["amd", "intel"]:
            print(f"Configuring LLM engine for {vendor.upper()} (Vulkan)...")
            env = {"CMAKE_ARGS": "-DGGML_VULKAN=on"}
        else:
            print("No dedicated GPU detected or unknown vendor. Relying on CPU.")
            
        if env is not None:
            full_env = os.environ.copy()
            full_env.update(env)
            
            print("\nBuilding and installing llama-cpp-python with hardware acceleration.")
            print("NOTE: This requires Visual Studio C++ Build Tools installed on your system.")
            print("This may take several minutes to compile...")
            
            try:
                subprocess.check_call(
                    [sys.executable, "-m", "pip", "install", "llama-cpp-python", "--upgrade", "--force-reinstall", "--no-cache-dir"],
                    env=full_env
                )
                print("\nSUCCESS: Hardware acceleration setup complete!")
            except subprocess.CalledProcessError:
                print("\nError: Failed to build with hardware acceleration. Please ensure Visual Studio C++ build tools are installed.")
                print("Falling back to standard CPU-only version...")
                subprocess.check_call([sys.executable, "-m", "pip", "install", "llama-cpp-python", "--upgrade"])
    else:
        print("Hardware auto-detection is currently implemented for Windows. Relying on default CPU installation.")
        
    print("\nSetup is finished! You can now run `python main.py` or package it using `python package.py`.")

if __name__ == "__main__":
    main()
