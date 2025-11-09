#pythra/styles.py
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, Union, Tuple, List, Dict, Any
import re # For hex validation

from .base import make_hashable

#Colors = Color()

# framework/styles.py

from typing import Union

class EdgeInsets:
    left_c=0
    top_c=0
    right_c=0 
    bottom_c=0
    """
    Represents padding or margin for a widget's edges.
    Compatible with reconciliation (hashable).
    """
    def __init__(self, left: float = 0.0, top: float = 0.0, right: float = 0.0, bottom: float = 0.0):
        """
        Initializes EdgeInsets. Values assumed to be pixels.

        Args:
            left (float): Padding/margin value for the left side. Defaults to 0.
            top (float): Padding/margin value for the top side. Defaults to 0.
            right (float): Padding/margin value for the right side. Defaults to 0.
            bottom (float): Padding/margin value for the bottom side. Defaults to 0.
        """
        self.left = max(-500.0, left)   # Ensure non-negative
        self.top = max(-500.0, top)
        self.right = max(-500.0, right)
        self.bottom = max(-500.0, bottom)

    # --- Static Constructors ---
    @staticmethod
    def all(value: float) -> 'EdgeInsets':
        """Creates EdgeInsets with the same value for all four sides."""
        val = max(-500.0, value)
        return EdgeInsets(left=val, top=val, right=val, bottom=val)

    @staticmethod
    def symmetric(horizontal: float = 0.0, vertical: float = 0.0) -> 'EdgeInsets':
        """Creates EdgeInsets with symmetric horizontal and vertical values."""
        h = max(-500.0, horizontal)
        v = max(-500.0, vertical)
        return EdgeInsets(left=h, right=h, top=v, bottom=v)

    @staticmethod
    def only(left: float = 0.0, top: float = 0.0, right: float = 0.0, bottom: float = 0.0) -> 'EdgeInsets':
         """Creates EdgeInsets with only the specified values set, others default to 0."""
         # Alias for the main constructor with clearer intent
         EdgeInsets.left_c=left
         EdgeInsets.top_c=top
         EdgeInsets.right_c=right
         EdgeInsets.bottom_c=bottom
         return EdgeInsets(left=left, top=top, right=right, bottom=bottom)

    @staticmethod
    def edit(operation: str='+',left: float = 0.0, top: float = 0.0, right: float = 0.0, bottom: float = 0.0) -> 'EdgeInsets':
        if operation == '+':
            left += EdgeInsets.left_c
            top += EdgeInsets.top_c
            right += EdgeInsets.right_c
            bottom += EdgeInsets.bottom_c
        elif operation == '-':
            left = EdgeInsets.left_c - left 
            top = EdgeInsets.top_c - top
            right = EdgeInsets.right_c - right
            bottom = EdgeInsets.bottom_c - bottom
        return EdgeInsets(left=left, top=top, right=right, bottom=bottom)

    

    # Deprecate or remove LRTB if 'only' is preferred for clarity
    # @staticmethod
    # def LRTB(...)

    # --- CSS Conversion ---
    def to_css_value(self) -> str:
        """
        Returns the CSS value string for padding/margin properties
        (e.g., '10px 5px 10px 5px'). Uses shorthand if possible.
        """
        # Check for simplifications
        if self.left == self.top == self.right == self.bottom:
            return f"{self.top}px" # All same: top
        if self.top == self.bottom and self.left == self.right:
            return f"{self.top}px {self.right}px" # Vertical Horizontal
        if self.left == self.right:
            return f"{self.top}px {self.right}px {self.bottom}px" # Top Horizontal Bottom
        # Full definition: Top Right Bottom Left
        return f"{self.top}px {self.right}px {self.bottom}px {self.left}px"

    def to_css(self) -> str:
        """
        Returns the full CSS padding or margin property string
        (e.g., 'padding: 10px 5px;').
        NOTE: Property name ('padding' or 'margin') must be added by caller.
        """
        # Return only the value part, property name decided by context
        return self.to_css_value() # Just return the value

    # --- Calculations ---
    def to_int_vertical(self) -> float: # Changed to float as inputs are float
        """Calculates the total vertical padding/margin (top + bottom)."""
        return self.top + self.bottom

    def to_int_horizontal(self) -> float: # Changed to float
        """Calculates the total horizontal padding/margin (left + right)."""
        return self.right + self.left

    # --- Compatibility Methods ---
    def __eq__(self, other):
        if not isinstance(other, EdgeInsets):
            return NotImplemented
        return (self.left == other.left and
                self.top == other.top and
                self.right == other.right and
                self.bottom == other.bottom)

    def __hash__(self):
        return hash((self.left, self.top, self.right, self.bottom))

    def __repr__(self):
         if self.left == self.top == self.right == self.bottom:
              return f"EdgeInsets.all({self.left})"
         if self.left == self.right and self.top == self.bottom:
              # Handle case where horizontal and vertical are also equal (covered by all)
              if self.left == self.top: return f"EdgeInsets.all({self.left})"
              return f"EdgeInsets.symmetric(horizontal={self.left}, vertical={self.top})"
         # Use 'only' for clarity if some values are 0
         args = []
         if self.left != 0.0: args.append(f"left={self.left}")
         if self.top != 0.0: args.append(f"top={self.top}")
         if self.right != 0.0: args.append(f"right={self.right}")
         if self.bottom != 0.0: args.append(f"bottom={self.bottom}")
         if not args: return "EdgeInsets()" # All zero
         return f"EdgeInsets.only({', '.join(args)})"


    def to_dict(self) -> Dict[str, float]:
         """Returns a simple dictionary representation."""
         return {'left': self.left, 'top': self.top, 'right': self.right, 'bottom': self.bottom}

    # --- ADDED to_tuple ---
    def to_tuple(self) -> Tuple[float, float, float, float]:
         """Returns a hashable tuple representation (left, top, right, bottom)."""
         return (self.left, self.top, self.right, self.bottom)


# print("Edge Insets", EdgeInsets.only(top=40, left=20).edit(operation='-',top=10))

class Alignment:
    """
    Represents alignment for widgets using flexbox concepts (justify-content, align-items).
    Ensures compatibility with reconciliation by being hashable.

    Attributes:
        justify_content (str): CSS value for justify-content (main axis alignment).
        align_items (str): CSS value for align-items (cross axis alignment).
    """
    def __init__(self, justify_content: str, align_items: str):
        """
        Initializes Alignment. It's recommended to use the static methods
        like Alignment.center(), Alignment.top_left(), etc.

        Args:
            justify_content (str): CSS value like 'flex-start', 'center', 'flex-end',
                                  'space-between', 'space-around', 'space-evenly'.
            align_items (str): CSS value like 'flex-start', 'center', 'flex-end',
                                'stretch', 'baseline'.
        """
        # Consider adding validation for allowed CSS values if needed
        self.justify_content = justify_content
        self.align_items = align_items

    # --- Static Constructors (Convenience Methods) ---
    @staticmethod
    def center():
        return Alignment('center', 'center')

    @staticmethod
    def top_left():
        return Alignment('flex-start', 'flex-start')

    @staticmethod
    def top_center():
        return Alignment('center', 'flex-start')

    @staticmethod
    def top_right():
        return Alignment('flex-end', 'flex-start')

    @staticmethod
    def center_left():
        return Alignment('flex-start', 'center')

    @staticmethod
    def center_right():
        return Alignment('flex-end', 'center')

    @staticmethod
    def bottom_left():
        return Alignment('flex-start', 'flex-end')

    @staticmethod
    def bottom_center():
        return Alignment('center', 'flex-end')

    @staticmethod
    def bottom_right():
        return Alignment('flex-end', 'flex-end')

    # Add others if needed, e.g., space_between variants
    @staticmethod
    def space_between_center(): # Example
        return Alignment('space-between', 'center')

    # --- Compatibility Methods ---

    def to_css_dict(self) -> dict:
        """
        Returns alignment properties as a dictionary suitable for CSS generation
        or applying as inline styles. Includes display:flex.
        """
        return {
            'display': 'flex',
            'justify-content': self.justify_content,
            'align-items': self.align_items
        }

    def to_css(self) -> str:
        """
        Converts the Alignment object to a CSS string snippet for flexbox layout.
        Includes display: flex.
        """
        return f"display: flex; justify-content: {self.justify_content}; align-items: {self.align_items};"

    # --- Add __eq__ and __hash__ for compatibility with style keys ---
    def __eq__(self, other):
        if not isinstance(other, Alignment):
            return NotImplemented
        return (self.justify_content == other.justify_content and
                self.align_items == other.align_items)

    def __hash__(self):
        # Hash a tuple of the relevant attributes
        return hash((self.justify_content, self.align_items))

    # --- Optional: Add representation for debugging ---
    def __repr__(self):
         # Try to find matching static method name for cleaner repr (optional)
         for name, method in Alignment.__dict__.items():
             if isinstance(method, staticmethod):
                 try:
                     instance = method.__func__() # Call the static method
                     if instance == self:
                          return f"Alignment.{name}()"
                 except Exception: # Catch potential errors during static method call
                     pass
         # Fallback representation
         return f"Alignment(justify_content='{self.justify_content}', align_items='{self.align_items}')"

    # --- Optional: Add method for reconciler prop representation ---
    def to_dict(self):
         """Returns a simple dictionary representation."""
         return {'justify_content': self.justify_content, 'align_items': self.align_items}

    # --- Optional: Add method for hashable tuple representation ---
    def to_tuple(self):
         """Returns a hashable tuple representation."""
         return (self.justify_content, self.align_items)

