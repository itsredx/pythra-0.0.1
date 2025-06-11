# pythra/__init__.py

"""
PyThra Framework Initialization

This package provides a Flutter-inspired UI framework for desktop applications
using Python, rendering via HTML/CSS/JS in a webview (like PySide6 QtWebEngine).
"""

# --- Core Framework Classes ---
try:
    from .core import Framework
    from .config import Config # Expose configuration access
except ImportError as e:
    print(f"PyThra Core/Config not loaded in __init__: {e}")
    Framework = None
    Config = None

# --- Base Widget and State Management ---
from .base import Widget
# Assuming Key class is defined in base.py or reconciler.py
# If in reconciler.py, change the import below:
# from .reconciler import Key
from .base import Key # Prefer placing Key in base.py as it's fundamental
from .state import State, StatefulWidget

# --- Styling Utilities and Constants ---
# Import common styling classes and enums/constants
from .styles import (
    # Layout & Sizing
    EdgeInsets, Alignment, TextAlign, Axis,
    MainAxisAlignment, CrossAxisAlignment, MainAxisSize,
    BoxConstraints,
    # Appearance
    Colors, BoxDecoration, BoxShadow, Offset,
    BorderRadius, BorderSide, BorderStyle,
    TextStyle,
    # Behavior/Misc
    ClipBehavior, ImageFit, BoxFit, Overflow, StackFit, ScrollPhysics,
    TextDirection, TextBaseline, VerticalDirection,
    # Button Specific
    ButtonStyle,
)

# --- Widget Implementations ---
# Expose common widgets directly. Users can import less common ones
# specifically from framework.widgets if needed.
from .widgets import (
    # --- Layout ---
    Container,
    Padding,
    Center,
    Align,
    AspectRatio,
    FittedBox,
    FractionallySizedBox,
    Row,
    Column,
    Flex, # Generic Flex (if distinct from Row/Column usage)
    Wrap,
    Stack,
    Positioned,
    Expanded,
    Spacer,
    SizedBox,
    ListView,
    GridView,
    ListTile,
    Divider,
    Placeholder,

    # --- Structure / Navigation ---
    Scaffold,
    AppBar,
    Drawer,
    EndDrawer,
    BottomNavigationBar,
    BottomNavigationBarItem,

    # --- Basic Elements ---
    Text,
    Image, # Requires AssetImage/NetworkImage from widgets too
    AssetImage,
    NetworkImage,
    Icon,

    # --- Buttons ---
    TextButton,
    ElevatedButton,
    IconButton,
    FloatingActionButton,
    SnackBarAction,

    # --- Overlays / Feedback ---
    Dialog,
    BottomSheet,
    SnackBar,

    # Add any other core widgets you want easily accessible...
)

# --- Define __all__ for explicit export control ---
# This list controls what `from framework import *` imports,
# and also serves as documentation for the public API.
__all__ = [
    # --- Core & Base ---
    # 'Framework', # Potentially None
    # 'Config',    # Potentially None
    # 'Framework', # Comment out if it can be None due to import error
    # 'Config',    # Comment out if it can be None
    'Widget',
    'Key',
    'State',
    'StatefulWidget',

    # --- Styling ---
    'EdgeInsets', 'Alignment', 'TextAlign', 'Axis',
    'MainAxisAlignment', 'CrossAxisAlignment', 'MainAxisSize',
    'BoxConstraints',
    'Colors', 'BoxDecoration', 'BoxShadow', 'Offset',
    'BorderRadius', 'BorderSide', 'BorderStyle',
    'TextStyle',
    'ClipBehavior', 'ImageFit', 'BoxFit', 'Overflow', 'StackFit', 'ScrollPhysics',
    'TextDirection', 'TextBaseline', 'VerticalDirection',
    'ButtonStyle',

    # --- Widgets ---
    # Layout
    'Container', 'Padding', 'Center', 'Align', 'AspectRatio', 'FittedBox',
    'FractionallySizedBox', 'Row', 'Column', 'Flex', 'Wrap', 'Stack',
    'Positioned', 'Expanded', 'Spacer', 'SizedBox', 'ListView', 'GridView',
    'ListTile', 'Divider', 'Placeholder',
    # Structure/Navigation
    'Scaffold', 'AppBar', 'Drawer', 'EndDrawer', 'BottomNavigationBar',
    'BottomNavigationBarItem',
    # Basic Elements
    'Text', 'Image', 'AssetImage', 'NetworkImage', 'Icon',
    # Buttons
    'TextButton', 'ElevatedButton', 'IconButton', 'FloatingActionButton',
    'SnackBarAction',
    # Overlays/Feedback
    'Dialog', 'BottomSheet', 'SnackBar',
]


# --- Package Version (Optional) ---
__version__ = "0.1.0" # Example version

print("PyThra Framework Package Initialized") # Optional: Confirmation message