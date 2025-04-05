# pythra/widgets.py
import uuid
import yaml
import os
from .api import Api
from .base import *
from .styles import *
from .config import Config
import weakref
from typing import Any, Dict, List, Optional, Set, Tuple, Union

config = Config()
assets_dir = config.get('assets_dir', 'assets')
port = config.get('assets_server_port')
Colors = Colors()



# --- Container Widget Refactored ---
class Container(Widget):
    """
    A layout widget that serves as a styled box to contain a single child widget.

    The `Container` widget allows styling and positioning of its child through various
    layout and style properties like padding, margin, width, height, background color,
    decoration, alignment, and more. It automatically generates and reuses shared CSS
    class names for identical style combinations to avoid redundancy and optimize rendering.

    Attributes:
        child (Optional[Widget]): A single widget to be contained within the container.
        padding: Internal spacing between the container edge and its child.
        color: Background color of the container.
        decoration: A BoxDecoration-like object providing additional styling such as border, border-radius, etc.
        foregroundDecoration: Overlay styling that appears in front of the child.
        width (int): Fixed width of the container in pixels.
        height (int): Fixed height of the container in pixels.
        constraints: A BoxConstraints-like object controlling layout bounds.
        margin: External spacing outside the container’s border.
        transform: A transform to apply (e.g., scale, rotate).
        alignment: How the child should be positioned within the container.
        clipBehavior: Whether and how to clip content that overflows the container.
        css_class (str): A generated or reused CSS class based on the style key.
        style_key (Tuple): A hashable representation of all visual style properties, used for class reuse.

    Class Attributes:
        shared_styles (Dict[Tuple, str]): Shared dictionary mapping unique style keys to generated CSS class names.
    """

    shared_styles: Dict[Tuple, str] = {} # Stores unique style definitions (Tuple key -> class_name)

    def __init__(self,
                 child: Optional[Widget] = None,
                 key: Optional[Key] = None,
                 # Style props...
                 padding=None, color=None, decoration=None,
                 foregroundDecoration=None, width=None, height=None,
                 constraints=None, margin=None, transform=None, alignment=None,
                 clipBehavior=None):

        super().__init__(key=key, children=[child] if child else [])
        self.child = child # Keep for convenience if needed, but main access via get_children

        # Store properties
        self.padding = padding
        self.color = color
        self.decoration = decoration # Assume BoxDecoration or similar
        self.foregroundDecoration = foregroundDecoration # Assume BoxDecoration or similar
        self.width = width
        self.height = height
        self.constraints = constraints # Assume BoxConstraints
        self.margin = margin
        self.transform = transform
        self.alignment = alignment # Assume Alignment object
        self.clipBehavior = clipBehavior

        # --- CSS Class Management ---
        # Generate a unique *hashable* style key
        self.style_key = tuple(make_hashable(prop) for prop in (
            self.padding, self.color, self.decoration, self.width, self.height,
            self.margin, self.alignment, self.clipBehavior
        ))

        if self.style_key not in Container.shared_styles:
            self.css_class = f"shared-container-{len(Container.shared_styles)}"
            Container.shared_styles[self.style_key] = self.css_class
        else:
            self.css_class = Container.shared_styles[self.style_key]

    def get_child(self) -> Optional[Widget]:
         """Convenience method for single child."""
         children = self.get_children()
         return children[0] if children else None

    def render_props(self) -> Dict[str, Any]:
        """Return properties for diffing comparison."""
        props = {
            # Use _get_render_safe_prop for complex objects if needed
            'padding': self._get_render_safe_prop(self.padding),
            'color': self.color,
            'decoration': self._get_render_safe_prop(self.decoration),
            'foregroundDecoration': self._get_render_safe_prop(self.foregroundDecoration),
            'width': self.width,
            'height': self.height,
            'constraints': self._get_render_safe_prop(self.constraints),
            'margin': self._get_render_safe_prop(self.margin),
            'transform': self._get_render_safe_prop(self.transform),
            'alignment': self._get_render_safe_prop(self.alignment),
            'clipBehavior': self.clipBehavior,
            # Crucially, include the assigned css_class itself!
            'css_class': self.css_class,
        }
        # Filter out None values if desired for cleaner diffs
        return {k: v for k, v in props.items() if v is not None}


    def get_required_css_classes(self) -> Set[str]:
        """Return the shared class name needed for this instance."""
        return {self.css_class}

    @staticmethod
    def generate_css_rScrollPhysicsule(style_key: Tuple, css_class: str) -> str:
        """
        Static method accessible by the Reconciler to generate the CSS rule string.
        """
        try:
            # Unpack based on the order defined in __init__ for style_key
            (padding, color, decoration, width, height, margin, alignment, clipBehavior) = style_key

            # Assume style objects have a `to_css()` method returning the CSS value string
            # or are basic types that can be used directly. Handle None carefully.
            padding_str = f'padding: {padding.to_css()};' if hasattr(padding, 'to_css') else ''
            margin_str = f'margin: {margin.to_css()};' if hasattr(margin, 'to_css') else ''
            width_str = f'width: {width}px;' if width is not None else ''
            height_str = f'height: {height}px;' if height is not None else ''
            color_str = f'background-color: {color};' if color else ''
            # Decoration might return multiple properties or a shorthand
            decoration_str = decoration.to_css() if hasattr(decoration, 'to_css') else ''
            clip_str = f'overflow: hidden;' if clipBehavior else '' # Adjust based on clipBehavior type
            # Alignment might set display, justify-content, align-items etc.
            alignment_str = alignment.to_css() if hasattr(alignment, 'to_css') else ''

            # Add box-sizing for predictable layout
            return f"""
            .{css_class} {{
                position: relative; /* Or other positioning as needed */
                box-sizing: border-box;
                {padding_str}
                {margin_str}
                {width_str}
                {height_str}
                {color_str}
                {decoration_str}
                {alignment_str}
                {clip_str}
            }}
            """
        except Exception as e:
            print(f"Error generating CSS for {css_class} with key {style_key}: {e}")
            return f"/* Error generating rule for .{css_class} */"


# --- Text Widget Refactored ---
class Text(Widget):
    """
    A Flutter-inspired Text widget for rendering styled text content within the framework.

    This widget supports shared style deduplication via dynamically generated CSS classes
    based on a unique style key (style, textAlign, overflow). This helps reduce repeated
    inline styles and improves CSS performance and reusability.

    Args:
        data (str): The text content to render.
        key (Optional[Key]): Optional unique key to identify this widget in the widget tree.
        style (Optional[TextStyle]): TextStyle object representing font, size, weight, color, etc.
        textAlign (Optional[str]): Horizontal text alignment (e.g., "left", "center", "right").
        overflow (Optional[str]): Text overflow behavior, e.g., "ellipsis", "clip", or "visible".

    Attributes:
        shared_styles (Dict[Tuple, str]): Class-level cache of style keys to CSS class names.
        style_key (Tuple): A hashable tuple of style-related properties.
        css_class (str): A CSS class name assigned to this specific style combination.

    Methods:
        render_props() -> Dict[str, Any]:
            Returns a dictionary of render-safe properties for widget diffing and updates.
        
        get_required_css_classes() -> Set[str]:
            Returns a set containing the CSS class required for this widget.
        
        generate_css_rule(style_key: Tuple, css_class: str) -> str:
            Static method to generate a valid CSS rule string based on a style key.
    """
    shared_styles: Dict[Tuple, str] = {}

    def __init__(self, data: str, key: Optional[Key] = None, style=None, textAlign=None, overflow=None):
        super().__init__(key=key)
        self.data = data
        self.style = style # Assume TextStyle object or similar
        self.textAlign = textAlign
        self.overflow = overflow

        # --- CSS Class Management ---
        self.style_key = tuple(make_hashable(prop) for prop in (
            self.style, self.textAlign, self.overflow
        ))

        if self.style_key not in Text.shared_styles:
            self.css_class = f"shared-text-{len(Text.shared_styles)}"
            Text.shared_styles[self.style_key] = self.css_class
        else:
            self.css_class = Text.shared_styles[self.style_key]

    def render_props(self) -> Dict[str, Any]:
        """Return properties for diffing."""
        props = {
            'data': self.data, # The text content itself is a key property
            'style': self._get_render_safe_prop(self.style),
            'textAlign': self.textAlign,
            'overflow': self.overflow,
            'css_class': self.css_class,
        }
        return {k: v for k, v in props.items() if v is not None}

    def get_required_css_classes(self) -> Set[str]:
        """Return the shared class name."""
        return {self.css_class}

    @staticmethod
    def generate_css_rule(style_key: Tuple, css_class: str) -> str:
        """Static method for Reconciler to generate CSS rule string."""
        try:
            (style, textAlign, overflow) = style_key

            # Assume style.to_css() returns combined font/color etc. rules
            style_str = style.to_css() if hasattr(style, 'to_css') else ''
            text_align_str = f"text-align: {textAlign};" if textAlign else ''
            overflow_str = f"overflow: {overflow}; white-space: nowrap; text-overflow: ellipsis;" if overflow == 'ellipsis' else (f"overflow: {overflow};" if overflow else '')


            # Basic styling for <p> tag often used for Text
            return f"""
            .{css_class} {{
                margin: 0; /* Reset default paragraph margin */
                padding: 0;
                {style_str}
                {text_align_str}
                {overflow_str}
            }}
            """
        except Exception as e:
            print(f"Error generating CSS for {css_class} with key {style_key}: {e}")
            return f"/* Error generating rule for .{css_class} */"


# --- TextButton Refactored ---
class TextButton(Widget):
    """
    A simple button, typically showing text, styled minimally.
    Compatible with the reconciliation rendering system.
    """
    shared_styles: Dict[Tuple, str] = {} # Class variable for shared CSS

    def __init__(self,
                 child: Widget, # Button usually requires a child (e.g., Text)
                 key: Optional[Key] = None,
                 onPressed: Optional[Callable] = None, # The actual callback function
                 onPressedName: Optional[str] = None, # Explicit name for the callback
                 style: Optional[ButtonStyle] = None):

        # Pass key and child list to the base Widget constructor
        super().__init__(key=key, children=[child])
        self.child = child # Keep reference if needed

        # Store callback and its identifier
        self.onPressed = onPressed
        # Determine the name/identifier to use in HTML/JS
        # Priority: Explicit name > function name > None
        self.onPressed_id = onPressedName if onPressedName else (onPressed.__name__ if onPressed else None)

        self.style = style or ButtonStyle() # Use default ButtonStyle if none provided

        # --- CSS Class Management ---
        # Use make_hashable or ensure ButtonStyle itself is hashable
        # For TextButton, often only a subset of ButtonStyle matters, but let's hash the whole object for now
        self.style_key = (make_hashable(self.style),)

        if self.style_key not in TextButton.shared_styles:
            self.css_class = f"shared-textbutton-{len(TextButton.shared_styles)}"
            TextButton.shared_styles[self.style_key] = self.css_class
            # Register the actual callback function when the style/class is first created
            # This is one approach, another is during tree traversal in Framework
            if self.onPressed and self.onPressed_id:
                Api().register_callback(self.onPressed_id, self.onPressed)
                print(f"[TextButton] Registered callback '{self.onPressed_id}' on style creation.")

        else:
            self.css_class = TextButton.shared_styles[self.style_key]
            # Re-register? Or assume registration persists? Let's assume it persists for now.
            # If styles change causing a *new* class, the new callback might need registration.
            # This highlights complexity - maybe registration should happen in Framework?

    def render_props(self) -> Dict[str, Any]:
        """Return properties for diffing by the Reconciler."""
        props = {
            # Include style details if they affect attributes/inline styles directly
            # 'style_details': self.style.to_dict(), # Example if needed
            'css_class': self.css_class,
            # Pass the identifier for the callback, not the function object
            'onPressed': self.onPressed_id,
            # Note: Child diffing handled separately
        }
        return {k: v for k, v in props.items() if v is not None}


    def get_required_css_classes(self) -> Set[str]:
        """Return the set of CSS class names needed."""
        return {self.css_class}

    @staticmethod
    def generate_css_rule(style_key: Tuple, css_class: str) -> str:
        """Static method callable by the Reconciler to generate the CSS rule."""
        try:
            # Unpack the style key (contains the hashable representation of ButtonStyle)
            style_repr, = style_key
            # How to get back the ButtonStyle object or its properties from style_repr?
            # This is tricky. We need the actual style properties.
            # --- Option A: Assume style_key IS the ButtonStyle (requires ButtonStyle to be hashable) ---
            # style_obj = style_repr # If style_key = (self.style,) and ButtonStyle is hashable

            # --- Option B: Store properties in style_key (more robust if ButtonStyle isn't easily hashable) ---
            # Example: style_key = (bgcolor, fgcolor, padding_tuple, ...)
            # Then unpack here: bgcolor, fgcolor, padding_tuple = style_key
            # style_obj = ButtonStyle(backgroundColor=bgcolor, ...) # Recreate if needed

            # Let's proceed assuming Option A for simplicity, ButtonStyle needs __hash__/__eq__
            style_obj = style_repr
            if not isinstance(style_obj, ButtonStyle):
                # This might happen if make_hashable returned something else
                print(f"Warning: Cannot generate CSS rule for TextButton {css_class}, style_key[0] is not ButtonStyle: {style_repr}")
                # Attempt to create a default style or return empty rule
                style_obj = ButtonStyle() # Default

            style_str = style_obj.to_css() if style_obj else ""

            # Basic TextButton styles often reset browser defaults
            return f"""
            .{css_class} {{
                display: inline-flex; /* Align icon/text */
                align-items: center;
                justify-content: center;
                padding: 8px 16px; /* Default padding? */
                margin: 4px;
                border: none; /* Text buttons often have no border */
                background-color: transparent; /* Usually transparent */
                color: inherit; /* Inherit text color */
                cursor: pointer;
                text-align: center;
                text-decoration: none;
                outline: none;
                -webkit-appearance: none; /* Remove default browser styles */
                -moz-appearance: none;
                appearance: none;
                {style_str} /* Apply styles from ButtonStyle */
            }}
            /* Add :hover, :active styles if possible via ButtonStyle or here */
            .{css_class}:hover {{
                 /* Example: background-color: rgba(0,0,0,0.05); */
                 /* TODO: Get hover styles from ButtonStyle if defined */
            }}
            """
        except Exception as e:
            print(f"Error generating CSS for TextButton {css_class} with key {style_key}: {e}")
            return f"/* Error generating rule for .{css_class} */"


# --- ElevatedButton Refactored ---
class ElevatedButton(Widget):
    """
    A Material Design elevated button with background color and shadow.
    Compatible with the reconciliation rendering system.
    """
    shared_styles: Dict[Tuple, str] = {}

    def __init__(self,
                 child: Widget,
                 key: Optional[Key] = None,
                 onPressed: Optional[Callable] = None,
                 onPressedName: Optional[str] = None,
                 style: Optional[ButtonStyle] = None):

        super().__init__(key=key, children=[child])
        self.child = child

        self.onPressed = onPressed
        self.onPressed_id = onPressedName if onPressedName else (onPressed.__name__ if onPressed else None)

        self.style = style or ButtonStyle( # Provide some sensible defaults for ElevatedButton
             backgroundColor=Colors.blue, # Example default
             foregroundColor=Colors.white, # Example default
             elevation=2,
             padding=EdgeInsets.symmetric(horizontal=16, vertical=8) # Example default
        )

        # --- CSS Class Management ---
        # Use a tuple of specific, hashable style properties relevant to ElevatedButton
        # Or use make_hashable(self.style) if ButtonStyle is complex but convertible
        self.style_key = make_hashable(self.style) # Requires ButtonStyle -> hashable tuple/dict

        if self.style_key not in ElevatedButton.shared_styles:
            self.css_class = f"shared-elevatedbutton-{len(ElevatedButton.shared_styles)}"
            ElevatedButton.shared_styles[self.style_key] = self.css_class
            # Register callback - see note in TextButton about timing/location
            if self.onPressed and self.onPressed_id:
                Api().register_callback(self.onPressed_id, self.onPressed)
                print(f"[ElevatedButton] Registered callback '{self.onPressed_id}' on style creation.")
        else:
            self.css_class = ElevatedButton.shared_styles[self.style_key]


    def render_props(self) -> Dict[str, Any]:
        """Return properties for diffing."""
        props = {
            # 'style_details': self.style.to_dict(), # Or specific props if needed
            'css_class': self.css_class,
            'onPressed': self.onPressed_id,
        }
        return {k: v for k, v in props.items() if v is not None}

    def get_required_css_classes(self) -> Set[str]:
        """Return the set of CSS class names needed."""
        return {self.css_class}

    @staticmethod
    def generate_css_rule(style_key: Tuple, css_class: str) -> str:
        """Static method callable by the Reconciler to generate the CSS rule."""
        try:
            # --- Reconstruct ButtonStyle or get properties from style_key ---
            # This depends heavily on how `make_hashable(self.style)` works
            # Assuming it produces a tuple/dict that can be used to reconstruct or access properties:

            # Example if make_hashable creates a dict:
            # style_dict = dict(style_key) # If style_key was tuple of tuples (('prop', val),..)
            # style_obj = ButtonStyle(**style_dict) # Recreate

            # Example if make_hashable returns the ButtonStyle instance directly (if hashable):
            style_obj = style_key # Assumes key is the ButtonStyle object itself

            if not isinstance(style_obj, ButtonStyle):
                print(f"Warning: Cannot generate CSS rule for ElevatedButton {css_class}, style_key is not ButtonStyle: {style_key}")
                style_obj = ButtonStyle() # Default

            style_str = style_obj.to_css() if style_obj else ""

            # Base styles for ElevatedButton
            return f"""
            .{css_class} {{
                display: inline-flex;
                align-items: center;
                justify-content: center;
                padding: 8px 16px; /* Sensible default */
                margin: 4px;
                border: none; /* Elevated buttons usually have no border */
                border-radius: 4px; /* Default rounding */
                background-color: {getattr(style_obj, 'backgroundColor', '#6200ee')}; /* Default blue */
                color: {getattr(style_obj, 'foregroundColor', 'white')}; /* Default white text */
                cursor: pointer;
                text-align: center;
                text-decoration: none;
                outline: none;
                box-shadow: 0 2px 2px 0 rgba(0,0,0,0.14), /* Default elevation */
                            0 3px 1px -2px rgba(0,0,0,0.12),
                            0 1px 5px 0 rgba(0,0,0,0.20);
                transition: box-shadow 0.28s cubic-bezier(0.4, 0, 0.2, 1); /* Smooth shadow transition */
                -webkit-appearance: none;
                -moz-appearance: none;
                appearance: none;
                {style_str} /* Apply specific styles from ButtonStyle */
            }}
            .{css_class}:hover {{
                 /* Example: Slightly raise shadow */
                 box-shadow: 0 4px 5px 0 rgba(0,0,0,0.14),
                             0 1px 10px 0 rgba(0,0,0,0.12),
                             0 2px 4px -1px rgba(0,0,0,0.20);
                 /* TODO: Get hover styles from ButtonStyle if defined */
            }}
            .{css_class}:active {{
                 /* Example: Flatten shadow */
                 box-shadow: 0 0 0 0 rgba(0,0,0,0);
                 /* TODO: Get active styles from ButtonStyle if defined */
            }}
            """
        except Exception as e:
            print(f"Error generating CSS for ElevatedButton {css_class} with key {style_key}: {e}")
            return f"/* Error generating rule for .{css_class} */"

    # Removed instance methods: to_html(), to_css(), to_js()


