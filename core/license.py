import os
import sys
import json
import logging
import requests
import subprocess
import tkinter as tk
from tkinter import messagebox, simpledialog

logger = logging.getLogger("dhurandhar.license")

# Points to your licenses.json on GitHub
GITHUB_USER = "GaganNaagu"
GITHUB_REPO = "Honey-MiniGame-Solver"
LICENSE_URL = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/master/licenses.json"

def get_hwid():
    """Generates a unique HWID for the current machine."""
    try:
        # Get machine GUID from Windows registry via cmd
        cmd = 'powershell (Get-ItemProperty -Path "HKLM:\\SOFTWARE\\Microsoft\\Cryptography").MachineGuid'
        hwid = subprocess.check_output(cmd, shell=True).decode().strip()
        return hwid
    except:
        # Fallback to a simpler ID if powershell fails
        import uuid
        return str(uuid.getnode())

def check_license(gui_root=None):
    """
    Checks if the application is authorized.
    If no license is found locally, prompts user.
    """
    hwid = get_hwid()
    config_dir = os.path.join(os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__)), "config")
    license_file = os.path.join(config_dir, "license.txt")

    # 1. Load local license key
    key = ""
    if os.path.exists(license_file):
        with open(license_file, 'r') as f:
            key = f.read().strip()

    # 2. If no key, prompt for one
    if not key:
        key = simpledialog.askstring("License Required", f"Your HWID: {hwid}\n\nPlease enter your License Key:", parent=gui_root)
        if not key:
            sys.exit(0)
        
        with open(license_file, 'w') as f:
            f.write(key)

    # 3. Verify against GitHub
    try:
        logger.info(f"Verifying license {key} for HWID {hwid}...")
        response = requests.get(LICENSE_URL, timeout=10)
        if response.status_code != 200:
            messagebox.showerror("Error", "Could not connect to license server.")
            sys.exit(0)

        licenses = response.json()
        
        if key not in licenses:
            messagebox.showerror("Invalid License", "The license key entered is invalid.")
            os.remove(license_file) # Clear invalid key
            sys.exit(0)

        auth_data = licenses[key]
        expected_hwid = auth_data.get("hwid")

        # If HWID is empty in JSON, this is the first activation - "bind" it
        # (Note: In a real system you'd need a backend to write this. 
        # For now, we assume the dev manually puts the HWID in GitHub)
        if expected_hwid and expected_hwid != hwid:
            messagebox.showerror("Hardware Mismatch", "This license is registered to another computer.")
            sys.exit(0)
        
        if auth_data.get("status") != "active":
            messagebox.showerror("License Expired", "This license is no longer active.")
            sys.exit(0)

        logger.info("License verified successfully.")
        return True

    except Exception as e:
        logger.error(f"License check failed: {e}")
        messagebox.showerror("Error", f"License check failed: {e}")
        sys.exit(0)