class TextAlign:
    """
    Represents horizontal text alignment options. Compatible with reconciliation.

    Attributes:
        value (str): The CSS text-align value (e.g., 'left', 'center', 'right', 'justify', 'start', 'end').
    """
    # Define constants for common values directly on the class
    LEFT = 'left'
    RIGHT = 'right'
    CENTER = 'center'
    JUSTIFY = 'justify'
    START = 'start' # Respects LTR/RTL directionality
    END = 'end'     # Respects LTR/RTL directionality

    def __init__(self, value: str):
        """
        Initializes TextAlign. Using class constants like TextAlign.CENTER is recommended.

        Args:
            value (str): A valid CSS text-align value.
        """
        # Optional: Add validation for allowed CSS values
        allowed_values = {self.LEFT, self.RIGHT, self.CENTER, self.JUSTIFY, self.START, self.END}
        if value not in allowed_values:
             # Or raise ValueError('Invalid TextAlign value')
             print(f"Warning: Using potentially invalid TextAlign value: '{value}'")
        self.value = value

    # --- Static Constructors (Optional, can use constants directly) ---
    @staticmethod
    def center(): return TextAlign(TextAlign.CENTER)
    @staticmethod
    def left(): return TextAlign(TextAlign.LEFT)
    @staticmethod
    def right(): return TextAlign(TextAlign.RIGHT)
    @staticmethod
    def justify(): return TextAlign(TextAlign.JUSTIFY)
    @staticmethod
    def start(): return TextAlign(TextAlign.START)
    @staticmethod
    def end(): return TextAlign(TextAlign.END)

    # --- Compatibility Methods ---

    def to_css_dict(self) -> dict:
        """Returns the CSS property as a dictionary."""
        return {'text-align': self.value}

    def to_css(self) -> str:
        """Returns the CSS property string (e.g., 'text-align: center;')."""
        return f"text-align: {self.value};"

    # --- Hashability & Equality ---
    def __eq__(self, other):
        if not isinstance(other, TextAlign):
            return NotImplemented
        return self.value == other.value

    def __hash__(self):
        return hash(self.value)

    # --- Representation ---
    def __repr__(self):
         # Try matching constants for cleaner representation
         for name, val in TextAlign.__dict__.items():
             if isinstance(val, str) and val == self.value: # Check class constants
                 return f"TextAlign.{name}"
         # Fallback
         return f"TextAlign('{self.value}')"

    # --- Reconciler Prop Representation ---
    def to_dict(self): return {'value': self.value}
    def to_tuple(self): return (self.value,) # Tuple for make_hashable

# --- BoxConstraints Refactored ---
class BoxConstraints:
    """
    Represents min/max width and height constraints for a widget.
    Compatible with reconciliation.
    """
    def __init__(self,
                 minWidth: Optional[float] = 0.0, # Default min width is 0
                 maxWidth: Optional[float] = float('inf'), # Default max width is infinity
                 minHeight: Optional[float] = 0.0, # Default min height is 0
                 maxHeight: Optional[float] = float('inf') # Default max height is infinity
                ):
        """
        Initializes BoxConstraints. Use float('inf') for unbounded max values.
        Units are assumed to be pixels for CSS conversion.

        Args:
            minWidth (float): Minimum width (default 0).
            maxWidth (float): Maximum width (default infinity).
            minHeight (float): Minimum height (default 0).
            maxHeight (float): Maximum height (default infinity).
        """
        # Validate inputs (ensure non-negative, min <= max)
        self.minWidth = max(0.0, minWidth) if minWidth is not None else 0.0
        self.maxWidth = max(self.minWidth, maxWidth) if maxWidth is not None else float('inf')
        self.minHeight = max(0.0, minHeight) if minHeight is not None else 0.0
        self.maxHeight = max(self.minHeight, maxHeight) if maxHeight is not None else float('inf')

    # --- Static Constructors (Optional) ---
    @staticmethod
    def tight(width: float, height: float):
        """Creates constraints forcing a specific size."""
        return BoxConstraints(minWidth=width, maxWidth=width, minHeight=height, maxHeight=height)

    @staticmethod
    def expand(width: Optional[float] = None, height: Optional[float] = None):
         """Creates constraints forcing maximum size (infinity)."""
         return BoxConstraints(minWidth=width or 0.0, maxWidth=float('inf'),
                               minHeight=height or 0.0, maxHeight=float('inf'))

    # --- Compatibility Methods ---

    def to_css_dict(self) -> dict:
        """Returns constraints as a dictionary of CSS properties."""
        styles = {}
        # Only include constraints that are not default (0 for min, inf for max)
        if self.minWidth > 0.0: styles['min-width'] = f"{self.minWidth}px"
        if self.maxWidth != float('inf'): styles['max-width'] = f"{self.maxWidth}px"
        if self.minHeight > 0.0: styles['min-height'] = f"{self.minHeight}px"
        if self.maxHeight != float('inf'): styles['max-height'] = f"{self.maxHeight}px"
        return styles

    def to_css(self) -> str:
        """Converts constraints to a CSS string snippet."""
        style_dict = self.to_css_dict()
        return " ".join(f"{prop}: {value};" for prop, value in style_dict.items())

    # --- Hashability & Equality ---
    def __eq__(self, other):
        if not isinstance(other, BoxConstraints):
            return NotImplemented
        return (self.minWidth == other.minWidth and
                self.maxWidth == other.maxWidth and
                self.minHeight == other.minHeight and
                self.maxHeight == other.maxHeight)

    def __hash__(self):
        # Hash a tuple of the defining attributes
        return hash((self.minWidth, self.maxWidth, self.minHeight, self.maxHeight))

    # --- Representation ---
    def __repr__(self):
        props = []
        if self.minWidth != 0.0: props.append(f"minWidth={self.minWidth}")
        if self.maxWidth != float('inf'): props.append(f"maxWidth={self.maxWidth}")
        if self.minHeight != 0.0: props.append(f"minHeight={self.minHeight}")
        if self.maxHeight != float('inf'): props.append(f"maxHeight={self.maxHeight}")
        return f"BoxConstraints({', '.join(props)})"

    # --- Reconciler Prop Representation ---
    def to_dict(self):
         return {'minWidth': self.minWidth, 'maxWidth': self.maxWidth,
                 'minHeight': self.minHeight, 'maxHeight': self.maxHeight}

    def to_tuple(self):
         """Returns a hashable tuple representation."""
         return (self.minWidth, self.maxWidth, self.minHeight, self.maxHeight)

class Color:
    """
    Provides utility methods for defining CSS colors (hex, rgba)
    and defines common Material Design 3 color role constants (approximations).

    Usage:
        color = Colors.primary
        custom_hex = Colors.hex("#FF5733")
        transparent_red = Colors.rgba(255, 0, 0, 0.5)
    """   

    # --- Material Design 3 Color Role Constants (Examples - Use your theme's values) ---
    # Primary Palette
    primary = '#6750A4'
    onPrimary = '#FFFFFF'
    primaryContainer = '#EADDFF'
    onPrimaryContainer = '#21005D'
    # Secondary Palette
    secondary = '#625B71'
    onSecondary = '#FFFFFF'
    secondaryContainer = '#E8DEF8'
    onSecondaryContainer = '#1D192B'
    # Tertiary Palette
    tertiary = '#7D5260'
    onTertiary = '#FFFFFF'
    tertiaryContainer = '#FFD8E4'
    onTertiaryContainer = '#31111D'
    # Error Palette
    error = '#B3261E'
    onError = '#FFFFFF'
    errorContainer = '#F9DEDC'
    onErrorContainer = '#410E0B'
    # Neutral Palette (Surface Tones)
    background = '#FFFBFE' # Often same as Surface
    onBackground = '#1C1B1F'
    surface = '#FFFBFE'
    onSurface = '#1C1B1F'
    surfaceVariant = '#E7E0EC'
    onSurfaceVariant = '#49454F'
    outline = '#79747E'
    outlineVariant = '#CAC4D0' # For dividers etc.
    shadow = '#000000'
    scrim = '#000000' # Often black with alpha applied separately
    # Inverse Tones (for Snackbars, etc.)
    inverseSurface = '#313033'
    inverseOnSurface = '#F4EFF4'
    inversePrimary = '#D0BCFF'
    # Fixed Tones (Less common in M3 theming but sometimes useful)
    # surfaceBright = '#FFFBFE'
    # surfaceDim = '#DED8E1'
    # surfaceContainerLowest = '#FFFFFF'
    # surfaceContainerLow = '#F7F2FA'
    # surfaceContainer = '#F3EDF7'
    # surfaceContainerHigh = '#ECE6F0'
    # surfaceContainerHighest = '#E6E0E9'

    # --- Common CSS Named Colors ---
    # Can be added if needed, but M3 roles are preferred
    red = 'red'
    blue = 'blue'
    green = 'green'
    white = 'white'
    black = 'black'
    grey = 'grey' # Or gray
    lightgrey = 'lightgrey' # Or lightgray
    darkgrey = 'darkgrey' # Or darkgray
    transparent = 'transparent'


    def __getattr__(self, name):
        """
        Retrieves the color name as an attribute of the class.
        
        Args:
            name (str): The name of the color attribute.

        Returns:
            str: The color name.
        """
        return name


    # --- Utility Methods ---
    @staticmethod
    def hex(hex_code: str) -> str:
        """
        Validates and returns a hexadecimal color code string (e.g., "#RRGGBB" or "#RGB").

        Args:
            hex_code (str): A hexadecimal color code string.

        Raises:
            ValueError: If the hex code is not in a valid format.

        Returns:
            str: The validated hex color code.
        """
        hex_code = hex_code.strip()
        # Basic validation for # followed by 3, 4, 6, or 8 hex digits
        if not re.match(r"^#([0-9a-fA-F]{3}|[0-9a-fA-F]{4}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})$", hex_code):
            raise ValueError(f"Invalid hex code format: '{hex_code}'. Should be #RGB, #RGBA, #RRGGBB, or #RRGGBBAA.")
        return hex_code

    @staticmethod
    def gradient(direction: str, color, color2, color3=None, color4=None, color5=None) -> str:
        """
        Validates and returns a hexadecimal color code string (e.g., "#RRGGBB" or "#RGB").

        Args:
            hex_code (str): A hexadecimal color code string.

        Raises:
            ValueError: If the hex code is not in a valid format.

        Returns:
            str: The validated hex color code.
        """
        # hex_code = hex_code.strip()
        # # Basic validation for # followed by 3, 4, 6, or 8 hex digits
        # if not re.match(r"^#([0-9a-fA-F]{3}|[0-9a-fA-F]{4}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})$", hex_code):
        #     raise ValueError(f"Invalid hex code format: '{hex_code}'. Should be #RGB, #RGBA, #RRGGBB, or #RRGGBBAA.")
        comma=", "
        return f"linear-gradient({direction}, {color}, {color2+comma if color3 else color2}{color3+comma if color3 else ""}{color4+comma if color4 else ""}{color5+comma if color5 else ""})"

    @staticmethod
    def rgba(red: int, green: int, blue: int, alpha: float) -> str:
        """
        Creates an rgba() CSS color string.

        Args:
            red (int): Red component (0-255).
            green (int): Green component (0-255).
            blue (int): Blue component (0-255).
            alpha (float): Alpha/opacity component (0.0 to 1.0).

        Raises:
            ValueError: If color components or alpha are out of range.

        Returns:
            str: The rgba(R, G, B, A) color string.
        """
        if not (0 <= red <= 255 and 0 <= green <= 255 and 0 <= blue <= 255):
            raise ValueError("RGB values must be between 0 and 255.")
        if not (0.0 <= alpha <= 1.0):
             raise ValueError("Alpha value must be between 0.0 and 1.0.")
        # Corrected order: R, G, B, A
        return f"rgba({red}, {green}, {blue}, {alpha})"

    # --- Removed __getattr__ ---
    # def __getattr__(self, name): ...