# --- IconButton Refactored ---
class IconButton(Widget):
    """
    A button containing an Icon, typically with minimal styling (transparent background).
    Compatible with the reconciliation rendering system.
    """
    shared_styles: Dict[Tuple, str] = {}

    def __init__(self,
                 icon: Widget, # Assume icon is passed as a Widget child
                 key: Optional[Key] = None,
                 onPressed: Optional[Callable] = None,
                 onPressedName: Optional[str] = None,
                 iconSize: Optional[int] = 24, # Default icon size
                 style: Optional[ButtonStyle] = None,
                 # Add specific IconButton props if needed (e.g., tooltip)
                 tooltip: Optional[str] = None):

        # IconButton's child IS the icon widget
        super().__init__(key=key, children=[icon])
        self.icon = icon # Keep direct reference if useful

        self.onPressed = onPressed
        self.onPressed_id = onPressedName if onPressedName else (onPressed.__name__ if onPressed else None)

        # IconButton often uses a minimal ButtonStyle, maybe override defaults?
        self.style = style or ButtonStyle(
            padding=EdgeInsets.all(8), # Default padding for touch target
            backgroundColor='transparent' # Default transparent background
        )
        self.iconSize = iconSize
        self.tooltip = tooltip # Store tooltip if provided

        # --- CSS Class Management ---
        # Style key might include iconSize if it affects CSS, or handle via props
        # Use make_hashable or ensure ButtonStyle is hashable
        self.style_key = (
            make_hashable(self.style),
            self.iconSize,
            # Add other relevant style props to key if needed
        )

        if self.style_key not in IconButton.shared_styles:
            self.css_class = f"shared-iconbutton-{len(IconButton.shared_styles)}"
            IconButton.shared_styles[self.style_key] = self.css_class
            # Register callback (Move to Framework recommended)
            # if self.onPressed and self.onPressed_id:
            #     Api().register_callback(self.onPressed_id, self.onPressed)
        else:
            self.css_class = IconButton.shared_styles[self.style_key]

    def render_props(self) -> Dict[str, Any]:
        """Return properties for diffing by the Reconciler."""
        props = {
            # 'style_details': self.style.to_dict(),
            'css_class': self.css_class,
            'onPressed': self.onPressed_id,
            'iconSize': self.iconSize, # Pass iconSize if JS needs it
            'tooltip': self.tooltip, # Pass tooltip for title attribute
            # Child (icon) diffing handled separately
        }
        return {k: v for k, v in props.items() if v is not None}

    def get_required_css_classes(self) -> Set[str]:
        """Return the set of CSS class names needed."""
        return {self.css_class}

    @staticmethod
    def generate_css_rule(style_key: Tuple, css_class: str) -> str:
        """Static method callable by the Reconciler to generate the CSS rule."""
        try:
            # Unpack style key
            style_repr, iconSize = style_key # Adapt if key structure changes

            # --- Reconstruct ButtonStyle or get properties ---
            # (Requires ButtonStyle hashability or make_hashable providing details)
            style_obj = style_repr # Assuming key[0] IS the ButtonStyle object
            if not isinstance(style_obj, ButtonStyle):
                 print(f"Warning: Cannot generate CSS rule for IconButton {css_class}, style_key[0] is not ButtonStyle: {style_repr}")
                 style_obj = ButtonStyle(padding=EdgeInsets.all(8), backgroundColor='transparent') # Default fallback

            style_str = style_obj.to_css() if style_obj else ""

            # Basic IconButton styles
            # Often includes resetting button defaults and centering the icon
            return f"""
            .{css_class} {{
                display: inline-flex;
                align-items: center;
                justify-content: center;
                padding: {getattr(style_obj.padding, 'to_css', lambda: '8px')()}; /* Use style padding or default */
                margin: 0; /* Reset margin */
                border: none;
                background-color: transparent; /* Usually transparent */
                color: inherit; /* Inherit color for icon */
                cursor: pointer;
                text-align: center;
                text-decoration: none;
                outline: none;
                border-radius: 50%; /* Often circular */
                width: calc({iconSize}px + {getattr(style_obj.padding, 'to_int_horizontal', lambda: 16)()}px); /* Size based on icon + padding */
                height: calc({iconSize}px + {getattr(style_obj.padding, 'to_int_vertical', lambda: 16)()}px);
                -webkit-appearance: none;
                -moz-appearance: none;
                appearance: none;
                overflow: hidden; /* Hide potential overflow if icon is slightly larger */
                {style_str} /* Apply other styles from ButtonStyle (e.g., overlayColor) */
            }}
            /* Style the icon *inside* the button if needed */
            .{css_class} > i, /* Assuming Font Awesome */
            .{css_class} > img,
            .{css_class} > svg {{ /* Or direct child widget */
                font-size: {iconSize}px;
                width: {iconSize}px;
                height: {iconSize}px;
                display: block; /* Prevent extra space */
            }}
            /* Add :hover, :active styles */
            .{css_class}:hover {{
                 background-color: rgba(0, 0, 0, 0.08); /* Example subtle hover */
            }}
            """
        except Exception as e:
            print(f"Error generating CSS for IconButton {css_class} with key {style_key}: {e}")
            return f"/* Error generating rule for .{css_class} */"

    # Removed instance methods: to_html(), to_css(), to_js()


# --- FloatingActionButton Refactored ---
class FloatingActionButton(Widget):
    """
    A circular Material Design button "floating" above the UI, usually with an icon.
    Compatible with the reconciliation rendering system.
    """
    shared_styles: Dict[Tuple, str] = {}

    def __init__(self,
                 child: Optional[Widget] = None, # Typically an Icon widget
                 key: Optional[Key] = None,
                 onPressed: Optional[Callable] = None,
                 onPressedName: Optional[str] = None,
                 style: Optional[ButtonStyle] = None,
                 tooltip: Optional[str] = None):

        # FAB child is optional but common
        super().__init__(key=key, children=[child] if child else [])
        self.child = child

        self.onPressed = onPressed
        self.onPressed_id = onPressedName if onPressedName else (onPressed.__name__ if onPressed else None)

        # FABs have specific style defaults (circular, shadow, background)
        self.style = style or ButtonStyle(
            shape=28, # Half of default 56px size for circular
            elevation=6,
            padding=EdgeInsets.all(16), # Padding around icon
            backgroundColor=Colors.blue # Example accent color
        )
        self.tooltip = tooltip

        # --- CSS Class Management ---
        # Key should include relevant style properties affecting appearance
        # Example using make_hashable on the ButtonStyle object
        self.style_key = make_hashable(self.style)

        if self.style_key not in FloatingActionButton.shared_styles:
            self.css_class = f"shared-fab-{len(FloatingActionButton.shared_styles)}"
            FloatingActionButton.shared_styles[self.style_key] = self.css_class
            # Register callback (Move to Framework recommended)
            # if self.onPressed and self.onPressed_id:
            #     Api().register_callback(self.onPressed_id, self.onPressed)
        else:
            self.css_class = FloatingActionButton.shared_styles[self.style_key]

    def render_props(self) -> Dict[str, Any]:
        """Return properties for diffing by the Reconciler."""
        props = {
            # 'style_details': self.style.to_dict(),
            'css_class': self.css_class,
            'onPressed': self.onPressed_id,
            'tooltip': self.tooltip,
            # Child (icon) diffing handled separately
        }
        return {k: v for k, v in props.items() if v is not None}

    def get_required_css_classes(self) -> Set[str]:
        """Return the set of CSS class names needed."""
        return {self.css_class}

    @staticmethod
    def generate_css_rule(style_key: Tuple, css_class: str) -> str:
        """Static method callable by the Reconciler to generate the CSS rule."""
        try:
            # --- Reconstruct ButtonStyle or get properties from style_key ---
            style_obj = style_key # Assuming key IS the ButtonStyle object (requires hashability)
            if not isinstance(style_obj, ButtonStyle):
                 print(f"Warning: Cannot generate CSS rule for FAB {css_class}, style_key is not ButtonStyle: {style_key}")
                 # Sensible FAB defaults
                 style_obj = ButtonStyle(shape=28, elevation=6, padding=EdgeInsets.all(16), backgroundColor=Colors.blue)

            style_str = style_obj.to_css() if style_obj else ""

            # Base styles for FloatingActionButton, including fixed positioning
            return f"""
            .{css_class} {{
                display: inline-flex; /* Use inline-flex to size based on content+padding */
                align-items: center;
                justify-content: center;
                position: fixed; /* <<< FAB is fixed position */
                bottom: 16px;    /* <<< Default position */
                right: 16px;     /* <<< Default position */
                width: 56px;     /* <<< Default size */
                height: 56px;    /* <<< Default size */
                padding: 0;      /* Reset padding, rely on inner container or direct style */
                margin: 0;
                border: none;
                border-radius: 50%; /* <<< Circular */
                background-color: {getattr(style_obj, 'backgroundColor', '#6200ee')};
                color: {getattr(style_obj, 'foregroundColor', 'white')};
                cursor: pointer;
                text-align: center;
                text-decoration: none;
                outline: none;
                box-shadow: 0 6px 10px 0 rgba(0,0,0,0.14), /* Default FAB shadow */
                            0 1px 18px 0 rgba(0,0,0,0.12),
                            0 3px 5px -1px rgba(0,0,0,0.20);
                transition: box-shadow 0.28s cubic-bezier(0.4, 0, 0.2, 1), transform 0.2s ease-out;
                -webkit-appearance: none;
                -moz-appearance: none;
                appearance: none;
                z-index: 1000; /* Ensure it's above most content */
                {style_str} /* Apply specific overrides from ButtonStyle */
            }}
            /* Style the icon *inside* the button */
            .{css_class} > * {{ /* Target direct child (icon) */
                display: block; /* Prevent extra space */
            }}
             /* Add :hover, :active styles */
            .{css_class}:hover {{
                 box-shadow: 0 12px 17px 2px rgba(0,0,0,0.14),
                             0 5px 22px 4px rgba(0,0,0,0.12),
                             0 7px 8px -4px rgba(0,0,0,0.20);
            }}
            """
            # Note: :active styles might involve slight scale transform too
        except Exception as e:
            print(f"Error generating CSS for FloatingActionButton {css_class} with key {style_key}: {e}")
            return f"/* Error generating rule for .{css_class} */"

    # Removed instance methods: to_html(), to_css(), to_js()

class Column(Widget):
    """
    A widget that displays its children in a vertical array.
    Compatible with the reconciliation rendering system.
    """
    shared_styles: Dict[Tuple, str] = {} # Class variable for shared CSS

    def __init__(self,
                 children: List[Widget], # Children are mandatory for Column usually
                 key: Optional[Key] = None,
                 # Layout properties
                 mainAxisAlignment=MainAxisAlignment.START,
                 mainAxisSize=MainAxisSize.MAX,
                 crossAxisAlignment=CrossAxisAlignment.CENTER,
                 textDirection=TextDirection.LTR,
                 verticalDirection=VerticalDirection.DOWN,
                 textBaseline=TextBaseline.alphabetic):

        # Pass key and children list to the base Widget constructor
        super().__init__(key=key, children=children)

        # Store layout properties
        self.mainAxisAlignment = mainAxisAlignment
        self.mainAxisSize = mainAxisSize
        self.crossAxisAlignment = crossAxisAlignment
        self.textDirection = textDirection
        self.verticalDirection = verticalDirection
        self.textBaseline = textBaseline # Note: CSS mapping is tricky

        # --- CSS Class Management ---
        # Generate a hashable style key from layout properties
        # Assuming the enum-like values (strings) are hashable directly
        self.style_key = (
            self.mainAxisAlignment,
            self.mainAxisSize,
            self.crossAxisAlignment,
            self.textDirection,
            self.verticalDirection,
            self.textBaseline,
        )

        # Use shared_styles dictionary to manage CSS classes
        if self.style_key not in Column.shared_styles:
            # Assign a new shared class name if style combo is new
            self.css_class = f"shared-column-{len(Column.shared_styles)}"
            Column.shared_styles[self.style_key] = self.css_class
        else:
            # Reuse existing class name for identical styles
            self.css_class = Column.shared_styles[self.style_key]

        # No need to call self.add_child here, base class handles children list

    def render_props(self) -> Dict[str, Any]:
        """
        Return properties relevant for diffing by the Reconciler.
        Includes layout properties and the assigned CSS class.
        """
        props = {
            'mainAxisAlignment': self.mainAxisAlignment,
            'mainAxisSize': self.mainAxisSize,
            'crossAxisAlignment': self.crossAxisAlignment,
            'textDirection': self.textDirection,
            'verticalDirection': self.verticalDirection,
            'textBaseline': self.textBaseline,
            'css_class': self.css_class, # Include the computed class
            # Note: We don't include 'children' here; child diffing is handled separately by the Reconciler
        }
        # Return all defined properties (filtering None isn't strictly needed unless desired)
        return props

    def get_required_css_classes(self) -> Set[str]:
        """
        Return the set of CSS class names needed by this specific Column instance.
        """
        # Currently, only the shared layout class is needed.
        return {self.css_class}

    @staticmethod
    def generate_css_rule(style_key: Tuple, css_class: str) -> str:
        """
        Static method callable by the Reconciler to generate the CSS rule string
        for a specific style combination identified by style_key and css_class.
        """
        try:
            # Unpack the style key tuple in the same order it was created
            (
                mainAxisAlignment, mainAxisSize, crossAxisAlignment,
                textDirection, verticalDirection, textBaseline
            ) = style_key

            # --- Translate framework properties to CSS Flexbox properties ---

            # Column implies flex-direction: column (or column-reverse)
            flex_direction = 'column'
            if verticalDirection == VerticalDirection.UP:
                flex_direction = 'column-reverse'

            # Main axis for Column is vertical -> maps to justify-content
            justify_content_val = mainAxisAlignment

            # Cross axis for Column is horizontal -> maps to align-items
            # Handle baseline alignment specifically
            align_items_val = crossAxisAlignment
            if crossAxisAlignment == CrossAxisAlignment.BASELINE:
                # For baseline alignment in flexbox, typically use align-items: baseline;
                # textBaseline (alphabetic/ideographic) might not have a direct, simple CSS equivalent
                # across all scenarios without knowing child content. Stick to 'baseline'.
                align_items_val = 'baseline'
            elif crossAxisAlignment == CrossAxisAlignment.STRETCH and mainAxisSize == MainAxisSize.MAX:
                # Default behavior for align-items: stretch might need width/height adjustments
                pass # Keep 'stretch'
            # If not baseline or stretch, use the value directly (e.g., 'center', 'flex-start', 'flex-end')


            # MainAxisSize determines height behavior
            height_style = ""
            if mainAxisSize == MainAxisSize.MAX:
                # Fill available vertical space. If parent is also flex, might need flex-grow.
                # Using height: 100% assumes parent has a defined height.
                # 'flex: 1;' is often better in flex contexts. Let's use fit-content for min.
                height_style = "flex-grow: 1; flex-basis: 0;" # Common pattern to fill space
                # Alternatively: height: 100%; # If parent has height
            elif mainAxisSize == MainAxisSize.MIN:
                # Wrap content height
                height_style = "height: fit-content;"

            # TextDirection maps to CSS direction
            direction_style = f"direction: {textDirection};"

            # Combine the CSS properties
            # Using text-align for cross-axis is generally incorrect for flex items themselves,
            # align-items controls the item alignment. Text-align applies *within* an item.
            styles = (
                f"display: flex; "
                f"flex-direction: {flex_direction}; "
                f"justify-content: {justify_content_val}; " # Main axis (Vertical)
                f"align-items: {align_items_val}; "       # Cross axis (Horizontal)
                f"{height_style} "
                f"{direction_style}"
                # Removed vertical-align as it's not for flexbox layout like this
            )

            # Return the complete CSS rule
            return f".{css_class} {{ {styles} }}"

        except Exception as e:
            print(f"Error generating CSS for Column {css_class} with key {style_key}: {e}")
            return f"/* Error generating rule for .{css_class} */"

    # Removed instance methods: to_html(), to_css()

class Row(Widget):
    """
    A widget that displays its children in a horizontal array.
    Compatible with the reconciliation rendering system.
    """
    shared_styles: Dict[Tuple, str] = {} # Class variable for shared CSS

    def __init__(self,
                 children: List[Widget], # Children are usually expected for Row
                 key: Optional[Key] = None,
                 # Layout properties
                 mainAxisAlignment=MainAxisAlignment.START,
                 mainAxisSize=MainAxisSize.MAX,
                 crossAxisAlignment=CrossAxisAlignment.CENTER,
                 textDirection=TextDirection.LTR,
                 # verticalDirection less directly applicable to Row layout itself
                 verticalDirection=VerticalDirection.DOWN, # Keep for consistency if needed?
                 textBaseline=TextBaseline.alphabetic):

        # Pass key and children list to the base Widget constructor
        super().__init__(key=key, children=children)

        # Store layout properties
        self.mainAxisAlignment = mainAxisAlignment
        self.mainAxisSize = mainAxisSize
        self.crossAxisAlignment = crossAxisAlignment
        self.textDirection = textDirection
        self.verticalDirection = verticalDirection # Store but may not directly impact Row CSS much
        self.textBaseline = textBaseline # Relevant for crossAxisAlignment='baseline'

        # --- CSS Class Management ---
        # Generate a hashable style key from layout properties
        self.style_key = (
            self.mainAxisAlignment,
            self.mainAxisSize,
            self.crossAxisAlignment,
            self.textDirection,
            self.verticalDirection, # Included for completeness, though less used in Row CSS
            self.textBaseline,
        )

        # Use shared_styles dictionary to manage CSS classes
        if self.style_key not in Row.shared_styles:
            # Assign a new shared class name if style combo is new
            self.css_class = f"shared-row-{len(Row.shared_styles)}"
            Row.shared_styles[self.style_key] = self.css_class
        else:
            # Reuse existing class name for identical styles
            self.css_class = Row.shared_styles[self.style_key]

    def render_props(self) -> Dict[str, Any]:
        """
        Return properties relevant for diffing by the Reconciler.
        Includes layout properties and the assigned CSS class.
        """
        props = {
            'mainAxisAlignment': self.mainAxisAlignment,
            'mainAxisSize': self.mainAxisSize,
            'crossAxisAlignment': self.crossAxisAlignment,
            'textDirection': self.textDirection,
            'verticalDirection': self.verticalDirection,
            'textBaseline': self.textBaseline,
            'css_class': self.css_class, # Include the computed class
        }
        return props

    def get_required_css_classes(self) -> Set[str]:
        """
        Return the set of CSS class names needed by this specific Row instance.
        """
        # Currently, only the shared layout class is needed.
        return {self.css_class}

    @staticmethod
    def generate_css_rule(style_key: Tuple, css_class: str) -> str:
        """
        Static method callable by the Reconciler to generate the CSS rule string
        for a specific style combination identified by style_key and css_class.
        """
        try:
            # Unpack the style key tuple in the same order it was created
            (
                mainAxisAlignment, mainAxisSize, crossAxisAlignment,
                textDirection, verticalDirection, textBaseline # Unpack all stored keys
            ) = style_key

            # --- Translate framework properties to CSS Flexbox properties for a Row ---

            # Row implies flex-direction: row (or row-reverse)
            # Use textDirection to determine actual flex-direction if RTL is needed
            flex_direction = 'row'
            # This mapping might need adjustment based on how LTR/RTL should interact
            # with flex-direction vs. just the 'direction' property.
            # Standard practice often uses 'direction' property, leaving flex-direction as row.
            # if textDirection == TextDirection.RTL:
            #     flex_direction = 'row-reverse' # Less common than using direction property

            # Main axis for Row is horizontal -> maps to justify-content
            justify_content_val = mainAxisAlignment

            # Cross axis for Row is vertical -> maps to align-items
            align_items_val = crossAxisAlignment
            if crossAxisAlignment == CrossAxisAlignment.BASELINE:
                 align_items_val = 'baseline'
            # Handle STRETCH if needed (default usually works if parent has height)

            # MainAxisSize determines width behavior
            width_style = ""
            if mainAxisSize == MainAxisSize.MAX:
                # Fill available horizontal space.
                width_style = "width: 100%;" # Or flex-grow: 1 if inside another flex container
            elif mainAxisSize == MainAxisSize.MIN:
                # Wrap content width
                width_style = "width: fit-content;" # Or width: auto; display: inline-flex;

            # TextDirection maps to CSS direction
            direction_style = f"direction: {textDirection};"

            # Combine the CSS properties
            styles = (
                f"display: flex; "
                f"flex-direction: {flex_direction}; " # Usually 'row'
                f"justify-content: {justify_content_val}; " # Main axis (Horizontal)
                f"align-items: {align_items_val}; "       # Cross axis (Vertical)
                f"{width_style} "
                f"{direction_style}"
            )

            # Return the complete CSS rule
            return f".{css_class} {{ {styles} }}"

        except Exception as e:
            print(f"Error generating CSS for Row {css_class} with key {style_key}: {e}")
            return f"/* Error generating rule for .{css_class} */"

    # Removed instance methods: to_html(), to_css()

class AssetImage:
    """Helper to generate URL for local assets served by the framework."""
    def __init__(self, file_name: str):
        # Basic check for leading slashes
        clean_file_name = file_name.lstrip('/')
        # TODO: Add more robust path joining and sanitization
        self.src = f'http://localhost:{port}/{assets_dir}/{clean_file_name}'

    def get_source(self) -> str:
        return self.src

    def __eq__(self, other):
        return isinstance(other, AssetImage) and self.src == other.src

    def __hash__(self):
        return hash(self.src)

    def __repr__(self):
        return f"AssetImage('{self.src}')"

class NetworkImage:
    """Helper to represent a network image URL."""
    def __init__(self, url: str):
        # TODO: Add URL validation if needed
        self.src = url

    def get_source(self) -> str:
        return self.src

    def __eq__(self, other):
        return isinstance(other, NetworkImage) and self.src == other.src

    def __hash__(self):
        return hash(self.src)

    def __repr__(self):
        return f"NetworkImage('{self.src}')"

# --- Image Widget Refactored ---
class Image(Widget):
    """
    Displays an image from an AssetImage or NetworkImage source.
    Compatible with the reconciliation rendering system.
    """
    shared_styles: Dict[Tuple, str] = {}

    def __init__(self,
                 image: Union[AssetImage, NetworkImage], # Image source object
                 key: Optional[Key] = None,
                 width: Optional[Union[int, str]] = None, # Allow '100%' etc.
                 height: Optional[Union[int, str]] = None,
                 fit: str = ImageFit.CONTAIN, # Use constants from styles.ImageFit
                 alignment: str = 'center'): # Alignment within its box if size differs

        # Image widget doesn't typically have children in Flutter sense
        super().__init__(key=key, children=[])

        if not isinstance(image, (AssetImage, NetworkImage)):
             raise TypeError("Image widget requires an AssetImage or NetworkImage instance.")

        self.image_source = image
        self.width = width
        self.height = height
        self.fit = fit
        self.alignment = alignment # Note: CSS object-position might be needed for alignment

        # --- CSS Class Management ---
        # Key includes properties affecting CSS style
        # Use make_hashable if alignment object is complex
        self.style_key = (
            self.fit,
            self.width, # Include size in key as it might affect CSS rules
            self.height,
            self.alignment,
        )

        if self.style_key not in Image.shared_styles:
            self.css_class = f"shared-image-{len(Image.shared_styles)}"
            Image.shared_styles[self.style_key] = self.css_class
        else:
            self.css_class = Image.shared_styles[self.style_key]

    def render_props(self) -> Dict[str, Any]:
        """Return properties for diffing."""
        props = {
            'src': self.image_source.get_source(), # The actual URL is the key content diff
            'width': self.width,
            'height': self.height,
            'fit': self.fit,
            'alignment': self.alignment,
            'css_class': self.css_class,
        }
        return {k: v for k, v in props.items() if v is not None}

    def get_required_css_classes(self) -> Set[str]:
        """Return the set of CSS class names needed."""
        return {self.css_class}

    @staticmethod
    def generate_css_rule(style_key: Tuple, css_class: str) -> str:
        """Static method callable by the Reconciler to generate the CSS rule."""
        try:
            # Unpack the style key
            fit, width, height, alignment = style_key

            # Translate properties to CSS
            fit_style = f"object-fit: {fit};" if fit else ""

            # Handle width/height units (px default, allow strings like '100%')
            width_style = ""
            if isinstance(width, (int, float)): width_style = f"width: {width}px;"
            elif isinstance(width, str): width_style = f"width: {width};"

            height_style = ""
            if isinstance(height, (int, float)): height_style = f"height: {height}px;"
            elif isinstance(height, str): height_style = f"height: {height};"

            # Map alignment to object-position (basic example)
            # See: https://developer.mozilla.org/en-US/docs/Web/CSS/object-position
            alignment_style = ""
            if alignment:
                 alignment_style = f"object-position: {alignment};" # Assumes alignment is CSS compatible ('center', 'top left', '50% 50%', etc.)

            # Combine styles
            styles = (
                f"{fit_style} "
                f"{width_style} "
                f"{height_style} "
                f"{alignment_style}"
            )

            # Return the complete CSS rule
            # Note: display:block often helpful for sizing images correctly
            return f".{css_class} {{ display: block; {styles} }}"

        except Exception as e:
            print(f"Error generating CSS for Image {css_class} with key {style_key}: {e}")
            return f"/* Error generating rule for .{css_class} */"

    # Removed instance methods: to_html(), to_css()


