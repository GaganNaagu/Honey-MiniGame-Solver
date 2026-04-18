import os
import subprocess
import sys
import json

def get_version():
    try:
        with open("version.json", "r") as f:
            return json.load(f).get("version", "unknown")
    except:
        return "1.0.0"

def build():
    version = get_version()
    print(f"Starting build process for Dhurandhar v{version}...")
    
    # Ensure pyinstaller is installed
    try:
        import PyInstaller
    except ImportError:
        print("PyInstaller not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

    # Build command
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
    print(f"BUILD COMPLETE (v{version})!")
    
    # 1. Copy to release folder
    os.makedirs("release", exist_ok=True)
    import shutil
    shutil.copy2("dist/Dhurandhar.exe", "release/Dhurandhar.exe")
    print("Updated 'release/Dhurandhar.exe'")
    
    # 2. Update version.json locally
    print(f"Publishing v{version}...")
    
    push = input("\nReady to PUSH update to all clients? (y/n): ").lower()
    if push == 'y':
        try:
            subprocess.check_call(["git", "add", "."])
            subprocess.check_call(["git", "commit", "-m", f"Release v{version}"])
            subprocess.check_call(["git", "push"])
            print("\n" + "*"*40)
            print("SUCCESS: Update is now LIVE for all users!")
            print("*"*40)
        except Exception as e:
            print(f"Git push failed: {e}")
    else:
        print("Push cancelled. Update not live.")

if __name__ == "__main__":
    build()
