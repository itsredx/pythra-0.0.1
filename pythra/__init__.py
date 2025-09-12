# pythra/__init__.py

"""
PyThra Framework Initialization

This package provides a Flutter-inspired UI framework for desktop applications
using Python, rendering via HTML/CSS/JS in a webview (like PySide6 QtWebEngine).
"""

# --- Core Framework Classes ---
from .core import Framework
from .config import Config # Expose configuration access

# --- Base Widget and State Management ---
from .base import Widget
# Assuming Key class is defined in base.py or reconciler.py
# If in reconciler.py, change the import below:
# from .reconciler import Key
from .base import Key # Prefer placing Key in base.py as it's fundamental
from .state import State, StatefulWidget, StatelessWidget
from .icons import Icons, IconData
from .controllers import TextEditingController, SliderController, VirtualListController
from .events import TapDetails, PanUpdateDetails
from .drived_widgets.dropdown.dropdown import DerivedDropdown
from .drived_widgets.dropdown.controller import DerivedDropdownController
from .drived_widgets.dropdown.style import DerivedDropdownTheme


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
    TextStyle, ScrollbarTheme, GradientBorderTheme,
    GradientTheme,SliderTheme, DropdownTheme,
    # Behavior/Misc
    ClipBehavior, ImageFit, BoxFit, Overflow, StackFit, ScrollPhysics,
    TextDirection, TextBaseline, VerticalDirection,
    # Button Specific
    ButtonStyle,
    # TextField Specific
    InputDecoration,
)

from .drawing import (
    PathCommandWidget, 
    MoveTo, 
    LineTo,
    ClosePath,
    ArcTo,
    QuadraticCurveTo,
    create_rounded_polygon_path,
    RoundedPolygon,
    PolygonClipper,
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
    SingleChildScrollView,
    Scrollbar,
    GlobalScrollbarStyle,
    Flex, # Generic Flex (if distinct from Row/Column usage)
    Wrap,
    Stack,
    Positioned,
    Expanded,
    Spacer,
    Padding,
    SizedBox,
    ListView,
    VirtualListView,
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
    AssetIcon,
    Icon,

    # --- Buttons ---
    TextButton,
    ElevatedButton,
    IconButton,
    FloatingActionButton,
    SnackBarAction,
    GestureDetector,

    # --- Overlays / Feedback ---
    Dialog,
    BottomSheet,
    SnackBar,
    Dropdown,
    Checkbox,

    # --- Path / Painters ---
    ClipPath,

    TextField,
    Slider,
    
    # Add any other core widgets you want easily accessible...
)

# --- Define __all__ for explicit export control ---
# This list controls what `from framework import *` imports,
# and also serves as documentation for the public API.
__all__ = [
    # --- Core & Base ---
    'Framework',
    'Config',
    'Widget',
    'Key',
    'State',
    'StatefulWidget',
    'StatelessWidget',

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
    'ListTile', 'Divider', 'Placeholder','SingleChildScrollView', 
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

    # --- Path / Painters ---
    'ClipPath',

    'TextField',

    'Slider',
]


# --- Package Version (Optional) ---
__version__ = "0.1.0" # Example version

print("PyThra Toolkit Initialized") # Optional: Confirmation message