# --- Icon Widget Refactored ---
class Icon(Widget):
    """
    Displays an icon, either from a font (like Font Awesome) or a custom image file.
    Compatible with the reconciliation rendering system.
    """
    shared_styles: Dict[Tuple, str] = {}

    def __init__(self,
                 # Provide one of these:
                 icon_name: Optional[str] = None, # e.g., 'home', 'gear' for Font Awesome
                 custom_icon: Optional[Union[str, AssetImage]] = None, # Asset path string or AssetImage
                 key: Optional[Key] = None,
                 size: int = 16,
                 color: Optional[str] = None):

        # Icon widget has no children
        super().__init__(key=key, children=[])

        if not icon_name and not custom_icon:
            raise ValueError("Icon widget requires either 'icon_name' or 'custom_icon'.")
        if icon_name and custom_icon:
             print("Warning: Both 'icon_name' and 'custom_icon' provided to Icon. Prioritizing 'custom_icon'.")
             icon_name = None # Prioritize custom image


        self.icon_name = icon_name
        # Ensure custom_icon is an AssetImage if it's a string path
        if isinstance(custom_icon, str):
             self.custom_icon_source = AssetImage(custom_icon)
        elif isinstance(custom_icon, AssetImage):
             self.custom_icon_source = custom_icon
        else:
            self.custom_icon_source = None # Should be None if icon_name is used

        self.size = size
        self.color = color

        # --- CSS Class Management ---
        # Key includes properties affecting styling
        self.style_key = (
            self.size,
            self.color,
            # Distinguish between font/image icon in key if CSS differs significantly
            'img' if self.custom_icon_source else 'font',
        )

        if self.style_key not in Icon.shared_styles:
            self.css_class = f"shared-icon-{len(Icon.shared_styles)}"
            Icon.shared_styles[self.style_key] = self.css_class
        else:
            self.css_class = Icon.shared_styles[self.style_key]

    def render_props(self) -> Dict[str, Any]:
        """Return properties for diffing."""
        props = {
            'icon_name': self.icon_name, # e.g., 'home'
            'custom_icon_src': self.custom_icon_source.get_source() if self.custom_icon_source else None,
            'size': self.size,
            'color': self.color,
            'css_class': self.css_class,
            # Indicate render type for potential JS patching logic
            'render_type': 'img' if self.custom_icon_source else 'font',
        }
        return {k: v for k, v in props.items() if v is not None}

    def get_required_css_classes(self) -> Set[str]:
        """Return the set of CSS class names needed."""
        return {self.css_class}

    @staticmethod
    def generate_css_rule(style_key: Tuple, css_class: str) -> str:
        """Static method callable by the Reconciler to generate the CSS rule."""
        try:
            # Unpack the style key
            size, color, render_type = style_key

            # Base styles common to both icon types
            common_styles = (
                 f"width: {size}px; "
                 f"height: {size}px; "
                 f"display: inline-block; " # Or block depending on layout needs
                 f"vertical-align: middle; " # Align with text nicely
                 f"line-height: {size}px; " # Helps center font icons vertically sometimes
            )

            specific_styles = ""
            if render_type == 'font':
                 specific_styles = (
                      f"font-size: {size}px; "
                      f"{f'color: {color};' if color else 'color: inherit;'}" # Inherit or set color
                 )
                 # Add font-family if using a specific icon font *not* globally included
                 # specific_styles += "font-family: 'YourIconFont';"
            elif render_type == 'img':
                 specific_styles = (
                      f"object-fit: contain; " # Or other fit as needed
                      f"background-color: transparent; " # Ensure no default background
                 )
                 # Color doesn't directly apply to <img>, use filter for basic tinting? (Advanced)
                 # if color: specific_styles += f"filter: ...;" # Complex

            # Return the complete CSS rule
            return f".{css_class} {{ {common_styles} {specific_styles} }}"

        except Exception as e:
            print(f"Error generating CSS for Icon {css_class} with key {style_key}: {e}")
            return f"/* Error generating rule for .{css_class} */"

    # Removed instance methods: to_html(), to_css()
    # Removed child methods: get_children(), remove_all_children() (implicit from base)

class ListView(Widget):
    """
    A scrollable list of widgets arranged linearly.
    Compatible with the reconciliation rendering system.
    """
    shared_styles: Dict[Tuple, str] = {} # Class variable for shared CSS

    def __init__(self,
                 children: List[Widget], # Children are core to ListView
                 key: Optional[Key] = None,
                 # Styling & Behavior properties
                 padding: Optional[EdgeInsets] = None,
                 scrollDirection: str = Axis.VERTICAL,
                 reverse: bool = False,
                 primary: bool = True, # Usually true if main scroll area
                 physics: str = ScrollPhysics.ALWAYS_SCROLLABLE, # Default allows scrolling
                 shrinkWrap: bool = False, # Affects sizing relative to content
                 # Properties affecting children/scrolling - might not directly influence CSS class
                 itemExtent: Optional[int] = None, # Fixed size for children (performance)
                 cacheExtent: Optional[int] = None, # Virtual scrolling hint (not directly CSS)
                 semanticChildCount: Optional[int] = None # Accessibility
                ):

        super().__init__(key=key, children=children)

        # Store properties
        self.padding = padding or EdgeInsets.all(0) # Default to no padding
        self.scrollDirection = scrollDirection
        self.reverse = reverse
        self.primary = primary # Influences default scroll behavior/bars
        self.physics = physics # Influences overflow CSS
        self.shrinkWrap = shrinkWrap # Influences sizing CSS (height/width)
        self.itemExtent = itemExtent # Passed to props, might influence JS/child styles
        self.cacheExtent = cacheExtent # Primarily for virtual scrolling logic, not direct CSS
        self.semanticChildCount = semanticChildCount # Used for aria attribute

        # --- CSS Class Management ---
        # Style key includes properties directly affecting the container's CSS rules
        # NOTE: itemExtent, cacheExtent are omitted as they don't typically change
        # the container's *own* CSS class rules directly. shrinkWrap is included as it affects sizing.
        self.style_key = (
            make_hashable(self.padding), # Use helper or ensure EdgeInsets is hashable
            self.scrollDirection,
            self.reverse,
            self.primary,
            self.physics,
            self.shrinkWrap, # Include shrinkWrap as it changes sizing rules
        )

        if self.style_key not in ListView.shared_styles:
            self.css_class = f"shared-listview-{len(ListView.shared_styles)}"
            ListView.shared_styles[self.style_key] = self.css_class
        else:
            self.css_class = ListView.shared_styles[self.style_key]

    def render_props(self) -> Dict[str, Any]:
        """Return properties for diffing by the Reconciler."""
        props = {
            'padding': self._get_render_safe_prop(self.padding),
            'scrollDirection': self.scrollDirection,
            'reverse': self.reverse,
            'primary': self.primary,
            'physics': self.physics,
            'shrinkWrap': self.shrinkWrap,
            'itemExtent': self.itemExtent, # Pass for potential use in child patching/layout JS
            'cacheExtent': self.cacheExtent, # Pass for potential JS use
            'semanticChildCount': self.semanticChildCount, # For aria-* attribute patching
            'css_class': self.css_class,
            # Children diffing handled separately
        }
        return {k: v for k, v in props.items() if v is not None} # Filter None

    def get_required_css_classes(self) -> Set[str]:
        """Return the set of CSS class names needed by this ListView instance."""
        return {self.css_class}

    @staticmethod
    def generate_css_rule(style_key: Tuple, css_class: str) -> str:
        """Static method callable by the Reconciler to generate the CSS rule."""
        try:
            # Unpack the style key tuple based on its creation order in __init__
            (padding_repr, scrollDirection, reverse, primary, physics, shrinkWrap) = style_key

            # --- Determine CSS based on properties ---

            # Flex direction
            flex_direction = "column" # Default for vertical
            if scrollDirection == Axis.HORIZONTAL:
                flex_direction = "row"
            if reverse:
                flex_direction += "-reverse"

            # Overflow based on physics and primary scroll view status
            overflow_style = ""
            axis_to_scroll = 'y' if scrollDirection == Axis.VERTICAL else 'x'
            if physics == ScrollPhysics.NEVER_SCROLLABLE:
                overflow_style = "overflow: hidden;"
            elif physics == ScrollPhysics.CLAMPING:
                 # Usually implies hidden, but let CSS default handle (might clip)
                 overflow_style = f"overflow-{axis_to_scroll}: hidden;" # More specific? Or just overflow: hidden? Let's use specific.
            elif physics == ScrollPhysics.ALWAYS_SCROLLABLE or physics == ScrollPhysics.BOUNCING:
                 # Standard CSS uses 'auto' or 'scroll'. 'auto' is generally preferred.
                 # 'bouncing' (-webkit-overflow-scrolling: touch;) is iOS specific, apply if needed.
                 overflow_style = f"overflow-{axis_to_scroll}: auto;"
                 if physics == ScrollPhysics.BOUNCING:
                       overflow_style += " -webkit-overflow-scrolling: touch;" # Add iOS momentum

            # Sizing based on shrinkWrap
            size_style = ""
            if shrinkWrap:
                # Wrap content size
                if scrollDirection == Axis.VERTICAL:
                     size_style = "height: fit-content; width: 100%;" # Fit height, fill width
                else: # HORIZONTAL
                     size_style = "width: fit-content; height: 100%;" # Fit width, fill height
            else:
                 # Expand to fill parent (common default for lists)
                 # Requires parent context, using 100% assumes parent has size.
                 # Using flex-grow is better if ListView is inside another flex container.
                 size_style = "flex-grow: 1; flex-basis: 0; width: 100%; height: 100%;" # Attempt to fill
                 # Need to handle potential conflict if both width/height 100% and overflow are set.
                 # Add min-height/min-width to prevent collapse?
                 size_style += " min-height: 0; min-width: 0;"


            # Padding
            # Reconstruct EdgeInsets or use representation directly if simple
            # Assuming padding_repr is hashable and usable by EdgeInsets.to_css() if needed
            # For now, assume padding_repr IS the EdgeInsets object if it was hashable
            padding_obj = padding_repr
            padding_style = ""
            if isinstance(padding_obj, EdgeInsets):
                 padding_style = f"padding: {padding_obj.to_css()};"
            elif padding_repr: # Handle fallback if not EdgeInsets obj
                 padding_style = f"padding: {padding_repr};" # Assumes it's already CSS string? Risky.


            # Combine styles
            styles = (
                f"display: flex; "
                f"flex-direction: {flex_direction}; "
                f"{padding_style} "
                f"{size_style} "
                f"{overflow_style}"
                # Other base styles? e.g., list-style: none; if using <ul> internally
            )

            # Return the complete CSS rule
            return f".{css_class} {{ {styles} }}"

        except Exception as e:
            print(f"Error generating CSS for ListView {css_class} with key {style_key}: {e}")
            return f"/* Error generating rule for .{css_class} */"

    # Removed instance methods: to_html(), to_css()

class GridView(Widget):
    """
    A scrollable, 2D array of widgets.
    Compatible with the reconciliation rendering system.
    """
    shared_styles: Dict[Tuple, str] = {} # Class variable for shared CSS

    def __init__(self,
                 children: List[Widget], # Grid items
                 key: Optional[Key] = None,
                 # Scroll/Layout properties for the main container
                 padding: Optional[EdgeInsets] = None,
                 scrollDirection: str = Axis.VERTICAL,
                 reverse: bool = False,
                 primary: bool = True,
                 physics: str = ScrollPhysics.ALWAYS_SCROLLABLE,
                 shrinkWrap: bool = False, # Affects sizing relative to content
                 # Grid specific properties
                 crossAxisCount: int = 2, # Number of columns (if vertical) or rows (if horizontal)
                 mainAxisSpacing: float = 0, # Gap between items along the main (scrolling) axis
                 crossAxisSpacing: float = 0, # Gap between items along the cross axis
                 childAspectRatio: float = 1.0, # Width / Height ratio for children
                 # Accessibility
                 semanticChildCount: Optional[int] = None
                ):

        super().__init__(key=key, children=children)

        # Store properties
        self.padding = padding or EdgeInsets.all(0)
        self.scrollDirection = scrollDirection
        self.reverse = reverse
        self.primary = primary
        self.physics = physics
        self.shrinkWrap = shrinkWrap
        self.crossAxisCount = max(1, crossAxisCount) # Ensure at least 1 column/row
        self.mainAxisSpacing = mainAxisSpacing
        self.crossAxisSpacing = crossAxisSpacing
        self.childAspectRatio = max(0.01, childAspectRatio) # Ensure positive aspect ratio
        self.semanticChildCount = semanticChildCount

        # --- CSS Class Management ---
        # Key includes properties affecting CSS rules for the container and item layout
        self.style_key = (
            make_hashable(self.padding),
            self.scrollDirection,
            self.reverse,
            self.primary,
            self.physics,
            self.shrinkWrap,
            self.crossAxisCount,
            self.mainAxisSpacing,
            self.crossAxisSpacing,
            self.childAspectRatio,
        )

        if self.style_key not in GridView.shared_styles:
            self.css_class = f"shared-gridview-{len(GridView.shared_styles)}"
            GridView.shared_styles[self.style_key] = self.css_class
        else:
            self.css_class = GridView.shared_styles[self.style_key]

    def render_props(self) -> Dict[str, Any]:
        """Return properties for diffing by the Reconciler."""
        props = {
            'padding': self._get_render_safe_prop(self.padding),
            'scrollDirection': self.scrollDirection,
            'reverse': self.reverse,
            'primary': self.primary,
            'physics': self.physics,
            'shrinkWrap': self.shrinkWrap,
            'crossAxisCount': self.crossAxisCount,
            'mainAxisSpacing': self.mainAxisSpacing,
            'crossAxisSpacing': self.crossAxisSpacing,
            'childAspectRatio': self.childAspectRatio,
            'semanticChildCount': self.semanticChildCount,
            'css_class': self.css_class,
            # Children diffing handled separately
        }
        return {k: v for k, v in props.items() if v is not None} # Filter None

    def get_required_css_classes(self) -> Set[str]:
        """Return the set of CSS class names needed by this GridView instance."""
        return {self.css_class}

    @staticmethod
    def generate_css_rule(style_key: Tuple, css_class: str) -> str:
        """Static method callable by the Reconciler to generate the CSS rule(s)."""
        try:
            # Unpack the style key tuple based on its creation order in __init__
            (padding_repr, scrollDirection, reverse, primary, physics, shrinkWrap,
             crossAxisCount, mainAxisSpacing, crossAxisSpacing, childAspectRatio) = style_key

            # --- Determine CSS for the GridView container ---

            # Scroll/Overflow behavior (similar to ListView)
            overflow_style = ""
            axis_to_scroll = 'y' if scrollDirection == Axis.VERTICAL else 'x'
            if physics == ScrollPhysics.NEVER_SCROLLABLE:
                overflow_style = "overflow: hidden;"
            elif physics == ScrollPhysics.CLAMPING:
                 overflow_style = f"overflow-{axis_to_scroll}: hidden;"
            elif physics == ScrollPhysics.ALWAYS_SCROLLABLE or physics == ScrollPhysics.BOUNCING:
                 overflow_style = f"overflow-{axis_to_scroll}: auto;"
                 if physics == ScrollPhysics.BOUNCING:
                       overflow_style += " -webkit-overflow-scrolling: touch;"

            # Sizing based on shrinkWrap (similar to ListView)
            size_style = ""
            if shrinkWrap:
                # Wrap content size - For Grid, this is tricky. 'fit-content' might work
                # but depends heavily on browser interpretation with grid layout.
                # Often, you might give it a max-width/max-height instead.
                # Let's default to width/height auto for shrinkWrap.
                 size_style = "width: auto; height: auto;"
            else:
                 # Expand to fill parent (common default)
                 size_style = "flex-grow: 1; flex-basis: 0; width: 100%; height: 100%;" # Assume parent is flex/has size
                 size_style += " min-height: 0; min-width: 0;" # Prevent collapse


            # Padding
            padding_obj = padding_repr # Assuming padding_repr is usable/EdgeInsets
            padding_style = ""
            if isinstance(padding_obj, EdgeInsets):
                 padding_style = f"padding: {padding_obj.to_css()};"
            elif padding_repr:
                 padding_style = f"padding: {padding_repr};" # Fallback


            # Grid Layout Properties
            # Use CSS Grid (display: grid) directly on the container
            grid_display_style = "display: grid;"
            grid_template_style = ""
            grid_gap_style = ""

            # Note: reverse for grid is complex, CSS grid doesn't have simple reverse.
            # Would likely need JS reordering or different grid population logic. Ignoring for CSS.

            if scrollDirection == Axis.VERTICAL:
                # Columns are fixed by crossAxisCount
                grid_template_style = f"grid-template-columns: repeat({crossAxisCount}, 1fr);"
                # Gap maps mainAxis (vertical) to row-gap, crossAxis (horizontal) to column-gap
                grid_gap_style = f"gap: {mainAxisSpacing}px {crossAxisSpacing}px;"
            else: # HORIZONTAL
                # Rows are fixed by crossAxisCount
                # We need to tell the grid how rows auto-size (usually auto)
                 grid_template_style = f"grid-template-rows: repeat({crossAxisCount}, auto);"
                 # Auto-flow columns
                 grid_template_style += " grid-auto-flow: column;"
                 # Define auto column width (often based on content or 1fr if filling)
                 # This is simplified, might need 'grid-auto-columns: min-content;' or similar
                 grid_template_style += " grid-auto-columns: 1fr;" # Example: columns fill space
                 # Gap maps mainAxis (horizontal) to column-gap, crossAxis (vertical) to row-gap
                 grid_gap_style = f"gap: {crossAxisSpacing}px {mainAxisSpacing}px;"


            # Combine styles for the main GridView container
            container_styles = (
                f"{padding_style} "
                f"{size_style} "
                f"{overflow_style} "
                f"{grid_display_style} "
                f"{grid_template_style} "
                f"{grid_gap_style}"
                # Ensure box-sizing for padding calculations
                "box-sizing: border-box;"
            )

            # --- Determine CSS for the Children (Grid Items) ---
            # Applied via a descendant selector: .{css_class} > *
            # We use '*' assuming reconciler places direct children into the grid container
            child_aspect_ratio_style = f"aspect-ratio: {childAspectRatio};" if childAspectRatio else ""
            # Ensure children handle potential overflow if their content is too big
            child_overflow_style = "overflow: hidden;" # Simple default, might need configuration

            child_styles = (
                 f"{child_aspect_ratio_style} "
                 f"{child_overflow_style}"
                 # Other potential styles for all grid items?
                 # e.g., min-width: 0; min-height: 0; to prevent flexbox-like blowing out
                 "min-width: 0; min-height: 0;"
            )

            # --- Assemble the full CSS rule string ---
            # Rule for the GridView container itself
            container_rule = f".{css_class} {{ {container_styles} }}"
            # Rule for the direct children (grid items)
            child_rule = f".{css_class} > * {{ {child_styles} }}" # Target direct children

            return f"{container_rule}\n{child_rule}" # Return both rules

        except Exception as e:
            print(f"Error generating CSS for GridView {css_class} with key {style_key}: {e}")
            return f"/* Error generating rule for .{css_class} */"

    # Removed instance methods: to_html(), to_css()

