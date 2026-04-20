import os
import sys
import json
import logging
import requests
import subprocess
import time
import threading
import tkinter as tk
from tkinter import messagebox, ttk

logger = logging.getLogger("dhurandhar.updater")

# This must match the version in version.json on GitHub
VERSION = "1.0.1"

GITHUB_USER = "GaganNaagu"
GITHUB_REPO = "Honey-MiniGame-Solver"
UPDATE_URL = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/master/version.json"

def start_update_check():
    """Run update check in a separate thread."""
    thread = threading.Thread(target=check_for_updates, daemon=True)
    thread.start()

def download_and_install(download_url):
    """Downloads the new EXE silently and triggers restart."""
    try:
        exe_path = sys.executable
        new_exe_path = exe_path + ".new"
        
        # Silent download
        response = requests.get(download_url, stream=True)
        with open(new_exe_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        # Create restart script
        batch_content = f"""@echo off
title Dhurandhar Updater
echo Applying update...
timeout /t 1 /nobreak > nul
del "{exe_path}"
move "{new_exe_path}" "{exe_path}"
start "" "{exe_path}"
del "%~f0"
"""
        batch_path = os.path.join(os.path.dirname(exe_path), "update_dhurandhar.bat")
        with open(batch_path, "w") as f:
            f.write(batch_content)
        
        subprocess.Popen([batch_path], shell=True)
        os._exit(0)
    except Exception as e:
        logger.error(f"Silent update failed: {e}")

def check_for_updates():
    """Checks for update silently. Returns True if updating (to stop main app)."""
    if not getattr(sys, 'frozen', False):
        return False

    try:
        # Add cache buster
        import time
        bust_url = f"{UPDATE_URL}?t={int(time.time())}"
        
        response = requests.get(bust_url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            remote_version = data.get("version")
            download_url = data.get("download_url")

            if remote_version and remote_version != VERSION:
                logger.info(f"Updating to v{remote_version}...")
                download_and_install(download_url)
                return True
    except Exception as e:
        logger.error(f"Update check failed: {e}")
    return False
