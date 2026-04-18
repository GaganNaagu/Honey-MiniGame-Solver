import os
import sys

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