# --- Stack Refactored ---
class Stack(Widget):
    """
    A widget that positions its children relative to the edges of its box,
    often overlapping them. Establishes a positioning context.
    Compatible with the reconciliation rendering system.
    """
    shared_styles: Dict[Tuple, str] = {}

    def __init__(self,
                 children: List[Widget],
                 key: Optional[Key] = None,
                 alignment=Alignment.top_left(), # How to align non-positioned children
                 textDirection=TextDirection.LTR,
                 fit=StackFit.loose, # How to size the stack itself
                 clipBehavior=ClipBehavior.HARD_EDGE, # Changed default to clip
                 # Overflow deprecated in Flutter, use clipBehavior instead
                 # overflow=Overflow.VISIBLE,
                 ):

        super().__init__(key=key, children=children)

        # Store properties
        self.alignment = alignment # Needs to map to CSS alignment for non-positioned items
        self.textDirection = textDirection
        self.fit = fit # Affects width/height rules
        self.clipBehavior = clipBehavior # Affects overflow/clip-path rules

        # --- CSS Class Management ---
        # Key includes properties affecting the Stack container's CSS
        self.style_key = (
            make_hashable(self.alignment),
            self.textDirection,
            self.fit,
            self.clipBehavior,
        )

        if self.style_key not in Stack.shared_styles:
            self.css_class = f"shared-stack-{len(Stack.shared_styles)}"
            Stack.shared_styles[self.style_key] = self.css_class
        else:
            self.css_class = Stack.shared_styles[self.style_key]

    def render_props(self) -> Dict[str, Any]:
        """Return properties for diffing."""
        props = {
            'alignment': self._get_render_safe_prop(self.alignment),
            'textDirection': self.textDirection,
            'fit': self.fit,
            'clipBehavior': self.clipBehavior,
            'css_class': self.css_class,
            # Children diffing handled separately
        }
        return {k: v for k, v in props.items() if v is not None}

    def get_required_css_classes(self) -> Set[str]:
        """Return the set of CSS class names needed."""
        return {self.css_class}

    @staticmethod
    def generate_css_rule(style_key: Tuple, css_class: str) -> str:
        """Static method callable by the Reconciler to generate the CSS rule."""
        try:
            # Unpack the style key
            alignment_repr, textDirection, fit, clipBehavior = style_key

            # --- Determine CSS ---
            # Base Stack style
            base_style = "position: relative; display: grid;" # Use grid for alignment

            # Sizing based on fit
            size_style = ""
            if fit == StackFit.expand:
                 size_style = "width: 100%; height: 100%;" # Expand to fill parent
            elif fit == StackFit.loose:
                 size_style = "width: fit-content; height: fit-content;" # Size to children
            # passthrough is harder to map directly, often default grid behavior works

            # Alignment for non-positioned children (using grid alignment)
            # Assuming Alignment object maps roughly to justify-items/align-items
            # Need to reconstruct or access Alignment properties
            alignment_obj = alignment_repr # Assumes alignment_repr is the Alignment object
            alignment_style = ""
            if isinstance(alignment_obj, Alignment):
                 # Map Alignment(justify, align) to grid properties
                 # This mapping might need refinement based on Alignment definition
                 alignment_style = f"justify-items: {getattr(alignment_obj, 'justify_content', 'start')}; align-items: {getattr(alignment_obj, 'align_items', 'start')};"
            else: # Fallback
                 alignment_style = "justify-items: start; align-items: start;"


            # Text Direction
            direction_style = f"direction: {textDirection};"

            # Clipping behavior
            clip_style = ""
            if clipBehavior == ClipBehavior.HARD_EDGE:
                clip_style = "overflow: hidden;"
            # ANTI_ALIAS might just be overflow: hidden; unless specific clipping needed
            # ANTI_ALIAS_WITH_SAVE_LAYER has no direct CSS equivalent easily.
            elif clipBehavior != ClipBehavior.NONE:
                 clip_style = "overflow: hidden;" # Default clipping

            # Combine styles
            styles = (
                f"{base_style} "
                f"{size_style} "
                f"{alignment_style} "
                f"{direction_style} "
                f"{clip_style}"
            )

            # Rule for the Stack container
            container_rule = f".{css_class} {{ {styles} }}"

            # Rule to make direct children occupy the same grid cell for stacking/alignment
            child_rule = f".{css_class} > * {{ grid-area: 1 / 1; }}" # Place all children in the first cell

            return f"{container_rule}\n{child_rule}"

        except Exception as e:
            print(f"Error generating CSS for Stack {css_class} with key {style_key}: {e}")
            return f"/* Error generating rule for .{css_class} */"

    # Removed instance methods: to_html(), to_css()


# --- Positioned Refactored ---
class Positioned(Widget):
    """
    Controls the position of a child within a Stack.
    Applies absolute positioning styles. Not a shared style component.
    """
    def __init__(self,
                 child: Widget, # Requires exactly one child
                 key: Optional[Key] = None,
                 top: Optional[Union[int, float, str]] = None, # Allow px, %, etc. later?
                 right: Optional[Union[int, float, str]] = None,
                 bottom: Optional[Union[int, float, str]] = None,
                 left: Optional[Union[int, float, str]] = None,
                 width: Optional[Union[int, float, str]] = None, # Allow specifying size too
                 height: Optional[Union[int, float, str]] = None):

        if not child:
             raise ValueError("Positioned widget requires a child.")
        # Positioned itself doesn't render, it modifies its child's wrapper
        # The child is the only element in its children list
        super().__init__(key=key, children=[child])

        self.child = child # Keep direct reference
        # Store positioning properties
        self.top = top
        self.right = right
        self.bottom = bottom
        self.left = left
        self.width = width
        self.height = height

    def render_props(self) -> Dict[str, Any]:
        """
        Return positioning properties. These will be used by the reconciler
        to apply inline styles or specific classes to the child's wrapper element.
        """
        props = {
            'position_type': 'absolute', # Indicate the required styling type
            'top': self.top,
            'right': self.right,
            'bottom': self.bottom,
            'left': self.left,
            'width': self.width,
            'height': self.height,
            # No css_class needed as styling is direct/instance-specific
        }
        # Pass non-None values
        return {k: v for k, v in props.items() if v is not None}

    def get_required_css_classes(self) -> Set[str]:
        """Positioned doesn't use shared CSS classes."""
        return set()

    # No generate_css_rule needed

    # Removed instance methods: to_html()


# --- Expanded Refactored ---
class Expanded(Widget):
    """
    Expands a child of a Row or Column to fill the available space along the main axis.
    Applies flexbox grow/shrink styles. Not a shared style component.
    """
    def __init__(self,
                 child: Widget, # Requires exactly one child
                 key: Optional[Key] = None,
                 flex: int = 1): # The flex-grow factor

        if not child:
             raise ValueError("Expanded widget requires a child.")
        super().__init__(key=key, children=[child])

        self.child = child # Keep direct reference
        self.flex = max(0, flex) # Ensure flex factor is non-negative

    def render_props(self) -> Dict[str, Any]:
        """
        Return flex property. Used by reconciler to apply inline styles
        or specific classes to the child's wrapper.
        """
        props = {
            'position_type': 'flex', # Indicate the required styling type
            'flex_grow': self.flex,
            'flex_shrink': 1, # Default shrink factor
            'flex_basis': '0%', # Allow grow/shrink from 0 basis
            # Might also need width/height 100% depending on cross-axis stretch
            'width': 'auto', # Let flexbox control main axis size
            'height': 'auto', # Let flexbox control main axis size
            # No css_class needed
        }
        return props

    def get_required_css_classes(self) -> Set[str]:
        """Expanded doesn't use shared CSS classes."""
        return set()

    # No generate_css_rule needed

    # Removed instance methods: to_html()

# --- Spacer Refactored ---
class Spacer(Widget):
    """
    Creates flexible empty space between widgets in a flex container (Row/Column).
    Applies flex-grow styles. Not a shared style component.
    """
    def __init__(self, flex: int = 1, key: Optional[Key] = None):
        # Spacer has no children
        super().__init__(key=key, children=[])
        self.flex = max(0, flex) # Ensure non-negative flex factor

    # No children methods needed beyond base class default (returns empty list)

    def render_props(self) -> Dict[str, Any]:
        """
        Return flex property. Used by reconciler to apply inline styles.
        """
        props = {
            'position_type': 'flex', # Indicate flex styling needed
            'flex_grow': self.flex,
            'flex_shrink': 0, # Spacer typically shouldn't shrink
            'flex_basis': '0%', # Grow from zero basis
            # Set min size to 0 to allow it to collapse if flex is 0
            'min_width': 0,
            'min_height': 0,
            # No css_class needed
        }
        return props

    def get_required_css_classes(self) -> Set[str]:
        """Spacer doesn't use shared CSS classes."""
        return set()

    # No generate_css_rule needed

    # Removed instance methods: to_html(), widget_id() (use base ID logic)


# --- SizedBox Refactored ---
class SizedBox(Widget):
    """
    Creates empty space with a fixed width and/or height.
    Applies direct size styles. Not a shared style component.
    """
    # Could potentially use shared styles if many identical sizes are common,
    # but direct styling is often simpler for this widget. Let's stick with direct.

    def __init__(self,
                 key: Optional[Key] = None,
                 height: Optional[Union[int, float, str]] = None,
                 width: Optional[Union[int, float, str]] = None):
        # SizedBox has no children
        super().__init__(key=key, children=[])
        self.height = height
        self.width = width

    # No children methods needed beyond base class default

    def render_props(self) -> Dict[str, Any]:
        """
        Return width/height properties for direct styling.
        """
        props = {
            'render_type': 'sized_box', # Indicate specific handling if needed
            'height': self.height,
            'width': self.width,
            # No css_class needed
        }
        return {k: v for k, v in props.items() if v is not None} # Filter None

    def get_required_css_classes(self) -> Set[str]:
        """SizedBox doesn't use shared CSS classes."""
        return set()

    # No generate_css_rule needed

    # Removed instance methods: to_html(), widget_id() (use base ID logic)

class AppBar(Widget):
    """
    A Material Design app bar, consisting of a toolbar and potentially other
    widgets like a TabBar and FlexibleSpaceBar.
    Compatible with the reconciliation rendering system.
    """
    shared_styles: Dict[Tuple, str] = {} # Class variable for shared CSS

    def __init__(self,
                 key: Optional[Key] = None,
                 # Content Widgets
                 leading: Optional[Widget] = None,
                 title: Optional[Widget] = None,
                 actions: Optional[List[Widget]] = None,
                 bottom: Optional[Widget] = None, # e.g., TabBar
                 # Style Properties
                 backgroundColor: Optional[str] = None, # Typically uses theme color
                 foregroundColor: Optional[str] = None, # Color for title/icons
                 elevation: Optional[float] = 4.0, # Default elevation
                 shadowColor: Optional[str] = Colors.rgba(0,0,0,0.2),
                 # Layout Properties
                 centerTitle: bool = False,
                 titleSpacing: Optional[float] = None, # Defaults usually handled by CSS/theme
                 toolbarHeight: Optional[float] = 56.0, # Common default height
                 leadingWidth: Optional[float] = None, # Usually calculated
                 pinned: bool = False, # If the app bar stays at the top when scrolling
                 ):

        # Collect children - order might matter for layout/semantics
        children = []
        if leading: children.append(leading)
        if title: children.append(title)
        if actions: children.extend(actions)
        if bottom: children.append(bottom) # Added bottom as a child

        super().__init__(key=key, children=children)

        # Store direct references and properties
        self.leading = leading
        self.title = title
        self.actions = actions or []
        self.bottom = bottom # Widget appearing below the main toolbar section
        self.backgroundColor = backgroundColor
        self.foregroundColor = foregroundColor
        self.elevation = elevation
        self.shadowColor = shadowColor
        self.centerTitle = centerTitle
        self.titleSpacing = titleSpacing # Spacing around the title
        self.toolbarHeight = toolbarHeight
        self.leadingWidth = leadingWidth
        self.pinned = pinned # Affects position: sticky/fixed

        # --- CSS Class Management ---
        # Key includes properties affecting the main AppBar container's CSS
        self.style_key = (
            self.backgroundColor,
            self.foregroundColor,
            self.elevation,
            self.shadowColor,
            self.toolbarHeight,
            self.pinned,
            # Note: centerTitle, titleSpacing, leadingWidth affect child layout,
            # handled via props/descendant CSS, not usually the main class key.
        )

        if self.style_key not in AppBar.shared_styles:
            self.css_class = f"shared-appbar-{len(AppBar.shared_styles)}"
            AppBar.shared_styles[self.style_key] = self.css_class
        else:
            self.css_class = AppBar.shared_styles[self.style_key]

    def render_props(self) -> Dict[str, Any]:
        """Return properties for diffing and layout control by the Reconciler."""
        props = {
            # Style props passed for potential direct patching if needed
            'backgroundColor': self.backgroundColor,
            'foregroundColor': self.foregroundColor,
            'elevation': self.elevation,
            'shadowColor': self.shadowColor,
            'toolbarHeight': self.toolbarHeight,
            'pinned': self.pinned,
            # Layout control props for reconciler/CSS
            'centerTitle': self.centerTitle,
            'titleSpacing': self.titleSpacing,
            'leadingWidth': self.leadingWidth,
            # The main CSS class
            'css_class': self.css_class,
            # Indicate if specific child slots are present for reconciler logic
            'has_leading': bool(self.leading),
            'has_title': bool(self.title),
            'has_actions': bool(self.actions),
            'has_bottom': bool(self.bottom),
        }
        return {k: v for k, v in props.items() if v is not None}

    def get_required_css_classes(self) -> Set[str]:
        """Return the set of CSS class names needed."""
        return {self.css_class}

    @staticmethod
    def generate_css_rule(style_key: Tuple, css_class: str) -> str:
        """Static method callable by the Reconciler to generate the CSS rule(s)."""
        try:
            # Unpack the style key
            (backgroundColor, foregroundColor, elevation, shadowColor,
             toolbarHeight, pinned) = style_key

            # --- Base AppBar Container Styles ---
            # Use flexbox for the main toolbar layout
            base_styles = (
                f"display: flex; "
                f"flex-direction: column; " # Stack main toolbar and bottom sections
                f"padding: 0; " # Usually no padding on the main container itself
                f"box-sizing: border-box; "
                f"width: 100%; "
                f"background-color: {backgroundColor or '#6200ee'}; " # Default color
                f"color: {foregroundColor or 'white'}; " # Default text/icon color
                f"z-index: 100; " # Ensure it's above content
            )

            # Elevation / Shadow
            shadow_style = ""
            if elevation and elevation > 0:
                 # Simple shadow, adjust as needed
                 offset_y = min(max(1, elevation), 6) # Example mapping elevation to Y offset
                 blur = offset_y * 2
                 spread = 0
                 shadow_style = f"box-shadow: 0 {offset_y}px {blur}px {spread}px {shadowColor or 'rgba(0,0,0,0.2)'};"
            base_styles += shadow_style

            # Pinned behavior
            position_style = "position: relative;"
            if pinned:
                 # Sticky is often preferred over fixed to interact with scrolling parent
                 position_style = "position: sticky; top: 0; "
            base_styles += position_style

            # --- Toolbar Row Styles (for leading, title, actions) ---
            # This will style a wrapper div created by the reconciler
            toolbar_row_styles = (
                 f"display: flex; "
                 f"align-items: center; "
                 f"height: {toolbarHeight or 56}px; "
                 f"padding: 0 16px; " # Default horizontal padding
            )

            # --- Child Wrapper Styles ---
            # These style wrapper divs created by the reconciler around specific children
            leading_styles = "flex-shrink: 0; margin-right: 16px;" # Prevent shrinking, add margin
            title_styles = "flex-grow: 1; text-align: left; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" # Grow, truncate
            center_title_styles = "text-align: center;" # Override for centered title
            actions_styles = "flex-shrink: 0; margin-left: auto; display: flex; align-items: center;" # Push to right, align items

            # --- Bottom Section Styles ---
            # Styles a wrapper div created by the reconciler if bottom exists
            bottom_styles = "width: 100%;" # Bottom usually spans full width

            # --- Assemble CSS Rules ---
            rules = [
                f".{css_class} {{ {base_styles} }}",
                # Styles for the *internal wrapper* div holding the toolbar items
                f".{css_class} > .appbar-toolbar-row {{ {toolbar_row_styles} }}",
                # Styles for wrappers around specific child slots
                f".{css_class} .appbar-leading {{ {leading_styles} }}",
                f".{css_class} .appbar-title {{ {title_styles} }}",
                f".{css_class} .appbar-title.centered {{ {center_title_styles} }}", # Specific class if centered
                f".{css_class} .appbar-actions {{ {actions_styles} }}",
                f".{css_class} .appbar-bottom {{ {bottom_styles} }}",
                # Ensure direct children of actions are spaced if needed (e.g., buttons)
                f".{css_class} .appbar-actions > * {{ margin-left: 8px; }}",
                f".{css_class} .appbar-actions > *:first-child {{ margin-left: 0; }}",
            ]

            return "\n".join(rules)

        except Exception as e:
            print(f"Error generating CSS for AppBar {css_class} with key {style_key}: {e}")
            return f"/* Error generating rule for .{css_class} */"

    # Removed instance methods: to_html(), to_css()

# --- BottomNavigationBarItem Refactored ---
class BottomNavigationBarItem(Widget):
    """
    Represents an item (icon and label) within a BottomNavigationBar.
    Receives its selected state and styling information from the parent.
    """
    # No shared styles needed if styling is mainly based on parent context + selected state
    # But we might add classes for structure: e.g., 'bnb-item', 'bnb-item-icon', 'bnb-item-label'

    def __init__(self,
                 icon: Widget, # The Icon widget
                 label: Optional[Widget] = None, # Optional Text widget for the label
                 key: Optional[Key] = None, # Key for reconciliation if items reorder
                 # Props typically set by the parent BottomNavigationBar:
                 selected: bool = False,
                 selectedColor: Optional[str] = None,
                 unselectedColor: Optional[str] = None,
                 iconSize: Optional[int] = None,
                 selectedFontSize: Optional[int] = None,
                 unselectedFontSize: Optional[int] = None,
                 showSelectedLabel: bool = True,
                 showUnselectedLabel: bool = True,
                 item_index: Optional[int] = None, # Index passed by parent for tap handling
                 parent_onTapName: Optional[str] = None # Callback name passed by parent
                 ):

        # Children are the icon and potentially the label
        children = [icon]
        if label and ((selected and showSelectedLabel) or (not selected and showUnselectedLabel)):
             # Only include label in children list if it should be shown
             children.append(label)

        super().__init__(key=key, children=children)

        self.icon_widget = icon # Keep references
        self.label_widget = label

        # Store state/style props passed from parent
        self.selected = selected
        self.selectedColor = selectedColor
        self.unselectedColor = unselectedColor
        self.iconSize = iconSize
        self.selectedFontSize = selectedFontSize
        self.unselectedFontSize = unselectedFontSize
        self.showSelectedLabel = showSelectedLabel
        self.showUnselectedLabel = showUnselectedLabel
        self.item_index = item_index
        self.parent_onTapName = parent_onTapName

        # --- CSS Class ---
        # Use structural classes, potentially modified by selected state
        self.base_css_class = "bnb-item"
        self.css_class = f"{self.base_css_class} {'selected' if self.selected else ''}"

    def render_props(self) -> Dict[str, Any]:
        """Pass data needed for the reconciler to patch attributes/styles."""
        props = {
            'css_class': self.css_class,
            'selected': self.selected,
            # Pass data needed for the click handler
            'item_index': self.item_index,
            'onTapName': self.parent_onTapName,
            # Pass styling information if reconciler needs to apply inline overrides
            # (preferable to handle via CSS classes: .bnb-item.selected)
            'current_color': self.selectedColor if self.selected else self.unselectedColor,
            'current_font_size': self.selectedFontSize if self.selected else self.unselectedFontSize,
            'show_label': (self.selected and self.showSelectedLabel) or (not self.selected and self.showUnselectedLabel),
        }
        # Note: We don't return icon/label widgets here, reconciler handles children
        return {k: v for k, v in props.items() if v is not None}

    def get_required_css_classes(self) -> Set[str]:
        """Return structural classes. Selection handled by reconciler adding/removing 'selected'."""
        # The reconciler should add/remove 'selected' class based on props.
        # The static CSS below defines rules for both .bnb-item and .bnb-item.selected
        return {self.base_css_class} # Only need the base class here

    @staticmethod
    def generate_css_rule(style_key: Tuple, css_class: str) -> str:
        """
        Generates CSS for the item structure and selected state.
        NOTE: This assumes style_key might hold parent BNV config like colors/sizes.
        However, a simpler approach is to pass these down via props and use more
        direct CSS rules without complex shared classes for the *item* itself.
        Let's define structural CSS directly.
        """
        # We won't use shared_styles for Item itself, styling is contextual.
        # Return CSS defining the structure and selected state for ALL items.
        # The key/class passed here might be unused if we define general rules.

        # Example: Get defaults from style_key if it contained them
        # parent_selectedColor, parent_unselectedColor, iconSize, ... = style_key
        # Or use hardcoded M3-like defaults here:
        selected_color = Colors.primary or '#005AC1' # M3 Primary
        unselected_color = Colors.onSurfaceVariant or '#49454F' # M3 On Surface Variant
        label_selected_size = 12 # M3 Label Medium
        label_unselected_size = 11 # M3 Label Small
        icon_size = 24 # M3 default icon size

        return f"""
        .bnb-item {{
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center; /* Center icon/label vertically */
            flex: 1; /* Distribute space equally */
            padding: 8px 0px 12px 0px; /* M3 vertical padding */
            gap: 4px; /* M3 space between icon and label */
            min-width: 40px; /* Minimum touch target */
            cursor: pointer;
            position: relative; /* For potential indicator positioning */
            overflow: hidden; /* Clip indicator/ripple */
            -webkit-tap-highlight-color: transparent; /* Remove tap highlight */
        }}
        .bnb-item .bnb-icon-container {{ /* Wrapper for icon + indicator */
             position: relative;
             display: flex; /* Needed for indicator */
             align-items: center;
             justify-content: center;
             width: 64px; /* M3 indicator width */
             height: 32px; /* M3 indicator height */
             border-radius: 16px; /* M3 indicator pill shape */
             margin-bottom: 4px; /* Adjusted gap */
             transition: background-color 0.2s ease-in-out; /* Indicator transition */
        }}
         .bnb-item .bnb-icon {{ /* Styles for the icon itself */
             color: {unselected_color};
             font-size: {icon_size}px;
             width: {icon_size}px;
             height: {icon_size}px;
             display: block;
             transition: color 0.2s ease-in-out;
             z-index: 1; /* Keep icon above indicator background */
        }}
        .bnb-item .bnb-label {{
             color: {unselected_color};
             font-size: {label_unselected_size}px;
             /* TODO: Apply M3 Label Small/Medium font weights/styles */
             font-weight: 500;
             line-height: 16px;
             text-align: center;
             transition: color 0.2s ease-in-out, font-size 0.2s ease-in-out;
        }}

        /* --- Selected State --- */
        .bnb-item.selected .bnb-icon-container {{
            background-color: {Colors.secondaryContainer or '#D7E3FF'}; /* M3 Indicator background */
        }}
        .bnb-item.selected .bnb-icon {{
            color: {Colors.onSecondaryContainer or '#001B3E'}; /* M3 Icon color on indicator */
            /* Or use selected_color if passed */
        }}
         .bnb-item.selected .bnb-label {{
            color: {Colors.onSurface or '#1C1B1F'}; /* M3 Label color when selected */
            font-size: {label_selected_size}px;
             /* TODO: Apply M3 Label Medium font weights/styles */
        }}
        """
    # Removed instance methods: to_html()


