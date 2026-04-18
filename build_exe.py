import os
import subprocess
import sys

def build():
    print("Starting build process for Dhurandhar...")
    
    # Ensure pyinstaller is installed
    try:
        import PyInstaller
    except ImportError:
        print("PyInstaller not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

    # Build command
    # --onefile: single exe
    # --noconsole: no terminal window (since we have a GUI)
    # --add-data: include assets (we'll keep them external for now to allow editing, 
    # but we need to ensure the exe knows where to look)
    
    cmd = [
        sys.executable,
        "-m", "PyInstaller",
        "--onefile",
        "--noconsole",
        "--name", "Dhurandhar",
        "--icon", "NONE",
        "main.py"
    ]
    
    print(f"Running command: {' '.join(cmd)}")
    subprocess.check_call(cmd)
    
    print("\n" + "="*40)
    print("BUILD COMPLETE!")
    print("Your executable is in the 'dist' folder.")
    print("IMPORTANT: Make sure to copy 'assets' and 'config' folders ")
    print("to the same location as Dhurandhar.exe if they aren't bundled.")
    print("="*40)

if __name__ == "__main__":
    build()
