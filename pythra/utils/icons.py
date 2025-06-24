# In your 'utils/icons.py' or wherever the provider lives
from .. import Config

config = Config()
assets_dir = config.get('assets_dir', 'assets')
port = config.get('assets_server_port')


class MaterialIconProvider:
    """
    A singleton class to build URLs for Material Icons served from a dedicated
    asset server.
    """
    _instance = None
    _base_url: str = None

    STYLE_MAP = {
        "filled": "baseline",
        "outlined": "outline",
        "rounded": "round",
        "sharp": "sharp",
        "two_tone": "two-tone"
    }

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MaterialIconProvider, cls).__new__(cls)
        return cls._instance

    def configure(self, base_url: str):
        """
        Sets the base URL for the icon asset server.
        Example: "http://localhost:{port}/{assets_dir}/icon/"
        """
        if not base_url.endswith('/'):
            base_url += '/'
        self._base_url = base_url
        print(f"MaterialIconProvider configured with base URL: {self._base_url}")

    def get_svg_url(self, icon_name: str, style: str = "filled") -> str:
        """
        Constructs and returns the full URL to a specific icon SVG.

        Args:
            icon_name: The name of the icon (e.g., 'search', 'settings').
            style: The style of the icon ('filled', 'outlined', etc.).
        """
        if self._base_url is None:
            #raise RuntimeError("MaterialIconProvider has not been configured. Call .configure() first.")
            self._base_url = f"http://localhost:{port}/{assets_dir}/icon/material-icons/"
        

        dir_style = self.STYLE_MAP.get(style.lower())
        if not dir_style:
            raise ValueError(f"Invalid Material Icon style '{style}'. Available: {list(self.STYLE_MAP.keys())}")

        # Construct the URL: e.g., http://.../asset/icon/search/baseline.svg
        icon_url = f"{self._base_url}{icon_name}/{dir_style}.svg"
        
        # We no longer check if the file exists. We assume the URL is correct
        # and let the browser handle it. This is faster and more standard.
        return icon_url