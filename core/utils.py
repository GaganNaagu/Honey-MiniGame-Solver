import os
import sys
import json
import logging

logger = logging.getLogger("dhurandhar.utils")

def get_base_path():
    """Get absolute path to resource, works for dev and for PyInstaller"""
    if getattr(sys, 'frozen', False):
        # We are running in a bundle
        return sys._MEIPASS
    else:
        # We are running in a normal Python environment
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def get_config_dir():
    """Config dir should always be relative to the EXE location, not inside _MEIPASS"""
    if getattr(sys, 'frozen', False):
        return os.path.join(os.path.dirname(sys.executable), "config")
    else:
        return os.path.join(get_base_path(), "config")

def get_assets_dir():
    """Assets should be external to allow writing templates"""
    if getattr(sys, 'frozen', False):
        return os.path.join(os.path.dirname(sys.executable), "assets")
    else:
        return os.path.join(get_base_path(), "assets")

def resolve_template_path(path):
    """Resolve a template path correctly for both absolute and relative storage."""
    if not path:
        return ""
        
    # If the path exists as is, use it
    if os.path.exists(path):
        return path
        
    # Otherwise, check if the filename exists in our current assets/templates directory
    filename = os.path.basename(path)
    current_templates_dir = os.path.join(get_assets_dir(), "templates")
    resolved = os.path.join(current_templates_dir, filename)
    
    if os.path.exists(resolved):
        return resolved
        
    # Return original path as fallback (will likely trigger FileNotFoundError later)
    return path

def get_default_config():
    """Provides the initial default configuration structure."""
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

def ensure_project_dirs():
    """Ensures config and assets/templates directories exist. Creates default config and copies assets if missing."""
    config_dir = get_config_dir()
    assets_dir = get_assets_dir()
    template_dir = os.path.join(assets_dir, "templates")
    
    os.makedirs(config_dir, exist_ok=True)
    os.makedirs(template_dir, exist_ok=True)
    
    # 1. Handle Config
    config_path = os.path.join(config_dir, "config.json")
    if not os.path.exists(config_path):
        logger.info(f"Config file missing. Creating default at {config_path}")
        with open(config_path, 'w') as f:
            json.dump(get_default_config(), f, indent=2)

    # 2. Handle Assets (Copy from bundle if running from EXE)
    if getattr(sys, 'frozen', False):
        import shutil
        base_path = sys._MEIPASS
        bundled_assets = os.path.join(base_path, "assets")
        
        if os.path.exists(bundled_assets):
            logger.info("Checking for bundled assets to extract...")
            for root, dirs, files in os.walk(bundled_assets):
                for file in files:
                    # Determine target path
                    rel_path = os.path.relpath(os.path.join(root, file), bundled_assets)
                    target_path = os.path.join(assets_dir, rel_path)
                    
                    # Create directory if missing
                    os.makedirs(os.path.dirname(target_path), exist_ok=True)
                    
                    # Copy if not exists
                    if not os.path.exists(target_path):
                        logger.info(f"Extracting bundled asset: {rel_path}")
                        shutil.copy2(os.path.join(root, file), target_path)
