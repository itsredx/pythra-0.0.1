# config.py
from __future__ import annotations
import importlib
import importlib.util
import sys
from pathlib import Path
from typing import Any, Dict, Optional
import yaml


class Config:
    """
    Singleton config loader that supports:
      - an embedded config module (default name: _embedded_config, attribute: CONFIG)
      - a fallback YAML file (config.yaml)

    Usage:
        cfg = Config()  # prefers embedded if available, else loads config.yaml
        value = cfg.get("app_name", "default")
        value2 = cfg.get_nested("db.host", "localhost")
        raw = cfga.s_dict()
        cfg.reload()    # re-read embedded/file (useful in dev)

    Parameters:
      config_file: path to YAML config (relative or absolute). Attempts sensible fallbacks.
      prefer_embedded: when True (default) try embedded module first, otherwise check file first.
      embedded_module_name: module name to import when looking for embedded config (default: "_embedded_config")
    """

    _instance: Optional["Config"] = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
        return cls._instance

    def __init__(
        self,
        config_file: str = "config.yaml",
        prefer_embedded: bool = True,
        embedded_module_name: str = "_embedded_config",
    ):
        # initialize only once
        if getattr(self, "_initialized", False):
            return

        self._initialized = True
        self.config_file_arg = config_file
        self.prefer_embedded = bool(prefer_embedded)
        self.embedded_module_name = embedded_module_name

        self._config: Dict[str, Any] = {}
        self._source: Optional[str] = None  # 'embedded' or 'file' or None

        # resolved file path (may be None if not found)
        self._resolved_config_path: Optional[Path] = self._resolve_config_path(config_file)

        # Load according to preference
        self.reload()

    # ----- public API -----
    def reload(self, prefer_embedded: Optional[bool] = None) -> None:
        """
        Reload the configuration. If prefer_embedded is provided, it overrides the instance preference
        just for this reload.
        """
        if prefer_embedded is None:
            prefer = self.prefer_embedded
        else:
            prefer = bool(prefer_embedded)

        # Try embedded first or last depending on preference
        if prefer:
            loaded = self._try_load_embedded() or self._try_load_file()
        else:
            loaded = self._try_load_file() or self._try_load_embedded()

        if not loaded:
            # nothing loaded; keep previous config but mark source None
            self._source = None
            self._config = {}
        # else _try_load_* already set _config and _source

    def as_dict(self) -> Dict[str, Any]:
        """Return the loaded configuration as a dict (may be empty)."""
        return dict(self._config)

    def get(self, key: str, default: Any = None) -> Any:
        """Shallow lookup in the top-level config dict."""
        return self._config.get(key, default)

    def get_nested(self, path: str, default: Any = None, sep: str = ".") -> Any:
        """
        Lookup nested keys using dot-path (e.g. "database.host").
        Returns default if any step is missing.
        """
        cur = self._config
        if not path:
            return default
        for part in path.split(sep):
            if not isinstance(cur, dict):
                return default
            if part in cur:
                cur = cur[part]
            else:
                return default
        return cur

    @property
    def is_embedded(self) -> bool:
        """True if the currently loaded config came from the embedded module."""
        return self._source == "embedded"

    @property
    def source(self) -> Optional[str]:
        """Return 'embedded'|'file'|None depending on where config came from."""
        return self._source

    @property
    def resolved_config_path(self) -> Optional[Path]:
        """If a filesystem config was resolved, return its Path, otherwise None."""
        return self._resolved_config_path

    # ----- internal helpers -----
    def _resolve_config_path(self, config_file: str) -> Optional[Path]:
        """
        Try to resolve the YAML config path using a few strategies:
          1. If config_file is absolute and exists -> return it
          2. If config_file relative to this file's parent parent (project root) exists -> return it
          3. If config_file relative to this file's parent (same folder as config.py) exists -> return it
          4. If config_file relative to cwd exists -> return it
          5. else return None
        """
        candidate = Path(config_file)
        # 1
        if candidate.is_absolute() and candidate.exists():
            return candidate.resolve()

        # project root: assume config.py is in <project>/lib or similar; try parent.parent/config_file
        here = Path(__file__).resolve().parent
        project_root = here.parent  # heuristics: config.py located in lib/ or project root
        p1 = (project_root / config_file).resolve()
        if p1.exists():
            return p1

        # same folder as config.py
        p2 = (here / config_file).resolve()
        if p2.exists():
            return p2

        # cwd
        p3 = (Path.cwd() / config_file).resolve()
        if p3.exists():
            return p3

        return None

    def _try_load_embedded(self) -> bool:
        """
        Try to import the embedded module and fetch CONFIG. Returns True on success.
        """
        try:
            print(f"[Config] trying to import {self.embedded_module_name}")
            module = importlib.import_module(self.embedded_module_name)
            print(f"[Config] imported {module}")
            # Accept module.CONFIG being a dict-like object
            cfg = getattr(module, "CONFIG", None) or getattr(module, "embedded_config", None)
            if isinstance(cfg, dict):
                self._config = dict(cfg)
                self._source = "embedded"
                return True
            else:
                # If CONFIG exists but isn't dict, coerce if possible
                if cfg is not None:
                    try:
                        self._config = dict(cfg)
                        self._source = "embedded"
                        return True
                    except Exception:
                        # unsupported type
                        return False
                return False
        except ModuleNotFoundError:
            return False
        except Exception:
            # Any other import error should not crash the loader; treat as not available
            return False

    def _try_load_file(self) -> bool:
        """
        Try to load YAML file from resolved path. Returns True on success.
        """
        if not self._resolved_config_path:
            return False
        try:
            with self._resolved_config_path.open("r", encoding="utf-8") as fh:
                data = yaml.safe_load(fh)
            if isinstance(data, dict):
                self._config = data
                self._source = "file"
                return True
            else:
                # YAML parsed but not dict -> store raw under a key
                self._config = {"__root__": data}
                self._source = "file"
                return True
        except Exception:
            return False

    # optional convenience: pretty print for debug
    def debug_print(self) -> None:
        print(f"[Config] source={self._source}; embedded_module={self.embedded_module_name}; config_file_arg={self.config_file_arg}")
        if self._resolved_config_path:
            print(f"[Config] resolved_config_path={self._resolved_config_path}")
        print(f"[Config] keys={list(self._config.keys())}")

# single shared instance helper (optional)
def get_config(*args, **kwargs) -> Config:
    """
    Convenience factory that returns the singleton Config instance.
    Arguments forwarded to Config() only on the first call.
    """
    return Config(*args, **kwargs)
