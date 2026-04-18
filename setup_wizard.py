"""
Dhurandhar — GUI Setup Wizard for in-game calibration.

Lets you capture positions, regions, and template images while in-game.
All data saves to config/config.json.

Usage:
    python setup_wizard.py
"""

import tkinter as tk
from tkinter import messagebox
import pyautogui
import keyboard
import mss
import json
import os
import numpy as np
import cv2
import logging

from core.utils import get_config_dir, get_assets_dir

logger = logging.getLogger("dhurandhar.setup")

# Paths
CONFIG_DIR = get_config_dir()
CONFIG_PATH = os.path.join(CONFIG_DIR, "config.json")
TEMPLATE_DIR = os.path.join(get_assets_dir(), "templates")


def ensure_dirs():
    os.makedirs(CONFIG_DIR, exist_ok=True)
    os.makedirs(TEMPLATE_DIR, exist_ok=True)


def load_config():
    config = get_default_config()
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, 'r') as f:
            try:
                saved = json.load(f)
                # Smart merge for each game section
                for game_key in ["honey_game", "jar_game"]:
                    if game_key in saved:
                        if game_key not in config:
                            config[game_key] = saved[game_key]
                        else:
                            for k, v in saved[game_key].items():
                                if isinstance(v, dict) and k in config[game_key]:
                                    config[game_key][k].update(v)
                                else:
                                    config[game_key][k] = v
            except json.JSONDecodeError:
                pass
    return config


def save_config(config):
    ensure_dirs()
    with open(CONFIG_PATH, 'w') as f:
        json.dump(config, f, indent=2)
    logger.info(f"Config saved to {CONFIG_PATH}")


def get_default_config():
    return {
        "honey_game": {
            "name": "Honey Scrape",
            "start_key": "e",
            "start_click": [960, 540],
            "hold_position": [960, 540],
            "hold_duration_ms": 1000,
            "scrape_region": [400, 300, 400, 300],
            "honey_texture_region": [400, 300, 100, 100],
            "scraper_reset_region": [400, 300, 100, 100],
            "drag_target": [1200, 540],
            "counter_region": [0, 0, 200, 50],
            "ui_region": [0, 0, 1920, 1080],
            "target_count": 10,
            "templates": {
                "ui_active": "",
                "clean": "",
                "scraper_reset": ""
            }
        },
        "jar_game": {
            "name": "Fill into Jar",
            "start_key": "e",
            "click_pos": [960, 540],
            "click_count": 4,
            "circle_center": [960, 540],
            "circle_radius": 100,
            "circle_speed_ms": 500,
            "final_check_region": [400, 300, 100, 100],
            "ui_region": [0, 0, 1920, 1080],
            "templates": {
                "ui_active": "",
                "final_check": ""
            }
        }
    }