# --- BottomNavigationBar Refactored ---
class BottomNavigationBar(Widget):
    """
    Displays navigation items at the bottom of the screen.
    Compatible with the reconciliation rendering system.
    """
    shared_styles: Dict[Tuple, str] = {}

    def __init__(self,
                 items: List[BottomNavigationBarItem],
                 key: Optional[Key] = None,
                 # State handled by parent:
                 currentIndex: int = 0,
                 onTap: Optional[Callable[[int], None]] = None, # Callback function in parent state
                 onTapName: Optional[str] = None, # Explicit name for the callback
                 # Styling properties
                 backgroundColor: Optional[str] = None, # M3 Surface Container
                 foregroundColor: Optional[str] = None, # M3 On Surface (rarely needed directly)
                 elevation: Optional[float] = 2.0, # M3 Elevation Level 2
                 shadowColor: Optional[str] = Colors.rgba(0,0,0,0.15), # M3 Shadow color (approx)
                 height: Optional[float] = 80.0, # M3 default height
                 # Item styling defaults (passed down to items)
                 selectedItemColor: Optional[str] = None, # M3 Primary / On Secondary Container
                 unselectedItemColor: Optional[str] = None, # M3 On Surface Variant
                 iconSize: int = 24, # M3 default
                 selectedFontSize: int = 12, # M3 Label Medium
                 unselectedFontSize: int = 11, # M3 Label Small
                 showSelectedLabels: bool = True,
                 showUnselectedLabels: bool = True,
                 # fixedColor: Optional[str] = None, # Deprecated/Less common
                 # landscapeLayout="centered" # Layout complex, handle with CSS media queries if needed
                 ):

        # --- Process Items: Inject state and styling props ---
        self.item_widgets = []
        actual_onTapName = onTapName if onTapName else (onTap.__name__ if onTap else None)
        if onTap and not actual_onTapName:
             print("Warning: BottomNavigationBar onTap provided without a usable name for JS.")

        for i, item in enumerate(items):
            if not isinstance(item, BottomNavigationBarItem):
                print(f"Warning: Item at index {i} is not a BottomNavigationBarItem, skipping.")
                continue

            is_selected = (i == currentIndex)
            # Create a *new* instance or *modify* the existing one with current props
            # Modifying is complex with immutability/rebuilds. Creating new is safer for reconciliation.
            processed_item = BottomNavigationBarItem(
                key=item.key or Key(f"bnb_item_{i}"), # Ensure key exists
                icon=item.icon_widget, # Pass original icon widget
                label=item.label_widget, # Pass original label widget
                # --- Props passed down ---
                selected=is_selected,
                selectedColor=selectedItemColor,
                unselectedColor=unselectedItemColor,
                iconSize=iconSize,
                selectedFontSize=selectedFontSize,
                unselectedFontSize=unselectedFontSize,
                showSelectedLabel=showSelectedLabels,
                showUnselectedLabel=showUnselectedLabels,
                item_index=i, # Pass index for click handling
                parent_onTapName=actual_onTapName # Pass callback name
            )
            self.item_widgets.append(processed_item)

        # Pass the *processed* items with injected state to the base Widget
        super().__init__(key=key, children=self.item_widgets)

        # Store own properties
        self.backgroundColor = backgroundColor
        self.foregroundColor = foregroundColor # Store if needed for direct text etc.
        self.elevation = elevation
        self.shadowColor = shadowColor
        self.height = height
        self.onTapName = actual_onTapName # Store the name to pass to props

        # --- CSS Class Management ---
        # Key includes properties affecting the main container's CSS
        self.style_key = (
            self.backgroundColor,
            self.elevation,
            self.shadowColor,
            self.height,
        )

        if self.style_key not in BottomNavigationBar.shared_styles:
            self.css_class = f"shared-bottomnav-{len(BottomNavigationBar.shared_styles)}"
            BottomNavigationBar.shared_styles[self.style_key] = self.css_class
             # Register callback centrally (Framework approach preferred)
             # if onTap and self.onTapName:
             #      Api().register_callback(self.onTapName, onTap)
        else:
            self.css_class = BottomNavigationBar.shared_styles[self.style_key]

    def render_props(self) -> Dict[str, Any]:
        """Return properties for diffing."""
        props = {
            'backgroundColor': self.backgroundColor,
            'elevation': self.elevation,
            'shadowColor': self.shadowColor,
            'height': self.height,
            'css_class': self.css_class,
            'onTapName': self.onTapName, # Pass name for potential event delegation setup
            # Children diffing handled separately
        }
        return {k: v for k, v in props.items() if v is not None}

    def get_required_css_classes(self) -> Set[str]:
        """Return the set of CSS class names needed."""
        # Also include item base class if its CSS is generated here (less ideal)
        return {self.css_class, "bnb-item"} # Include item base class name

    @staticmethod
    def generate_css_rule(style_key: Tuple, css_class: str) -> str:
        """Static method callable by the Reconciler to generate the CSS rule(s)."""
        try:
            # Unpack the style key
            (backgroundColor, elevation, shadowColor, height) = style_key

            # --- Base BottomNavigationBar Container Styles ---
            # M3 uses Surface Container color role
            bg_color = backgroundColor or Colors.surfaceContainer or '#F3EDF7'
            # M3 Elevation Level 2 shadow (approximate)
            shadow_str = ""
            if elevation and elevation >= 2:
                 shadow_str = f"box-shadow: 0px 1px 3px 1px {shadowColor or 'rgba(0, 0, 0, 0.15)'}, 0px 1px 2px 0px {shadowColor or 'rgba(0, 0, 0, 0.3)'};"
            elif elevation and elevation > 0: # Level 1 approx
                 shadow_str = f"box-shadow: 0px 1px 3px 0px {shadowColor or 'rgba(0, 0, 0, 0.3)'}, 0px 1px 1px 0px {shadowColor or 'rgba(0, 0, 0, 0.15)'};"


            styles = (
                f"display: flex; "
                f"flex-direction: row; "
                f"justify-content: space-around; " # Distribute items
                f"align-items: stretch; " # Stretch items vertically
                f"height: {height or 80}px; " # M3 default height
                f"width: 100%; "
                f"background-color: {bg_color}; "
                f"position: fixed; " # Usually fixed at bottom
                f"bottom: 0; "
                f"left: 0; "
                f"right: 0; "
                f"{shadow_str} "
                f"box-sizing: border-box; "
                f"z-index: 100; " # Ensure visibility
            )

            # Generate rule for the main container
            container_rule = f".{css_class} {{ {styles} }}"

            # --- Generate Item Rules ---
            # Call the static method of BottomNavigationBarItem to get its rules
            # Pass relevant defaults from BNV style_key if needed by Item's CSS
            # This assumes Item's generate_css_rule doesn't need complex key
            item_rules = BottomNavigationBarItem.generate_css_rule(None, "bnb-item") # Use base class name

            return f"{container_rule}\n{item_rules}" # Combine container and item rules

        except Exception as e:
            print(f"Error generating CSS for BottomNavigationBar {css_class} with key {style_key}: {e}")
            return f"/* Error generating rule for .{css_class} */"

    # Removed instance methods: to_html(), to_css()

class Scaffold(Widget):
    """
    Implements the basic visual layout structure based on Material Design.
    Manages AppBar, Body, Drawers, BottomNavigationBar, FAB, etc.
    Compatible with the reconciliation rendering system.
    """
    shared_styles: Dict[Tuple, str] = {} # For Scaffold container styles

    def __init__(self,
                 key: Optional[Key] = None,
                 # --- Content Slots ---
                 appBar: Optional[AppBar] = None,
                 body: Optional[Widget] = None,
                 floatingActionButton: Optional[Widget] = None, # Often FAB widget
                 bottomNavigationBar: Optional[BottomNavigationBar] = None,
                 drawer: Optional[Widget] = None, # Often Drawer widget
                 endDrawer: Optional[Widget] = None,
                 bottomSheet: Optional[Widget] = None, # TODO: Handle rendering/interaction
                 persistentFooterButtons: Optional[List[Widget]] = None, # TODO: Handle rendering/layout
                 snackBar: Optional[Widget] = None, # TODO: Handle rendering/positioning
                 # --- Styling & Behavior ---
                 backgroundColor: Optional[str] = None, # M3 Surface Color Role
                 extendBody: bool = False, # Body draws under BottomNav
                 extendBodyBehindAppBar: bool = False, # Body draws under AppBar
                 drawerScrimColor: Optional[str] = Colors.rgba(0, 0, 0, 0.4), # M3 Scrim color (approx)
                 # resizeToAvoidBottomInset: bool = True, # Handled by browser/CSS usually
                 # --- Drawer Control (Data passed, interaction handled by Drawer widget itself) ---
                 # drawerDragStartBehavior=None,
                 # drawerEdgeDragWidth=None,
                 # drawerEnableOpenDragGesture=True,
                 # endDrawerEnableOpenDragGesture=True,
                 # onDrawerChanged=None, # Callbacks handled by Drawer widget's onPressed etc.
                 # onEndDrawerChanged=None,
                 # --- Persistent Footer (Simplified) ---
                 # persistentFooterAlignment=MainAxisAlignment.CENTER,
                 # --- Other ---
                 # primary: bool = True, # Less relevant for scaffold container itself
                 ):

        # Collect children that are directly part of the main layout flow
        # Drawers, FAB, Snackbar, BottomSheet often overlay or are positioned fixed/absolute
        # Let's pass only the body conceptually, others handled by reconciler based on slots
        layout_children = [body] if body else []
        super().__init__(key=key, children=layout_children) # Pass key, body is main child

        # Store references to slot widgets
        self.appBar = appBar
        self.body = body
        self.floatingActionButton = floatingActionButton
        self.bottomNavigationBar = bottomNavigationBar
        self.drawer = drawer
        self.endDrawer = endDrawer
        self.bottomSheet = bottomSheet # TODO: Implement rendering
        self.persistentFooterButtons = persistentFooterButtons or [] # TODO: Implement rendering
        self.snackBar = snackBar # TODO: Implement rendering

        # Store properties affecting layout/style
        self.backgroundColor = backgroundColor # M3 Surface
        self.extendBody = extendBody
        self.extendBodyBehindAppBar = extendBodyBehindAppBar
        self.drawerScrimColor = drawerScrimColor

        # --- CSS Class Management ---
        # Key includes properties affecting the main scaffold container's CSS
        self.style_key = (
            self.backgroundColor,
            # Add other top-level style props if they directly affect the container CSS class
        )

        if self.style_key not in Scaffold.shared_styles:
            self.css_class = f"shared-scaffold-{len(Scaffold.shared_styles)}"
            Scaffold.shared_styles[self.style_key] = self.css_class
        else:
            self.css_class = Scaffold.shared_styles[self.style_key]

    def render_props(self) -> Dict[str, Any]:
        """Return properties for the Reconciler."""
        props = {
            'css_class': self.css_class,
            'backgroundColor': self.backgroundColor,
            'extendBody': self.extendBody,
            'extendBodyBehindAppBar': self.extendBodyBehindAppBar,
            'drawerScrimColor': self.drawerScrimColor,
            # Flags indicating which slots are filled (Reconciler uses these)
            'has_appBar': bool(self.appBar),
            'has_body': bool(self.body),
            'has_floatingActionButton': bool(self.floatingActionButton),
            'has_bottomNavigationBar': bool(self.bottomNavigationBar),
            'has_drawer': bool(self.drawer),
            'has_endDrawer': bool(self.endDrawer),
            'has_bottomSheet': bool(self.bottomSheet),
            'has_snackBar': bool(self.snackBar),
            'has_persistentFooterButtons': bool(self.persistentFooterButtons),
        }
        return {k: v for k, v in props.items() if v is not None}

    def get_required_css_classes(self) -> Set[str]:
        """Return the set of CSS class names needed."""
        return {self.css_class} # Only the main container class

    @staticmethod
    def generate_css_rule(style_key: Tuple, css_class: str) -> str:
        """
        Static method for Reconciler. Generates CSS for the Scaffold layout structure
        using descendant selectors based on the main css_class.
        """
        try:
            # Unpack the style key
            (backgroundColor,) = style_key

            # --- M3 Color Roles (Defaults) ---
            bg_color = backgroundColor or Colors.surface or '#FFFBFE' # M3 Surface
            scrim_color = Colors.rgba(0, 0, 0, 0.4) # Approx M3 Scrim

            # --- Base Scaffold Container Styles ---
            # Using CSS Grid for main layout (AppBar, Body, BottomNav) seems robust
            container_styles = f"""
                display: grid;
                grid-template-rows: auto 1fr auto; /* AppBar, Body (flexible), BottomNav */
                grid-template-columns: 100%; /* Single column */
                height: 100vh; /* Fill viewport height */
                width: 100vw; /* Fill viewport width */
                overflow: hidden; /* Prevent body scrollbars, body scrolls internally */
                position: relative; /* Context for drawers, FABs etc. */
                background-color: {bg_color};
                box-sizing: border-box;
            """

            # --- Slot Wrapper Styles (Targeted by Reconciler) ---
            appbar_styles = "grid-row: 1; grid-column: 1; position: relative; z-index: 10;" # Place in first row
            body_styles = "grid-row: 2; grid-column: 1; overflow: auto; position: relative; z-index: 1;" # Place in second row, allow scroll
            # Add padding to body to avoid appbar/bottomnav unless extended
            body_padding_styles = "padding-top: var(--appbar-height, 56px); padding-bottom: var(--bottomnav-height, 80px);"
            body_padding_extend_appbar = "padding-top: 0;"
            body_padding_extend_bottomnav = "padding-bottom: 0;"

            bottomnav_styles = "grid-row: 3; grid-column: 1; position: relative; z-index: 10;" # Place in third row

            # --- Drawer Styles ---
            drawer_base = f"""
                position: fixed; /* Fixed relative to viewport */
                top: 0;
                bottom: 0;
                width: 300px; /* Default width, Drawer widget can override */
                max-width: 80%;
                background-color: {Colors.surfaceContainerHigh or '#ECE6F0'}; /* M3 Surface Container High */
                z-index: 1000; /* Above app content, below scrim */
                transition: transform 0.3s cubic-bezier(0.4, 0.0, 0.2, 1); /* M3 Standard Easing */
                box-shadow: 0 8px 10px -5px rgba(0,0,0,0.2), /* M3 Elevation */
                            0 16px 24px 2px rgba(0,0,0,0.14),
                            0 6px 30px 5px rgba(0,0,0,0.12);
                overflow-y: auto; /* Allow drawer content to scroll */
            """
            drawer_left_closed = "transform: translateX(-105%);" # Start fully off-screen
            drawer_left_open = "transform: translateX(0);"
            drawer_right_closed = "transform: translateX(105%);"
            drawer_right_open = "transform: translateX(0);"

            # --- Scrim Styles ---
            scrim_styles = f"""
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background-color: {scrim_color};
                opacity: 0;
                visibility: hidden;
                transition: opacity 0.3s ease-in-out, visibility 0.3s;
                z-index: 900; /* Below drawer, above content */
            """
            scrim_active_styles = "opacity: 1; visibility: visible;"

            # --- Assemble Rules ---
            rules = [
                # Main Scaffold Container
                f".{css_class} {{ {container_styles} }}",
                # Slot Wrappers (Reconciler adds these classes)
                f".{css_class} > .scaffold-appbar {{ {appbar_styles} }}",
                f".{css_class} > .scaffold-body {{ {body_styles} }}",
                f".{css_class}:not(.extendBody) > .scaffold-body:not(.extendBodyBehindAppBar) {{ {body_padding_styles} }}",
                f".{css_class}.extendBodyBehindAppBar > .scaffold-body {{ {body_padding_extend_appbar} }}",
                f".{css_class}.extendBody > .scaffold-body {{ {body_padding_extend_bottomnav} }}",
                f".{css_class} > .scaffold-bottomnav {{ {bottomnav_styles} }}",
                 # Drawers (Reconciler adds these classes based on presence)
                f".{css_class} > .scaffold-drawer-left {{ {drawer_base} left: 0; {drawer_left_closed} }}",
                f".{css_class} > .scaffold-drawer-left.open {{ {drawer_left_open} }}",
                f".{css_class} > .scaffold-drawer-right {{ {drawer_base} right: 0; {drawer_right_closed} }}",
                f".{css_class} > .scaffold-drawer-right.open {{ {drawer_right_open} }}",
                # Scrim (Reconciler adds this element if drawers are present)
                f".{css_class} > .scaffold-scrim {{ {scrim_styles} }}",
                f".{css_class} > .scaffold-scrim.active {{ {scrim_active_styles} }}",
                # TODO: Add styles for FAB, SnackBar, BottomSheet positioning (likely fixed position)
            ]

            return "\n".join(rules)

        except Exception as e:
            print(f"Error generating CSS for Scaffold {css_class} with key {style_key}: {e}")
            return f"/* Error generating rule for .{css_class} */"

    # Removed instance methods: to_html(), to_css()        

class Divider(Widget):
    """
    A thin horizontal line, typically used to separate content.
    Compatible with the reconciliation rendering system. Styles applied directly.
    """
    # Could use shared_styles, but often simple enough for direct props/styling
    # shared_styles: Dict[Tuple, str] = {}

    def __init__(self,
                 key: Optional[Key] = None,
                 height: float = 1, # Usually 1px high
                 thickness: Optional[float] = None, # Flutter uses thickness for line, height for space
                 indent: Optional[float] = 0, # Space before the line
                 endIndent: Optional[float] = 0, # Space after the line
                 margin: Optional[EdgeInsets] = None, # Space above/below (use instead of height?)
                 color: Optional[str] = None # M3 Outline Variant
                 ):

        # Divider has no children
        super().__init__(key=key, children=[])

        # Store properties
        # Map Flutter-like names to CSS concepts where needed
        self.height_prop = height # This Flutter prop often represents vertical space, use margin instead
        self.thickness = thickness if thickness is not None else 1.0 # Actual line thickness
        self.indent = indent
        self.endIndent = endIndent
        self.margin = margin # EdgeInsets for vertical spacing is clearer than 'height'
        self.color = color or Colors.outlineVariant or '#CAC4D0' # M3 Outline Variant

        # No shared CSS class needed if styles are applied directly by reconciler

    def render_props(self) -> Dict[str, Any]:
        """Return properties for styling by the Reconciler."""
        # Convert layout props into CSS-friendly values if possible
        css_margin = None
        if isinstance(self.margin, EdgeInsets):
             css_margin = self.margin.to_css()
        elif self.height_prop is not None and self.height_prop > 0: # Fallback using height for margin
             css_margin = f"{self.height_prop / 2.0}px 0" # Approximate vertical margin

        props = {
            'render_type': 'divider', # Help reconciler identify
            'height': self.thickness, # CSS height controls line thickness
            'color': self.color,      # CSS background-color for the line
            'margin': css_margin,     # Use margin for vertical spacing
            # Use padding on the container for indent/endIndent
            'padding_left': self.indent,
            'padding_right': self.endIndent,
            # No css_class
        }
        # Filter out None values before returning
        return {k: v for k, v in props.items() if v is not None}

    def get_required_css_classes(self) -> Set[str]:
        """Divider doesn't use shared CSS classes."""
        return set()

    # No generate_css_rule needed

    # Removed instance methods: to_html(), get_children(), remove_all_children()

class Drawer(Widget):
    """
    Represents the content panel displayed typically from the side edge (e.g., left) of a Scaffold.
    Its visibility is controlled externally (e.g., by Scaffold JS).
    Compatible with the reconciliation rendering system.
    """
    shared_styles: Dict[Tuple, str] = {} # For shared Drawer styling

    # Remove Singleton pattern (__new__) - Allow multiple instances

    def __init__(self,
                 child: Widget, # Drawer must have content
                 key: Optional[Key] = None,
                 # Styling Properties
                 width: int = 304, # M3 Default width
                 backgroundColor: Optional[str] = None, # M3 Surface Container High
                 elevation: Optional[float] = 1.0, # M3 Elevation Level 1 (when open)
                 shadowColor: Optional[str] = Colors.rgba(0,0,0,0.15), # Approx shadow
                 padding: Optional[EdgeInsets] = None, # Padding inside the drawer
                 # borderSide: Optional[BorderSide] = None, # Border between drawer/content? M3 uses shadow.
                 # divider: Optional[Widget] = None # Divider often placed inside child content
                 ):

        # Drawer usually has one main child (often a Column)
        super().__init__(key=key, children=[child])
        self.child = child # Keep reference if needed

        # Store styling properties
        self.width = width
        self.backgroundColor = backgroundColor or Colors.surfaceContainerHigh or '#ECE6F0'
        self.elevation = elevation
        self.shadowColor = shadowColor
        self.padding = padding # Reconciler will apply this if needed

        # --- CSS Class Management ---
        # Key includes properties affecting the Drawer container's base style
        # Note: Elevation/Shadow is often applied by the wrapper class (.scaffold-drawer-left)
        # So, the key might only need background and width? Let's include width for now.
        self.style_key = (
            self.backgroundColor,
            self.width,
            make_hashable(self.padding), # Include padding if it affects the main div style
            # Elevation/shadow managed by the .scaffold-drawer class generated by Scaffold
        )

        if self.style_key not in Drawer.shared_styles:
            self.css_class = f"shared-drawer-content-{len(Drawer.shared_styles)}" # Class for *content* styling
            Drawer.shared_styles[self.style_key] = self.css_class
        else:
            self.css_class = Drawer.shared_styles[self.style_key]

        # Removed self.is_open - state managed externally
        # Removed self.initialized flag

    def render_props(self) -> Dict[str, Any]:
        """Return properties for the Reconciler."""
        props = {
            'css_class': self.css_class, # For specific content styling if needed
            'backgroundColor': self.backgroundColor,
            'width': self.width, # Pass width for potential inline style override
            'padding': self._get_render_safe_prop(self.padding),
            # Note: Elevation/shadow are handled by the Scaffold's wrapper class for the drawer
            # Child diffing handled separately
        }
        return {k: v for k, v in props.items() if v is not None}

    def get_required_css_classes(self) -> Set[str]:
        """Return the set of CSS class names needed."""
        return {self.css_class} # Class for the drawer's content area

    @staticmethod
    def generate_css_rule(style_key: Tuple, css_class: str) -> str:
        """
        Static method for Reconciler. Generates CSS for the Drawer's inner content container.
        The main positioning, background, shadow, transition are handled by the
        `.scaffold-drawer-left/right` classes generated by Scaffold.
        This rule handles padding, potentially background inside the drawer.
        """
        try:
            # Unpack key
            backgroundColor, width, padding_repr = style_key # Adapt if key changes

            # This rule styles the element rendered *for the Drawer widget itself*,
            # which lives *inside* the .scaffold-drawer-left/right wrapper.
            padding_obj = padding_repr # Assumes usable representation
            padding_style = ""
            if isinstance(padding_obj, EdgeInsets):
                 padding_style = f"padding: {padding_obj.to_css()};"
            elif padding_repr:
                 padding_style = f"padding: {padding_repr};"

            # Background color might be redundant if set on the main wrapper,
            # but could be useful if the wrapper style is different.
            bg_style = f"background-color: {backgroundColor};" if backgroundColor else ""

            # Content container should fill height and allow scrolling internally if needed
            # Note: Outer wrapper (.scaffold-drawer-*) already has overflow: auto
            styles = (
                f"width: 100%; " # Fill the width provided by the outer wrapper
                f"height: 100%; " # Fill the height
                f"{padding_style} "
                f"{bg_style} " # Optional background for content area itself
                f"box-sizing: border-box; "
            )

            return f".{css_class} {{ {styles} }}"

        except Exception as e:
            print(f"Error generating CSS for Drawer Content {css_class} with key {style_key}: {e}")
            return f"/* Error generating rule for .{css_class} */"

    # Removed: __new__, to_html(), to_css(), toggle()
    # State (is_open) and toggle logic moved outside the widget.

