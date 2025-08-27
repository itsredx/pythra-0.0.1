# pythra/config.py (Complete and Corrected)

from __future__ import annotations
import importlib
import importlib.util
import sys
from pathlib import Path
from typing import Any, Dict, Optional
import yaml

# A dictionary with the default configuration.
# This will be written to the new config.yaml file.
DEFAULT_CONFIG = {
    'app_name': 'My Pythra App',
    'win_width': 1280,
    'win_height': 720,
    'frameless': False,
    'maximixed': False, # Note: Typo from original code, kept for consistency
    'fixed_size': False,
    'Debug': False,
    'web_dir': 'web',
    'assets_dir': 'assets',
    'assets_server_port': 8008,
}

class Config:
    _instance: Optional["Config"] = None

    def __new__(cls, *args, **kwargs):
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