class VisualSelector:
    """Full-screen transparent overlay for click-and-drag visual selection."""
    def __init__(self, on_selected):
        self.on_selected = on_selected
        self.top = tk.Toplevel()
        self.top.attributes('-fullscreen', True)
        self.top.attributes('-alpha', 0.3)
        self.top.configure(cursor="crosshair")
        self.top.attributes("-topmost", True)
        
        self.canvas = tk.Canvas(self.top, bg="black", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        self.start_x = None
        self.start_y = None
        self.rect_id = None

        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        # Allow Esc to cancel
        self.top.bind("<Escape>", lambda e: self.top.destroy())

    def on_press(self, event):
        self.start_x = event.x
        self.start_y = event.y
        self.rect_id = self.canvas.create_rectangle(
            self.start_x, self.start_y, self.start_x, self.start_y,
            outline="red", width=2, fill="gray", stipple="gray50"
        )

    def on_drag(self, event):
        if self.rect_id:
            self.canvas.coords(
                self.rect_id,
                self.start_x, self.start_y, event.x, event.y
            )

    def on_release(self, event):
        end_x, end_y = event.x, event.y
        x = min(self.start_x, end_x)
        y = min(self.start_y, end_y)
        w = abs(end_x - self.start_x)
        h = abs(end_y - self.start_y)
        
        self.top.destroy()
        if w > 10 and h > 10:
            self.on_selected((x, y, w, h))


class SetupWizard:
    def __init__(self, root, game_key, on_back):
        self.root = root
        self.game_key = game_key
        self.on_back = on_back
        self.config = load_config()
        self.sct = mss.mss()
        self.waiting_for = None
        self._pending_f2 = None

        # Clear existing widgets
        for widget in self.root.winfo_children():
            widget.destroy()

        self._build_ui()

    def _build_ui(self):
        game_name = self.config.get(self.game_key, {}).get("name", "Minigame")
        
        # ── Header ──
        header = tk.Frame(self.root, bg="#0d1117")
        header.pack(fill="x", pady=(15, 5))
        
        tk.Button(
            header, text="← Back", command=self.on_back,
            bg="#21262d", fg="#c9d1d9", font=("Segoe UI", 9),
            relief="flat", padx=10, pady=2, cursor="hand2"
        ).pack(side="left", padx=15)

        tk.Label(
            header, text=f"⚙ {game_name}",
            font=("Segoe UI", 16, "bold"), fg="#58a6ff", bg="#0d1117"
        ).pack(side="left", padx=10)

        # ── Status Bar ──
        self.status_var = tk.StringVar(value="Ready — pick a step below")
        tk.Label(
            self.root, textvariable=self.status_var,
            font=("Segoe UI", 10, "bold"), fg="#3fb950", bg="#161b22",
            relief="flat", padx=10, pady=6
        ).pack(fill="x", padx=15, pady=5)

        # ── Scrollable Buttons Frame ──
        canvas = tk.Canvas(self.root, bg="#0d1117", highlightthickness=0, height=400)
        scrollbar = tk.Scrollbar(self.root, orient="vertical", command=canvas.yview)
        btn_frame = tk.Frame(canvas, bg="#0d1117")

        btn_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=btn_frame, anchor="nw", width=530)
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True, padx=(15, 0), pady=5)
        scrollbar.pack(side="right", fill="y", pady=5, padx=(0, 5))

        # ── Step Definitions based on game_key ──
        if self.game_key == "honey_game":
            steps = [
                ("STEP 1 — INIT", "📐 UI Detection Region", "ui_region", "region", "Where to look for the UI"),
                ("STEP 1 — INIT", "📸 Capture UI Active", "ui_active", "template", "Screenshot of the UI window"),
                None,
                ("STEP 2 — CLICK", "📍 Start Click Position", "start_click", "point", "Button to click after UI appears"),
                ("STEP 3 — HOLD", "📍 Hold Position", "hold_position", "point", "Where to hold mouse down"),
                None,
                ("STEP 4 — SCRAPE", "📐 Scrape Region", "scrape_region", "region", "Area to sweep back and forth"),
                None,
                ("STEP 5 — TEXTURE", "📐 Honey Texture Region", "honey_texture_region", "region", "Area to check for clean/dirty"),
                ("STEP 5 — TEXTURE", "📸 Capture CLEAN Honey", "clean", "template", "Screenshot of clean honey"),
                None,
                ("STEP 5 — RESET", "📐 Scraper Reset Region", "scraper_reset_region", "region", "Area to check for tool reset"),
                ("STEP 5 — RESET", "📸 Capture Scraper Reset", "scraper_reset", "template", "Screenshot of reset tool"),
                None,
                ("STEP 6 — DRAG", "📍 Drag Target", "drag_target", "point", "Where to drop the honey"),
            ]
        else: # jar_game
            steps = [
                ("STEP 1 — INIT", "📐 UI Detection Region", "ui_region", "region", "Where to look for the UI"),
                ("STEP 1 — INIT", "📸 Capture UI Active", "ui_active", "template", "Screenshot of the UI window"),
                None,
                ("STEP 2 — CLICK", "📍 Click Position (4x)", "click_pos", "point", "Position to click 4 times"),
                None,
                ("STEP 3 — ROTATE", "📍 Circle Center", "circle_center", "point", "Center of the clockwise rotation"),
                None,
                ("STEP 4 — VERIFY", "📐 5x Check Region", "final_check_region", "region", "Where the 5x text appears"),
                ("STEP 4 — VERIFY", "📸 Capture 5x Template", "final_check", "template", "Screenshot of the 5x indicator"),
            ]

        for item in steps:
            if item is None:
                tk.Frame(btn_frame, height=1, bg="#30363d").pack(fill="x", pady=6)
                continue

            step_label, btn_text, key, ctype, desc = item
            row = tk.Frame(btn_frame, bg="#0d1117")
            row.pack(fill="x", pady=2)
            tk.Label(row, text=step_label, font=("Consolas", 7, "bold"), fg="#484f58", bg="#0d1117", anchor="w").pack(fill="x", padx=12)
            btn = tk.Button(row, text=btn_text, command=lambda k=key, t=ctype: self._start_capture(k, t),
                            bg="#21262d", fg="#c9d1d9", font=("Segoe UI", 10), relief="flat", padx=12, pady=5, cursor="hand2", anchor="w")
            btn.pack(fill="x", padx=8)
            tk.Label(row, text=desc, font=("Segoe UI", 8), fg="#6e7681", bg="#0d1117", anchor="w").pack(fill="x", padx=16, pady=(0, 2))

        # ── Current Values ──
        tk.Frame(self.root, height=1, bg="#30363d").pack(fill="x", padx=15, pady=8)
        self.values_text = tk.Text(self.root, height=10, bg="#0d1117", fg="#7ee787", font=("Consolas", 9), relief="flat", padx=10, pady=5, borderwidth=0)
        self.values_text.pack(fill="x", padx=15)
        self._update_values_display()

        # ── Bottom Buttons ──
        bottom = tk.Frame(self.root, bg="#0d1117")
        bottom.pack(fill="x", padx=15, pady=10)
        tk.Button(bottom, text="💾 Save Config", command=self._save, bg="#238636", fg="white", font=("Segoe UI", 11, "bold"), relief="flat", padx=20, pady=8, cursor="hand2").pack(fill="x")

        keyboard.on_press_key('f2', self._on_f2_thread, suppress=False)
        self._poll_f2()

    def _poll_f2(self):
        if self._pending_f2 is not None:
            px, py = self._pending_f2
            self._pending_f2 = None
            self._process_f2(px, py)
        self.root.after(50, self._poll_f2)

    def _on_f2_thread(self, event):
        if self.waiting_for:
            pos = pyautogui.position()
            self._pending_f2 = (pos.x, pos.y)

    def _process_f2(self, px, py):
        if not self.waiting_for: return
        key, mode = self.waiting_for[0], self.waiting_for[1]
        if mode == "point":
            self.config[self.game_key][key] = [px, py]
            self.status_var.set(f"✅ {key} = ({px}, {py})")
            self.waiting_for = None
        elif mode == "template":
            region = self.waiting_for[2]
            self._capture_template(key, region)
            self.waiting_for = None
        self._update_values_display()

    def _capture_template(self, name, region):
        x, y, w, h = region
        monitor = {"left": x, "top": y, "width": w, "height": h}
        img = np.array(self.sct.grab(monitor))
        img_bgr = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
        filename = f"{self.game_key}_{name}.png"
        filepath = os.path.join(TEMPLATE_DIR, filename)
        cv2.imwrite(filepath, img_bgr)
        self.config[self.game_key]["templates"][name] = filename
        self.status_var.set(f"✅ Template saved: {filename}")

    def _start_capture(self, key, capture_type):
        if capture_type == "template":
            if key == "ui_active":
                region = self.config[self.game_key].get("ui_region", [0, 0, 1920, 1080])
            else:
                # Get the corresponding region for this template
                region_map = {
                    "clean": "honey_texture_region",
                    "scraper_reset": "scraper_reset_region",
                    "final_check": "final_check_region"
                }
                region_key = region_map.get(key, "ui_region")
                region = self.config[self.game_key].get(region_key, [0,0,100,100])
            
            self.waiting_for = (key, "template", region)
            self.status_var.set(f"⏳ Press F2 to capture {key}...")
        elif capture_type == "region":
            self.root.withdraw()
            def on_selected(region):
                self.config[self.game_key][key] = list(region)
                self.root.deiconify()
                self._update_values_display()
            VisualSelector(on_selected)
        elif capture_type == "point":
            self.waiting_for = (key, "point")
            self.status_var.set(f"⏳ Hover and press F2...")

    def _update_values_display(self):
        self.values_text.delete("1.0", tk.END)
        cfg = self.config.get(self.game_key, {})
        text = json.dumps(cfg, indent=2)
        self.values_text.insert("1.0", text)

    def _save(self):
        save_config(self.config)
        messagebox.showinfo("Saved", "Config updated successfully.")