class EndDrawer(Widget):
    """
    Represents the content panel displayed typically from the end edge (e.g., right) of a Scaffold.
    Its visibility is controlled externally (e.g., by Scaffold JS).
    Compatible with the reconciliation rendering system.
    """
    shared_styles: Dict[Tuple, str] = {} # For shared EndDrawer styling (if any distinct from Drawer)

    # Remove Singleton pattern (__new__)

    def __init__(self,
                 child: Widget, # EndDrawer must have content
                 key: Optional[Key] = None,
                 # Styling Properties (Similar to Drawer)
                 width: int = 304, # M3 Default width
                 backgroundColor: Optional[str] = None, # M3 Surface Container High
                 elevation: Optional[float] = 1.0, # M3 Elevation Level 1 (when open)
                 shadowColor: Optional[str] = Colors.rgba(0,0,0,0.15), # Approx shadow
                 padding: Optional[EdgeInsets] = None, # Padding inside the drawer
                 # borderSide: Optional[BorderSide] = None, # Border Left? M3 uses shadow.
                 ):

        super().__init__(key=key, children=[child])
        self.child = child # Keep reference if needed

        # Store styling properties
        self.width = width
        self.backgroundColor = backgroundColor or Colors.surfaceContainerHigh or '#ECE6F0'
        self.elevation = elevation # Note: Elevation applied by Scaffold wrapper
        self.shadowColor = shadowColor # Note: Shadow applied by Scaffold wrapper
        self.padding = padding

        # --- CSS Class Management ---
        # Key includes properties affecting the EndDrawer's *content* container style
        # Often identical to Drawer, could potentially share the same dictionary/logic
        self.style_key = (
            self.backgroundColor,
            self.width, # Width might affect internal layout if % widths used
            make_hashable(self.padding),
        )

        # Could reuse Drawer.shared_styles if styling is identical
        if self.style_key not in EndDrawer.shared_styles:
            self.css_class = f"shared-enddrawer-content-{len(EndDrawer.shared_styles)}"
            EndDrawer.shared_styles[self.style_key] = self.css_class
        else:
            self.css_class = EndDrawer.shared_styles[self.style_key]

        # Removed self.is_open and self.initialized

    def render_props(self) -> Dict[str, Any]:
        """Return properties for the Reconciler."""
        props = {
            'css_class': self.css_class,
            'backgroundColor': self.backgroundColor, # Passed in case reconciler needs it
            'width': self.width, # Pass width for reconciler info / potential overrides
            'padding': self._get_render_safe_prop(self.padding),
            # Child diffing handled separately
        }
        return {k: v for k, v in props.items() if v is not None}

    def get_required_css_classes(self) -> Set[str]:
        """Return the set of CSS class names needed."""
        return {self.css_class} # Class for the drawer's content area

    @staticmethod
    def generate_css_rule(style_key: Tuple, css_class: str) -> str:
        """
        Static method for Reconciler. Generates CSS for the EndDrawer's inner content container.
        Positioning, background, shadow, transition are handled by `.scaffold-drawer-right`.
        This rule handles padding, maybe internal background. Often identical to Drawer's rule.
        """
        try:
            # Unpack key
            backgroundColor, width, padding_repr = style_key

            padding_obj = padding_repr
            padding_style = ""
            if isinstance(padding_obj, EdgeInsets):
                 padding_style = f"padding: {padding_obj.to_css()};"
            elif padding_repr:
                 padding_style = f"padding: {padding_repr};"

            bg_style = f"background-color: {backgroundColor};" if backgroundColor else ""

            # Content container fills the wrapper provided by Scaffold
            styles = (
                f"width: 100%; "
                f"height: 100%; "
                f"{padding_style} "
                f"{bg_style} "
                f"box-sizing: border-box; "
                # Allow internal scrolling if content overflows
                # Note: Outer wrapper (.scaffold-drawer-*) already has overflow: auto
                # "overflow-y: auto;" # Maybe not needed here if outer handles it
            )

            return f".{css_class} {{ {styles} }}"

        except Exception as e:
            print(f"Error generating CSS for EndDrawer Content {css_class} with key {style_key}: {e}")
            return f"/* Error generating rule for .{css_class} */"

    # Removed: __new__, to_html(), to_css(), toggle()

# --- BottomSheet Refactored ---
class BottomSheet(Widget):
    """
    A Material Design Bottom Sheet panel that slides up from the bottom.
    Visibility controlled externally. Drag behavior requires separate JS implementation.
    Compatible with the reconciliation rendering system.
    """
    shared_styles: Dict[Tuple, str] = {}

    # Remove Singleton pattern (__new__)

    def __init__(self,
                 child: Widget, # Content of the bottom sheet
                 key: Optional[Key] = None,
                 # Styling Properties
                 # height: Optional[Union[int, str]] = None, # Height often determined by content or screen %
                 maxHeight: Optional[Union[int, str]] = "60%", # M3 recommends max height
                 backgroundColor: Optional[str] = None, # M3 Surface Container Low
                 # shape: Optional[ShapeBorder] = None, # M3 uses shape, e.g., rounded top corners
                 # For simplicity, use border-radius for now
                 borderTopRadius: Optional[int] = 28, # M3 default corner radius
                 elevation: Optional[float] = 1.0, # M3 Elevation Level 1
                 shadowColor: Optional[str] = Colors.rgba(0,0,0,0.15), # Approx shadow
                 padding: Optional[EdgeInsets] = None, # Padding inside the sheet
                 # Behavior Properties
                 enableDrag: bool = True, # Flag for JS drag handler
                 showDragHandle: bool = True, # M3 usually shows a drag handle
                 # State (controlled externally)
                 # is_open: bool = False, # Handled by parent state/JS toggle class
                 # Modal Properties (Info for Scaffold/Framework)
                 isModal: bool = True, # Most M3 bottom sheets are modal
                 barrierColor: Optional[str] = Colors.rgba(0, 0, 0, 0.4), # M3 Scrim
                 # Callbacks (handled by parent state)
                 onDismissed: Optional[Callable] = None,
                 onDismissedName: Optional[str] = None,
                 ):

        # BottomSheet conceptually holds the child content
        super().__init__(key=key, children=[child])
        self.child = child # Keep reference

        # Store properties
        self.maxHeight = maxHeight
        self.backgroundColor = backgroundColor or Colors.surfaceContainerLow or '#F7F2FA'
        self.borderTopRadius = borderTopRadius
        self.elevation = elevation
        self.shadowColor = shadowColor
        self.padding = padding or EdgeInsets.symmetric(horizontal=16, vertical=24) # Default padding
        self.enableDrag = enableDrag
        self.showDragHandle = showDragHandle
        self.isModal = isModal
        self.barrierColor = barrierColor
        self.onDismissedName = onDismissedName if onDismissedName else (onDismissed.__name__ if onDismissed else None)

        # --- CSS Class Management ---
        # Key includes properties affecting the bottom sheet container's style
        self.style_key = (
            self.maxHeight,
            self.backgroundColor,
            self.borderTopRadius,
            self.elevation,
            self.shadowColor,
            make_hashable(self.padding),
            self.showDragHandle,
        )

        if self.style_key not in BottomSheet.shared_styles:
            self.css_class = f"shared-bottomsheet-{len(BottomSheet.shared_styles)}"
            BottomSheet.shared_styles[self.style_key] = self.css_class
        else:
            self.css_class = BottomSheet.shared_styles[self.style_key]

        # Removed self.is_open, self.initialized

    def render_props(self) -> Dict[str, Any]:
        """Return properties for the Reconciler."""
        props = {
            'css_class': self.css_class,
            'maxHeight': self.maxHeight,
            'backgroundColor': self.backgroundColor,
            'borderTopRadius': self.borderTopRadius,
            'elevation': self.elevation,
            'shadowColor': self.shadowColor,
            'padding': self._get_render_safe_prop(self.padding),
            'enableDrag': self.enableDrag, # Flag for JS
            'showDragHandle': self.showDragHandle,
            'isModal': self.isModal, # Info for Scaffold/Framework
            'barrierColor': self.barrierColor, # Info for Scaffold/Framework
            'onDismissedName': self.onDismissedName, # For JS interaction
            # Children diffing handled separately
        }
        return {k: v for k, v in props.items() if v is not None}

    def get_required_css_classes(self) -> Set[str]:
        """Return the set of CSS class names needed."""
        return {self.css_class}

    @staticmethod
    def generate_css_rule(style_key: Tuple, css_class: str) -> str:
        """Static method for Reconciler to generate CSS for BottomSheet."""
        try:
            # Unpack key
            (maxHeight, backgroundColor, borderTopRadius, elevation,
             shadowColor, padding_repr, showDragHandle) = style_key

            # --- Base Styles ---
            # Fixed position at bottom, translates up/down
            base_styles = f"""
                position: fixed;
                left: 0;
                right: 0;
                bottom: 0;
                width: 100%;
                max-width: 640px; /* M3 Max width for standard bottom sheet */
                margin: 0 auto; /* Center if max-width applies */
                max-height: {maxHeight or '60%'};
                background-color: {backgroundColor};
                border-top-left-radius: {borderTopRadius or 28}px;
                border-top-right-radius: {borderTopRadius or 28}px;
                z-index: 1100; /* Above scrim, below potential dialogs */
                transform: translateY(100%); /* Start hidden below screen */
                transition: transform 0.3s cubic-bezier(0.4, 0.0, 0.2, 1); /* M3 Standard Easing */
                display: flex;
                flex-direction: column; /* Stack drag handle and content */
                overflow: hidden; /* Hide content overflow initially */
                box-sizing: border-box;
            """

            # Elevation/Shadow (M3 Level 1)
            shadow_style = ""
            if elevation and elevation >= 1:
                 shadow_str = f"box-shadow: 0px 1px 3px 0px {shadowColor or 'rgba(0, 0, 0, 0.3)'}, 0px 1px 1px 0px {shadowColor or 'rgba(0, 0, 0, 0.15)'};"
            base_styles += shadow_str

            # --- Drag Handle Styles ---
            drag_handle_styles = ""
            if showDragHandle:
                drag_handle_styles = f"""
                .{css_class}::before {{ /* Using pseudo-element for drag handle */
                    content: "";
                    display: block;
                    width: 32px;
                    height: 4px;
                    border-radius: 2px;
                    background-color: {Colors.onSurfaceVariant or '#CAC4D0'}; /* M3 Handle color */
                    margin: 16px auto 8px auto; /* Spacing */
                    flex-shrink: 0; /* Prevent shrinking */
                    cursor: {'grab' if True else 'auto'}; /* TODO: Check enableDrag prop here? */
                }}
                """

            # --- Content Area Styles ---
            # Styles the wrapper div reconciler creates for the child
            padding_obj = padding_repr
            padding_style = ""
            if isinstance(padding_obj, EdgeInsets):
                 padding_style = f"padding: {padding_obj.to_css()};"
            elif padding_repr:
                 padding_style = f"padding: {padding_repr};"

            content_area_styles = f"""
            .{css_class} > .bottomsheet-content {{
                flex-grow: 1; /* Allow content to fill remaining space */
                overflow-y: auto; /* Allow content itself to scroll */
                {padding_style}
                box-sizing: border-box;
            }}
            """

            # --- Open State ---
            # Applied by JS when opening (e.g., adding 'open' class)
            open_styles = f"""
            .{css_class}.open {{
                transform: translateY(0%);
            }}
            """

            return f"{drag_handle_styles}\n.{css_class} {{ {base_styles} }}\n{content_area_styles}\n{open_styles}"

        except Exception as e:
            print(f"Error generating CSS for BottomSheet {css_class} with key {style_key}: {e}")
            return f"/* Error generating rule for .{css_class} */"

    # Removed: __new__, to_html(), toggle()

# --- Center Refactored ---
class Center(Widget):
    """
    A layout widget that centers its child within itself.
    Uses flexbox for centering. Compatible with reconciliation.
    """
    shared_styles: Dict[Tuple, str] = {}

    def __init__(self,
                 child: Widget, # Requires exactly one child
                 key: Optional[Key] = None,
                 # Add width/height factors if needed (like Flutter's Center)
                 # widthFactor: Optional[float] = None,
                 # heightFactor: Optional[float] = None,
                 ):

        super().__init__(key=key, children=[child])
        self.child = child # Keep reference

        # --- CSS Class Management ---
        # Center has fixed styling, so the key is simple (or could be omitted)
        self.style_key = ('center-widget',) # Simple key, always the same style

        if self.style_key not in Center.shared_styles:
            self.css_class = f"shared-center-{len(Center.shared_styles)}"
            Center.shared_styles[self.style_key] = self.css_class
        else:
            self.css_class = Center.shared_styles[self.style_key]

    def render_props(self) -> Dict[str, Any]:
        """Return properties for the Reconciler."""
        props = {
            'css_class': self.css_class,
            # Children diffing handled separately
        }
        return props

    def get_required_css_classes(self) -> Set[str]:
        """Return the set of CSS class names needed."""
        return {self.css_class}

    @staticmethod
    def generate_css_rule(style_key: Tuple, css_class: str) -> str:
        """Static method for Reconciler to generate the centering CSS rule."""
        try:
            # Style is always the same for Center widget
            styles = (
                "display: flex; "
                "justify-content: center; " # Center horizontally
                "align-items: center; "    # Center vertically
                "width: 100%; "            # Often needs to fill parent width
                "height: 100%; "           # Often needs to fill parent height
                # If parent isn't flex/grid, these might not work as expected
                # Consider adding text-align: center; as fallback?
            )
            return f".{css_class} {{ {styles} }}"

        except Exception as e:
            print(f"Error generating CSS for Center {css_class}: {e}")
            return f"/* Error generating rule for .{css_class} */"

    # Removed instance methods: to_html()

class ListTile(Widget):
    """
    A single fixed-height row that typically contains some text as well as a
    leading or trailing icon. Conforms to Material 3 list item specs.
    Compatible with the reconciliation rendering system.
    """
    shared_styles: Dict[Tuple, str] = {} # For base ListTile structure/styling

    def __init__(self,
                 key: Optional[Key] = None,
                 # --- Content Slots ---
                 leading: Optional[Widget] = None,
                 title: Optional[Widget] = None, # Usually Text
                 subtitle: Optional[Widget] = None, # Usually Text
                 trailing: Optional[Widget] = None, # Icon, Checkbox, etc.
                 # --- Interaction ---
                 onTap: Optional[Callable] = None,
                 onTapName: Optional[str] = None,
                 enabled: bool = True,
                 selected: bool = False, # For highlighting selected state
                 # --- Styling ---
                 # M3 uses container color/shape based on context (e.g., inside List, Card)
                 # We'll apply base padding/height here.
                 # Color roles applied via context or theme normally.
                 contentPadding: Optional[EdgeInsets] = None,
                 minVerticalPadding: Optional[float] = None, # M3 uses this
                 minLeadingWidth: Optional[float] = None, # M3 uses this
                 horizontalTitleGap: Optional[float] = 16.0, # M3 gap
                 dense: bool = False, # Compact layout variant
                 selectedColor: Optional[str] = None, # M3 Primary (for icon/text when selected)
                 selectedTileColor: Optional[str] = None, # M3 Primary Container (background when selected)
                 # focusColor, hoverColor etc. would ideally be handled by CSS :hover/:focus
                 ):

        # Collect children in specific order for layout
        children = []
        if leading: children.append(leading)
        if title: children.append(title)
        if subtitle: children.append(subtitle)
        if trailing: children.append(trailing)

        super().__init__(key=key, children=children)

        # Store references and properties
        self.leading = leading
        self.title = title
        self.subtitle = subtitle
        self.trailing = trailing
        self.onTap = onTap
        self.onTapName = onTapName if onTapName else (onTap.__name__ if onTap else None)
        self.enabled = enabled
        self.selected = selected

        # Styling/Layout Props
        self.contentPadding = contentPadding # Often EdgeInsets.symmetric(horizontal=16)
        self.minVerticalPadding = minVerticalPadding
        self.minLeadingWidth = minLeadingWidth
        self.horizontalTitleGap = horizontalTitleGap
        self.dense = dense
        self.selectedColor = selectedColor or Colors.primary or '#005AC1'
        self.selectedTileColor = selectedTileColor # or Colors.primaryContainer or ...

        # --- CSS Class Management ---
        # Key includes properties affecting base layout/style class
        # Padding/gaps are better handled by CSS rules directly or props if dynamic needed
        self.style_key = (
             self.dense,
             self.enabled, # Might affect opacity/cursor
             # Other base structural styles if any
        )

        if self.style_key not in ListTile.shared_styles:
            self.css_class = f"shared-listtile-{len(ListTile.shared_styles)}"
            ListTile.shared_styles[self.style_key] = self.css_class
            # Register callback centrally (Framework approach preferred)
            # if self.onTap and self.onTapName:
            #     Api().register_callback(self.onTapName, self.onTap)
        else:
            self.css_class = ListTile.shared_styles[self.style_key]

        # Add selected class dynamically based on prop
        self.current_css_class = f"{self.css_class} {'dense' if self.dense else ''} {'selected' if self.selected else ''} {'disabled' if not self.enabled else ''}"


    def render_props(self) -> Dict[str, Any]:
        """Return properties for the Reconciler."""
        props = {
            'css_class': self.current_css_class, # Pass the combined class string
            'enabled': self.enabled,
            'selected': self.selected,
            'onTapName': self.onTapName, # For click handling
            # Pass layout hints for reconciler/JS if needed, or rely on CSS
            'contentPadding': self._get_render_safe_prop(self.contentPadding),
            'minVerticalPadding': self.minVerticalPadding,
            'minLeadingWidth': self.minLeadingWidth,
            'horizontalTitleGap': self.horizontalTitleGap,
            'dense': self.dense,
            'selectedColor': self.selectedColor,
            'selectedTileColor': self.selectedTileColor,
            # Flags indicating which slots are filled
            'has_leading': bool(self.leading),
            'has_title': bool(self.title),
            'has_subtitle': bool(self.subtitle),
            'has_trailing': bool(self.trailing),
        }
        return {k: v for k, v in props.items() if v is not None}

    def get_required_css_classes(self) -> Set[str]:
        """Return the base CSS class name."""
        # Selection/dense/disabled handled by adding classes in render_props/reconciler
        return {self.css_class}

    @staticmethod
    def generate_css_rule(style_key: Tuple, css_class: str) -> str:
        """Static method for Reconciler to generate CSS for ListTile structure."""
        try:
            # Unpack key
            (dense,) = style_key # Assuming only dense affects base class structure significantly

            # --- M3 Defaults ---
            min_height = 56 # M3 default minimum height
            dense_min_height = 48 # M3 dense minimum height
            horizontal_padding = 16 # M3 default horizontal padding
            title_gap = 16 # M3 default gap
            leading_width = 40 # M3 leading area width (icon typically 24px)

            # --- Base ListTile Styles ---
            base_styles = f"""
                display: grid; /* Use grid for precise slot layout */
                grid-template-columns: auto 1fr auto; /* leading, title/subtitle (flexible), trailing */
                grid-template-rows: auto auto; /* Row for title, row for subtitle */
                grid-template-areas: /* Define grid areas */
                    "leading title trailing"
                    "leading subtitle trailing";
                align-items: center; /* Center items vertically by default */
                width: 100%;
                min-height: {dense_min_height if dense else min_height}px;
                padding: 8px {horizontal_padding}px; /* Default vertical padding, specific horizontal */
                box-sizing: border-box;
                position: relative; /* For potential ink ripple/overlays */
                gap: 0 {title_gap}px; /* No row gap, specific column gap */
                cursor: default; /* Default cursor */
                overflow: hidden; /* Clip content */
            """

            # --- Styles for Child Slot Wrappers ---
            # Reconciler will wrap children with these classes
            leading_styles = f"grid-area: leading; display: flex; align-items: center; justify-content: center; min-width: {leading_width}px; height: 100%;"
            title_styles = f"grid-area: title; align-self: end; /* Align title to bottom if subtitle exists */"
            subtitle_styles = f"grid-area: subtitle; align-self: start; color: {Colors.onSurfaceVariant or '#49454F'}; font-size: 12px; /* M3 Subtitle style approx */" # M3 On Surface Variant
            # Adjust title alignment when no subtitle
            title_no_subtitle_styles = "align-self: center;" # Center title vertically if no subtitle
            trailing_styles = f"grid-area: trailing; display: flex; align-items: center; justify-content: center; height: 100%;"

            # --- State Styles ---
            enabled_styles = "cursor: pointer;" # Only show pointer if enabled and has onTap
            disabled_styles = "opacity: 0.38; pointer-events: none;" # M3 disabled style
            selected_styles = f"""
                background-color: {Colors.primaryContainer or '#D7E3FF'}; /* M3 Selected background */
                color: {Colors.onPrimaryContainer or '#001B3E'}; /* M3 Selected text/icon color */
            """
            # Apply selected color to specific elements (icon/text) within the selected tile
            selected_child_styles = f"color: {Colors.onPrimaryContainer or '#001B3E'};"


            # --- Assemble Rules ---
            rules = [
                f".{css_class} {{ {base_styles} }}",
                # Wrappers added by reconciler
                f".{css_class} > .listtile-leading {{ {leading_styles} }}",
                f".{css_class} > .listtile-title {{ {title_styles} }}",
                 # Adjust title alignment when subtitle is NOT present (more specific selector)
                f".{css_class}:not(:has(> .listtile-subtitle)) > .listtile-title {{ {title_no_subtitle_styles} }}",
                f".{css_class} > .listtile-subtitle {{ {subtitle_styles} }}",
                f".{css_class} > .listtile-trailing {{ {trailing_styles} }}",
                # State classes (added by reconciler based on props)
                f".{css_class}:not(.disabled) {{ {enabled_styles} }}", # Apply pointer only if enabled
                f".{css_class}.disabled {{ {disabled_styles} }}",
                f".{css_class}.selected {{ {selected_styles} }}",
                # Apply selected color to text/icons within selected tile
                f".{css_class}.selected .listtile-leading > *, "
                f".{css_class}.selected .listtile-title > *, "
                f".{css_class}.selected .listtile-subtitle > *, "
                f".{css_class}.selected .listtile-trailing > * {{ {selected_child_styles} }}",

            ]

            return "\n".join(rules)

        except Exception as e:
            print(f"Error generating CSS for ListTile {css_class} with key {style_key}: {e}")
            return f"/* Error generating rule for .{css_class} */"

    # Removed instance methods: to_html(), to_css()

