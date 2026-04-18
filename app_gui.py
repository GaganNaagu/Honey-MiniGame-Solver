import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import logging
import sys
import os

class TextHandler(logging.Handler):
    def __init__(self, text_widget):
        super().__init__()
        self.text_widget = text_widget

    def emit(self, record):
        msg = self.format(record)
        def append():
            self.text_widget.configure(state='normal')
            self.text_widget.insert(tk.END, msg + '\n')
            self.text_widget.configure(state='disabled')
            self.text_widget.yview(tk.END)
        self.text_widget.after(0, append)

class MainGUI:
    def __init__(self, controller, on_start_callback, on_stop_callback, on_setup_callback, version="1.0.0"):
        self.controller = controller
        self.on_start_callback = on_start_callback
        self.on_stop_callback = on_stop_callback
        self.on_setup_callback = on_setup_callback
        self.version = version
        
        self.root = tk.Tk()
        self.root.title("Dhurandhar Automation Hub")
        self.root.geometry("800x600")
        self.root.configure(bg='#0d1117')
        self.root.attributes('-topmost', True)
        
        self.is_running = False
        self.config_missing = not controller.config
        self._setup_styles()
        self._build_ui()
        self._setup_logging()
        
        if self.config_missing:
            self.root.after(500, lambda: logging.warning("⚠️ No configuration found! Please go to the SETUP tab to calibrate your minigames."))
            self.root.after(500, lambda: self.notebook.select(self.setup_tab))

    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        
        bg_color = '#0d1117'
        fg_color = '#c9d1d9'
        accent_color = '#58a6ff'

        style.configure('TFrame', background=bg_color)
        style.configure('TLabel', background=bg_color, foreground=fg_color, font=("Segoe UI", 10))
        style.configure('TNotebook', background=bg_color, borderwidth=0)
        style.configure('TNotebook.Tab', background='#161b22', foreground='#8b949e', padding=[20, 10], font=("Segoe UI", 11, "bold"))
        style.map('TNotebook.Tab', 
                  background=[('selected', '#0d1117')],
                  foreground=[('selected', '#58a6ff')])

    def _build_ui(self):
        for widget in self.root.winfo_children():
            widget.destroy()

        # --- Header ---
        header = tk.Frame(self.root, bg='#0d1117', pady=20)
        header.pack(fill='x')
        tk.Label(header, text="DHURANDHAR", font=("Segoe UI", 28, "bold"), fg='#58a6ff', bg='#0d1117').pack()
        tk.Label(header, text=f"v{self.version}", font=("Consolas", 9, "bold"), fg='#3fb950', bg='#0d1117').pack()
        tk.Label(header, text="High-Performance Vision Automation", font=("Segoe UI", 10), fg='#8b949e', bg='#0d1117').pack()

        # --- Main Tabs ---
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=20, pady=10)

        # Tab 1: Play
        self.play_tab = tk.Frame(self.notebook, bg='#0d1117')
        self.notebook.add(self.play_tab, text="  ▶ PLAY  ")

        # Tab 2: Setup
        self.setup_tab = tk.Frame(self.notebook, bg='#0d1117')
        self.notebook.add(self.setup_tab, text="  ⚙ SETUP  ")

        self._build_play_tab()
        self._build_setup_tab()

        # --- Console / Logs (Always visible at bottom) ---
        console_frame = tk.Frame(self.root, bg='#0d1117', padx=20, height=200)
        console_frame.pack_propagate(False) # Keep the fixed height
        console_frame.pack(fill='both', expand=False, pady=(0, 20))

        tk.Label(console_frame, text="TERMINAL LOGS", font=("Segoe UI", 9, "bold"), fg='#484f58', bg='#0d1117').pack(anchor='w', pady=(0, 5))
        self.log_text = scrolledtext.ScrolledText(console_frame, bg='#010409', fg='#7ee787', height=8,
                                                  font=("Consolas", 10), borderwidth=1, 
                                                  highlightbackground="#30363d", highlightthickness=1)
        self.log_text.pack(fill='both', expand=True)
        self.log_text.configure(state='disabled')

    def _build_play_tab(self):
        container = tk.Frame(self.play_tab, bg='#0d1117', pady=30)
        container.pack(expand=True)

        tk.Label(container, text="Select Minigame to Start", font=("Segoe UI", 14, "bold"), fg='#c9d1d9', bg='#0d1117').pack(pady=(0, 20))

        self.game_var = tk.IntVar(value=0)
        games_frame = tk.Frame(container, bg='#0d1117')
        games_frame.pack()

        games = [("🍯 Honey Scrape", 0), ("🏺 Fill into Jar", 1)]
        for text, val in games:
            rb = tk.Radiobutton(games_frame, text=text, variable=self.game_var, value=val,
                                 bg='#161b22', fg='#c9d1d9', selectcolor='#58a6ff',
                                 activebackground='#161b22', activeforeground='#58a6ff',
                                 font=("Segoe UI", 12), indicatoron=0, width=20, pady=15, 
                                 relief='flat', cursor='hand2', command=self._on_game_change)
            rb.pack(side='left', padx=10)

        tk.Frame(container, height=40, bg='#0d1117').pack()

        # Big Play Button
        self.btn_toggle = tk.Button(container, text="START MACRO (F6)", command=self.toggle_macro,
                                    bg='#238636', fg='white', font=("Segoe UI", 16, "bold"),
                                    relief='flat', width=25, pady=15, cursor='hand2')
        self.btn_toggle.pack()
        
        tk.Label(container, text="The macro will run according to your calibration.", font=("Segoe UI", 9), fg='#8b949e', bg='#0d1117').pack(pady=10)

    def _build_setup_tab(self):
        container = tk.Frame(self.setup_tab, bg='#0d1117', pady=40)
        container.pack(expand=True)

        tk.Label(container, text="Calibration & Setup", font=("Segoe UI", 18, "bold"), fg='#58a6ff', bg='#0d1117').pack(pady=(0, 10))
        tk.Label(container, text="Configure screen regions and capture templates for each minigame.", 
                 font=("Segoe UI", 11), fg='#8b949e', bg='#0d1117', wraplength=400, justify='center').pack(pady=(0, 30))

        tk.Button(container, text="Open Setup Wizard", command=self.on_setup_callback,
                  bg='#21262d', fg='#c9d1d9', font=("Segoe UI", 13, "bold"),
                  relief='flat', width=30, pady=15, cursor='hand2').pack()

        tk.Label(container, text="Note: Requires game to be open in Borderless/Windowed mode.", 
                 font=("Segoe UI", 9, "italic"), fg='#484f58', bg='#0d1117').pack(pady=20)

    def _setup_logging(self):
        handler = TextHandler(self.log_text)
        handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", "%H:%M:%S"))
        logging.getLogger().addHandler(handler)

    def _on_game_change(self):
        choice = self.game_var.get()
        self.controller.set_active_handler(choice)
        logging.info(f"Selected Minigame: {'Honey Scrape' if choice == 0 else 'Fill into Jar'}")

    def toggle_macro(self):
        if self.is_running:
            self.stop_macro()
        else:
            self.start_macro()

    def start_macro(self):
        if self.is_running: return
        self.is_running = True
        self.btn_toggle.configure(text="STOP MACRO (F6)", bg='#da3633')
        self.on_start_callback()

    def stop_macro(self):
        if not self.is_running: return
        self.is_running = False
        self.btn_toggle.configure(text="START MACRO (F6)", bg='#238636')
        self.on_stop_callback()

    def update_status(self, text):
        logging.info(f"STATUS: {text}")

    def run(self):
        self.root.mainloop()