Colors = Color()

# Assume Offset helper exists or define it here/import
# Example definition if needed:
class Offset:
     def __init__(self, dx: float, dy: float):
         self.dx = dx
         self.dy = dy
     def to_css(self):
         return f"{self.dx}px {self.dy}px"
     def __eq__(self, other):
         return isinstance(other, Offset) and self.dx == other.dx and self.dy == other.dy
     def __hash__(self):
         return hash((self.dx, self.dy))
     def __repr__(self):
         return f"Offset({self.dx}, {self.dy})"
# End Example Offset definition

class BoxShadow:
    """
    Represents a CSS box-shadow effect. Compatible with reconciliation.
    """
    def __init__(self,
                 color: str = 'rgba(0,0,0,0.2)', # Default shadow color
                 offset: Offset = Offset(0, 2), # Default offset (dx, dy)
                 blurRadius: float = 4.0, # Default blur
                 spreadRadius: float = 0.0, # Default spread
                 # Add inset keyword if needed later
                 ):
        """
        Initializes the box shadow.

        Args:
            color (str): The color of the shadow (CSS color string).
            offset (Offset): An Offset object specifying dx and dy.
            blurRadius (float): The blur radius in pixels. Must be non-negative.
            spreadRadius (float): The spread radius in pixels.
        """
        self.color = color
        if not isinstance(offset, Offset):
             raise TypeError("offset must be an Offset instance.")
        self.offset = offset
        self.blurRadius = max(0.0, blurRadius) # Ensure non-negative
        self.spreadRadius = spreadRadius

    # --- Compatibility Methods ---

    def to_css(self) -> str:
        """
        Converts the box shadow to a CSS box-shadow value string.
        Format: offset-x offset-y blur-radius spread-radius color
        """
        # Format: h-offset v-offset blur spread color
        return f'{self.offset.dx}px {self.offset.dy}px {self.blurRadius}px {self.spreadRadius}px {self.color}'

    def to_css_dict(self) -> dict:
         """Returns the CSS property as a dictionary."""
         return {'box-shadow': self.to_css()}

    # --- Hashability & Equality ---
    def __eq__(self, other):
        if not isinstance(other, BoxShadow):
            return NotImplemented
        return (self.color == other.color and
                self.offset == other.offset and
                self.blurRadius == other.blurRadius and
                self.spreadRadius == other.spreadRadius)

    def __hash__(self):
        # Hash a tuple of the relevant attributes
        # Ensure offset is hashable (Offset class needs __hash__)
        return hash((self.color, self.offset, self.blurRadius, self.spreadRadius))

    # --- Representation ---
    def __repr__(self):
        return f"BoxShadow(color='{self.color}', offset={self.offset!r}, blurRadius={self.blurRadius}, spreadRadius={self.spreadRadius})"

    # --- Reconciler Prop Representation ---
    def to_dict(self):
         return {'color': self.color, 'offset': {'dx': self.offset.dx, 'dy': self.offset.dy},
                 'blurRadius': self.blurRadius, 'spreadRadius': self.spreadRadius}

    def to_tuple(self):
         """Returns a hashable tuple representation."""
         # Hash offset's tuple representation if Offset is complex
         return (self.color, self.offset, self.blurRadius, self.spreadRadius)



# --- ClipBehavior Refactored (Using Enum) ---
class ClipBehavior:
    """Specifies how content should be clipped."""
    NONE = 'none' # CSS overflow: visible (effectively)
    HARD_EDGE = 'hardEdge' # CSS overflow: hidden
    ANTI_ALIAS = 'antiAlias' # CSS overflow: hidden (visual effect not guaranteed)
    ANTI_ALIAS_WITH_SAVE_LAYER = 'antiAliasWithSaveLayer' # CSS overflow: hidden (effect not CSS)

    def to_css_overflow(self) -> Optional[str]:
         """Maps enum value to CSS overflow property value."""
         if self == ClipBehavior.NONE:
              return 'visible' # Or None if default is desired
         elif self in [ClipBehavior.HARD_EDGE, ClipBehavior.ANTI_ALIAS, ClipBehavior.ANTI_ALIAS_WITH_SAVE_LAYER]:
              return 'hidden'
         return None # Default or unmapped

# --- ImageFit (Keep as String Constants) ---
class ImageFit:
    """CSS object-fit values."""
    CONTAIN = 'contain'
    COVER = 'cover'
    FILL = 'fill'
    NONE = 'none'
    SCALE_DOWN = 'scale-down'

# --- MainAxisSize (Keep as conceptual values) ---
class MainAxisSize:
    """Conceptual sizing behavior for main axis in Flex/Row/Column."""
    MIN = 'min' # Wrap content size
    MAX = 'max' # Fill available space

# --- Axis Constants ---
class Axis:
    """Specifies the primary direction for layout widgets like Flex, ListView."""
    VERTICAL = 'vertical'
    HORIZONTAL = 'horizontal'

# --- MainAxisAlignment Constants (for Flexbox justify-content) ---
class MainAxisAlignment:
    """How children should be placed along the main axis in a flex layout."""
    START = 'flex-start'
    END = 'flex-end'
    CENTER = 'center'
    SPACE_BETWEEN = 'space-between'
    SPACE_AROUND = 'space-around'
    SPACE_EVENLY = 'space-evenly'

# --- CrossAxisAlignment Constants (for Flexbox align-items) ---
class CrossAxisAlignment:
    """How children should be placed along the cross axis in a flex layout."""
    START = 'flex-start'
    END = 'flex-end'
    CENTER = 'center'
    STRETCH = 'stretch' # Make children fill the cross axis.
    BASELINE = 'baseline' # Align children along their text baseline.

class TextStyle:
    """
    Holds styling information for text (font, color, decoration, etc.).
    Compatible with reconciliation.
    """
    def __init__(self,
                 color: Optional[str] = None,
                 # Font properties
                 fontFamily: Optional[str] = None, # e.g., 'Roboto', 'Arial', sans-serif
                 fontSize: Optional[Union[int, float]] = None, # Assumed px
                 fontWeight: Optional[Union[str, int]] = None, # e.g., 'bold', 'normal', 400, 700
                 fontStyle: Optional[str] = None, # e.g., 'italic', 'normal'
                 # Spacing
                 letterSpacing: Optional[Union[int, float, str]] = None, # number (px) or string ('normal')
                 wordSpacing: Optional[Union[int, float, str]] = None, # number (px) or string ('normal')
                 lineHeight: Optional[Union[int, float, str]] = None, # number (multiplier), px, or 'normal'
                 # Decoration
                 textDecoration: Optional[str] = None, # e.g., 'underline', 'line-through', 'none'
                 decorationColor: Optional[str] = None, # Color of the decoration line
                 decorationStyle: Optional[str] = None, # e.g., 'solid', 'wavy', 'dotted'
                 decorationThickness: Optional[Union[int, float, str]] = None, # number (px) or string ('auto')
                 # Add other properties like textShadow, fontFeatures, etc. if needed
                 ):
        """
        Initializes the TextStyle object.

        Args:
            color: Text color (CSS color string).
            fontFamily: CSS font-family value.
            fontSize: Font size in pixels.
            fontWeight: CSS font-weight value.
            fontStyle: CSS font-style value.
            letterSpacing: CSS letter-spacing value (number assumes px).
            wordSpacing: CSS word-spacing value (number assumes px).
            lineHeight: CSS line-height value (number is multiplier, or include units).
            textDecoration: CSS text-decoration-line value.
            decorationColor: CSS text-decoration-color value.
            decorationStyle: CSS text-decoration-style value.
            decorationThickness: CSS text-decoration-thickness value.
        """
        self.color = color
        self.fontFamily = fontFamily
        self.fontSize = fontSize
        self.fontWeight = fontWeight
        self.fontStyle = fontStyle
        self.letterSpacing = letterSpacing
        self.wordSpacing = wordSpacing
        self.lineHeight = lineHeight
        self.textDecoration = textDecoration
        self.decorationColor = decorationColor
        self.decorationStyle = decorationStyle
        self.decorationThickness = decorationThickness

    # --- Compatibility Methods ---

    def _format_css_value(self, value: Any, default_unit: str = 'px') -> Optional[str]:
        """Helper to format values for CSS, adding units if needed."""
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return f"{value}{default_unit}"
        return str(value) # Assume string values are already correct CSS values

    def to_css_dict(self) -> Dict[str, str]:
        """Converts text style properties to a dictionary of CSS styles."""
        styles = {}
        if self.color: styles['color'] = self.color
        if self.fontFamily: styles['font-family'] = self.fontFamily
        if self.fontSize: styles['font-size'] = self._format_css_value(self.fontSize)
        if self.fontWeight: styles['font-weight'] = str(self.fontWeight)
        if self.fontStyle: styles['font-style'] = self.fontStyle
        if self.letterSpacing: styles['letter-spacing'] = self._format_css_value(self.letterSpacing)
        if self.wordSpacing: styles['word-spacing'] = self._format_css_value(self.wordSpacing)
        if self.lineHeight: styles['line-height'] = self._format_css_value(self.lineHeight, default_unit='') # Unitless multiplier is common
        # Combine text-decoration properties if possible
        if self.textDecoration: styles['text-decoration-line'] = self.textDecoration
        if self.decorationColor: styles['text-decoration-color'] = self.decorationColor
        if self.decorationStyle: styles['text-decoration-style'] = self.decorationStyle
        if self.decorationThickness: styles['text-decoration-thickness'] = self._format_css_value(self.decorationThickness)
        # Could try to combine into shorthand `text-decoration` but it's complex
        return styles

    def to_css(self) -> str:
        """Converts text style attributes to a CSS string snippet."""
        style_dict = self.to_css_dict()
        return " ".join(f"{prop}: {value};" for prop, value in style_dict.items())

    # --- Hashability & Equality ---
    def __eq__(self, other):
        if not isinstance(other, TextStyle):
            return NotImplemented
        # Compare all attributes
        return (self.color == other.color and
                self.fontFamily == other.fontFamily and
                self.fontSize == other.fontSize and
                self.fontWeight == other.fontWeight and
                self.fontStyle == other.fontStyle and
                self.letterSpacing == other.letterSpacing and
                self.wordSpacing == other.wordSpacing and
                self.lineHeight == other.lineHeight and
                self.textDecoration == other.textDecoration and
                self.decorationColor == other.decorationColor and
                self.decorationStyle == other.decorationStyle and
                self.decorationThickness == other.decorationThickness)

    def __hash__(self):
        # Hash a tuple of all attributes
        return hash((
            self.color, self.fontFamily, self.fontSize, self.fontWeight,
            self.fontStyle, self.letterSpacing, self.wordSpacing, self.lineHeight,
            self.textDecoration, self.decorationColor, self.decorationStyle,
            self.decorationThickness
        ))

    # --- Representation ---
    def __repr__(self):
        props = []
        for attr in ['color', 'fontFamily', 'fontSize', 'fontWeight', 'fontStyle',
                     'letterSpacing', 'wordSpacing', 'lineHeight', 'textDecoration',
                     'decorationColor', 'decorationStyle', 'decorationThickness']:
            value = getattr(self, attr)
            if value is not None:
                props.append(f"{attr}={value!r}")
        return f"TextStyle({', '.join(props)})"

    # --- Reconciler Prop Representation ---
    def to_dict(self):
        """Returns a simple dictionary representation."""
        return {attr: getattr(self, attr) for attr in [
            'color', 'fontFamily', 'fontSize', 'fontWeight', 'fontStyle',
            'letterSpacing', 'wordSpacing', 'lineHeight', 'textDecoration',
            'decorationColor', 'decorationStyle', 'decorationThickness'
        ] if getattr(self, attr) is not None}

    def to_tuple(self):
         """Returns a hashable tuple representation."""
         return tuple(getattr(self, attr) for attr in [
            'color', 'fontFamily', 'fontSize', 'fontWeight', 'fontStyle',
            'letterSpacing', 'wordSpacing', 'lineHeight', 'textDecoration',
            'decorationColor', 'decorationStyle', 'decorationThickness'
        ])

