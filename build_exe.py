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
    # We bundle 'assets' and ensure all dependencies are collected
    # We use --noupx because it often breaks Python 3.13 DLL loading
    sep = ";" if os.name == 'nt' else ":"
    cmd = [
        sys.executable,
        "-m", "PyInstaller",
        "--onefile",
        "--noconsole",
        "--clean",
        "--noupx",
        "--name", "Dhurandhar",
        "--add-data", f"assets{sep}assets",
        "--collect-all", "requests",
        "--collect-all", "cv2",
        "--collect-all", "numpy",
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
    src = "dist/Dhurandhar.exe"
    dst = "release/Dhurandhar.exe"
    
    shutil.copy2(src, dst)
    
    # Verification
    src_size = os.path.getsize(src)
    dst_size = os.path.getsize(dst)
    if src_size != dst_size or dst_size < 1000000: # Should be at least ~1MB
        print(f"ERROR: File copy failed or file is too small! ({dst_size} bytes)")
        sys.exit(1)
        
    print(f"Updated 'release/Dhurandhar.exe' ({dst_size // 1024 // 1024} MB)")
    
    # 2. Update version.json locally
    print(f"Publishing v{version}...")
    
    push = input("\nReady to PUSH update to all clients? (y/n): ").lower()
    if push == 'y':
        try:
            # Force add the EXE and add everything else
            subprocess.check_call(["git", "add", "-f", "release/Dhurandhar.exe"])
            subprocess.check_call(["git", "add", "version.json", "licenses.json"])
            
            # Check if there are actually changes to commit
            status = subprocess.run(["git", "diff", "--cached", "--quiet"])
            if status.returncode != 0:
                subprocess.check_call(["git", "commit", "-m", f"Release v{version}"])
                print("Pushing to GitHub (this may take a minute for 70MB)...")
                subprocess.check_call(["git", "push"])
                print("\n" + "*"*40)
                print("SUCCESS: Update is now LIVE for all users!")
                print("*"*40)
            else:
                print("\nNo changes detected in version.json or code. Push skipped.")
        except Exception as e:
            print(f"Git operation failed: {e}")
    else:
        print("Push cancelled. Update not live.")

if __name__ == "__main__":
    build()
