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
    """Downloads the new EXE with progress and triggers restart."""
    try:
        progress_win = tk.Tk()
        progress_win.title("Updating Dhurandhar...")
        progress_win.geometry("350x120")
        progress_win.configure(bg='#0d1117')
        progress_win.attributes("-topmost", True)
        
        # Center progress window
        progress_win.update_idletasks()
        x = (progress_win.winfo_screenwidth() // 2) - 175
        y = (progress_win.winfo_screenheight() // 2) - 60
        progress_win.geometry(f'+{x}+{y}')

        tk.Label(progress_win, text="Downloading Latest Version...", fg='white', bg='#0d1117', pady=10).pack()
        progress = ttk.Progressbar(progress_win, orient="horizontal", length=280, mode="determinate")
        progress.pack(pady=10)
        
        def do_download():
            try:
                exe_path = sys.executable
                new_exe_path = exe_path + ".new"
                
                response = requests.get(download_url, stream=True)
                total_size = int(response.headers.get('content-length', 0))
                downloaded = 0
                
                with open(new_exe_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            if total_size > 0:
                                val = (downloaded / total_size) * 100
                                progress['value'] = val
                                progress_win.update()

                progress_win.destroy()
                
                if messagebox.askyesno("Update Ready", "Download complete! Restart now to apply update?"):
                    batch_content = f"""@echo off
title Dhurandhar Updater
echo Waiting for application to close...
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
                messagebox.showerror("Error", f"Update failed: {e}")
                progress_win.destroy()

        progress_win.after(100, do_download)
        progress_win.mainloop()
    except Exception as e:
        logger.error(f"UI Download failed: {e}")

def check_for_updates():
    """Checks for update and prompts user."""
    if not getattr(sys, 'frozen', False):
        return # Skip in dev mode

    try:
        response = requests.get(UPDATE_URL, timeout=10)
        if response.status_code == 200:
            data = response.json()
            remote_version = data.get("version")
            download_url = data.get("download_url")

            if remote_version and remote_version != VERSION:
                root = tk.Tk()
                root.withdraw()
                if messagebox.askyesno("Update Available", f"A new version (v{remote_version}) is available!\n\nDo you want to update now?"):
                    download_and_install(download_url)
                root.destroy()
    except Exception as e:
        logger.error(f"Update check failed: {e}")