# --- SnackBarAction Refactored ---
class SnackBarAction(Widget):
    """
    Represents the action button within a SnackBar.
    Usually styled as a text button with specific coloring.
    Compatible with the reconciliation rendering system.
    """
    shared_styles: Dict[Tuple, str] = {}

    # Remove Singleton pattern (__new__)

    def __init__(self,
                 label: Widget, # Typically a Text widget
                 key: Optional[Key] = None,
                 onPressed: Optional[Callable] = None,
                 onPressedName: Optional[str] = None,
                 textColor: Optional[str] = None # M3 Inverse Primary
                 ):

        # SnackBarAction wraps the label widget
        super().__init__(key=key, children=[label])
        self.label = label

        self.onPressed = onPressed
        self.onPressed_id = onPressedName if onPressedName else (onPressed.__name__ if onPressed else None)
        # M3 uses Inverse Primary color role for the action button
        self.textColor = textColor or Colors.inversePrimary or '#D0BCFF'

        # --- CSS Class Management ---
        # Style key includes properties affecting the action button's style
        self.style_key = (
            self.textColor,
            # Add other relevant style props if needed (e.g., font weight from theme)
        )

        if self.style_key not in SnackBarAction.shared_styles:
            self.css_class = f"shared-snackbar-action-{len(SnackBarAction.shared_styles)}"
            SnackBarAction.shared_styles[self.style_key] = self.css_class
            # Register callback centrally (Framework approach preferred)
            # if self.onPressed and self.onPressed_id:
            #     Api().register_callback(self.onPressed_id, self.onPressed)
        else:
            self.css_class = SnackBarAction.shared_styles[self.style_key]

    def render_props(self) -> Dict[str, Any]:
        """Return properties for the Reconciler."""
        props = {
            'css_class': self.css_class,
            'onPressedName': self.onPressed_id, # For click handler setup
            'textColor': self.textColor, # Pass color for potential direct style patch
            # Children (label) handled separately
        }
        return {k: v for k, v in props.items() if v is not None}

    def get_required_css_classes(self) -> Set[str]:
        """Return the set of CSS class names needed."""
        return {self.css_class}

    @staticmethod
    def generate_css_rule(style_key: Tuple, css_class: str) -> str:
        """Static method for Reconciler to generate CSS for SnackBarAction."""
        try:
            # Unpack key
            (textColor,) = style_key

            # Base styles mimicking a TextButton optimized for SnackBar
            styles = f"""
                display: inline-block; /* Or inline-flex if icon possible */
                padding: 8px 8px; /* M3 recommends min 48x48 target, padding helps */
                margin-left: 8px; /* Space from content */
                background: none;
                border: none;
                color: {textColor or Colors.inversePrimary or '#D0BCFF'};
                font-size: 14px; /* M3 Button Label */
                font-weight: 500;
                text-transform: uppercase; /* M3 often uses uppercase */
                letter-spacing: 0.1px;
                cursor: pointer;
                text-align: center;
                text-decoration: none;
                outline: none;
                border-radius: 4px; /* Slight rounding for hover/focus state */
                transition: background-color 0.2s ease-in-out;
                -webkit-appearance: none;
                -moz-appearance: none;
                appearance: none;
            """
            # Hover state (subtle background)
            hover_styles = f"background-color: rgba(255, 255, 255, 0.08);" # Example hover

            return f".{css_class} {{ {styles} }}\n.{css_class}:hover {{ {hover_styles} }}"

        except Exception as e:
            print(f"Error generating CSS for SnackBarAction {css_class} with key {style_key}: {e}")
            return f"/* Error generating rule for .{css_class} */"

    # Removed: __new__, to_html()


# --- SnackBar Refactored ---
class SnackBar(Widget):
    """
    Provides brief messages about app processes at the bottom of the screen.
    Visibility and timer controlled externally. Implements M3 styling.
    Compatible with the reconciliation rendering system.
    """
    shared_styles: Dict[Tuple, str] = {}

    # Remove Singleton pattern (__new__)

    def __init__(self,
                 content: Widget, # Main content, usually Text
                 key: Optional[Key] = None,
                 action: Optional[SnackBarAction] = None,
                 # Styling Properties
                 backgroundColor: Optional[str] = None, # M3 Inverse Surface
                 textColor: Optional[str] = None, # M3 Inverse On Surface
                 padding: Optional[EdgeInsets] = None, # Padding inside snackbar
                 shapeRadius: Optional[int] = 4, # M3 corner radius
                 elevation: Optional[float] = 6.0, # M3 Elevation level 3 (approx)
                 shadowColor: Optional[str] = Colors.rgba(0,0,0,0.25), # Approx shadow
                 width: Optional[Union[int, str]] = None, # Usually adapts, but can be set
                 maxWidth: Optional[Union[int, str]] = 600, # Max width recommended
                 # Behavior (used by external controller)
                 duration: int = 4000, # Duration in milliseconds (M3 default 4s)
                 # State (controlled externally via .open class)
                 # is_open: bool = False,
                 ):

        # Collect children: content and action
        children = [content]
        if action:
            # Ensure action is SnackBarAction
            if not isinstance(action, SnackBarAction):
                 print(f"Warning: SnackBar action should be a SnackBarAction widget, got {type(action)}. Rendering may be incorrect.")
            children.append(action)

        super().__init__(key=key, children=children)

        # Store references and properties
        self.content = content
        self.action = action
        self.backgroundColor = backgroundColor or Colors.inverseSurface or '#313033'
        self.textColor = textColor or Colors.inverseOnSurface or '#F4EFF4'
        self.padding = padding or EdgeInsets.symmetric(horizontal=16, vertical=14)
        self.shapeRadius = shapeRadius
        self.elevation = elevation
        self.shadowColor = shadowColor
        self.width = width
        self.maxWidth = maxWidth
        self.duration = duration # Passed via props for external timer use

        # --- CSS Class Management ---
        self.style_key = (
            self.backgroundColor,
            self.textColor, # Affects default text color inside
            make_hashable(self.padding),
            self.shapeRadius,
            self.elevation,
            self.shadowColor,
            self.width,
            self.maxWidth,
        )

        if self.style_key not in SnackBar.shared_styles:
            self.css_class = f"shared-snackbar-{len(SnackBar.shared_styles)}"
            SnackBar.shared_styles[self.style_key] = self.css_class
        else:
            self.css_class = SnackBar.shared_styles[self.style_key]

        # Removed is_open, initialized, current_id

    def render_props(self) -> Dict[str, Any]:
        """Return properties for the Reconciler."""
        props = {
            'css_class': self.css_class,
            'backgroundColor': self.backgroundColor,
            'textColor': self.textColor,
            'padding': self._get_render_safe_prop(self.padding),
            'shapeRadius': self.shapeRadius,
            'elevation': self.elevation,
            'shadowColor': self.shadowColor,
            'width': self.width,
            'maxWidth': self.maxWidth,
            'duration': self.duration, # For external controller
            'has_action': bool(self.action), # Help reconciler with layout
            # Children diffing handled separately
        }
        return {k: v for k, v in props.items() if v is not None}

    def get_required_css_classes(self) -> Set[str]:
        """Return the set of CSS class names needed."""
        classes = {self.css_class}
        # Include action class if action exists and its CSS isn't globally defined elsewhere
        if self.action:
            classes.update(self.action.get_required_css_classes())
        return classes

    @staticmethod
    def generate_css_rule(style_key: Tuple, css_class: str) -> str:
        """Static method for Reconciler to generate CSS for SnackBar."""
        try:
            # Unpack key
            (backgroundColor, textColor, padding_repr, shapeRadius,
             elevation, shadowColor, width, maxWidth) = style_key

            # --- Base Styles ---
            # Fixed position, centered horizontally, animation setup
            base_styles = f"""
                position: fixed;
                bottom: 16px; /* Position from bottom */
                left: 50%;
                transform: translate(-50%, 150%); /* Start below screen */
                opacity: 0;
                min-height: 48px; /* M3 min height */
                width: {width or 'fit-content'}; /* Fit content or specified width */
                max-width: {f'{maxWidth}px' if isinstance(maxWidth, int) else (maxWidth or '600px')};
                margin: 8px; /* Margin from edges if width allows */
                padding: 0; /* Padding applied to inner container */
                background-color: {backgroundColor};
                color: {textColor};
                border-radius: {shapeRadius or 4}px;
                z-index: 1200; /* High z-index */
                transition: transform 0.3s cubic-bezier(0.4, 0.0, 0.2, 1), /* M3 Standard Easing */
                            opacity 0.2s linear;
                display: flex; /* Use flex for content/action layout */
                align-items: center;
                justify-content: space-between; /* Space out content and action */
                box-sizing: border-box;
                pointer-events: none; /* Allow clicks through when hidden */
            """

            # Elevation/Shadow (M3 Level 3 approx)
            shadow_style = ""
            if elevation and elevation >= 3:
                shadow_str = f"box-shadow: 0px 3px 5px -1px {shadowColor or 'rgba(0, 0, 0, 0.2)'}, 0px 6px 10px 0px {shadowColor or 'rgba(0, 0, 0, 0.14)'}, 0px 1px 18px 0px {shadowColor or 'rgba(0, 0, 0, 0.12)'};"
            elif elevation and elevation > 0: # Lower elevation fallback
                shadow_str = f"box-shadow: 0px 1px 3px 0px {shadowColor or 'rgba(0, 0, 0, 0.3)'}, 0px 1px 1px 0px {shadowColor or 'rgba(0, 0, 0, 0.15)'};"
            base_styles += shadow_str


            # --- Content/Action Wrapper Styles ---
            # Reconciler wraps content and action
            padding_obj = padding_repr
            padding_style = ""
            if isinstance(padding_obj, EdgeInsets):
                padding_style = f"padding: {padding_obj.to_css()};"
            elif padding_repr:
                padding_style = f"padding: {padding_repr};" # Fallback

            content_styles = f"flex-grow: 1; {padding_style} font-size: 14px; /* M3 Body Medium */"
            action_wrapper_styles = f"flex-shrink: 0; {padding_style.replace('padding','').replace(';','')} /* Apply padding from props, typically only right */" # Isolate action padding if needed


            # --- Open State ---
            # Applied by JS when showing (e.g., adding 'open' class)
            open_styles = f"""
            .{css_class}.open {{
                transform: translate(-50%, 0%); /* Slide up */
                opacity: 1;
                pointer-events: auto; /* Allow interaction when open */
            }}
            """

            # --- Assemble Rules ---
            rules = [
                 f".{css_class} {{ {base_styles} }}",
                 f".{css_class} > .snackbar-content {{ {content_styles} }}",
                 f".{css_class} > .snackbar-action-wrapper {{ {action_wrapper_styles} }}", # Wrapper for action
                 open_styles
            ]
            return "\n".join(rules)

        except Exception as e:
            print(f"Error generating CSS for SnackBar {css_class} with key {style_key}: {e}")
            return f"/* Error generating rule for .{css_class} */"

    # Removed: __new__, to_html(), get_id(), toggle()

# --- Placeholder Refactored ---
class Placeholder(Widget):
    """
    A widget that draws a box with a cross inside, useful for indicating
    where content will eventually go. Can also display a child.
    Compatible with the reconciliation rendering system.
    """
    shared_styles: Dict[Tuple, str] = {} # For the placeholder box style

    def __init__(self,
                 key: Optional[Key] = None,
                 child: Optional[Widget] = None, # Optional child to display instead of placeholder box
                 # Styling for the placeholder box itself (when no child)
                 color: Optional[str] = None, # M3 Outline
                 strokeWidth: float = 1.0, # Thickness of the dashed lines
                 height: Optional[Union[int, float, str]] = 100, # Default height
                 width: Optional[Union[int, float, str]] = 100, # Default width
                 fallbackText: str = "Placeholder", # Text inside the box
                 ):

        # Pass child to base class (even if None, helps reconciler know structure)
        super().__init__(key=key, children=[child] if child else [])
        self.child = child

        # Store properties for placeholder appearance
        self.color = color or Colors.outline or '#79747E' # M3 Outline
        self.strokeWidth = strokeWidth
        self.height = height
        self.width = width
        self.fallbackText = fallbackText

        # --- CSS Class Management ---
        # Key includes properties affecting the placeholder box style
        self.style_key = (
            self.color,
            self.strokeWidth,
            # Height/width handled by render_props/inline style for flexibility
        )

        if self.style_key not in Placeholder.shared_styles:
            self.css_class = f"shared-placeholder-{len(Placeholder.shared_styles)}"
            Placeholder.shared_styles[self.style_key] = self.css_class
        else:
            self.css_class = Placeholder.shared_styles[self.style_key]

    def render_props(self) -> Dict[str, Any]:
        """Return properties for the Reconciler."""
        props = {
            'css_class': self.css_class if not self.child else '', # Only apply class if showing placeholder box
            'render_type': 'placeholder', # Help reconciler identify
            'has_child': bool(self.child),
            # Pass dimensions for direct styling by reconciler if no child
            'width': self.width,
            'height': self.height,
            # Pass placeholder text if no child
            'fallbackText': self.fallbackText if not self.child else None,
            # Pass color/stroke for direct styling if no child
            'color': self.color if not self.child else None,
            'strokeWidth': self.strokeWidth if not self.child else None,
        }
        # Note: If child exists, reconciler renders the child, otherwise renders placeholder div
        return {k: v for k, v in props.items() if v is not None}

    def get_required_css_classes(self) -> Set[str]:
        """Return the CSS class if rendering the placeholder box."""
        return {self.css_class} if not self.child else set()

    @staticmethod
    def generate_css_rule(style_key: Tuple, css_class: str) -> str:
        """Static method for Reconciler to generate CSS for the Placeholder box."""
        try:
            # Unpack key
            color, strokeWidth = style_key

            # Styles for the placeholder box itself
            styles = f"""
                display: flex;
                justify-content: center;
                align-items: center;
                border: {strokeWidth or 1}px dashed {color or '#79747E'};
                color: {color or '#79747E'};
                font-size: 12px;
                text-align: center;
                box-sizing: border-box;
                overflow: hidden; /* Prevent text overflow */
                position: relative; /* Context for potential pseudo-element cross */
            """
            # Optional: Add a visual cross using pseudo-elements (more complex)
            # cross_styles = f"""
            # .{css_class}::before, .{css_class}::after {{
            #     content: '';
            #     position: absolute;
            #     background-color: {color or '#79747E'};
            # }}
            # .{css_class}::before {{ /* Line 1 (\) */
            #     width: {strokeWidth or 1}px;
            #     left: 50%; top: 0; bottom: 0;
            #     transform: translateX(-50%) rotate(45deg);
            #     transform-origin: center;
            # }}
            # .{css_class}::after {{ /* Line 2 (/) */
            #     height: {strokeWidth or 1}px;
            #     top: 50%; left: 0; right: 0;
            #     transform: translateY(-50%) rotate(45deg);
            #     transform-origin: center;
            # }}
            # """
            # Note: A simple dashed border is often sufficient and simpler.

            return f".{css_class} {{ {styles} }}" #\n{cross_styles}"

        except Exception as e:
            print(f"Error generating CSS for Placeholder {css_class} with key {style_key}: {e}")
            return f"/* Error generating rule for .{css_class} */"

    # Removed instance methods: to_html()


# --- Padding Refactored ---
class Padding(Widget):
    """
    A widget that insets its child by the given padding.
    Applies padding styles directly. Not a shared style component usually.
    """
    def __init__(self,
                 padding: EdgeInsets, # Padding is required
                 key: Optional[Key] = None,
                 child: Optional[Widget] = None, # Can have one child or none
                 ):

        if not isinstance(padding, EdgeInsets):
             raise TypeError("Padding widget requires an EdgeInsets instance.")

        super().__init__(key=key, children=[child] if child else [])
        self.child = child # Keep reference
        self.padding = padding

    def render_props(self) -> Dict[str, Any]:
        """Return padding property for direct styling by Reconciler."""
        props = {
            'render_type': 'padding', # Help reconciler identify
            'padding': self._get_render_safe_prop(self.padding), # Pass padding details
            # No css_class needed
        }
        return props # No need to filter None here

    def get_required_css_classes(self) -> Set[str]:
        """Padding doesn't use shared CSS classes."""
        return set()

    # No generate_css_rule needed

    # Removed instance methods: to_html()


# --- Align Refactored ---
class Align(Widget):
    """
    Aligns its child within itself and optionally sizes itself based on the child.
    Uses flexbox for alignment. Not typically a shared style component.
    """
    def __init__(self,
                 alignment: Alignment, # Alignment is required
                 key: Optional[Key] = None,
                 child: Optional[Widget] = None,
                 # Add width/height factors if needed
                 # widthFactor: Optional[float] = None,
                 # heightFactor: Optional[float] = None,
                 ):

        if not isinstance(alignment, Alignment):
             raise TypeError("Align widget requires an Alignment instance.")

        super().__init__(key=key, children=[child] if child else [])
        self.child = child # Keep reference
        self.alignment = alignment
        # self.widthFactor = widthFactor
        # self.heightFactor = heightFactor

    def render_props(self) -> Dict[str, Any]:
        """Return alignment properties for direct styling by Reconciler."""
        props = {
            'render_type': 'align', # Help reconciler identify
            'alignment': self._get_render_safe_prop(self.alignment), # Pass alignment details
            # 'widthFactor': self.widthFactor,
            # 'heightFactor': self.heightFactor,
            # No css_class needed
        }
        return {k: v for k, v in props.items() if v is not None}

    def get_required_css_classes(self) -> Set[str]:
        """Align doesn't use shared CSS classes."""
        return set()

    # No generate_css_rule needed

    # Removed instance methods: to_html()

# --- AspectRatio Refactored ---
class AspectRatio(Widget):
    """
    A widget that attempts to size its child to a specific aspect ratio.
    Uses the padding-bottom CSS trick for maintaining ratio.
    Compatible with the reconciliation rendering system.
    """
    # AspectRatio styling is instance-specific based on the ratio value.
    # No shared styles needed.

    def __init__(self,
                 aspectRatio: float, # The ratio (width / height) is required
                 key: Optional[Key] = None,
                 child: Optional[Widget] = None):

        if aspectRatio <= 0:
             raise ValueError("aspectRatio must be positive")

        super().__init__(key=key, children=[child] if child else [])
        self.child = child
        self.aspectRatio = aspectRatio

    def render_props(self) -> Dict[str, Any]:
        """Return aspect ratio for direct styling by Reconciler."""
        props = {
            'render_type': 'aspect_ratio', # Help reconciler identify
            'aspectRatio': self.aspectRatio,
            # Children diffing handled separately
        }
        return props

    def get_required_css_classes(self) -> Set[str]:
        """AspectRatio doesn't use shared CSS classes."""
        return set()

    # No generate_css_rule needed

    # Removed instance methods: to_html()

