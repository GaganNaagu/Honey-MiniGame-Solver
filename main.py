"""
Dhurandhar — CLI Control.

Usage:
    python main.py          -> Run minigame macro
    python main.py --setup  -> Setup wizard
"""

import sys
import os
import json
import keyboard
import threading
import logging
from core.utils import get_config_dir, get_assets_dir
from core.updater import start_update_check, VERSION

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

logger = logging.getLogger("dhurandhar")


def setup_logging(debug=False):
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(name)s] %(message)s",
        datefmt="%H:%M:%S"
    )


def load_config():
    # Priority 1: config/config.json relative to app location
    # Priority 2: config.json in the same folder as app
    # Priority 3: Current Working Directory
    
    config_dir = get_config_dir()
    app_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
    
    paths_to_check = [
        os.path.join(config_dir, "config.json"),
        os.path.join(app_dir, "config.json"),
        os.path.join(os.getcwd(), "config", "config.json"),
        os.path.join(os.getcwd(), "config.json")
    ]
    
    for config_path in paths_to_check:
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                logger.info(f"Loaded config from: {config_path}")
                return json.load(f)
                
    return None


def main():
    args = sys.argv[1:]

    # Add more debug if requested, or by default just INFO
    debug = "--debug" in args
    setup_logging(debug)
    
    # Check for updates in the background
    start_update_check()

    if "--setup" in args:
        from setup_wizard import LandingPage
        app = LandingPage()
        app.run()
        return

    config = load_config()
    if config is None:
        logger.warning("No config found. Launching with default/empty config.")
        config = {}

    from core.vision import Vision
    from core.input import Input
    from core.controller import Controller
    from minigames import HoneyScrapeHandler, FillJarHandler

    vision = Vision()
    input_sim = Input(jitter=5, delay_variance=0.2)
    controller = Controller(vision, input_sim, config)

    # Register all available handlers
    controller.register_handler(HoneyScrapeHandler())
    controller.register_handler(FillJarHandler())

    # --- GUI VERSION ---
    if "--cli" not in args:
        from app_gui import MainGUI
        
        gui = None

        def start_macro():
            controller.start(
                on_status=lambda text: gui.update_status(text),
                on_done=lambda: gui.stop_macro()
            )

        def stop_macro():
            controller.stop()

        def open_setup():
            from setup_wizard import LandingPage
            # Reuse the existing root and provide a way to get back
            LandingPage(root=gui.root, on_exit_callback=gui._build_ui)

        gui = MainGUI(
            controller, 
            on_start_callback=start_macro, 
            on_stop_callback=stop_macro,
            on_setup_callback=open_setup
        )

        def toggle():
            if gui.is_running:
                gui.stop_macro()
            else:
                gui.start_macro()

        keyboard.add_hotkey('f6', toggle, suppress=False)
        
        logger.info(f"Dhurandhar GUI Started (v{VERSION}).")
        logger.info("Select a minigame and press START or F6.")
        gui.run()
        return

    # --- CLI VERSION (Old behavior) ---
    # Simple terminal selection
    print("\n" + "="*40)
    print("  DHURANDHAR MINIGAME SELECTOR")
    print("="*40)
    print("  1. Honey Scrape")
    print("  2. Fill into Jar")
    print("="*40)
    
    try:
        choice = input("\n  Select minigame (1-2) [default 1]: ").strip()
        if choice == "2":
            controller.set_active_handler(1)
            game_name = "Fill into Jar"
        else:
            controller.set_active_handler(0)
            game_name = "Honey Scrape"
    except EOFError:
        controller.set_active_handler(0)
        game_name = "Honey Scrape"

    is_running = False

    def toggle_cli():
        nonlocal is_running
        if is_running:
            logger.info("F6 Pressed: Stopping...")
            controller.stop()
            is_running = False
        else:
            logger.info("F6 Pressed: Starting...")
            is_running = True
            controller.start(
                on_status=lambda text: logger.info(f"STATUS: {text}"),
                on_done=lambda: _on_done_cli()
            )

    def _on_done_cli():
        nonlocal is_running
        logger.info("Macro Finished.")
        controller.stop()
        is_running = False

    keyboard.add_hotkey('f6', toggle_cli, suppress=False)

    logger.info("="*40)
    logger.info(f"READY: {game_name}")
    logger.info("Press F6 to Start/Stop the macro.")
    logger.info("Press Ctrl+C in this terminal to exit.")
    logger.info("="*40)

    try:
        keyboard.wait()
    except KeyboardInterrupt:
        logger.info("Exiting...")
        controller.stop()


if __name__ == "__main__":
    main()
