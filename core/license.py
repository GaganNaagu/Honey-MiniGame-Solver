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

class LicenseWindow(tk.Toplevel):
    def __init__(self, parent, hwid):
        super().__init__(parent)
        self.hwid = hwid
        self.result = None
        
        self.title("License Required")
        self.geometry("400x250")
        self.configure(bg='#0d1117')
        self.resizable(False, False)
        self.attributes("-topmost", True)
        
        # Center the window
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'+{x}+{y}')

        tk.Label(self, text="Authentication Required", font=("Segoe UI", 14, "bold"), fg='#58a6ff', bg='#0d1117').pack(pady=15)
        
        # HWID Section
        hwid_frame = tk.Frame(self, bg='#0d1117')
        hwid_frame.pack(fill='x', padx=20)
        tk.Label(hwid_frame, text="Your HWID:", font=("Segoe UI", 9), fg='#8b949e', bg='#0d1117').pack(side='left')
        
        self.hwid_entry = tk.Entry(hwid_frame, font=("Consolas", 10), bg='#161b22', fg='#7ee787', borderwidth=0)
        self.hwid_entry.insert(0, hwid)
        self.hwid_entry.configure(state='readonly')
        self.hwid_entry.pack(side='left', fill='x', expand=True, padx=5)
        
        tk.Button(hwid_frame, text="Copy", command=self.copy_hwid, bg='#21262d', fg='white', relief='flat', padx=10).pack(side='right')

        # License Key Section
        tk.Label(self, text="Enter License Key:", font=("Segoe UI", 10), fg='#c9d1d9', bg='#0d1117').pack(pady=(20, 5))
        self.key_entry = tk.Entry(self, font=("Segoe UI", 11), bg='#161b22', fg='white', insertbackground='white')
        self.key_entry.pack(fill='x', padx=20, pady=5)
        self.key_entry.focus_set()

        tk.Button(self, text="Activate License", command=self.submit, bg='#238636', fg='white', font=("Segoe UI", 10, "bold"), relief='flat', pady=8).pack(fill='x', padx=20, pady=20)
        
        self.protocol("WM_DELETE_WINDOW", lambda: sys.exit(0))
        self.wait_window()

    def copy_hwid(self):
        self.clipboard_clear()
        self.clipboard_append(self.hwid)
        messagebox.showinfo("Copied", "HWID copied to clipboard!")

    def submit(self):
        self.result = self.key_entry.get().strip()
        if self.result:
            self.destroy()

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
        # Create a temporary root if none exists to host the dialog
        temp_root = gui_root if gui_root else tk.Tk()
        if not gui_root: temp_root.withdraw()
        
        win = LicenseWindow(temp_root, hwid)
        key = win.result
        
        if not key:
            sys.exit(0)
        
        with open(license_file, 'w') as f:
            f.write(key)
        
        if not gui_root: temp_root.destroy()

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