# --- BorderStyle Constants ---
class BorderStyle:
    """
    A class representing various border styles.
    
    This class defines the different types of border styles that can be applied to widgets.

    Attributes:
        NONE (str): No border.
        DOTTED (str): Dotted border.
        DASHED (str): Dashed border.
        SOLID (str): Solid border.
        DOUBLE (str): Double border.
        GROOVE (str): Groove border.
        RIDGE (str): Ridge border.
        INSET (str): Inset border.
        OUTSET (str): Outset border.
        HIDDEN (str): Hidden border.
    """
    NONE = 'none'
    DOTTED = 'dotted'
    DASHED = 'dashed'
    SOLID = 'solid'
    DOUBLE ='double'
    GROOVE = 'groove'
    RIDGE = 'ridge'
    INSET = 'inset'
    OUTSET = 'outset'
    HIDDEN = 'hidden'


# --- BorderRadius Refactored ---
class BorderRadius:
    """
    Represents the radius for the corners of a box. Compatible with reconciliation.
    """
    def __init__(self,
                 topLeft: float = 0.0,
                 topRight: float = 0.0,
                 bottomRight: float = 0.0,
                 bottomLeft: float = 0.0):
        """
        Initializes BorderRadius. Values are typically in pixels.

        Args:
            topLeft (float): Radius for the top-left corner.
            topRight (float): Radius for the top-right corner.
            bottomRight (float): Radius for the bottom-right corner.
            bottomLeft (float): Radius for the bottom-left corner.
        """
        self.topLeft = max(0.0, topLeft) # Ensure non-negative
        self.topRight = max(0.0, topRight)
        self.bottomRight = max(0.0, bottomRight)
        self.bottomLeft = max(0.0, bottomLeft)

    # --- Static Constructors ---
    @staticmethod
    def all(value: float) -> 'BorderRadius':
        """Creates a BorderRadius with the same radius for all corners."""
        radius = max(0.0, value)
        return BorderRadius(radius, radius, radius, radius)

    @staticmethod
    def circular(radius: float) -> 'BorderRadius':
         """Creates a BorderRadius with the same radius for all corners (alias for all)."""
         return BorderRadius.all(radius)

    @staticmethod
    def vertical(top: float = 0.0, bottom: float = 0.0) -> 'BorderRadius':
         """Creates a BorderRadius with the same radius for top-left/top-right and bottom-left/bottom-right."""
         top_r = max(0.0, top)
         bottom_r = max(0.0, bottom)
         return BorderRadius(topLeft=top_r, topRight=top_r, bottomRight=bottom_r, bottomLeft=bottom_r)

    @staticmethod
    def horizontal(left: float = 0.0, right: float = 0.0) -> 'BorderRadius':
         """Creates a BorderRadius with the same radius for top-left/bottom-left and top-right/bottom-right."""
         left_r = max(0.0, left)
         right_r = max(0.0, right)
         return BorderRadius(topLeft=left_r, topRight=right_r, bottomRight=right_r, bottomLeft=left_r)

    # --- Compatibility Methods ---

    def to_css_value(self) -> str:
        """
        Returns the CSS value string for the border-radius property
        (e.g., '10px 5px 10px 5px'). Uses shorthand if possible.
        """
        # Check for simplifications
        if self.topLeft == self.topRight == self.bottomRight == self.bottomLeft:
            return f"{self.topLeft}px" # All same
        if self.topLeft == self.bottomRight and self.topRight == self.bottomLeft:
            return f"{self.topLeft}px {self.topRight}px" # Top-left/bottom-right, Top-right/bottom-left
        if self.topRight == self.bottomLeft:
             return f"{self.topLeft}px {self.topRight}px {self.bottomRight}px" # Top-left, Top-right/bottom-left, Bottom-right
        # Full definition
        return f"{self.topLeft}px {self.topRight}px {self.bottomRight}px {self.bottomLeft}px"

    def to_css_dict(self) -> dict:
         """Returns the CSS property as a dictionary."""
         return {'border-radius': self.to_css_value()}

    def to_css(self) -> str:
        """Returns the full CSS property string (e.g., 'border-radius: 10px;')."""
        return f"border-radius: {self.to_css_value()};"

    # --- Hashability & Equality ---
    def __eq__(self, other):
        if not isinstance(other, BorderRadius):
            return NotImplemented
        return (self.topLeft == other.topLeft and
                self.topRight == other.topRight and
                self.bottomRight == other.bottomRight and
                self.bottomLeft == other.bottomLeft)

    def __hash__(self):
        return hash((self.topLeft, self.topRight, self.bottomRight, self.bottomLeft))

    # --- Representation ---
    def __repr__(self):
         if self.topLeft == self.topRight == self.bottomRight == self.bottomLeft:
              return f"BorderRadius.all({self.topLeft})"
         # Add checks for vertical/horizontal if desired
         return f"BorderRadius(topLeft={self.topLeft}, topRight={self.topRight}, bottomRight={self.bottomRight}, bottomLeft={self.bottomLeft})"

    # --- Reconciler Prop Representation ---
    def to_dict(self):
         return {'topLeft': self.topLeft, 'topRight': self.topRight,
                 'bottomRight': self.bottomRight, 'bottomLeft': self.bottomLeft}

    def to_tuple(self):
         """Returns a hashable tuple representation."""
         return (self.topLeft, self.topRight, self.bottomRight, self.bottomLeft)