# --- FittedBox Refactored ---
class FittedBox(Widget):
    """
    Scales and positions its child within itself according to fit.
    Applies object-fit styles or uses transform depending on complexity.
    Compatible with the reconciliation rendering system.
    """
    # Styling is instance-specific based on fit/alignment. No shared styles.

    def __init__(self,
                 key: Optional[Key] = None,
                 child: Optional[Widget] = None, # Requires a child to fit
                 fit: str = BoxFit.CONTAIN, # How to fit the child
                 alignment: Alignment = Alignment.center(), # Alignment within the box
                 clipBehavior=ClipBehavior.HARD_EDGE, # Usually clips content
                 ):

        if not child:
             # FittedBox without a child doesn't make much sense
             print("Warning: FittedBox created without a child.")

        super().__init__(key=key, children=[child] if child else [])
        self.child = child
        self.fit = fit
        self.alignment = alignment
        self.clipBehavior = clipBehavior # Affects overflow

    def render_props(self) -> Dict[str, Any]:
        """Return fit/alignment for direct styling by Reconciler."""
        props = {
            'render_type': 'fitted_box', # Help reconciler identify
            'fit': self.fit,
            'alignment': self._get_render_safe_prop(self.alignment),
            'clipBehavior': self.clipBehavior,
            # Children diffing handled separately
        }
        return props

    def get_required_css_classes(self) -> Set[str]:
        """FittedBox doesn't use shared CSS classes."""
        return set()

    # No generate_css_rule needed

    # Removed instance methods: to_html()

# --- FractionallySizedBox Refactored ---
class FractionallySizedBox(Widget):
    """
    Sizes its child to a fraction of the total available space.
    Applies percentage width/height styles.
    Compatible with the reconciliation rendering system.
    """
    # Styling is instance-specific based on factors. No shared styles.

    def __init__(self,
                 key: Optional[Key] = None,
                 child: Optional[Widget] = None,
                 widthFactor: Optional[float] = None, # Fraction of available width (0.0 to 1.0+)
                 heightFactor: Optional[float] = None, # Fraction of available height
                 alignment: Alignment = Alignment.center(), # How to align the child within the full space
                 ):

        if widthFactor is None and heightFactor is None:
             raise ValueError("FractionallySizedBox requires at least one of widthFactor or heightFactor.")

        super().__init__(key=key, children=[child] if child else [])
        self.child = child
        self.widthFactor = widthFactor
        self.heightFactor = heightFactor
        self.alignment = alignment

    def render_props(self) -> Dict[str, Any]:
        """Return factors/alignment for direct styling by Reconciler."""
        props = {
            'render_type': 'fractionally_sized', # Help reconciler identify
            'widthFactor': self.widthFactor,
            'heightFactor': self.heightFactor,
            'alignment': self._get_render_safe_prop(self.alignment),
            # Children diffing handled separately
        }
        return {k: v for k, v in props.items() if v is not None}

    def get_required_css_classes(self) -> Set[str]:
        """FractionallySizedBox doesn't use shared CSS classes."""
        return set()

    # No generate_css_rule needed

    # Removed instance methods: to_html()

# --- Flex Refactored ---
class Flex(Widget):
    """
    A widget that displays its children in a one-dimensional array, either
    horizontally (Row) or vertically (Column). This is a more general version.
    Compatible with the reconciliation rendering system.
    """
    shared_styles: Dict[Tuple, str] = {}

    def __init__(self,
                 children: List[Widget],
                 key: Optional[Key] = None,
                 # Layout Properties
                 direction: str = Axis.HORIZONTAL, # HORIZONTAL (Row) or VERTICAL (Column)
                 mainAxisAlignment: str = MainAxisAlignment.START,
                 crossAxisAlignment: str = CrossAxisAlignment.CENTER, # Default center cross-axis
                 # mainAxisSize: str = MainAxisSize.MAX, # Not directly applicable to generic Flex CSS usually
                 # textDirection, verticalDirection, textBaseline if needed like Row/Column
                 padding: Optional[EdgeInsets] = None, # Padding inside the flex container
                 ):

        super().__init__(key=key, children=children)

        # Store properties
        self.direction = direction
        self.mainAxisAlignment = mainAxisAlignment
        self.crossAxisAlignment = crossAxisAlignment
        self.padding = padding or EdgeInsets.all(0)

        # --- CSS Class Management ---
        # Key includes properties affecting the flex container style
        self.style_key = (
            self.direction,
            self.mainAxisAlignment,
            self.crossAxisAlignment,
            make_hashable(self.padding),
        )

        if self.style_key not in Flex.shared_styles:
            self.css_class = f"shared-flex-{len(Flex.shared_styles)}"
            Flex.shared_styles[self.style_key] = self.css_class
        else:
            self.css_class = Flex.shared_styles[self.style_key]

    def render_props(self) -> Dict[str, Any]:
        """Return properties for the Reconciler."""
        props = {
            'css_class': self.css_class,
            'direction': self.direction, # Pass for informational purposes if needed
            'mainAxisAlignment': self.mainAxisAlignment,
            'crossAxisAlignment': self.crossAxisAlignment,
            'padding': self._get_render_safe_prop(self.padding),
            # Children diffing handled separately
        }
        return {k: v for k, v in props.items() if v is not None}

    def get_required_css_classes(self) -> Set[str]:
        """Return the set of CSS class names needed."""
        return {self.css_class}

    @staticmethod
    def generate_css_rule(style_key: Tuple, css_class: str) -> str:
        """Static method for Reconciler to generate CSS for Flex container."""
        try:
            # Unpack key
            direction, mainAxisAlignment, crossAxisAlignment, padding_repr = style_key

            # --- Determine CSS Flexbox Properties ---
            flex_direction = 'row' if direction == Axis.HORIZONTAL else 'column'

            # Main Axis -> justify-content
            justify_content_val = mainAxisAlignment

            # Cross Axis -> align-items
            align_items_val = crossAxisAlignment

            # Padding
            padding_obj = padding_repr
            padding_style = ""
            if isinstance(padding_obj, EdgeInsets):
                 padding_style = f"padding: {padding_obj.to_css()};"
            elif padding_repr:
                 padding_style = f"padding: {padding_repr};" # Fallback

            # Combine styles
            styles = (
                f"display: flex; "
                f"flex-direction: {flex_direction}; "
                f"justify-content: {justify_content_val}; "
                f"align-items: {align_items_val}; "
                f"{padding_style} "
                f"box-sizing: border-box; "
                # Default sizing? Flex often needs context. Fill available space?
                # "width: 100%; height: 100%;" # Add if needed, or let parent control
            )

            return f".{css_class} {{ {styles} }}"

        except Exception as e:
            print(f"Error generating CSS for Flex {css_class} with key {style_key}: {e}")
            return f"/* Error generating rule for .{css_class} */"

    # Removed instance methods: to_html()

# --- Wrap Refactored ---
class Wrap(Widget):
    """
    Displays its children in multiple horizontal or vertical runs.
    Uses CSS Flexbox with wrapping enabled.
    Compatible with the reconciliation rendering system.
    """
    shared_styles: Dict[Tuple, str] = {}

    def __init__(self,
                 children: List[Widget],
                 key: Optional[Key] = None,
                 # Layout Properties
                 direction: str = Axis.HORIZONTAL, # Axis of the runs
                 alignment: str = MainAxisAlignment.START, # Alignment of items within a run
                 spacing: float = 0, # Gap between items in the main axis direction
                 runAlignment: str = MainAxisAlignment.START, # Alignment of runs in the cross axis
                 runSpacing: float = 0, # Gap between runs in the cross axis direction
                 crossAxisAlignment: str = CrossAxisAlignment.START, # Align items within a run cross-axis
                 clipBehavior=ClipBehavior.NONE, # Clip content if overflow
                 # verticalDirection not typically used for Wrap layout control
                 ):

        super().__init__(key=key, children=children)

        # Store properties
        self.direction = direction
        self.alignment = alignment
        self.spacing = spacing
        self.runAlignment = runAlignment
        self.runSpacing = runSpacing
        self.crossAxisAlignment = crossAxisAlignment
        self.clipBehavior = clipBehavior

        # --- CSS Class Management ---
        # Key includes properties affecting the wrap container style
        self.style_key = (
            self.direction,
            self.alignment,
            self.spacing,
            self.runAlignment,
            self.runSpacing,
            self.crossAxisAlignment,
            self.clipBehavior,
        )

        if self.style_key not in Wrap.shared_styles:
            self.css_class = f"shared-wrap-{len(Wrap.shared_styles)}"
            Wrap.shared_styles[self.style_key] = self.css_class
        else:
            self.css_class = Wrap.shared_styles[self.style_key]

    def render_props(self) -> Dict[str, Any]:
        """Return properties for the Reconciler."""
        props = {
            'css_class': self.css_class,
            'direction': self.direction,
            'alignment': self.alignment,
            'spacing': self.spacing,
            'runAlignment': self.runAlignment,
            'runSpacing': self.runSpacing,
            'crossAxisAlignment': self.crossAxisAlignment,
            'clipBehavior': self.clipBehavior,
            # Children diffing handled separately
        }
        return {k: v for k, v in props.items() if v is not None}

    def get_required_css_classes(self) -> Set[str]:
        """Return the set of CSS class names needed."""
        return {self.css_class}

    @staticmethod
    def generate_css_rule(style_key: Tuple, css_class: str) -> str:
        """Static method for Reconciler to generate CSS for Wrap container."""
        try:
            # Unpack key
            (direction, alignment, spacing, runAlignment,
             runSpacing, crossAxisAlignment, clipBehavior) = style_key

            # --- Determine CSS Flexbox Properties for Wrapping ---
            flex_direction = 'row' if direction == Axis.HORIZONTAL else 'column'

            # Main axis alignment (within a run) -> justify-content
            justify_content_val = alignment

            # Cross axis alignment (within a run) -> align-items
            align_items_val = crossAxisAlignment

            # Run alignment (between runs) -> align-content
            align_content_val = runAlignment

            # Spacing & RunSpacing -> gap property
            # gap: row-gap column-gap;
            row_gap = runSpacing if direction == Axis.HORIZONTAL else spacing
            column_gap = spacing if direction == Axis.HORIZONTAL else runSpacing
            gap_style = f"gap: {row_gap}px {column_gap}px;"

            # Clipping
            clip_style = ""
            if clipBehavior != ClipBehavior.NONE:
                 clip_style = "overflow: hidden;" # Basic clipping

            # Combine styles
            styles = (
                f"display: flex; "
                f"flex-wrap: wrap; " # <<< Enable wrapping
                f"flex-direction: {flex_direction}; "
                f"justify-content: {justify_content_val}; " # Alignment within run
                f"align-items: {align_items_val}; "       # Cross alignment within run
                f"align-content: {align_content_val}; "   # Alignment between runs
                f"{gap_style} "
                f"{clip_style} "
                f"box-sizing: border-box; "
                # Default sizing? Wrap often sizes to content or needs parent constraints.
                # "width: 100%;" # Add if typically expected to fill width
            )

            return f".{css_class} {{ {styles} }}"

        except Exception as e:
            print(f"Error generating CSS for Wrap {css_class} with key {style_key}: {e}")
            return f"/* Error generating rule for .{css_class} */"

    # Removed instance methods: to_html()


class Dialog(Widget):
    """
    Displays an M3-style Dialog box within the main application window.
    Visibility is controlled externally. Doesn't create a separate native window.
    Compatible with the reconciliation rendering system.
    """
    shared_styles: Dict[Tuple, str] = {}

    # Remove Singleton pattern (__new__)

    def __init__(self,
                 key: Optional[Key] = None, # Key for the Dialog itself
                 # --- Content Slots ---
                 icon: Optional[Widget] = None, # Optional icon at the top
                 title: Optional[Widget] = None, # Usually Text
                 content: Optional[Widget] = None, # Main body content
                 actions: Optional[List[Widget]] = None, # Usually TextButtons/Buttons
                 # --- Styling (M3 Inspired) ---
                 backgroundColor: Optional[str] = None, # M3 Surface Container High
                 shape: Optional[BorderRadius] = None, # M3 Shape (Corner radius)
                 elevation: Optional[float] = 3.0, # M3 Elevation Level 3
                 shadowColor: Optional[str] = Colors.rgba(0,0,0,0.25), # Approx shadow
                 padding: Optional[EdgeInsets] = None, # Padding for overall dialog container
                 iconPadding: Optional[EdgeInsets] = None,
                 titlePadding: Optional[EdgeInsets] = None,
                 contentPadding: Optional[EdgeInsets] = None,
                 actionsPadding: Optional[EdgeInsets] = None,
                 # --- Behavior (Info for external controller) ---
                 isModal: bool = True, # Typically modal
                 barrierColor: Optional[str] = Colors.rgba(0, 0, 0, 0.4), # M3 Scrim
                 # Callbacks (triggered by actions)
                 # Dismissal often handled by action buttons calling a close function
                 # onDismissed: Optional[Callable] = None, # Not directly part of Dialog widget
                 # onDismissedName: Optional[str] = None,
                 # --- State ---
                 # is_open: bool = False, # Managed externally
                 ):

        # Collect children in order
        children = []
        if icon: children.append(icon)
        if title: children.append(title)
        if content: children.append(content)
        if actions: children.extend(actions)

        super().__init__(key=key, children=children)

        # Store references and properties
        self.icon = icon
        self.title = title
        self.content = content
        self.actions = actions or []
        self.backgroundColor = backgroundColor or Colors.surfaceContainerHigh or '#ECE6F0'
        self.shape = shape or BorderRadius.all(28) # M3 Large shape
        self.elevation = elevation
        self.shadowColor = shadowColor
        self.padding = padding or EdgeInsets.all(24) # M3 Default padding
        # Default internal paddings (adjust as needed)
        self.iconPadding = iconPadding or EdgeInsets.only(bottom=16)
        self.titlePadding = titlePadding or EdgeInsets.only(bottom=16)
        self.contentPadding = contentPadding or EdgeInsets.only(bottom=24)
        self.actionsPadding = actionsPadding or EdgeInsets.only(top=8) # Space above actions

        self.isModal = isModal
        self.barrierColor = barrierColor

        # --- CSS Class Management ---
        self.style_key = (
            self.backgroundColor,
            make_hashable(self.shape),
            self.elevation,
            self.shadowColor,
            make_hashable(self.padding),
            # Include internal paddings if they affect the main CSS class
            make_hashable(self.iconPadding),
            make_hashable(self.titlePadding),
            make_hashable(self.contentPadding),
            make_hashable(self.actionsPadding),
        )

        if self.style_key not in Dialog.shared_styles:
            self.css_class = f"shared-dialog-{len(Dialog.shared_styles)}"
            Dialog.shared_styles[self.style_key] = self.css_class
        else:
            self.css_class = Dialog.shared_styles[self.style_key]

    def render_props(self) -> Dict[str, Any]:
        """Return properties for the Reconciler."""
        props = {
            'css_class': self.css_class,
            'backgroundColor': self.backgroundColor, # Pass for potential override
            'shape': self._get_render_safe_prop(self.shape),
            'elevation': self.elevation,
            'shadowColor': self.shadowColor,
            'padding': self._get_render_safe_prop(self.padding),
            'iconPadding': self._get_render_safe_prop(self.iconPadding),
            'titlePadding': self._get_render_safe_prop(self.titlePadding),
            'contentPadding': self._get_render_safe_prop(self.contentPadding),
            'actionsPadding': self._get_render_safe_prop(self.actionsPadding),
            'isModal': self.isModal, # Info for Framework/JS
            'barrierColor': self.barrierColor, # Info for Framework/JS
            # Flags for reconciler structure generation
            'has_icon': bool(self.icon),
            'has_title': bool(self.title),
            'has_content': bool(self.content),
            'has_actions': bool(self.actions),
        }
        return {k: v for k, v in props.items() if v is not None}

    def get_required_css_classes(self) -> Set[str]:
        """Return the set of CSS class names needed."""
        return {self.css_class}

    @staticmethod
    def generate_css_rule(style_key: Tuple, css_class: str) -> str:
        """Static method for Reconciler to generate CSS for Dialog structure."""
        try:
            # Unpack key
            (backgroundColor, shape_repr, elevation, shadowColor, padding_repr,
             iconPad_repr, titlePad_repr, contentPad_repr, actionsPad_repr) = style_key

            # --- Base Dialog Styles ---
            # Fixed position, centered, animation setup
            base_styles = f"""
                position: fixed;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%) scale(0.9); /* Start slightly small */
                opacity: 0;
                max-width: calc(100vw - 32px); /* Prevent touching edges */
                width: 320px; /* M3 typical width */
                max-height: calc(100vh - 32px);
                background-color: {backgroundColor};
                /* Shape/Radius */
                {'border-radius: {shape_repr.top_left}px {shape_repr.top_right}px {shape_repr.bottom_right}px {shape_repr.bottom_left}px;'.format(shape_repr=shape_repr) if isinstance(shape_repr, BorderRadius) else f'border-radius: {shape_repr}px;' if isinstance(shape_repr, int) else 'border-radius: 28px;'}
                z-index: 1300; /* High z-index for dialogs */
                transition: transform 0.2s cubic-bezier(0.4, 0.0, 0.2, 1), /* M3 Easing */
                            opacity 0.15s linear;
                display: flex;
                flex-direction: column; /* Stack icon/title/content/actions */
                overflow: hidden; /* Hide overflow during animation/layout */
                box-sizing: border-box;
                pointer-events: none; /* Allow clicks through when hidden */
            """

            # Elevation/Shadow (M3 Level 3)
            shadow_style = ""
            if elevation and elevation >= 3:
                shadow_str = f"box-shadow: 0px 3px 5px -1px {shadowColor or 'rgba(0, 0, 0, 0.2)'}, 0px 6px 10px 0px {shadowColor or 'rgba(0, 0, 0, 0.14)'}, 0px 1px 18px 0px {shadowColor or 'rgba(0, 0, 0, 0.12)'};"
            elif elevation and elevation > 0: # Fallback shadow
                 shadow_str = f"box-shadow: 0px 1px 3px 0px {shadowColor or 'rgba(0, 0, 0, 0.3)'}, 0px 1px 1px 0px {shadowColor or 'rgba(0, 0, 0, 0.15)'};"
            base_styles += shadow_str

            # --- Child Slot Wrapper Styles ---
            # Padding applied via these wrappers
            main_padding_obj = padding_repr # Overall dialog padding
            main_pad_style = ""
            if isinstance(main_padding_obj, EdgeInsets): main_pad_style = main_padding_obj.to_css()
            elif main_padding_obj: main_pad_style = f"padding: {main_padding_obj};"

            icon_pad_obj = iconPad_repr
            icon_pad_style = ""
            if isinstance(icon_pad_obj, EdgeInsets): icon_pad_style = icon_pad_obj.to_css()
            elif icon_pad_obj: icon_pad_style = f"padding: {icon_pad_obj};"

            title_pad_obj = titlePad_repr
            title_pad_style = ""
            if isinstance(title_pad_obj, EdgeInsets): title_pad_style = title_pad_obj.to_css()
            elif title_pad_obj: title_pad_style = f"padding: {title_pad_obj};"

            content_pad_obj = contentPad_repr
            content_pad_style = ""
            if isinstance(content_pad_obj, EdgeInsets): content_pad_style = content_pad_obj.to_css()
            elif content_pad_obj: content_pad_style = f"padding: {content_pad_obj};"

            actions_pad_obj = actionsPad_repr
            actions_pad_style = ""
            if isinstance(actions_pad_obj, EdgeInsets): actions_pad_style = actions_pad_obj.to_css()
            elif actions_pad_obj: actions_pad_style = f"padding: {actions_pad_obj};"

            # Styles for wrappers added by reconciler
            icon_styles = f"padding: {icon_pad_style or '0 0 16px 0'}; text-align: center;"
            title_styles = f"padding: {title_pad_style or '0 0 16px 0'}; text-align: center; font-size: 24px; font-weight: 400; color: {Colors.onSurface or '#1C1B1F'};" # M3 Headline Small
            content_styles = f"padding: {content_pad_style or '0 0 24px 0'}; flex-grow: 1; overflow-y: auto; color: {Colors.onSurfaceVariant or '#49454F'}; font-size: 14px; line-height: 20px;" # M3 Body Medium
            actions_styles = f"padding: {actions_pad_style or '8px 0 0 0'}; display: flex; justify-content: flex-end; gap: 8px; flex-shrink: 0;" # Align actions to end (right)


            # --- Open State ---
            open_styles = f"""
            .{css_class}.open {{
                transform: translate(-50%, -50%) scale(1); /* Scale to full size */
                opacity: 1;
                pointer-events: auto; /* Allow interaction */
            }}
            """

             # --- Scrim Styles --- (Duplicated from BottomSheet/Drawer - could be global)
            scrim_color = Colors.rgba(0, 0, 0, 0.4) # Approx M3 Scrim
            scrim_styles = f"""
            .dialog-scrim {{ /* Use a specific class for dialog scrim */
                position: fixed; top: 0; left: 0; right: 0; bottom: 0;
                background-color: {scrim_color};
                opacity: 0; visibility: hidden;
                transition: opacity 0.2s linear, visibility 0.2s;
                z-index: 1299; /* Below dialog, above everything else */
                pointer-events: none; /* Default */
            }}
            """
            scrim_active_styles = """
            .dialog-scrim.active {
                 opacity: 1; visibility: visible; pointer-events: auto; /* Allow click to dismiss */
            }
            """

            # --- Assemble Rules ---
            rules = [
                 f".{css_class} {{ {base_styles} }}",
                 # Wrappers added by reconciler
                 f".{css_class} > .dialog-icon {{ {icon_styles} }}",
                 f".{css_class} > .dialog-title {{ {title_styles} }}",
                 f".{css_class} > .dialog-content {{ {content_styles} }}",
                 f".{css_class} > .dialog-actions {{ {actions_styles} }}",
                 open_styles,
                 scrim_styles, # Include scrim styles
                 scrim_active_styles
            ]
            return "\n".join(rules)

        except Exception as e:
            print(f"Error generating CSS for Dialog {css_class} with key {style_key}: {e}")
            return f"/* Error generating rule for .{css_class} */"

    # Removed: __new__, to_html()