import os
import sys
import json
import logging
import requests
import subprocess
import time
import threading

logger = logging.getLogger("dhurandhar.updater")

# This must match the version in version.json on GitHub
VERSION = "1.0.0"

GITHUB_USER = "GaganNaagu"
GITHUB_REPO = "Honey-MiniGame-Solver"
# We check the version.json on the master branch
UPDATE_URL = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/master/version.json"

def start_update_check():
    """Run update check in a separate thread so it doesn't block the GUI startup."""
    thread = threading.Thread(target=check_for_updates, daemon=True)
    thread.start()

def check_for_updates():
    """Checks for a new version on GitHub."""
    if not getattr(sys, 'frozen', False):
        logger.info("Running in dev mode, skipping update check.")
        return

    try:
        logger.info(f"Checking for updates at {UPDATE_URL}...")
        response = requests.get(UPDATE_URL, timeout=10)
        if response.status_code != 200:
            logger.warning(f"Could not reach update server (Status: {response.status_code})")
            return

        data = response.json()
        latest_version = data.get("version")
        download_url = data.get("download_url")

        if latest_version and latest_version > VERSION:
            logger.info(f"New update found! {VERSION} -> {latest_version}")
            # Give the user 2 seconds to see the message in the console
            time.sleep(2)
            download_and_install(download_url)
        else:
            logger.info("Application is up to date.")
            
    except Exception as e:
        logger.error(f"Update check failed: {e}")

def download_and_install(url):
    """Downloads the new EXE and replaces the old one using a batch script."""
    try:
        exe_path = sys.executable
        new_exe_path = exe_path + ".new"

        logger.info(f"Downloading new version from {url}...")
        r = requests.get(url, stream=True)
        r.raise_for_status()
        
        with open(new_exe_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

        logger.info("Download complete. Creating update script...")
        
        # Create self-replacing batch script
        # This waits for the main process to exit, swaps files, and restarts
        batch_content = f"""@echo off
title Dhurandhar Updater
echo Waiting for application to close...
timeout /t 2 /nobreak > nul
echo Replacing executable...
del "{exe_path}"
move "{new_exe_path}" "{exe_path}"
echo Restarting...
start "" "{exe_path}"
del "%~f0"
"""
        batch_path = os.path.join(os.path.dirname(exe_path), "update_dhurandhar.bat")
        with open(batch_path, "w") as f:
            f.write(batch_content)

        logger.info("Executing update script and exiting.")
        subprocess.Popen([batch_path], shell=True)
        os._exit(0) # Immediate exit
    except Exception as e:
        logger.error(f"Failed to install update: {e}")