class BorderSide:
    """
    Represents the style of a single side of a border.
    Used by BoxDecoration or for individual border properties (border-top, etc.).
    Compatible with reconciliation.
    """
    # Define a constant for no border
    NONE = None # Or potentially an instance: BorderSide(width=0, style=BorderStyle.NONE)

    def __init__(self,
                 width: float = 1.0, # Default width
                 style: str = BorderStyle.SOLID, # Default style
                 color: str = Colors.black # Default color
                 # Removed borderRadius - Radius applies to the box (BorderRadius), not a single side's style
                 # borderRadius=None
                 ):
        """
        Initializes the BorderSide.

        Args:
            width (float): The width of the border line in pixels. Defaults to 1.0.
                           Use 0 for no border width.
            style (str): The border style (e.g., BorderStyle.SOLID, BorderStyle.DASHED).
                         Defaults to BorderStyle.SOLID. Use BorderStyle.NONE for no visible border.
            color (str): The color of the border line (CSS color string). Defaults to Colors.black.
        """
        self.width = max(0.0, width) # Ensure non-negative
        # Add validation for style if desired
        self.style = style if style else BorderStyle.NONE # Default to NONE if None/empty provided
        self.color = color if color else Colors.black # Default color if None/empty

    # --- Compatibility Methods ---

    def to_css_shorthand_value(self) -> str:
        """
        Returns the CSS shorthand value string for the 'border' property
        (e.g., '1px solid black'). Returns 'none' if style is NONE or width is 0.
        """
        if self.style == BorderStyle.NONE or self.width <= 0:
            return 'none'
        # Format: width style color
        return f"{self.width}px {self.style} {self.color}"

    def to_css_dict(self) -> Dict[str, str]:
        """
        Returns border properties as a dictionary of individual CSS properties.
        Useful if applying to specific sides (e.g., border-top-width).
        """
        styles = {}
        if self.style == BorderStyle.NONE or self.width <= 0:
             # Set style to none, implicitly hiding width/color
             styles['border-style'] = BorderStyle.NONE
             styles['border-width'] = '0px' # Explicitly set width to 0
        else:
            styles['border-width'] = f"{self.width}px"
            styles['border-style'] = self.style
            styles['border-color'] = self.color
        return styles

    def to_css(self) -> str:
        """
        DEPRECATED? Returns individual CSS properties as a string snippet.
        Using the shorthand value or dictionary is generally better.
        """
        style_dict = self.to_css_dict()
        return " ".join(f"{prop}: {value};" for prop, value in style_dict.items())

    # --- Hashability & Equality ---
    def __eq__(self, other):
        if not isinstance(other, BorderSide):
            return NotImplemented
        # Treat width=0 or style=NONE as equivalent to no border for comparison? Optional.
        # Simple comparison for now:
        return (self.width == other.width and
                self.style == other.style and
                self.color == other.color)

    def __hash__(self):
        # Hash based on the defining attributes
        return hash((self.width, self.style, self.color))

    # --- Representation ---
    def __repr__(self):
        # Show defaults only if non-standard
        props = []
        if self.width != 1.0: props.append(f"width={self.width}")
        if self.style != BorderStyle.SOLID: props.append(f"style='{self.style}'")
        if self.color != Colors.black: props.append(f"color='{self.color}'")
        if not props: return "BorderSide()" # All defaults
        return f"BorderSide({', '.join(props)})"

    # --- Reconciler Prop Representation ---
    def to_dict(self):
         """Returns a simple dictionary representation."""
         return {'width': self.width, 'style': self.style, 'color': self.color}

    def to_tuple(self):
         """Returns a hashable tuple representation."""
         return (self.width, self.style, self.color)

    # Removed to_int() - unclear purpose, width is directly accessible.
    # Removed borderRadius - Belongs on BoxDecoration/BorderRadius.
    # Removed border_to_css() - Replaced by to_css_shorthand_value().

# framework/styles.py

from typing import Optional, Union, Tuple, Dict, Any

# Assuming other style classes are defined/imported and compatible:
# from .styles import Colors, EdgeInsets, BorderSide, BorderRadius, TextStyle, Alignment, BoxShadow, Offset

class ButtonStyle:
    """
    Defines the visual properties of buttons (TextButton, ElevatedButton, etc.).
    Compatible with reconciliation. Aggregates other style objects.

    Args:
            backgroundColor: Background color.
            foregroundColor: Text and icon color.
            disabledBackgroundColor: Background when disabled.
            disabledForegroundColor: Text/icon color when disabled.
            shadowColor: Color used for the elevation shadow.
            elevation: Elevation level (used for box-shadow).
            padding: Internal padding.
            minimumSize: Minimum width/height tuple (pixels).
            maximumSize: Maximum width/height tuple (pixels).
            side: Border definition (BorderSide object).
            shape: Corner radius (number for all corners or BorderRadius object).
            textStyle: TextStyle object for button label.
            alignment: Alignment object if button uses flex/grid for content.
    """
    def __init__(self,
                 # --- Colors ---
                 backgroundColor: Optional[str] = None, # Button background
                 foregroundColor: Optional[str] = None, # Text/Icon color
                 disabledBackgroundColor: Optional[str] = None, # Background when disabled
                 disabledForegroundColor: Optional[str] = None, # Text/Icon when disabled
                 shadowColor: Optional[str] = None, # Color of elevation shadow
                 hoverColor: Optional[str] = None,
                 activeColor: Optional[str] = None,
                 # overlayColor: Optional[str] = None, # TODO: Handle hover/focus/pressed overlay (CSS :hover/:active or JS)
                 # --- Shape & Border ---
                 elevation: Optional[float] = None, # Shadow depth (used to generate BoxShadow)
                 padding: Optional[EdgeInsets] = None, # Padding inside the button
                 margin: Optional[EdgeInsets] = None, # margin outside the button
                 minimumSize: Optional[Tuple[Optional[float], Optional[float]]] = None, # (minWidth, minHeight) in px
                 maximumSize: Optional[Tuple[Optional[float], Optional[float]]] = None, # (maxWidth, maxHeight) in px
                 side: Optional[BorderSide] = None, # Border properties
                 shape: Optional[Union[float, BorderRadius]] = None, # Corner radius (number or BorderRadius object)
                 # --- Content Style ---
                 textStyle: Optional[TextStyle] = None, # Style for text content
                 alignment: Optional[Alignment] = None, # How content (icon+label) is aligned if button is flex container
                 # iconColor: Optional[str] = None, # Specific icon color override? (or use foregroundColor)
                 # iconSize: Optional[float] = None, # Icon size? (Usually handled by Icon widget itself)
                 ):
        """
        Initializes the ButtonStyle.

        Args:
            backgroundColor: Background color.
            foregroundColor: Text and icon color.
            disabledBackgroundColor: Background when disabled.
            disabledForegroundColor: Text/icon color when disabled.
            shadowColor: Color used for the elevation shadow.
            elevation: Elevation level (used for box-shadow).
            padding: Internal padding.
            minimumSize: Minimum width/height tuple (pixels).
            maximumSize: Maximum width/height tuple (pixels).
            side: Border definition (BorderSide object).
            shape: Corner radius (number for all corners or BorderRadius object).
            textStyle: TextStyle object for button label.
            alignment: Alignment object if button uses flex/grid for content.
        """
        self.backgroundColor = backgroundColor
        self.foregroundColor = foregroundColor
        self.disabledBackgroundColor = disabledBackgroundColor
        self.disabledForegroundColor = disabledForegroundColor
        self.shadowColor = shadowColor
        self.hoverColor = hoverColor
        self.activeColor = activeColor
        self.elevation = elevation
        self.padding = padding
        self.margin = margin
        self.minimumSize = minimumSize
        self.maximumSize = maximumSize
        self.side = side
        self.shape = shape
        self.textStyle = textStyle
        self.alignment = alignment
        # Removed icon - Icon should be passed as child widget

    # --- Compatibility Methods ---

    def to_css_dict(self) -> Dict[str, str]:
        """Converts button style properties to a dictionary of CSS styles."""
        styles = {}
        if self.backgroundColor: styles['background-color'] = self.backgroundColor
        if self.foregroundColor: styles['color'] = self.foregroundColor # Applies to text/icon color usually
        if self.hoverColor: styles['hover-color'] = self.hoverColor
        if self.activeColor: styles['active-color'] = self.activeColor
        # Disabled colors handled by specific .disabled class rules, not here directly

        # --- Shadow ---
        # Generate box-shadow based on elevation
        if self.elevation is not None and self.elevation > 0:
            # Basic elevation mapping (improve as needed)
            offset_y = min(max(1, self.elevation * 0.8), 6)
            blur = max(4, self.elevation * 1.5)
            spread = max(0, self.elevation * 0.2 - 1)
            color = self.shadowColor or Colors.rgba(0,0,0,0.2)
            styles['box-shadow'] = f"0px {offset_y}px {blur}px {spread}px {color}"

        if self.padding and isinstance(self.padding, EdgeInsets): styles['padding'] = self.padding.to_css() # Use EdgeInsets method
        if self.margin and isinstance(self.margin, EdgeInsets): styles['margin'] = self.margin.to_css() # Use EdgeInsets method
        if self.minimumSize:
            min_w, min_h = self.minimumSize
            if min_w is not None: styles['min-width'] = f"{min_w}px"
            if min_h is not None: styles['min-height'] = f"{min_h}px"
        if self.maximumSize:
            max_w, max_h = self.maximumSize
            if max_w is not None: styles['max-width'] = f"{max_w}px"
            if max_h is not None: styles['max-height'] = f"{max_h}px"

        # --- Border & Shape ---
        if self.side and isinstance(self.side, BorderSide):
            # Use shorthand if available and not NONE
            shorthand = self.side.to_css_shorthand_value()
            if shorthand != 'none':
                 styles['border'] = shorthand
            else:
                 styles['border'] = 'none' # Explicitly set to none
        else:
            # Default: buttons often have no border unless specified
            styles['border'] = 'none'

        if self.shape:
            print("Shape value in btnStyle: ", self.shape.to_css_value())
            if isinstance(self.shape, BorderRadius):
                styles['border-radius'] = self.shape.to_css_value()
            elif isinstance(self.shape, (int, float)):
                 styles['border-radius'] = f"{max(0.0, self.shape)}px"

        # --- Text Style ---
        # Note: Text styles apply to text *within* the button.
        # Best applied via CSS descendant selector (e.g., .button-class > .text-class)
        # or if the button directly renders text. Including here might override wrongly.
        # if self.textStyle and isinstance(self.textStyle, TextStyle):
        #     styles.update(self.textStyle.to_css_dict()) # Merge text styles

        # --- Alignment ---
        # Applies if the button itself uses flex/grid to lay out an icon and label
        if self.alignment and isinstance(self.alignment, Alignment):
             # Usually buttons use flex to align icon+label
             styles['display'] = 'inline-flex' # Use inline-flex for button
             styles['justify-content'] = self.alignment.justify_content
             styles['align-items'] = self.alignment.align_items
             styles['gap'] = '8px' # Default gap between icon/label?

        return styles

    def to_css(self) -> str:
        """Converts button style properties to a CSS string snippet."""
        style_dict = self.to_css_dict()
        return " ".join(f"{prop}: {value};" for prop, value in style_dict.items())

    # --- Hashability & Equality ---
    def __eq__(self, other):
        if not isinstance(other, ButtonStyle):
            return NotImplemented
        # Compare all relevant attributes
        # Ensure nested objects are comparable (__eq__ implemented)
        return (self.backgroundColor == other.backgroundColor and
                self.foregroundColor == other.foregroundColor and
                self.disabledBackgroundColor == other.disabledBackgroundColor and
                self.disabledForegroundColor == other.disabledForegroundColor and
                self.shadowColor == other.shadowColor and
                self.hoverColor == other.hoverColor and
                self.activeColor == other.activeColor and
                self.elevation == other.elevation and
                self.padding == other.padding and
                self.margin == other.margin and
                self.minimumSize == other.minimumSize and
                self.maximumSize == other.maximumSize and
                self.side == other.side and
                self.shape == other.shape and
                self.textStyle == other.textStyle and
                self.alignment == other.alignment)

    def __hash__(self):
        # Hash a tuple of hashable representations of attributes
        # Ensure nested objects (EdgeInsets, BorderSide, BorderRadius, TextStyle, Alignment) are hashable
        return hash((
            self.backgroundColor, self.foregroundColor,
            self.disabledBackgroundColor, self.disabledForegroundColor,
            self.shadowColor, self.hoverColor, self.activeColor, self.elevation, self.padding, self.margin,
            self.minimumSize, self.maximumSize, # Tuples are hashable
            self.side, self.shape, self.textStyle, self.alignment
        ))

    # --- Representation ---
    def __repr__(self):
        props = []
        # Add checks to show only non-default/non-None values
        attrs = ['backgroundColor', 'foregroundColor', 'disabledBackgroundColor', 'disabledForegroundColor',
                 'shadowColor', 'hoverColor', 'activeColor', 'elevation', 'padding', 'margin','minimumSize', 'maximumSize',
                 'side', 'shape', 'textStyle', 'alignment']
        for attr in attrs:
            value = getattr(self, attr)
            if value is not None: # Simple check for None
                # Add more sophisticated default checks if needed
                 props.append(f"{attr}={value!r}")
        return f"ButtonStyle({', '.join(props)})"

    # --- Reconciler Prop Representation ---
    def to_dict(self):
        """Returns a simple dictionary representation."""
        # Convert nested objects to dicts too
        return {attr: getattr(self, attr).to_dict() if hasattr(getattr(self, attr), 'to_dict') else getattr(self, attr)
                for attr in [
                    'backgroundColor', 'foregroundColor', 'disabledBackgroundColor', 'disabledForegroundColor',
                    'shadowColor', 'hoverColor', 'activeColor', 'elevation', 'padding', 'margin', 'minimumSize', 'maximumSize',
                    'side', 'shape', 'textStyle', 'alignment'
                ] if getattr(self, attr) is not None}

    def to_tuple(self):
         """Returns a hashable tuple representation."""
         # Convert nested objects to tuples too
         return tuple(getattr(self, attr).to_tuple() if hasattr(getattr(self, attr), 'to_tuple') else getattr(self, attr)
                      for attr in [
                          'backgroundColor', 'foregroundColor', 'disabledBackgroundColor', 'disabledForegroundColor',
                          'shadowColor', 'hoverColor', 'activeColor', 'elevation', 'padding', 'margin', 'minimumSize', 'maximumSize',
                          'side', 'shape', 'textStyle', 'alignment'
                      ])

