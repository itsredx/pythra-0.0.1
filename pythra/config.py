# =============================================================================
# PYTHRA CONFIG SYSTEM - The "Settings Manager" for Your App
# =============================================================================

"""
PyThra Configuration System

This file handles all the settings for your PyThra application - think of it as the
"control panel" where you can adjust how your app looks and behaves.

What does this manage?
- Window size and appearance (width, height, frameless mode)
- Debug settings (helpful during development)
- File locations (where to find your assets, web files, etc.)
- Server settings (port numbers for serving files)

The system automatically creates a config.yaml file in your project if one doesn't exist!
"""

from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, Optional
import yaml

# =============================================================================
# DEFAULT CONFIGURATION - The "Factory Settings" for PyThra Apps
# =============================================================================

# This is like the "factory defaults" - if you don't have a config file,
# PyThra will use these sensible default values to get you started.
DEFAULT_CONFIG = {
    # === WINDOW SETTINGS ===
    'app_name': 'My Pythra App',        # What shows in the window title bar
    'win_width': 1280,                  # Window width in pixels (1280 = good laptop size)
    'win_height': 720,                  # Window height in pixels (720 = HD ready)
    'frameless': False,                 # True = no title bar/borders (fullscreen app look)
    'maximixed': False,                 # True = start maximized (Note: typo kept for compatibility)
    'fixed_size': False,                # True = user can't resize the window
    
    # === DEVELOPMENT SETTINGS ===
    'Debug': True,                      # True = show debug info, False = production mode
    
    # === FILE LOCATIONS ===
    'render_dir': 'render',                   # Folder for HTML, CSS, JavaScript files
    'assets_dir': 'assets',             # Folder for images, fonts, other static files
    
    # === NETWORK SETTINGS ===
    'assets_server_port': 8008,         # Port number for serving your app's files (8008 is usually free)
}

# =============================================================================
# CONFIG CLASS - The "Settings Manager" That Loads Your App Configuration  
# =============================================================================

class Config:
    """
    The "Settings Manager" for your PyThra app - handles loading and managing configuration.
    
    **What does this class do?**
    1. **Singleton Pattern**: Only one Config exists per app (like having one "settings panel")
    2. **Auto-Creation**: Creates a config.yaml file if you don't have one
    3. **Smart Loading**: Reads your settings from config.yaml
    4. **Fallback System**: Uses defaults if something goes wrong
    
    **Real-world analogy:**
    Think of this like your phone's Settings app:
    - It remembers your preferences even after restart
    - It has sensible defaults for new users
    - It creates the settings file if it gets corrupted
    - Only one settings manager exists at a time
    
    **How it works:**
    ```python
    # PyThra automatically creates this for you:
    config = Config('config.yaml')  # Loads or creates config.yaml
    window_width = config.get('win_width')  # Gets the window width setting
    ```
    """
    
    # Singleton pattern: Only one Config instance can exist
    _instance: Optional["Config"] = None

    def __new__(cls, *args, **kwargs):
        """Ensures only one Config instance exists (singleton pattern)"""
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
        return cls._instance

    def __init__(self, config_path: str = "config.yaml"):
        if getattr(self, "_initialized", False):
            return
        self._initialized = True
        
        # --- THIS IS THE FIX ---
        # The Config class now takes a single, unambiguous path.
        self.config_file_path = Path(config_path).resolve()
        self._config: Dict[str, Any] = {}
        
        # Load the configuration. This method will now also CREATE the file.
        self.reload()
        # --- END OF FIX ---

    def reload(self):
        """
        Loads the configuration from the specified file. If the file does not
        exist, it creates it with default values.
        """
        try:
            with self.config_file_path.open("r", encoding="utf-8") as fh:
                data = yaml.safe_load(fh)
            if isinstance(data, dict):
                self._config = data
            else:
                print(f"[Config] Warning: '{self.config_file_path}' does not contain a valid dictionary.")
                self._create_default_config()
        except FileNotFoundError:
            print(f"[Config] File not found at '{self.config_file_path}'. Creating with default values.")
            self._create_default_config()
        except Exception as e:
            print(f"[Config] Error loading config file: {e}")
            self._config = DEFAULT_CONFIG.copy()

    def _create_default_config(self):
        """Writes the default configuration to the file."""
        self._config = DEFAULT_CONFIG.copy()
        try:
            with self.config_file_path.open("w", encoding="utf-8") as fh:
                yaml.dump(self._config, fh, indent=4, sort_keys=False)
            print(f"[Config] Created default config file at '{self.config_file_path}'")
        except Exception as e:
            print(f"[Config] FATAL: Could not write default config file: {e}")

    def as_dict(self) -> Dict[str, Any]:
        return dict(self._config)

    def get(self, key: str, default: Any = None) -> Any:
        return self._config.get(key, default)