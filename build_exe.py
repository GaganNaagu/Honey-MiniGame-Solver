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
    print("Your executable is in the 'dist' folder.")
    print("\nNEXT STEPS FOR PUBLISHING:")
    print(f"1. Ensure 'version' in 'version.json' is higher than current.")
    print(f"2. Upload 'dist/Dhurandhar.exe' to GitHub Releases.")
    print(f"3. Commit and push 'version.json' to GitHub.")
    print("="*40)
    
    push = input("\nWould you like to commit and push current changes to GitHub? (y/n): ").lower()
    if push == 'y':
        msg = input("Commit message [Update]: ") or "Update"
        try:
            subprocess.check_call(["git", "add", "."])
            subprocess.check_call(["git", "commit", "-m", msg])
            subprocess.check_call(["git", "push"])
            print("Successfully pushed to GitHub!")
        except Exception as e:
            print(f"Git push failed: {e}")

if __name__ == "__main__":
    build()
