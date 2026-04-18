# Dhurandhar Development Guide

This document explains how to run, modify, and extend the Dhurandhar automation framework.

## 🛠 Prerequisites

- **Python 3.10+** (Windows only)
- A virtual environment is recommended.

## 🚀 Running from Source

To run the application in development mode:

```bash
# Activate your virtual environment
.venv\Scripts\activate

# Run the main GUI
python main.py

# Run the setup wizard directly
python main.py --setup

# Run in CLI mode (no GUI)
python main.py --cli
```

## 📂 Project Structure

- `main.py`: Entry point. Handles CLI arguments and launches the GUI/Engine.
- `app_gui.py`: The modern tabbed interface (Play/Setup).
- `setup_wizard.py`: The calibration interface for capturing regions and templates.
- `core/`:
    - `vision.py`: Screen capture and template matching logic.
    - `input.py`: Humanized mouse/keyboard simulation.
    - `controller.py`: The state machine that manages handlers.
    - `utils.py`: Path resolution for dev and production.
- `minigames/`: Handler plugins for specific games.
- `assets/templates/`: Captured Success/UI images used for vision gating.
- `config/config.json`: All coordinates and thresholds.

## 🏗 Adding a New Minigame

The framework uses a plugin architecture. To add a new game:

1. Create a new handler in `minigames/` (e.g., `my_game_handler.py`).
2. Inherit from a base handler class (if defined) or follow the `HoneyScrapeHandler` pattern.
3. Register the handler in `main.py`:
   ```python
   from minigames import MyGameHandler
   controller.register_handler(MyGameHandler())
   ```
4. Update the GUI in `app_gui.py` and `setup_wizard.py` to include the new game in the menus.

## 📦 Building the EXE

The project includes a dedicated build script:

```bash
python build_exe.py
```

This will generate `dist/Dhurandhar.exe`. 

**Note:** Always ensure the `assets` and `config` folders are present in the same directory as the `.exe` for it to function correctly.

## 🔍 Debugging

Run with the `--debug` flag to see detailed vision logs in the terminal:

```bash
python main.py --debug
```

Vision events, template match scores, and mouse movements will be printed to the log area.