class ScrollPhysics:
    """
    Specifies the scrolling behavior of a widget.

    Attributes:
        BOUNCING: Allows scrolling beyond content bounds with a spring-like effect.
        CLAMPING: Prevents scrolling beyond content bounds.
        ALWAYS_SCROLLABLE: Enables scrolling even if content does not overflow.
        NEVER_SCROLLABLE: Disables scrolling regardless of content size.
    """
    BOUNCING = 'bouncing'
    CLAMPING = 'clamping'
    ALWAYS_SCROLLABLE = 'alwaysScrollable'
    NEVER_SCROLLABLE = 'neverScrollable'
    
class Overflow:
    """
    Defines how content overflow is handled in a widget.

    Attributes:
        VISIBLE: Content is visible beyond the bounds of the widget.
        HIDDEN: Content is clipped to the bounds of the widget.
        SCROLL: Adds scrolling to manage content overflow.
        AUTO: Automatically decides based on the content size.
    """
    VISIBLE = 'visible'
    HIDDEN = 'hidden'
    SCROLL = 'scroll'
    AUTO = 'auto'    

class StackFit:
    """
    Determines how children are sized within a Stack widget.

    Attributes:
        loose: Children take up as little space as possible.
        expand: Children expand to fill the Stack's available space.
        passthrough: Children retain their original size.
    """
    loose = 'loose'
    expand = 'expand'
    passthrough = 'passthrough'

class TextDirection:
    """
    Specifies the direction in which text flows.

    Attributes:
        LTR: Text flows from left to right.
        RTL: Text flows from right to left.
    """
    LTR = 'ltr'
    RTL = 'rtl'

class TextBaseline():
    """
    Specifies the alignment of text baselines.

    Attributes:
        alphabetic: Aligns the baseline to the bottom of alphabetic characters.
        ideographic: Aligns the baseline to the middle of ideographic characters.
    """
    alphabetic = 'text-bottom'
    ideographic = 'middle'

class VerticalDirection:
    """
    Determines the vertical arrangement of children.

    Attributes:
        DOWN: Children are arranged from top to bottom.
        UP: Children are arranged from bottom to top.
    """
    DOWN = 'down'
    UP = 'up'


class BoxFit:
    """
    Defines how an image or box is fitted into its allocated space.

    Attributes:
        CONTAIN: Scales to fit within the bounds while maintaining aspect ratio.
        COVER: Scales to fill the bounds while maintaining aspect ratio, possibly cropping.
        FILL: Stretches to fill the bounds, disregarding aspect ratio.
        NONE: Does not scale; the content's original size is used.
    """
    CONTAIN = 'contain'
    COVER = 'cover'
    FILL = 'fill'
    NONE = 'none'
    
# --- BoxDecoration Refactored ---
class BoxDecoration:
    """
    Describes how to paint a box (background, border, shadow, shape).
    Compatible with reconciliation.
    """
    def __init__(self,
                 color: Optional[str] = None,
                 # image: Optional[DecorationImage] = None, # TODO: If image backgrounds needed
                 border: Optional[Union[str, BorderSide]] = None, # Allow BorderSide object or CSS string? Prefer object.
                 borderRadius: Optional[Union[int, float, BorderRadius]] = None, # Allow number or BorderRadius obj
                 boxShadow: Optional[Union[BoxShadow, List[BoxShadow]]] = None, # Allow single or list
                 # gradient: Optional[Gradient] = None, # TODO: If gradients needed
                 # shape: BoxShape = BoxShape.rectangle, # TODO: If specific shapes like circle needed
                 # For simplicity, sticking to properties easily mappable to CSS:
                 transform: Optional[str] = None, # Raw CSS transform string
                 # Padding is usually handled by Padding widget, not BoxDecoration
                 # padding: Optional[EdgeInsets] = None,
                 visible: bool = True,
                 ):
        """
        Initializes the BoxDecoration.

        Args:
            color: Background color.
            border: Border definition (BorderSide object preferred).
            borderRadius: Corner radius (number for all corners or BorderRadius object).
            boxShadow: BoxShadow object or list of BoxShadow objects.
            transform: CSS transform string (e.g., 'rotate(45deg)').
        """
        self.color = color
        self.border = border
        self.borderRadius = borderRadius
        self.visible = visible
        # Ensure boxShadow is always a list for consistent handling
        if isinstance(boxShadow, BoxShadow):
            self.boxShadow = [boxShadow]
        elif isinstance(boxShadow, list):
            self.boxShadow = boxShadow
        else:
            self.boxShadow = None
        self.transform = transform
        # self.padding = padding # Removed padding, use Padding widget

    # --- Compatibility Methods ---

    def to_css_dict(self) -> Dict[str, str]:
        """Converts decoration properties to a dictionary of CSS styles."""
        styles = {}
        if self.color:
            styles['background'] = self.color
        if self.border:
            if isinstance(self.border, BorderSide):
                 # Assumes BorderSide has a way to generate full border property
                 if hasattr(self.border, 'border_to_css_shorthand'):
                      styles['border'] = self.border.border_to_css_shorthand() # Example method name
                 else: # Fallback using individual properties if needed
                      border_dict = self.border.to_css_dict() # Assume BorderSide returns dict
                      styles.update(border_dict)
            elif isinstance(self.border, str): # Allow raw CSS string (less safe)
                 styles['border'] = self.border
        if self.borderRadius:
            if isinstance(self.borderRadius, BorderRadius):
                # Assumes BorderRadius has a way to generate border-radius property
                 styles['border-radius'] = self.borderRadius.to_css_value() # Example method name
            elif isinstance(self.borderRadius, (int, float)):
                 styles['border-radius'] = f"{self.borderRadius}px"
            # Else handle string? For now, require object or number
        if self.boxShadow:
            # Combine multiple shadows with comma
            shadow_strings = [shadow.to_css() for shadow in self.boxShadow if isinstance(shadow, BoxShadow)]
            if shadow_strings:
                 styles['box-shadow'] = ", ".join(shadow_strings)
        if self.transform:
            styles['transform'] = self.transform
        # if self.padding and isinstance(self.padding, EdgeInsets): # Padding removed
        #     styles['padding'] = self.padding.to_css()
        return styles

    def to_css(self) -> str:
        """Converts decoration properties to a CSS string snippet."""
        style_dict = self.to_css_dict()
        return " ".join(f"{prop}: {value};" for prop, value in style_dict.items())

    # --- Hashability & Equality ---
    def __eq__(self, other):
        if not isinstance(other, BoxDecoration):
            return NotImplemented
        # Compare all relevant attributes
        # Note: Comparing lists requires order to be the same for equality
        return (self.color == other.color and
                self.border == other.border and
                self.borderRadius == other.borderRadius and
                self.boxShadow == other.boxShadow and # Relies on BoxShadow __eq__ and list order
                self.transform == other.transform)

    def __hash__(self):
        # Hash a tuple of hashable representations of attributes
        # Ensure nested objects (BorderSide, BorderRadius, BoxShadow) are hashable
        # Convert list of shadows to tuple for hashing
        shadow_tuple = tuple(self.boxShadow) if self.boxShadow else None
        return hash((
            self.color,
            self.border, # Relies on BorderSide/str hash
            self.borderRadius, # Relies on BorderRadius/number hash
            shadow_tuple, # Relies on BoxShadow hash
            self.transform
        ))

    # --- Representation ---
    def __repr__(self):
        props = []
        if self.color: props.append(f"color='{self.color}'")
        if self.border: props.append(f"border={self.border!r}")
        if self.borderRadius: props.append(f"borderRadius={self.borderRadius!r}")
        if self.boxShadow: props.append(f"boxShadow={self.boxShadow!r}")
        if self.transform: props.append(f"transform='{self.transform}'")
        return f"BoxDecoration({', '.join(props)})"

    # --- Reconciler Prop Representation ---
    def to_dict(self):
         # Convert nested objects to dicts too if needed for serialization
         border_repr = self.border.to_dict() if hasattr(self.border, 'to_dict') else self.border
         radius_repr = self.borderRadius.to_dict() if hasattr(self.borderRadius, 'to_dict') else self.borderRadius
         shadow_repr = [s.to_dict() for s in self.boxShadow if hasattr(s, 'to_dict')] if self.boxShadow else None

         return {'color': self.color, 'border': border_repr,
                 'borderRadius': radius_repr, 'boxShadow': shadow_repr,
                 'transform': self.transform}

    def to_tuple(self):
         """Returns a hashable tuple representation."""
         shadow_tuple = tuple(self.boxShadow) if self.boxShadow else None
         return (self.color, self.border, self.borderRadius, shadow_tuple, self.transform)