class LandingPage:
    def __init__(self, root=None, on_exit_callback=None):
        ensure_dirs()
        self.on_exit_callback = on_exit_callback
        if root:
            self.root = root
            # Clear previous widgets if reused
            for widget in self.root.winfo_children():
                widget.destroy()
        else:
            self.root = tk.Tk()
            
        self.root.title("Dhurandhar Hub")
        self.root.geometry("500x400")
        self.root.configure(bg='#0d1117')
        self.root.attributes('-topmost', True)
        self._build_ui()

    def _build_ui(self):
        for widget in self.root.winfo_children():
            widget.destroy()

        tk.Label(self.root, text="Select Minigame to Setup", font=("Segoe UI", 18, "bold"), fg="#58a6ff", bg="#0d1117").pack(pady=30)

        games = [
            ("🍯 Honey Scrape", "honey_game"),
            ("🏺 Fill into Jar", "jar_game")
        ]

        for name, key in games:
            tk.Button(
                self.root, text=name,
                command=lambda k=key: SetupWizard(self.root, k, self._build_ui),
                bg="#21262d", fg="#c9d1d9", font=("Segoe UI", 12),
                relief="flat", width=25, pady=10, cursor="hand2"
            ).pack(pady=10)

        if self.on_exit_callback:
            tk.Button(self.root, text="Return to Menu", command=self.on_exit_callback, bg="#21262d", fg="white", font=("Segoe UI", 10), relief="flat", width=15).pack(pady=10)
        else:
            tk.Button(self.root, text="Exit", command=self.root.destroy, bg="#da3633", fg="white", font=("Segoe UI", 10), relief="flat", width=10).pack(pady=20)

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    LandingPage().run()