# --- BoxDecoration Refactored ---
class BoxDecoration:
    """
    Describes how to paint a box (background, border, shadow, shape).
    Compatible with reconciliation.
    """
    def __init__(self,
                 color: Optional[str] = None,
                 # image: Optional[DecorationImage] = None, # TODO: If image backgrounds needed
                 border: Optional[Union[str, BorderSide]] = None, # Allow BorderSide object or CSS string? Prefer object.
                 borderRadius: Optional[Union[int, float, BorderRadius]] = None, # Allow number or BorderRadius obj
                 boxShadow: Optional[Union[BoxShadow, List[BoxShadow]]] = None, # Allow single or list
                 # gradient: Optional[Gradient] = None, # TODO: If gradients needed
                 # shape: BoxShape = BoxShape.rectangle, # TODO: If specific shapes like circle needed
                 # For simplicity, sticking to properties easily mappable to CSS:
                 transform: Optional[str] = None, # Raw CSS transform string
                 # Padding is usually handled by Padding widget, not BoxDecoration
                 # padding: Optional[EdgeInsets] = None,
                 ):
        """
        Initializes the BoxDecoration.

        Args:
            color: Background color.
            border: Border definition (BorderSide object preferred).
            borderRadius: Corner radius (number for all corners or BorderRadius object).
            boxShadow: BoxShadow object or list of BoxShadow objects.
            transform: CSS transform string (e.g., 'rotate(45deg)').
        """
        self.color = color
        self.border = border
        self.borderRadius = borderRadius
        # Ensure boxShadow is always a list for consistent handling
        if isinstance(boxShadow, BoxShadow):
            self.boxShadow = [boxShadow]
        elif isinstance(boxShadow, list):
            self.boxShadow = boxShadow
        else:
            self.boxShadow = None
        self.transform = transform
        # self.padding = padding # Removed padding, use Padding widget

    # --- Compatibility Methods ---

    def to_css_dict(self) -> Dict[str, str]:
        """Converts decoration properties to a dictionary of CSS styles."""
        styles = {}
        if self.color:
            styles['background'] = self.color
        if self.border:
            if isinstance(self.border, BorderSide):
                 # Assumes BorderSide has a way to generate full border property
                 if hasattr(self.border, 'border_to_css_shorthand'):
                      styles['border'] = self.border.border_to_css_shorthand() # Example method name
                 else: # Fallback using individual properties if needed
                      border_dict = self.border.to_css_dict() # Assume BorderSide returns dict
                      styles.update(border_dict)
            elif isinstance(self.border, str): # Allow raw CSS string (less safe)
                 styles['border'] = self.border
        if self.borderRadius:
            if isinstance(self.borderRadius, BorderRadius):
                # Assumes BorderRadius has a way to generate border-radius property
                 styles['border-radius'] = self.borderRadius.to_css_value() # Example method name
            elif isinstance(self.borderRadius, (int, float)):
                 styles['border-radius'] = f"{self.borderRadius}px"
            # Else handle string? For now, require object or number
        if self.boxShadow:
            # Combine multiple shadows with comma
            shadow_strings = [shadow.to_css() for shadow in self.boxShadow if isinstance(shadow, BoxShadow)]
            if shadow_strings:
                 styles['box-shadow'] = ", ".join(shadow_strings)
        if self.transform:
            styles['transform'] = self.transform
        # if self.padding and isinstance(self.padding, EdgeInsets): # Padding removed
        #     styles['padding'] = self.padding.to_css()
        return styles

    def to_css(self) -> str:
        """Converts decoration properties to a CSS string snippet."""
        style_dict = self.to_css_dict()
        return " ".join(f"{prop}: {value};" for prop, value in style_dict.items())

    # --- Hashability & Equality ---
    def __eq__(self, other):
        if not isinstance(other, BoxDecoration):
            return NotImplemented
        # Compare all relevant attributes
        # Note: Comparing lists requires order to be the same for equality
        return (self.color == other.color and
                self.border == other.border and
                self.borderRadius == other.borderRadius and
                self.boxShadow == other.boxShadow and # Relies on BoxShadow __eq__ and list order
                self.transform == other.transform)

    def __hash__(self):
        # Hash a tuple of hashable representations of attributes
        # Ensure nested objects (BorderSide, BorderRadius, BoxShadow) are hashable
        # Convert list of shadows to tuple for hashing
        shadow_tuple = tuple(self.boxShadow) if self.boxShadow else None
        return hash((
            self.color,
            self.border, # Relies on BorderSide/str hash
            self.borderRadius, # Relies on BorderRadius/number hash
            shadow_tuple, # Relies on BoxShadow hash
            self.transform
        ))

    # --- Representation ---
    def __repr__(self):
        props = []
        if self.color: props.append(f"color='{self.color}'")
        if self.border: props.append(f"border={self.border!r}")
        if self.borderRadius: props.append(f"borderRadius={self.borderRadius!r}")
        if self.boxShadow: props.append(f"boxShadow={self.boxShadow!r}")
        if self.transform: props.append(f"transform='{self.transform}'")
        return f"BoxDecoration({', '.join(props)})"

    # --- Reconciler Prop Representation ---
    def to_dict(self):
         # Convert nested objects to dicts too if needed for serialization
         border_repr = self.border.to_dict() if hasattr(self.border, 'to_dict') else self.border
         radius_repr = self.borderRadius.to_dict() if hasattr(self.borderRadius, 'to_dict') else self.borderRadius
         shadow_repr = [s.to_dict() for s in self.boxShadow if hasattr(s, 'to_dict')] if self.boxShadow else None

         return {'color': self.color, 'border': border_repr,
                 'borderRadius': radius_repr, 'boxShadow': shadow_repr,
                 'transform': self.transform}

    def to_tuple(self):
         """Returns a hashable tuple representation."""
         shadow_tuple = tuple(self.boxShadow) if self.boxShadow else None
         return (self.color, self.border, self.borderRadius, shadow_tuple, self.transform)





# class InputDecoration:
#     """
#     Defines the visual decoration for a TextField.

#     This class encapsulates properties like labels, icons, hints, error text,
#     and border styles, allowing for consistent and reusable text field styling
#     that mimics Material Design's filled or outlined text fields.
#     """
#     def __init__(self,
#                  label: Optional[str] = None,
#                  hintText: Optional[str] = None,
#                  errorText: Optional[str] = None,
#                  # You can add prefixIcon and suffixIcon as Widget later
                 
#                  # --- Colors ---
#                  fillColor: Optional[str] = None, # Background of the input
#                  focusColor: Optional[str] = None, # Color of the border/label when focused
                 
#                  # --- Borders ---
#                  # For simplicity, we can use a single border style and change its color based on state
#                  border: Optional[BorderSide] = None,
#                  focusedBorder: Optional[BorderSide] = None,
#                  errorBorder: Optional[BorderSide] = None,
                 
#                  # --- Flags ---
#                  filled: bool = True, # Determines if fillColor is used
#                  ):
#         self.label = label
#         self.hintText = hintText
#         self.errorText = errorText
        
#         self.fillColor = fillColor
#         self.focusColor = focusColor
        
#         self.border = border
#         self.focusedBorder = focusedBorder
#         self.errorBorder = errorBorder
        
#         self.filled = filled

#     def to_tuple(self) -> Tuple:
#         """
#         Creates a hashable tuple representation for use in style keys.
#         This is crucial for the shared styling system.
#         """
#         # make_hashable will handle converting BorderSide to a tuple
#         return (
#             self.label, self.hintText, self.errorText, self.fillColor,
#             self.focusColor, make_hashable(self.border),
#             make_hashable(self.focusedBorder), make_hashable(self.errorBorder),
#             self.filled
#         )

#     def __eq__(self, other):
#         if not isinstance(other, InputDecoration):
#             return NotImplemented
#         return self.to_tuple() == other.to_tuple()

#     def __hash__(self):
#         return hash(self.to_tuple())



# in pythra/styles.py

# ... (other imports) ...
# Make sure BorderSide is defined before this class or imported
# from .styles import BorderSide, Colors

class InputDecoration:
    """
    Defines the visual decoration for a TextField.

    This class encapsulates properties like labels, icons, hints, error text,
    and border styles, allowing for consistent and reusable text field styling
    that mimics Material Design's filled or outlined text fields.
    """
    def __init__(self,
                 label: Optional[str] = None,
                 hintText: Optional[str] = None,
                 errorText: Optional[str] = None,
                 
                 # --- Colors ---
                 fillColor: Optional[str] = None,
                 focusColor: Optional[str] = None,
                 labelColor: Optional[str] = None, # NEW: Color for the label
                 errorColor: Optional[str] = None, # NEW: Color for border/label/text in error state
                 
                 # --- Borders ---
                 borderRadius: Optional[BorderRadius] = None,
                 border: Optional[BorderSide] = None,
                 focusedBorder: Optional[BorderSide] = None,
                 errorBorder: Optional[BorderSide] = None,
                 
                 # --- Flags ---
                 filled: bool = True
                 ):
        
        # --- Store user-provided values ---
        self.label = label
        self.hintText = hintText
        self.errorText = errorText
        
        self.filled = filled

        # --- Set smart, M3-style defaults if values are not provided ---
        self.fillColor = fillColor if fillColor is not None else (fillColor if self.filled else 'transparent')
        # print("FILL FROM STYLE.PY: ", self.fillColor, self.label)
        self.focusColor = focusColor if focusColor is not None else Colors.primary
        self.labelColor = labelColor if labelColor is not None else Colors.onSurfaceVariant
        self.errorColor = errorColor if errorColor is not None else Colors.error

        self.borderRadius = borderRadius if borderRadius is not None else BorderRadius.all(4)

        self.border = border if border is not None else BorderSide(
            width=1.0, 
            style=BorderStyle.SOLID, 
            color=Colors.outline
        )
        self.focusedBorder = focusedBorder if focusedBorder is not None else BorderSide(
            width=2.0, 
            style=BorderStyle.SOLID, 
            color=self.focusColor # Use the focus color for the focused border
        )
        self.errorBorder = errorBorder if errorBorder is not None else BorderSide(
            width=2.0, 
            style=BorderStyle.SOLID, 
            color=self.errorColor # Use the error color for the error border
        )

    def to_tuple(self) -> Tuple:
        """Creates a hashable tuple representation for use in style keys."""
        # Note: We now hash the final, resolved values, not the initial ones.
        return (
            self.label, self.hintText, self.errorText, self.fillColor,
            self.focusColor, self.labelColor, self.errorColor,
            self.borderRadius.to_css(),
            make_hashable(self.border),
            make_hashable(self.focusedBorder),
            make_hashable(self.errorBorder),
            self.filled
        )

    def __eq__(self, other):
        if not isinstance(other, InputDecoration):
            return NotImplemented
        return self.to_tuple() == other.to_tuple()

    def __hash__(self):
        return hash(self.to_tuple())


# In pythra/styles.py



# ... (keep all your other style classes)

@dataclass
class ScrollbarTheme:
    """
    Holds the styling information for a custom scrollbar.
    Maps directly to CSS scrollbar pseudo-element properties.
    """
    width: int = 12  # The width of the vertical scrollbar in pixels.
    height: int = 12 # The height of the horizontal scrollbar in pixels.
    
    thumbColor: Optional[str] = "#888" # Color of the draggable thumb.
    thumbHoverColor: Optional[str] = "#555" # Color of the thumb on hover.
    
    trackColor: Optional[str] = "#f1f1f1" # Color of the track (the groove).
    
    # The radius of the corners on the thumb.
    radius: int = 6 
    trackRadius: int = 8 
    
    # Creates a "padding" effect around the thumb by using a transparent border.
    thumbPadding: int = 3 
    trackMargin: Optional[EdgeInsets] = 0 

    def to_tuple(self) -> Tuple:
        """Returns a hashable tuple representation for use as a style key."""
        return (
            self.width, self.height, self.thumbColor, self.thumbHoverColor,
            self.trackColor, self.radius, self.trackRadius, self.thumbPadding, self.trackMargin
        )

# In pythra/styles.py

# ... (keep all your other style classes like EdgeInsets, Colors, etc.)

@dataclass
class SliderTheme:
    """
    Defines the visual properties of a Slider widget.

    This data class holds customizable properties for colors and dimensions,
    allowing for consistent theming of sliders across an application.
    """
    # Colors
    activeTrackColor: Optional[str] = None
    inactiveTrackColor: Optional[str] = None
    thumbColor: Optional[str] = None
    overlayColor: Optional[str] = None # Color of the halo effect when dragging

    # Dimensions
    trackHeight: float = 4.0
    thumbSize: float = 14.0
    thumbBorderWidth: float = 2.0
    thumbBorderColor: Optional[str] = None
    overlaySize: float = 8.0 # The 'spread' of the overlay halo in pixels


    def to_tuple(self) -> Tuple:
        """Creates a hashable tuple for use in style keys."""
        print("thumbBorderColor: ", self.thumbBorderColor)
        return (
            self.activeTrackColor, self.inactiveTrackColor, self.thumbColor,
            self.overlayColor, self.trackHeight, self.thumbSize,
            self.thumbBorderWidth, self.thumbBorderColor, self.overlaySize
        )

# In pythra/styles.py

# ... (keep all your other style classes like EdgeInsets, SliderTheme, etc.)

@dataclass
class CheckboxTheme:
    """
    Defines the visual properties for a Checkbox widget.
    """
    # Colors
    activeColor: Optional[str] = None      # The background color of the box when checked.
    checkColor: Optional[str] = None       # The color of the checkmark icon.
    inactiveColor: Optional[str] = None    # The color of the border when unchecked.
    splashColor: Optional[str] = None      # The color of the ripple/splash effect on press.

    # Dimensions
    size: float = 18.0                     # The width and height of the checkbox square.
    strokeWidth: float = 2.0               # The thickness of the border and checkmark.
    splashRadius: float = 20.0             # The radius of the splash effect.

    def to_tuple(self) -> Tuple:
        """Creates a hashable tuple for use in style keys."""
        return (
            self.activeColor, self.checkColor, self.inactiveColor,
            self.splashColor, self.size, self.strokeWidth, self.splashRadius
        )


# In pythra/styles.py

# ... (keep all your other style classes)

@dataclass
class SwitchTheme:
    """
    Defines the visual properties for a Switch widget.
    """
    # Color of the sliding circle (thumb).
    thumbColor: Optional[str] = None
    # Color of the track when the switch is ON.
    activeTrackColor: Optional[str] = None
    # Color of the track when the switch is OFF.
    inactiveTrackColor: Optional[str] = None
    # Optional color for the thumb when the switch is ON.
    activeThumbColor: Optional[str] = None

    def to_tuple(self) -> Tuple:
        """Creates a hashable tuple for use in style keys."""
        return (
            self.thumbColor,
            self.activeTrackColor,
            self.inactiveTrackColor,
            self.activeThumbColor,
        )


# In pythra/styles.py

# ... (keep all your other style classes)

@dataclass
class RadioTheme:
    """
    Defines the visual properties for a Radio button widget.
    """
    # The color of the radio button's fill and border when selected.
    fillColor: Optional[str] = None
    # The color of the splash/ripple effect on press.
    splashColor: Optional[str] = None

    def to_tuple(self) -> Tuple:
        """Creates a hashable tuple for use in style keys."""
        return (self.fillColor, self.splashColor)



class DropdownTheme:
    """Encapsulates the styling properties for the Dropdown widget."""

    def __init__(
        self,
        backgroundColor=Colors.hex("#FFFFFF"),
        borderColor=Colors.hex("#AAAAAA"),
        hoverColor=Colors.rgba(0, 0, 0, 0.1),
        dropdownHoverColor=Colors.rgba(0, 0, 0, 0.08),
        itemHoverColor=Colors.rgba(103, 80, 164, 0.1),
        width = "100%",
        height = "auto",
        dropDownHeight = "auto",
        borderWidth=1.0,
        borderRadius=8.0,
        textColor=Colors.hex("#000000"),
        fontSize=14.0,
        padding=EdgeInsets.symmetric(vertical=8, horizontal=12),
        dropdownColor=Colors.hex("#FFFFFF"),
        dropdownTextColor=Colors.hex("#000000"),
        selectedItemColor=Colors.hex("#E0E0E0"),
        selectedItemShape= BorderRadius.all(4),
        dropdownMargin=EdgeInsets.only(top=45),
        itemPadding = EdgeInsets.symmetric(horizontal=12, vertical=8),
    ):
        self.backgroundColor = backgroundColor
        self.borderColor = borderColor
        self.hoverColor = hoverColor
        self.dropdownHoverColor = dropdownHoverColor
        self.itemHoverColor = itemHoverColor
        self.width = width
        self.height = height
        self.dropDownHeight = dropDownHeight
        self.borderWidth = borderWidth
        self.borderRadius = borderRadius
        self.textColor = textColor
        self.fontSize = fontSize
        self.padding = padding
        self.dropdownColor = dropdownColor
        self.dropdownTextColor = dropdownTextColor
        self.selectedItemColor = selectedItemColor
        self.selectedItemShape = selectedItemShape
        self.dropdownMargin = dropdownMargin
        self.itemPadding = itemPadding



@dataclass
class GradientBorderTheme:
    """
    Defines the visual properties for a GradientBorderContainer.
    """
    # A list of CSS colors for the gradient.
    gradientColors: List[str] = field(default_factory=lambda: [
        '#ff4d4d', '#ffb86b', '#ffd166', '#7bed9f',
        '#6ad3ff', '#a78bfa', '#ff4d4d'
    ])
    
    # The CSS angle or direction for the linear gradient (e.g., '270deg', 'to right').
    gradientDirection: str = '270deg'
    
    # The speed of the animation (e.g., '5s', '10s').
    animationSpeed: str = '5s'
    
    # The animation timing function (e.g., 'linear', 'ease-in-out').
    animationTiming: str = 'linear'

    def to_tuple(self) -> Tuple:
        """Creates a hashable tuple for use in style keys."""
        return (
            tuple(self.gradientColors), # Convert list to tuple for hashing
            self.gradientDirection,
            self.animationSpeed,
            self.animationTiming
        )


# In pythra/styles.py

# Rename GradientBorderTheme to GradientTheme
@dataclass
class GradientTheme: # <-- RENAMED
    """
    Defines the visual properties for an animated gradient effect.
    """
    # A list of CSS colors for the gradient.
    gradientColors: List[str] = field(default_factory=lambda: [
        '#ff4d4d', '#ffb86b', '#ffd166', '#7bed9f',
        '#6ad3ff', '#a78bfa', '#ff4d4d'
    ])
    
    # The CSS angle or direction for the linear gradient.
    gradientDirection: str = '270deg'
    
    # The speed of the animation.
    animationSpeed: str = '5s'
    
    # The animation timing function.
    animationTiming: str = 'linear'

    # --- NEW: Rotation Animation ---
    # Set to a time (e.g., '10s') to enable rotation. Set to None to disable.
    rotationSpeed: Optional[str] = None 

    def to_tuple(self) -> Tuple:
        """Creates a hashable tuple for use in style keys."""
        return (
            tuple(self.gradientColors),
            self.gradientDirection,
            self.animationSpeed,
            self.animationTiming,
            self.rotationSpeed # <-- ADD TO TUPLE
        )