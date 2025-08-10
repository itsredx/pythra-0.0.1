# pythra/widgets.py
import uuid
import yaml
import os
import html
from .api import Api
from .base import *
from .state import *
from .styles import *
from .icons import *
from .controllers import *
from .config import Config
from .events import TapDetails, PanUpdateDetails
import weakref
from typing import Any, Dict, List, Optional, Set, Tuple, Union, Callable


from .drawing import (
    PathCommandWidget, 
    MoveTo, 
    LineTo,
    ClosePath,
    ArcTo,
) # Import the new command widgets
#from .drawing import Path

config = Config()
assets_dir = config.get('assets_dir', 'assets')
port = config.get('assets_server_port')
#Colors = Colors()



class Container(Widget):
    """
    A layout widget that serves as a styled box to contain a single child widget.
    Now supports animated gradient backgrounds.
    """
    shared_styles: Dict[Tuple, str] = {}

    def __init__(self,
                 child: Optional[Widget] = None,
                 key: Optional[Key] = None,
                 padding: Optional[EdgeInsets] = None,
                 color: Optional[str] = None,
                 decoration: Optional[BoxDecoration] = None,
                 width: Optional[Any] = None,
                 height: Optional[Any] = None,
                 constraints: Optional[BoxConstraints] = None,
                 margin: Optional[EdgeInsets] = None,
                 transform: Optional[str] = None,
                 alignment: Optional[Alignment] = None,
                 clipBehavior: Optional[ClipBehavior] = None,
                 visible: bool = True,
                 gradient: Optional[GradientTheme] = None): # <-- NEW PARAMETER

        super().__init__(key=key, children=[child] if child else [])

        self.padding = padding
        self.color = color
        self.decoration = decoration
        self.width = width
        self.height = height
        self.constraints = constraints
        self.margin = margin
        self.transform = transform
        self.alignment = alignment
        self.clipBehavior = clipBehavior
        self.visible = visible
        self.gradient = gradient # <-- STORE IT

        # --- UPDATED CSS Class Management ---
        # The style key now includes the gradient theme.
        self.style_key = tuple(make_hashable(prop) for prop in (
            self.padding, self.color, self.decoration, self.width, self.height,
            self.constraints, self.margin, self.transform, self.alignment,
            self.clipBehavior, self.gradient # <-- ADD GRADIENT TO KEY
        ))

        if self.style_key not in Container.shared_styles:
            self.css_class = f"shared-container-{len(Container.shared_styles)}"
            Container.shared_styles[self.style_key] = self.css_class
        else:
            self.css_class = Container.shared_styles[self.style_key]

    def render_props(self) -> Dict[str, Any]:
        # This method remains the same, as all styling is baked into the CSS class.
        instance_styles = {}
        if not self.visible:
            instance_styles['display'] = 'none'
        else: instance_styles['display'] = 'block'
        
        # We can remove 'display: block' as the CSS rule will handle it.
        # This makes the props cleaner.

        return {
            'css_class': self.css_class,
            'style': instance_styles if not self.visible else {}
        }

    def get_required_css_classes(self) -> Set[str]:
        return {self.css_class}

    @staticmethod
    def generate_css_rule(style_key: Tuple, css_class: str) -> str:
        """
        Static method updated to generate CSS for solid colors OR animated gradients.
        """
        try:
            # 1. Unpack the style_key tuple, now with the gradient at the end.
            (padding_tuple, color, decoration_tuple, width, height,
             constraints_tuple, margin_tuple, transform, alignment_tuple,
             clipBehavior, gradient_tuple) = style_key

            styles = ["box-sizing: border-box;"]
            extra_rules = [] # For storing @keyframes

            # --- HANDLE GRADIENT BACKGROUND ---
            if gradient_tuple:
                grad_theme = GradientTheme(*gradient_tuple)
                gradient_str = ", ".join(grad_theme.gradientColors)
                
                if grad_theme.rotationSpeed:
                    # --- TRUE ROTATING GRADIENT LOGIC (using @property) ---
                    
                    # 1. Register a custom property for the gradient angle.
                    #    This tells the browser it's a real angle it can animate.
                    extra_rules.append(f"""
                    @property --gradient-angle-{css_class} {{
                        syntax: '<angle>';
                        initial-value: 0deg;
                        inherits: false;
                    }}
                    """)

                    # 2. Define the keyframe animation for the angle property.
                    keyframes_name = f"bgRotate-{css_class}"
                    extra_rules.append(f"""
                    @keyframes {keyframes_name} {{
                        0% {{ --gradient-angle-{css_class}: 0deg; }}
                        100% {{ --gradient-angle-{css_class}: 360deg; }}
                    }}
                    """)

                    # 3. Style the main container to use the conic-gradient and the animation.
                    #    We use a repeating-conic-gradient for a seamless loop.
                    styles.extend([
                        f"background: repeating-conic-gradient(from var(--gradient-angle-{css_class}), {gradient_str});",
                        f"animation: {keyframes_name} {grad_theme.rotationSpeed} linear infinite;"
                    ])

                else:
                    # --- SCROLLING (existing) GRADIENT LOGIC ---
                    keyframes_name = f"bgShift-{css_class}"
                    extra_rules.append(f"""
                    @keyframes {keyframes_name} {{
                        0% {{ background-position: 0% 50%; }}
                        50% {{ background-position: 100% 50%; }}
                        100% {{ background-position: 0% 50%; }}
                    }}
                    """)
                    styles.append(f"background: linear-gradient({grad_theme.gradientDirection}, {gradient_str});")
                    styles.append("background-size: 400% 400%;")
                    styles.append(f"animation: {keyframes_name} {grad_theme.animationSpeed} {grad_theme.animationTiming} infinite;")

            # Handle Decoration and solid Color (if no gradient is present)
            elif decoration_tuple and isinstance(decoration_tuple, tuple):
                deco_obj = BoxDecoration(*decoration_tuple)
                styles.append(deco_obj.to_css())

            if color and not gradient_tuple: # Solid color only applies if there's no gradient
                styles.append(f"background: {color};")
            
            # --- The rest of the styling logic remains the same ---
            if padding_tuple: styles.append(f"padding: {EdgeInsets(*padding_tuple).to_css_value()};")
            if margin_tuple: styles.append(f"margin: {EdgeInsets(*margin_tuple).to_css_value()};")
            if width is not None: styles.append(f"width: {width}px;" if isinstance(width, (int, float)) else f"width: {width};")
            if height is not None: styles.append(f"height: {height}px;" if isinstance(height, (int, float)) else f"height: {height};")
            
            if constraints_tuple:
                styles.append(BoxConstraints(*constraints_tuple).to_css())

            if alignment_tuple:
                align_obj = Alignment(*alignment_tuple)
                styles.append("display: flex;")
                styles.append(f"justify-content: {align_obj.justify_content};")
                styles.append(f"align-items: {align_obj.align_items};")

            if transform: styles.append(f"transform: {transform};")

            if clipBehavior and hasattr(clipBehavior, 'to_css_overflow'):
                overflow_val = clipBehavior.to_css_overflow()
                if overflow_val: styles.append(f"overflow: {overflow_val};")
            
            # Assemble and return the final CSS rules.
            main_rule = f".{css_class} {{ {' '.join(filter(None, styles))} }}"
            
            # Prepend any extra rules (like @keyframes) to the main rule
            return "\n".join(extra_rules) + "\n" + main_rule

        except Exception as e:
            import traceback
            print(f"ERROR generating CSS for Container {css_class} with key {style_key}:")
            traceback.print_exc()
            return f"/* Error generating rule for .{css_class} */"



# class Container(Widget):
#     """
#     A layout widget that serves as a styled box to contain a single child widget.

#     The `Container` widget allows styling and positioning of its child through various
#     layout and style properties like padding, margin, width, height, background color,
#     decoration, alignment, and more. It automatically generates and reuses shared CSS
#     class names for identical style combinations to avoid redundancy and optimize rendering.
#     """

#     # Class-level cache for mapping unique style definitions to a CSS class name.
#     # Key: A hashable tuple representing a unique combination of style properties.
#     # Value: A generated unique CSS class name (e.g., "shared-container-0").
#     shared_styles: Dict[Tuple, str] = {}
#     visible_bool: bool = True

#     def __init__(self,
#                  child: Optional[Widget] = None,
#                  key: Optional[Key] = None,
#                  padding: Optional[EdgeInsets] = None,
#                  color: Optional[str] = None,
#                  decoration: Optional[BoxDecoration] = None,
#                  width: Optional[Any] = None,
#                  height: Optional[Any] = None,
#                  constraints: Optional[BoxConstraints] = None,
#                  margin: Optional[EdgeInsets] = None,
#                  transform: Optional[str] = None,
#                  alignment: Optional[Alignment] = None,
#                  clipBehavior: Optional[ClipBehavior] = None,
#                  visible: bool = True,
#                  ):

#         super().__init__(key=key, children=[child] if child else [])

#         # --- Store all style properties ---
#         self.padding = padding
#         self.color = color
#         self.decoration = decoration
#         self.width = width
#         self.height = height
#         self.constraints = constraints
#         self.margin = margin
#         self.transform = transform
#         self.alignment = alignment
#         self.clipBehavior = clipBehavior
#         self.visible = visible

#         # --- CSS Class Management ---
#         # 1. Create a unique, hashable key from all style properties.
#         #    The `make_hashable` helper is crucial here. It converts style objects
#         #    like EdgeInsets into tuples, making them usable as dictionary keys.
#         self.style_key = tuple(make_hashable(prop) for prop in (
#             self.padding, self.color, self.decoration, self.width, self.height,
#             self.constraints, self.margin, self.transform, self.alignment,
#             self.clipBehavior,
#         ))

#         Container.visible_bool = self.visible
#         # print(self.style_key)

#         # 2. Check the cache. If this style combination is new, create a new class.
#         #    Otherwise, reuse the existing one.
#         if self.style_key not in Container.shared_styles:
#             self.css_class = f"shared-container-{len(Container.shared_styles)}"
#             Container.shared_styles[self.style_key] = self.css_class
#         else:
#             self.css_class = Container.shared_styles[self.style_key]

#     def render_props(self) -> Dict[str, Any]:
#         """
#         Return properties for diffing. For a styled container, the only property
#         that matters for rendering is the CSS class, as all styles are baked into it.
#         """
#         # This simplification is key. The DOM element only needs its class.
#         # The complex style logic lives entirely in the CSS generation.
#         # --- NEW LOGIC ---
#         instance_styles = {}
#         if not self.visible:
#             instance_styles['display'] = 'none'
#         else: instance_styles['display'] = 'block'

#         return {
#             'css_class': self.css_class,
#             'style': instance_styles # Pass the dynamic styles here
#             }

#     def get_required_css_classes(self) -> Set[str]:
#         """Return the shared class name needed for this instance."""
#         return {self.css_class}

#     @staticmethod
#     def generate_css_rule(style_key: Tuple, css_class: str) -> str:
#         """
#         Static method that correctly unpacks the style_key and generates the CSS rule.
#         This is called by the Reconciler when it encounters a new CSS class.
#         """
#         try:
#             # 1. Unpack the style_key tuple. The order MUST match the creation order in __init__.
#             (padding_tuple, color, decoration_tuple, width, height,
#              constraints_tuple, margin_tuple, transform, alignment_tuple,
#              clipBehavior) = style_key

#             styles = ["box-sizing: border-box;"]

#             # if not visible:
#             #     styles.append("display: none;")

#             # 2. Reconstruct style objects from their tuple representations and generate CSS.

#             # Handle Decoration and Color. Decoration can also contain a color.
#             # If both are present, the explicit `color` property overrides the one in `decoration`.
#             if decoration_tuple and isinstance(decoration_tuple, tuple):
#                 # Reconstruct from the tuple created by `make_hashable`.
#                 # This assumes BoxDecoration.to_tuple() produces a tuple that
#                 # matches the __init__ signature.
#                 deco_obj = BoxDecoration(*decoration_tuple)
#                 # print("Container Deco: ",deco_obj.to_css())
#                 styles.append(deco_obj.to_css())

#             if color:
#                 # This will override any background-color from decoration if present.
#                 styles.append(f"background: {color};")
            
#             # Handle Padding and Margin
#             if padding_tuple and isinstance(padding_tuple, tuple):
#                 styles.append(f"padding: {EdgeInsets(*padding_tuple).to_css_value()};")
            
#             if margin_tuple and isinstance(margin_tuple, tuple):
#                 styles.append(f"margin: {EdgeInsets(*margin_tuple).to_css_value()};")
#                 # print(f"margin: {EdgeInsets(*margin_tuple).to_css_value()};")

#             # Handle explicit Width and Height
#             if width is not None:
#                 styles.append(f"width: {width}px;" if isinstance(width, (int, float)) else f"width: {width};")

#             if height is not None:
#                 styles.append(f"height: {height}px;" if isinstance(height, (int, float)) else f"height: {height};")
            
#             # Handle BoxConstraints
#             if constraints_tuple and isinstance(constraints_tuple, tuple):
#                 constraints_obj = BoxConstraints(*constraints_tuple)
#                 styles.append(constraints_obj.to_css())

#             # Handle Alignment (for positioning the child)
#             if alignment_tuple and isinstance(alignment_tuple, tuple):
#                 align_obj = Alignment(*alignment_tuple)
#                 # An alignment object implies a flex container to position the child
#                 styles.append("display: flex;")
#                 styles.append(f"justify-content: {align_obj.justify_content};")
#                 styles.append(f"align-items: {align_obj.align_items};")

#             # Handle Transform
#             if transform:
#                 styles.append(f"transform: {transform};")

#             # Handle Clipping
#             if clipBehavior and hasattr(clipBehavior, 'to_css_overflow'):
#                 overflow_val = clipBehavior.to_css_overflow()
#                 if overflow_val:
#                     styles.append(f"overflow: {overflow_val};")
            
#             # 3. Assemble and return the final CSS rule.
#             # The `filter(None, ...)` removes any empty strings from the list.
#             return f".{css_class} {{ {' '.join(filter(None, styles))} }}"

#         except Exception as e:
#             import traceback
#             print(f"ERROR generating CSS for Container {css_class} with key {style_key}:")
#             traceback.print_exc()
#             return f"/* Error generating rule for .{css_class} */"


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
            self.style.to_css() if self.style else self.style, self.textAlign, self.overflow
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
            style_str = style if style else ''
            # print("Style str: ", style)
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
                 style: Optional[ButtonStyle] = None,
                 onPressedArgs: Optional[List] = [],
                 ):

        # Pass key and child list to the base Widget constructor
        super().__init__(key=key, children=[child])
        self.child = child # Keep reference if needed

        # Store callback and its identifier
        self.onPressed = onPressed
        # Determine the name/identifier to use in HTML/JS
        # Priority: Explicit name > function name > None
        self.onPressed_id = onPressedName if onPressedName else (onPressed.__name__ if onPressed else None)

        self.style = style or ButtonStyle() # Use default ButtonStyle if none provided
        self.onPressedArgs = onPressedArgs

        # --- CSS Class Management ---
        # Use make_hashable or ensure ButtonStyle itself is hashable
        # For TextButton, often only a subset of ButtonStyle matters, but let's hash the whole object for now
        self.style_key = (make_hashable(self.style.to_css()),)

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
            'onPressedName': self.onPressed_id,
            'onPressedArgs': self.onPressedArgs,
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
            # --- Unpack the style_key tuple ---
            # Assumes order from ButtonStyle.to_tuple() or make_hashable(ButtonStyle)
            # This MUST match the structure created in __init__
            try:
                # Option A: style_key = (hashable_button_style_repr,)
                style_repr = style_key[0] # Get the representation
                print(style_repr)

                # Option B: style_key = (prop1, prop2, ...) - unpack directly
                # (textColor, textStyle_tuple, padding_tuple, ...) = style_key # Example unpack

            except (ValueError, TypeError, IndexError) as unpack_error:
                 print(f"Warning: Could not unpack style_key for TextButton {css_class}. Using defaults. Key: {style_key}. Error: {unpack_error}")
                 style_repr = None # Will trigger default ButtonStyle() below

            # --- Reconstruct/Access ButtonStyle ---
            # This remains the most complex part depending on style_key structure
            style_obj = None
            try:
                 if isinstance(style_repr, tuple): # Check if it's a tuple of props
                      # Attempt reconstruction (requires knowing tuple order)
                      # style_obj = ButtonStyle(*style_repr) # Example if tuple matches init
                      pass # Skip reconstruction for now, access values if possible or use defaults
                 elif isinstance(style_repr, ButtonStyle): # If key stored the object directly
                      style_obj = style_repr
            except Exception as recon_error:
                 print(f"Warning: Error reconstructing ButtonStyle for {css_class} from key. Error: {recon_error}")

            if not isinstance(style_obj, ButtonStyle):
                 # print(f"  Using default fallback style for TextButton {css_class}")
                 style_obj = ButtonStyle() # Default (or TextButton specific defaults)

            # Use getattr for safe access
            # M3 Text Buttons often use Primary color for text
            fg_color = getattr(style_obj, 'foregroundColor', Colors.primary or '#6750A4')
            bg_color = getattr(style_obj, 'backgroundColor', 'transparent') # Usually transparent
            padding_obj = getattr(style_obj, 'padding', EdgeInsets.symmetric(horizontal=12)) # M3 has specific padding
            # print("Padding: ", style_obj.padding)
            text_style_obj = getattr(style_obj, 'textStyle', None) # Get text style if provided
            shape_obj = getattr(style_obj, 'shape', BorderRadius.all(20)) # M3 full rounded shape often
            min_height = getattr(style_obj, 'minimumSize', (None, 40)) or 40 # M3 min height 40px

            # --- Base TextButton Styles (M3 Inspired) ---
            base_styles_dict = {
                'display': 'inline-flex',
                'align-items': 'center',
                'justify-content': 'center',
                # 'padding': padding_obj.to_css() if padding_obj else '4px 12px', # Use style padding or M3-like default
                # 'margin': '4px', # Default margin between adjacent buttons
                'border': 'none', # Text buttons have no border
                # 'border-radius': shape_obj.to_css_value() if isinstance(shape_obj, BorderRadius) else f"{shape_obj or 20}px", # Use shape or M3 default
                # 'background-color': bg_color or 'transparent',
                # 'color': fg_color, # Use style foreground or M3 primary
                'cursor': 'pointer',
                'text-align': 'center',
                'text-decoration': 'none',
                'outline': 'none',
                # 'min-height': f"{min_height}px", # M3 min target size
                'min-width': '48px', # Ensure min width for touch target even if padding is small
                'box-sizing': 'border-box',
                'position': 'relative', # For state layer/ripple
                'overflow': 'hidden', # Clip state layer/ripple
                'transition': 'background-color 0.15s linear', # For hover/active state
                '-webkit-appearance': 'none',
                '-moz-appearance': 'none',
                'appearance': 'none',
                
            }

            # --- Assemble Main Rule ---
            main_rule = f".{css_class} {{ {' '.join(f'{k}: {v};' for k, v in base_styles_dict.items())} {style_repr}}}"

            # --- State Styles ---
            # M3 uses semi-transparent state layers matching the text color
            hover_bg_color = Colors.rgba(0,0,0,0.08) # Fallback dark overlay
            active_bg_color = Colors.rgba(0,0,0,0.12) # Fallback dark overlay
            try: # Try to make overlay from foreground color
                 # Basic check: Assume hex format #RRGGBB
                 if fg_color and fg_color.startswith('#') and len(fg_color) == 7:
                     r, g, b = int(fg_color[1:3], 16), int(fg_color[3:5], 16), int(fg_color[5:7], 16)
                     hover_bg_color = Colors.rgba(r, g, b, 0.50) # 8% opacity overlay
                     active_bg_color = Colors.rgba(r, g, b, 0.00) # 12% opacity overlay
            except: pass # Ignore errors, use fallback

            hover_rule = f".{css_class}:hover {{ background-color: transparent; color: red; }}"
            active_rule = f".{css_class}:active {{ background-color: {active_bg_color}; }}"

            # Disabled state
            disabled_color = Colors.rgba(0,0,0,0.38) # M3 Disabled content approx
            disabled_rule = f".{css_class}.disabled {{ color: {disabled_color}; background-color: transparent; cursor: default; pointer-events: none; }}"

            # Apply TextStyle to children (e.g., direct Text widget child)
            text_style_rule = ""
            if isinstance(text_style_obj, TextStyle):
                 # Apply base text style - M3 uses Button label style
                 base_text_styles = "font-weight: 500; font-size: 14px; letter-spacing: 0.1px; line-height: 20px;"
                 # Merge with specific TextStyle passed in
                 specific_text_styles = text_style_obj.to_css()
                 text_style_rule = f".{css_class} > * {{ {base_text_styles} {specific_text_styles} }}"
            else:
                  # Apply default M3 Button label style if no TextStyle provided
                  default_text_styles = "font-weight: 500; font-size: 14px; letter-spacing: 0.1px; line-height: 20px;"
                  text_style_rule = f".{css_class} > * {{ {default_text_styles} }}"

            # print("\n".join([main_rule, text_style_rule, hover_rule, active_rule, disabled_rule]))
            return "\n".join([main_rule, text_style_rule, hover_rule, active_rule, disabled_rule])

        except Exception as e:
            import traceback
            print(f"Error generating CSS for TextButton {css_class} with key {style_key}: {e}")
            traceback.print_exc()
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
                 style: Optional[ButtonStyle] = None,
                 callbackArgs: Optional[List] = None):

        super().__init__(key=key, children=[child])
        self.child = child

        self.onPressed = onPressed
        self.onPressed_id = onPressedName if onPressedName else (onPressed.__name__ if onPressed else None)
        self.callbackArgs = callbackArgs

        self.style = style or ButtonStyle( # Provide some sensible defaults for ElevatedButton
             backgroundColor=Colors.blue, # Example default
             foregroundColor=Colors.white, # Example default
             elevation=2,
             padding=EdgeInsets.symmetric(horizontal=16, vertical=8), # Example default
             margin=EdgeInsets.all(4)
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
            'onPressedName': self.onPressed_id,
            'onPressedArgs': self.callbackArgs if self.callbackArgs else [],
        }
        return {k: v for k, v in props.items() if v is not None}

    def get_required_css_classes(self) -> Set[str]:
        """Return the set of CSS class names needed."""
        return {self.css_class}

    # framework/widgets.py (Inside ElevatedButton class)

    @staticmethod
    def generate_css_rule(style_key: Tuple, css_class: str) -> str:
        """Static method callable by the Reconciler to generate the CSS rule."""
        try:
            # --- Unpack the style_key tuple ---
            # This order MUST match the order defined in ButtonStyle.to_tuple()
            # or the output of make_hashable(ButtonStyle(...))
            try:
                (bgColor, fgColor, disBgColor, disFgColor, shadowColor, elevation,
                 padding_tuple, margin_tuple, minSize_tuple, maxSize_tuple, side_tuple, shape_repr,
                 textStyle_tuple, alignment_tuple) = style_key
            except (ValueError, TypeError) as unpack_error:
                 # Handle cases where the key doesn't match the expected structure
                 print(f"Warning: Could not unpack style_key for ElevatedButton {css_class}. Using defaults. Key: {style_key}. Error: {unpack_error}")
                 # Set default values if unpacking fails
                 bgColor, fgColor, elevation = ('#6200ee', 'white', 2.0) # Basic defaults
                 padding_tuple, minSize_tuple, maxSize_tuple, side_tuple, shape_repr = (None,) * 5
                 textStyle_tuple, alignment_tuple, shadowColor, disBgColor, disFgColor = (None,) * 5


            # --- Base Button Styles ---
            base_styles_dict = {
                'display': 'inline-flex', # Use inline-flex to size with content but allow block behavior
                'align-items': 'center', # Vertically center icon/text
                'justify-content': 'center', # Horizontally center icon/text
                'padding': {EdgeInsets(*padding_tuple).to_css_value()} if padding_tuple else '8px 16px', # Default padding (M3 like)
                'margin': {EdgeInsets(*margin_tuple).to_css_value()} if margin_tuple else '4px', # Default margin
                'border': 'none', # Elevated buttons usually have no border by default
                'border-radius': '20px', # M3 full rounded shape (default for elevated)
                'background-color': bgColor or '#6200ee', # Use provided or default
                'color': fgColor or 'white', # Use provided or default
                'cursor': 'pointer',
                'text-align': 'center',
                'text-decoration': 'none',
                'outline': 'none',
                'box-sizing': 'border-box',
                'overflow': 'hidden', # Clip potential ripple effects
                'position': 'relative', # For potential ripple pseudo-elements
                'transition': 'box-shadow 0.28s cubic-bezier(0.4, 0, 0.2, 1), background-color 0.15s linear', # Smooth transitions
                '-webkit-appearance': 'none', # Reset default styles
                '-moz-appearance': 'none',
                'appearance': 'none',
            }

            # --- Apply specific styles from unpacked key ---

            # Padding
            if padding_tuple:
                 # Recreate EdgeInsets or use tuple directly if to_css_value works
                 try:
                      padding_obj = EdgeInsets(*padding_tuple) # Assumes tuple is (l,t,r,b)
                      base_styles_dict['padding'] = padding_obj.to_css_value()
                 except Exception: pass # Ignore if padding_tuple isn't valid

            if margin_tuple:
                 # Recreate EdgeInsets or use tuple directly if to_css_value works
                 try:
                      margin_obj = EdgeInsets(*margin_tuple) # Assumes tuple is (l,t,r,b)
                      base_styles_dict['margin'] = margin_obj.to_css_value()
                 except Exception: pass # Ignore if margin_tuple isn't valid

            # Minimum/Maximum Size
            if minSize_tuple:
                 min_w, min_h = minSize_tuple
                 if min_w is not None: base_styles_dict['min-width'] = f"{min_w}px"
                 if min_h is not None: base_styles_dict['min-height'] = f"{min_h}px"
            if maxSize_tuple:
                 max_w, max_h = maxSize_tuple
                 if max_w is not None: base_styles_dict['max-width'] = f"{max_w}px"
                 if max_h is not None: base_styles_dict['max-height'] = f"{max_h}px"

            # Border (Side)
            if side_tuple:
                 try:
                      side_obj = BorderSide(*side_tuple) # Assumes tuple is (w, style, color)
                      shorthand = side_obj.to_css_shorthand_value()
                      if shorthand != 'none': base_styles_dict['border'] = shorthand
                      else: base_styles_dict['border'] = 'none'
                 except Exception: pass

            # Shape (BorderRadius)
            if shape_repr:
                if isinstance(shape_repr, tuple) and len(shape_repr) == 4: # Assumes (tl, tr, br, bl)
                    try:
                         shape_obj = BorderRadius(*shape_repr)
                         base_styles_dict['border-radius'] = shape_obj.to_css_value()
                    except Exception: pass
                elif isinstance(shape_repr, (int, float)): # Single value
                     base_styles_dict['border-radius'] = f"{max(0.0, shape_repr)}px"

            # Elevation / Shadow
            effective_elevation = elevation if elevation is not None else 2.0 # Default elevation = 2
            if effective_elevation > 0:
                 # M3 Elevation Level 2 (approx)
                 offset_y = 1 + effective_elevation * 0.5
                 blur = 2 + effective_elevation * 1.0
                 spread = 0 # Generally 0 for M3 elevations 1-3
                 s_color = shadowColor or Colors.rgba(0,0,0,0.2)
                 # Use multiple shadows for better M3 feel
                 shadow1 = f"0px {offset_y * 0.5}px {blur * 0.5}px {spread}px rgba(0,0,0,0.15)" # Ambient
                 shadow2 = f"0px {offset_y}px {blur}px {spread+1}px rgba(0,0,0,0.10)" # Key
                 base_styles_dict['box-shadow'] = f"{shadow1}, {shadow2}"


            # Text Style (Apply to direct text children - using descendant selector)
            text_style_css = ""
            if textStyle_tuple:
                 try:
                      ts_obj = TextStyle(*textStyle_tuple) # Assumes tuple matches TextStyle init
                      text_style_css = ts_obj.to_css()
                 except Exception: pass

            # Alignment (Applies flex to button itself if needed for icon+label)
            if alignment_tuple:
                 try:
                      align_obj = Alignment(*alignment_tuple) # Assumes tuple is (justify, align)
                      base_styles_dict['display'] = 'inline-flex' # Use flex to align internal items
                      base_styles_dict['justify-content'] = align_obj.justify_content
                      base_styles_dict['align-items'] = align_obj.align_items
                      base_styles_dict['gap'] = '8px' # Default gap
                 except Exception: pass


            # --- Assemble CSS Rules ---
            main_rule = f".{css_class} {{ {' '.join(f'{k}: {v};' for k, v in base_styles_dict.items())} }}"

            # Hover state (M3: Raise elevation slightly, potentially overlay)
            hover_shadow_str = "" # Calculate slightly higher shadow based on elevation
            if effective_elevation > 0:
                  h_offset_y = 1 + (effective_elevation + 2) * 0.5 # Increase elevation effect
                  h_blur = 2 + (effective_elevation + 2) * 1.0
                  h_spread = 0
                  h_s_color = shadowColor or Colors.rgba(0,0,0,0.25) # Slightly darker?
                  h_shadow1 = f"0px {h_offset_y * 0.5}px {h_blur * 0.5}px {h_spread}px rgba(0,0,0,0.18)"
                  h_shadow2 = f"0px {h_offset_y}px {h_blur}px {h_spread+1}px rgba(0,0,0,0.13)"
                  hover_shadow_str = f"box-shadow: {h_shadow1}, {h_shadow2};"
            hover_rule = f".{css_class}:hover {{ {hover_shadow_str} /* Add background overlay? */ }}"

            # Active state (M3: Lower/remove elevation)
            active_rule = f".{css_class}:active {{ box-shadow: none; /* Add background overlay? */ }}"

            # Disabled state (Handled by adding .disabled class)
            disabled_bg = disBgColor or Colors.rgba(0,0,0,0.12) # M3 Disabled container approx
            disabled_fg = disFgColor or Colors.rgba(0,0,0,0.38) # M3 Disabled content approx
            disabled_rule = f".{css_class}.disabled {{ background-color: {disabled_bg}; color: {disabled_fg}; box-shadow: none; cursor: default; pointer-events: none; }}"

            # Apply text style to children (e.g., direct Text widget child)
            text_style_rule = ""
            if text_style_css:
                 # Target direct children or specific class if Text widget adds one
                 text_style_rule = f".{css_class} > * {{ {text_style_css} }}"


            return "\n".join([main_rule, hover_rule, active_rule, disabled_rule, text_style_rule])

        except Exception as e:
            import traceback
            print(f"Error generating CSS for ElevatedButton {css_class} with key {style_key}: {e}")
            traceback.print_exc()
            return f"/* Error generating rule for .{css_class} */"

    # Removed instance methods: to_html(), to_css(), to_js()


# --- IconButton Refactored ---
class IconButton(Widget):
    """
    A button containing an Icon, typically with minimal styling (transparent background).
    This widget is fully compatible with the declarative, CSS-driven reconciliation system.
    """
    # Class-level cache for mapping unique style definitions to a CSS class name.
    shared_styles: Dict[Tuple, str] = {}

    def __init__(self,
                 icon: Widget,  # The Icon widget is the required child
                 key: Optional[Key] = None,
                 onPressed: Optional[Callable] = None,
                 onPressedName: Optional[str] = None,
                 iconSize: Optional[int] = 24,  # Default M3 icon size
                 style: Optional[ButtonStyle] = None,
                 tooltip: Optional[str] = None,
                 enabled: bool = True):

        super().__init__(key=key, children=[icon])
        self.icon = icon

        self.onPressed = onPressed
        self.onPressed_id = onPressedName if onPressedName else (onPressed.__name__ if onPressed else None)

        # Use a default ButtonStyle if none is provided. This ensures self.style is never None.
        self.style = style if isinstance(style, ButtonStyle) else ButtonStyle()
        self.iconSize = iconSize
        self.tooltip = tooltip
        self.enabled = enabled

        # --- CSS Class Management ---
        # 1. Create a unique, hashable key from the ButtonStyle and iconSize.
        self.style_key = (
            make_hashable(self.style),  # Converts the ButtonStyle object to a hashable tuple
            self.iconSize,
        )

        # 2. Check the cache to reuse or create a new CSS class.
        if self.style_key not in IconButton.shared_styles:
            self.css_class = f"shared-iconbutton-{len(IconButton.shared_styles)}"
            IconButton.shared_styles[self.style_key] = self.css_class
        else:
            self.css_class = IconButton.shared_styles[self.style_key]

        # Dynamically add stateful classes for the current render
        self.current_css_class = f"{self.css_class} {'disabled' if not self.enabled else ''}"

    def render_props(self) -> Dict[str, Any]:
        """Return properties for diffing by the Reconciler."""
        # The DOM element only needs its class, callback name, and tooltip.
        # All complex styling is handled by the generated CSS.
        props = {
            'css_class': self.current_css_class,
            'onPressedName': self.onPressed_id,
            'tooltip': self.tooltip,
            'enabled': self.enabled, # Pass enabled state for JS if needed
        }
        return {k: v for k, v in props.items() if v is not None}

    def get_required_css_classes(self) -> Set[str]:
        """Return the base shared CSS class name needed."""
        return {self.css_class}

    @staticmethod
    def generate_css_rule(style_key: Tuple, css_class: str) -> str:
        """Static method callable by the Reconciler to generate the CSS rule."""
        try:
            # 1. Reliably unpack the style_key tuple.
            style_tuple, icon_size = style_key

            # 2. Reconstruct the ButtonStyle object from its tuple representation.
            # This relies on ButtonStyle having a to_tuple() method and an __init__
            # that can accept the unpacked tuple.
            # A safer but more verbose way is to have `make_hashable` produce a dict
            # and pass it as kwargs: `style_obj = ButtonStyle(**style_dict)`
            # Assuming a simple tuple for now:
            style_obj = ButtonStyle(*style_tuple)

            # --- Define Defaults and Extract Properties from Style Object ---
            default_padding = EdgeInsets.all(8)
            padding_obj = getattr(style_obj, 'padding', default_padding)
            bg_color = getattr(style_obj, 'backgroundColor', 'transparent')
            fg_color = getattr(style_obj, 'foregroundColor', 'inherit') # Default to inherit color
            border_obj = getattr(style_obj, 'side', None)
            shape_obj = getattr(style_obj, 'shape', None)

            # --- Base IconButton Styles (M3 Inspired) ---
            base_styles = {
                'display': 'inline-flex',
                'align-items': 'center',
                'justify-content': 'center',
                'padding': padding_obj.to_css_value() if isinstance(padding_obj, EdgeInsets) else '8px',
                'margin': '0',
                'border': 'none',
                'background-color': bg_color,
                'color': fg_color,
                'cursor': 'pointer',
                'outline': 'none',
                'border-radius': '50%',  # Default to circular
                'overflow': 'hidden',
                'position': 'relative',
                'box-sizing': 'border-box',
                'transition': 'background-color 0.15s linear',
                '-webkit-appearance': 'none', 'appearance': 'none',
            }

            # Calculate total size based on icon and padding
            h_padding = padding_obj.to_int_horizontal() if isinstance(padding_obj, EdgeInsets) else 16
            v_padding = padding_obj.to_int_vertical() if isinstance(padding_obj, EdgeInsets) else 16
            base_styles['width'] = f"calc({icon_size or 24}px + {h_padding}px)"
            base_styles['height'] = f"calc({icon_size or 24}px + {v_padding}px)"

            # Apply border and shape overrides from the style object
            if isinstance(border_obj, BorderSide):
                shorthand = border_obj.to_css_shorthand_value()
                if shorthand != 'none': base_styles['border'] = shorthand
            
            if shape_obj:
                if isinstance(shape_obj, BorderRadius):
                    base_styles['border-radius'] = shape_obj.to_css_value()
                elif isinstance(shape_obj, (int, float)):
                    base_styles['border-radius'] = f"{max(0.0, shape_obj)}px"

            # Assemble the main rule string
            main_rule_str = ' '.join(f'{k}: {v};' for k, v in base_styles.items())
            main_rule = f".{css_class} {{ {main_rule_str} }}"

            # --- Icon Styling (Child Selector) ---
            icon_rule = f"""
            .{css_class} > i, .{css_class} > img, .{css_class} > svg, .{css_class} > * {{
                font-size: {icon_size or 24}px;
                width: {icon_size or 24}px;
                height: {icon_size or 24}px;
                display: block;
                object-fit: contain;
            }}"""

            # --- State Styles ---
            # Create a semi-transparent overlay based on the foreground color for hover/active states
            hover_bg_color = 'rgba(0, 0, 0, 0.08)' # Default dark overlay
            active_bg_color = 'rgba(0, 0, 0, 0.12)'
            if fg_color and fg_color.startswith('#') and len(fg_color) == 7:
                 try:
                     r, g, b = int(fg_color[1:3], 16), int(fg_color[3:5], 16), int(fg_color[5:7], 16)
                     hover_bg_color = f'rgba({r}, {g}, {b}, 0.08)'
                     active_bg_color = f'rgba({r}, {g}, {b}, 0.12)'
                 except ValueError: pass # Keep defaults if hex parse fails

            hover_rule = f".{css_class}:hover {{ background-color: {hover_bg_color}; }}"
            active_rule = f".{css_class}:active {{ background-color: {active_bg_color}; }}"

            # Disabled state (applied via .disabled class by reconciler)
            disabled_color = 'rgba(0, 0, 0, 0.38)' # M3 disabled content color
            disabled_rule = f".{css_class}.disabled {{ color: {disabled_color}; background-color: transparent; cursor: default; pointer-events: none; }}"

            return "\n".join([main_rule, icon_rule, hover_rule, active_rule, disabled_rule])

        except Exception as e:
            import traceback
            print(f"ERROR generating CSS for IconButton {css_class} with key {style_key}:")
            traceback.print_exc()
            return f"/* Error generating rule for .{css_class} */"

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
            'onPressedName': self.onPressed_id,
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
            # This depends *exactly* on how the style_key was created.
            # Assuming style_key = make_hashable(self.style) which produces a tuple:
            try:
                # Example unpack based on assumed ButtonStyle.to_tuple() order
                (bgColor, fgColor, disBgColor, disFgColor, shadowColor, elevation,
                 padding_tuple, minSize_tuple, maxSize_tuple, side_tuple, shape_repr,
                 textStyle_tuple, alignment_tuple) = style_key
                style_reconstructed = True
            except (ValueError, TypeError) as unpack_error:
                 print(f"Warning: Could not unpack style_key for FAB {css_class}. Using defaults. Key: {style_key}. Error: {unpack_error}")
                 style_reconstructed = False
                 # Set defaults needed below if unpacking fails
                 bgColor = Colors.primaryContainer or '#EADDFF'
                 fgColor = Colors.onPrimaryContainer or '#21005D'
                 elevation = 6.0
                 shape_repr = 28 # Default radius for circular 56px FAB
                 shadowColor = Colors.shadow or '#000000'

            # --- Base FAB Styles ---
            # Define defaults using M3 roles where possible
            fab_size = 56 # Standard FAB size
            fab_padding = 16 # Standard FAB icon padding
            fab_radius = fab_size / 2 # Default circular

            # --- Apply Styles based on Unpacked/Default Values ---
            base_styles_dict = {
                'display': 'inline-flex',
                'align-items': 'center',
                'justify-content': 'center',
                'position': 'fixed', # FAB is fixed
                'bottom': '16px',   # Default position
                'right': '16px',    # Default position
                'width': f"{fab_size}px",
                'height': f"{fab_size}px",
                'padding': f"{fab_padding}px", # Apply uniform padding for icon centering
                'margin': '0',
                'border': 'none',
                'border-radius': f"{fab_radius}px", # Default circular
                'background-color': bgColor or (Colors.primaryContainer or '#EADDFF'), # M3 Primary Container
                'color': fgColor or (Colors.onPrimaryContainer or '#21005D'), # M3 On Primary Container
                'cursor': 'pointer',
                'text-decoration': 'none',
                'outline': 'none',
                'box-sizing': 'border-box',
                'overflow': 'hidden', # Clip ripple/shadow correctly
                # M3 Transition for shadow/transform
                'transition': 'box-shadow 0.28s cubic-bezier(0.4, 0, 0.2, 1), transform 0.15s ease-out, background-color 0.15s linear',
                '-webkit-appearance': 'none', 'moz-appearance': 'none', 'appearance': 'none',
                'z-index': 1000, # High z-index
            }

            # --- Apply Overrides from Style Key (if reconstructed successfully) ---
            if style_reconstructed:
                 # Override specific defaults if they were set in the ButtonStyle key
                 if bgColor is not None: base_styles_dict['background-color'] = bgColor
                 if fgColor is not None: base_styles_dict['color'] = fgColor
                 # Override padding if provided in key
                 if padding_tuple:
                     try: padding_obj = EdgeInsets(*padding_tuple); base_styles_dict['padding'] = padding_obj.to_css_value()
                     except: pass
                 # Override shape if provided in key
                 if shape_repr:
                     if isinstance(shape_repr, tuple) and len(shape_repr) == 4:
                          try: shape_obj = BorderRadius(*shape_repr); base_styles_dict['border-radius'] = shape_obj.to_css_value()
                          except: pass
                     elif isinstance(shape_repr, (int, float)): base_styles_dict['border-radius'] = f"{max(0.0, shape_repr)}px"
                 # Note: width/height overrides are less common for standard FAB, but could be added if needed

            # --- Elevation / Shadow (Based on M3 levels) ---
            eff_elevation = elevation if style_reconstructed and elevation is not None else 6.0 # Default level 6
            s_color = shadowColor or Colors.shadow or '#000000'
            if eff_elevation >= 6: # M3 Level 3 Shadow (High elevation)
                shadow1 = f"0px 3px 5px -1px rgba(0,0,0,0.2)" # Adjusted based on M3 spec examples
                shadow2 = f"0px 6px 10px 0px rgba(0,0,0,0.14)"
                shadow3 = f"0px 1px 18px 0px rgba(0,0,0,0.12)"
                base_styles_dict['box-shadow'] = f"{shadow1}, {shadow2}, {shadow3}"
            elif eff_elevation >= 3: # M3 Level 2 Shadow
                shadow1 = f"0px 1px 3px 1px rgba(0,0,0,0.15)"
                shadow2 = f"0px 1px 2px 0px rgba(0,0,0,0.30)"
                base_styles_dict['box-shadow'] = f"{shadow1}, {shadow2}"
            elif eff_elevation > 0: # M3 Level 1 Shadow
                shadow1 = f"0px 1px 3px 0px rgba(0,0,0,0.30)"
                shadow2 = f"0px 1px 1px 0px rgba(0,0,0,0.15)"
                base_styles_dict['box-shadow'] = f"{shadow1}, {shadow2}"
            else:
                 base_styles_dict['box-shadow'] = 'none' # No shadow if elevation is 0


            # --- Assemble Main Rule ---
            main_rule = f".{css_class} {{ {' '.join(f'{k}: {v};' for k, v in base_styles_dict.items())} }}"

            # --- Icon Styling (Child Selector) ---
            icon_rule = f"""
            .{css_class} > i, /* Font Awesome */
            .{css_class} > img, /* Custom Image */
            .{css_class} > svg, /* SVG Icon */
            .{css_class} > * {{ /* General direct child */
                display: block; /* Prevent extra space */
                width: 24px; /* M3 Standard icon size */
                height: 24px;
                object-fit: contain; /* For img/svg */
                /* Color is inherited from button */
            }}"""

            # --- State Styles ---
            # Hover: Raise elevation more
            hover_shadow_str = ""
            if eff_elevation >= 1: # Only show hover elevation if base has elevation
                 # M3 Hover elevation often adds +2dp equivalent
                 h_elevation = eff_elevation + 2
                 if h_elevation >= 12: # M3 Level 5 Shadow (Max hover approx)
                      h_shadow1 = f"0px 5px 5px -3px rgba(0,0,0,0.2)"; h_shadow2 = f"0px 8px 10px 1px rgba(0,0,0,0.14)"; h_shadow3 = f"0px 3px 14px 2px rgba(0,0,0,0.12)";
                      hover_shadow_str = f"box-shadow: {h_shadow1}, {h_shadow2}, {h_shadow3};"
                 elif h_elevation >= 8: # M3 Level 4 Shadow
                      h_shadow1 = f"0px 3px 5px -1px rgba(0,0,0,0.2)"; h_shadow2 = f"0px 7px 10px 1px rgba(0,0,0,0.14)"; h_shadow3 = f"0px 2px 16px 1px rgba(0,0,0,0.12)";
                      hover_shadow_str = f"box-shadow: {h_shadow1}, {h_shadow2}, {h_shadow3};"
                 else: # Slightly higher than base
                      h_shadow1 = f"0px 3px 5px -1px rgba(0,0,0,0.2)"; h_shadow2 = f"0px 6px 10px 0px rgba(0,0,0,0.14)"; h_shadow3 = f"0px 1px 18px 0px rgba(0,0,0,0.12)";
                      hover_shadow_str = f"box-shadow: {h_shadow1}, {h_shadow2}, {h_shadow3};" # Use base shadow slightly stronger
            hover_rule = f".{css_class}:hover {{ {hover_shadow_str} }}"

            # Active: Usually slight transform or minimal shadow change
            active_rule = f".{css_class}:active {{ transform: scale(0.98); /* Example subtle press */ }}"

            # Disabled state (add .disabled class)
            disabled_bg = disBgColor or Colors.rgba(0,0,0,0.12) # M3 Disabled container approx
            disabled_fg = disFgColor or Colors.rgba(0,0,0,0.38) # M3 Disabled content approx
            disabled_rule = f".{css_class}.disabled {{ background-color: {disabled_bg}; color: {disabled_fg}; box-shadow: none; cursor: default; pointer-events: none; }}"


            return "\n".join([main_rule, icon_rule, hover_rule, active_rule, disabled_rule])

        except Exception as e:
            import traceback
            print(f"Error generating CSS for FloatingActionButton {css_class} with key {style_key}: {e}")
            traceback.print_exc()
            return f"/* Error generating rule for .{css_class} */"
    # Removed instance methods: to_html(), to_css(), to_js()



class SingleChildScrollView(Widget):
    """
    A widget that makes its single child scrollable.

    This is useful for content that might be larger than its container,
    like a tall form on a small screen. It uses a shared CSS class to
    apply the necessary overflow and direction styles.
    """
    shared_styles: Dict[Tuple, str] = {}

    def __init__(self,
                 child: Widget,
                 key: Optional[Key] = None,
                 scrollDirection: str = Axis.VERTICAL,
                 reverse: bool = False,
                 padding: Optional[EdgeInsets] = None,
                 # physics property is less relevant here as it's not a list,
                 # but we can map it to CSS overflow behavior.
                 physics: Optional[str] = None # e.g., ScrollPhysics.NEVER_SCROLLABLE
                 ):

        super().__init__(key=key, children=[child])
        self.child = child

        # Store properties that will define the CSS
        self.scrollDirection = scrollDirection
        self.reverse = reverse
        self.padding = padding
        self.physics = physics

        # --- CSS Class Management ---
        # The style key includes all properties that affect the CSS output.
        self.style_key = (
            self.scrollDirection,
            self.reverse,
            make_hashable(self.padding),
            self.physics,
        )

        # Use the standard pattern to get a shared CSS class
        if self.style_key not in SingleChildScrollView.shared_styles:
            self.css_class = f"shared-scrollview-{len(SingleChildScrollView.shared_styles)}"
            SingleChildScrollView.shared_styles[self.style_key] = self.css_class
        else:
            self.css_class = SingleChildScrollView.shared_styles[self.style_key]

    def render_props(self) -> Dict[str, Any]:
        """Passes the CSS class to the reconciler."""
        # The only prop needed for the DOM element itself is the class.
        # The child's rendering is handled separately by the reconciler.
        return {'css_class': self.css_class}

    def get_required_css_classes(self) -> Set[str]:
        """Returns the shared CSS class name for this instance."""
        return {self.css_class}

    @staticmethod
    def generate_css_rule(style_key: Tuple, css_class: str) -> str:
        """
        Static method that generates the CSS rule for a scrollable container.
        This is called by the Reconciler when it encounters a new style key.
        """
        try:
            # 1. Unpack the style_key tuple in the correct order.
            (scrollDirection, reverse, padding_tuple, physics) = style_key

            # 2. Translate properties into CSS.
            styles = [
                # A scroll view must establish a flex context if it wants
                # its child to size correctly within it.
                "display: flex;",
                # It should typically fill the space it's given.
                "width: 100%;",
                "height: 100%;",
                "box-sizing: border-box;",
            ]

            # --- Flex Direction ---
            # This makes the child grow correctly inside the scroll area.
            flex_direction = 'column' if scrollDirection == Axis.VERTICAL else 'row'
            if reverse:
                flex_direction += '-reverse'
            styles.append(f"flex-direction: {flex_direction};")

            # --- Scrolling ---
            # Set the overflow property based on the scroll direction.
            if physics == ScrollPhysics.NEVER_SCROLLABLE:
                styles.append("overflow: hidden;")
            else:
                if scrollDirection == Axis.VERTICAL:
                    styles.append("overflow-x: hidden;")
                    styles.append("overflow-y: auto;")
                else: # HORIZONTAL
                    styles.append("overflow-x: auto;")
                    styles.append("overflow-y: hidden;")
            
            # --- Padding ---
            # Reconstruct the EdgeInsets object from its tuple representation.
            if padding_tuple and isinstance(padding_tuple, tuple):
                padding_obj = EdgeInsets(*padding_tuple)
                styles.append(f"padding: {padding_obj.to_css_value()};")

            # 3. Assemble and return the final CSS rule.
            # We also need to style the child to ensure it takes up the
            # necessary space to trigger scrolling.
            container_rule = f".{css_class} {{ {' '.join(styles)} }}"
            
            # This rule ensures the direct child of the scroll view can grow.
            # Using `flex-shrink: 0` is important to prevent the child from
            # being squished by the container, allowing it to overflow and
            # thus become scrollable.
            child_rule = f".{css_class} > * {{ flex-shrink: 0; }}"

            return f"{container_rule}\n{child_rule}"

        except Exception as e:
            import traceback
            print(f"ERROR generating CSS for SingleChildScrollView {css_class} with key {style_key}:")
            traceback.print_exc()
            return f"/* Error generating rule for .{css_class} */"


# In pythra/widgets.py

# ... (other widgets)

class GlobalScrollbarStyle(Widget):
    """
    A special non-rendering widget that applies a custom scrollbar style
    to the entire application window (the body's scrollbar).

    This widget should be placed once in your widget tree, typically at
    the top level, for example, as a child of your main Scaffold or Container.
    """
    # Use a class-level cache to ensure the global style is only generated once
    # per unique theme. The key here can be simple, as there's only one global
    # scrollbar per window.
    shared_styles: Dict[Tuple, str] = {}

    def __init__(self, key: Optional[Key] = None, theme: Optional[ScrollbarTheme] = None):
        # This widget has no children and renders nothing itself.
        super().__init__(key=key, children=[])

        self.theme = theme or ScrollbarTheme()

        # Generate a unique key for the theme.
        self.style_key = self.theme.to_tuple()

        # We still use the shared_styles pattern to get a unique class name,
        # but the CSS we generate won't use this class name. It's just for
        # triggering the static method.
        if self.style_key not in GlobalScrollbarStyle.shared_styles:
            # The class name is just a placeholder to trigger the generation
            self.css_class = f"global-scrollbar-theme-{len(GlobalScrollbarStyle.shared_styles)}"
            GlobalScrollbarStyle.shared_styles[self.style_key] = self.css_class
        else:
            self.css_class = GlobalScrollbarStyle.shared_styles[self.style_key]

    def render_props(self) -> Dict[str, Any]:
        """This widget renders nothing, so it returns empty props."""
        return {}

    def get_required_css_classes(self) -> Set[str]:
        """Tells the reconciler to generate the CSS for this style key."""
        return {self.css_class}

    @staticmethod
    def generate_css_rule(style_key: Tuple, css_class: str) -> str:
        """
        Generates CSS that targets the global `::-webkit-scrollbar` pseudo-elements,
        ignoring the provided `css_class`. This is the correct approach based on
        the working example provided.
        """
        try:
            # Unpack the theme tuple from the style key
            (
                scroll_width, scroll_height, thumb_color, thumb_hover_color,
                track_color, radius, thumb_padding # thumb_padding is now unused but kept for compatibility
            ) = style_key

            # This CSS is taken directly from your working example.
            # It targets the global scrollbar, not a specific class.
            webkit_css = f"""
                ::-webkit-scrollbar {{
                    width: {scroll_width}px;
                    height: {scroll_height}px;
                }}
                ::-webkit-scrollbar-track {{
                    background: {track_color};
                }}
                ::-webkit-scrollbar-thumb {{
                    background-color: {thumb_color};
                    border-radius: {radius}px;
                }}
                ::-webkit-scrollbar-thumb:hover {{
                    background-color: {thumb_hover_color};
                }}
            """
            
            # This is the equivalent for Firefox.
            firefox_css = f"""
                body {{
                    scrollbar-width: thin;
                    scrollbar-color: {thumb_color} {track_color};
                }}
            """

            return f"{webkit_css}\n{firefox_css}"

        except Exception as e:
            import traceback
            print(f"ERROR generating CSS for GlobalScrollbarStyle: {e}")
            traceback.print_exc()
            return "/* Error generating global scrollbar style */"


# In pythra/widgets.py

class Scrollbar(Widget):
    """
    A robust, customizable scrollbar widget powered by the SimpleBar.js library.
    It provides a consistent, themeable scrolling experience across all browsers.

    This widget renders a container div that is automatically initialized by SimpleBar.
    It supports both initial page load and dynamic insertion via DOM patches.
    """
    # A class-level cache to share CSS for identical themes.
    shared_styles: Dict[Tuple, str] = {}

    def __init__(self,
                 child: Widget,
                 key: Optional[Key] = None,
                 theme: Optional[ScrollbarTheme] = None,
                 width: Optional[Any] = '100%',
                 height: Optional[Any] = '100%',
                 autoHide: bool = True):
        """
        Args:
            child (Widget): The content that will be scrollable.
            key (Optional[Key]): A unique key for reconciliation.
            theme (Optional[ScrollbarTheme]): A theme object to customize the scrollbar's appearance.
            width (Optional[Any]): The width of the scrollable area (e.g., '100%', 300).
            height (Optional[Any]): The height of the scrollable area (e.g., '100%', 500).
            autoHide (bool): If true, scrollbars will hide when not in use.
        """
        super().__init__(key=key, children=[child])
        self.child = child
        self.theme = theme or ScrollbarTheme()
        self.width = width
        self.height = height
        self.autoHide = autoHide

        # The style key is based *only* on the theme, not the dimensions.
        # This allows multiple scrollbars of different sizes to share the same visual style.
        self.style_key = self.theme.to_tuple()

        if self.style_key not in Scrollbar.shared_styles:
            self.css_class = f"simplebar-themed-{len(Scrollbar.shared_styles)}"
            Scrollbar.shared_styles[self.style_key] = self.css_class
        else:
            self.css_class = Scrollbar.shared_styles[self.style_key]

    def render_props(self) -> Dict[str, Any]:
        """
        Provides all the necessary information for the reconciler and patch generator.
        """
        return {
            'css_class': self.css_class,
            # This 'attributes' dict is used to add the 'data-simplebar' attribute
            # which is essential for SimpleBar's automatic initialization on page load.
            'attributes': {
                'data-simplebar': 'true',
            },
            # These options are passed to the 'new SimpleBar()' constructor in JavaScript.
            'simplebar_options': {
                'autoHide': self.autoHide,
            },
            # A flag to signal the patch script that this element needs JS initialization
            # when it is dynamically inserted.
            'init_simplebar': True,
            # Pass the instance itself so the patcher can access _style_override.
            'widget_instance': self,
        }
    
    @property
    def _style_override(self) -> Dict:
        """
        Applies direct inline styles for dimensions, as they are unique per instance
        and should not be part of the shared CSS class.
        """
        styles = {}
        if self.width is not None:
            styles['width'] = f"{self.width}px" if isinstance(self.width, (int, float)) else self.width
        if self.height is not None:
            styles['height'] = f"{self.height}px" if isinstance(self.height, (int, float)) else self.height
        return styles

    def get_required_css_classes(self) -> Set[str]:
        """Tells the reconciler which shared CSS class this widget needs."""
        return {self.css_class}

    @staticmethod
    def generate_css_rule(style_key: Tuple, css_class: str) -> str:
        """
        Generates CSS that *overrides* SimpleBar's default styles, scoped
        to this widget's unique theme class. This is how we apply custom themes.
        """
        try:
            (width, height, thumb_color, thumb_hover_color,
             track_color, radius, track_radius, thumb_padding, track_margin) = style_key
            
            # These selectors precisely target the DOM elements created by SimpleBar.
            return f"""
                /* Style the scrollbar track (the groove it runs in) */
                .{css_class} .simplebar-track.simplebar-vertical {{
                    background: {track_color};
                    width: {width}px;
                    border-radius: {track_radius}px;
                    margin: {track_margin};
                }}
                .{css_class} .simplebar-track.simplebar-horizontal {{
                    background: {track_color};
                    height: {height}px;
                    border-radius: {track_radius}px;
                }}

                /* Style the draggable scrollbar thumb */
                .{css_class} .simplebar-scrollbar::before {{
                    background-color: {thumb_color};
                    border-radius: {radius}px;
                    /* Use a transparent border to create padding inside the thumb */
                    border: {thumb_padding}px solid transparent;
                    background-clip: content-box;
                    opacity: 1; /* Override auto-hide opacity if needed */
                }}

                .{css_class} .simplebar-scrollbar::after {{
                    background-color: {thumb_color};
                    border-radius: {radius}px;
                    /* Use a transparent border to create padding inside the thumb */
                    border: {thumb_padding}px solid transparent;
                    background-clip: content-box;
                    opacity: 1; /* Override auto-hide opacity if needed */
                }}

                /* Style the thumb on hover */
                .{css_class} .simplebar-track:hover .simplebar-scrollbar::before {{
                    background-color: {thumb_hover_color};
                }}
                .{css_class} {{
                    /* height: -webkit-fill-available; */
                    height: inherit;
                }}
                .{css_class}  .simplebar-track.simplebar-horizontal {{
                    display: none;
                }}
                .simplebar-scrollbar {{
                    display: none;
                }}
            """
        except Exception as e:
            import traceback
            print(f"ERROR generating CSS for Themed SimpleBar {css_class}: {e}")
            traceback.print_exc()
            return ""


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
            # width_style = ""
            if crossAxisAlignment == CrossAxisAlignment.BASELINE:
                # For baseline alignment in flexbox, typically use align-items: baseline;
                # textBaseline (alphabetic/ideographic) might not have a direct, simple CSS equivalent
                # across all scenarios without knowing child content. Stick to 'baseline'.
                align_items_val = 'baseline'
            elif crossAxisAlignment == CrossAxisAlignment.STRETCH and mainAxisSize == MainAxisSize.MAX:
                # Default behavior for align-items: stretch might need width/height adjustments
                pass # Keep 'stretch'
                # width_style = "height: -webkit-fill-available;"
            # If not baseline or stretch, use the value directly (e.g., 'center', 'flex-start', 'flex-end')


            # MainAxisSize determines height behavior
            height_style = ""
            if mainAxisSize == MainAxisSize.MAX:
                # Fill available vertical space. If parent is also flex, might need flex-grow.
                # Using height: 100% assumes parent has a defined height.
                # 'flex: 1;' is often better in flex contexts. Let's use fit-content for min.
                height_style = "height: 100%;" # Common pattern to fill space
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
            height_style = ""
            if crossAxisAlignment == CrossAxisAlignment.BASELINE:
                 align_items_val = 'baseline'
            elif crossAxisAlignment == CrossAxisAlignment.STRETCH:
                height_style = "height: 100%;"
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
                f"{height_style}"
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

class AssetIcon:
    """
    A helper class that represents a path to a custom icon image
    located in the framework's assets directory.
    """
    def __init__(self, file_name: str):
        # Basic check for leading slashes
        clean_file_name = file_name.lstrip('/')
        # TODO: Add more robust path joining and sanitization
        self.src = f'http://localhost:{port}/{assets_dir}/icons/{clean_file_name}'

    def get_source(self) -> str:
        return self.src

    def __eq__(self, other):
        return isinstance(other, AssetIcon) and self.src == other.src

    def __hash__(self):
        return hash(self.src)

    def __repr__(self):
        return f"AssetIcon('{self.src}')"

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
                 alignment: str = 'center',
                 borderRadius: Optional[BorderRadius] = None,
                 ): # Alignment within its box if size differs

        # Image widget doesn't typically have children in Flutter sense
        super().__init__(key=key, children=[])

        if not isinstance(image, (AssetImage, NetworkImage)):
             raise TypeError("Image widget requires an AssetImage or NetworkImage instance.")

        self.image_source = image
        self.width = width
        self.height = height
        self.fit = fit
        self.alignment = alignment # Note: CSS object-position might be needed for alignment
        self.borderRadius = borderRadius

        # --- CSS Class Management ---
        # Key includes properties affecting CSS style
        # Use make_hashable if alignment object is complex
        self.style_key = (
            self.fit,
            self.width, # Include size in key as it might affect CSS rules
            self.height,
            self.alignment,
            self.borderRadius,
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
            'border_radius': self.borderRadius,
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
            fit, width, height, alignment, border_radius = style_key

            # Translate properties to CSS
            fit_style = f"object-fit: {fit};" if fit else ""

            # Handle width/height units (px default, allow strings like '100%')
            width_style = ""
            if isinstance(width, (int, float)): width_style = f"width: {width}px;"
            elif isinstance(width, str): width_style = f"width: {width};"

            height_style = ""
            if isinstance(height, (int, float)): height_style = f"height: {height}px;"
            elif isinstance(height, str): height_style = f"height: {height};"

            border_radius_style = ""
            # print("Image Border Radius: ",border_radius.to_css_value())
            border_radius_style = f"border-radius: {border_radius.to_css_value()};" if border_radius else ""
            # print("Image Border Radius: ",border_radius_style)
            

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
                f"{border_radius_style}"
            )

            # Return the complete CSS rule
            # Note: display:block often helpful for sizing images correctly
            return f".{css_class} {{ display: block; {styles}}}"

        except Exception as e:
            print(f"Error generating CSS for Image {css_class} with key {style_key}: {e}")
            return f"/* Error generating rule for .{css_class} */"

    # Removed instance methods: to_html(), to_css()


from .icons import IconData # Import the new data class

class Icon(Widget):
    """
    Displays an icon from a font using an IconData object. This widget renders
    a <span> tag and relies on the browser's font rendering (ligatures)
    to display the correct symbol.
    """
    shared_styles: Dict[Tuple, str] = {}

    def __init__(self,
                 icon: IconData, # The required IconData object
                 key: Optional[Key] = None,
                 size: int = 24,
                 color: Optional[str] = None,
                 # Variable font settings
                 fill: bool = False,
                 weight: Optional[int] = 400, # Range 100-700
                 grade: Optional[int] = 0,   # Range -50-200
                 optical_size: Optional[int] = 24
                ):

        super().__init__(key=key, children=[])

        if not isinstance(icon, IconData):
            raise TypeError("Icon widget requires an IconData object. Use Icons.home, etc.")

        self.icon = icon
        self.size = size
        self.color = color
        self.fill = fill
        self.weight = weight
        self.grade = grade
        self.optical_size = optical_size

        # The style key now includes all font variation settings
        self.style_key = (
            self.icon.fontFamily,
            self.size,
            self.color,
            self.fill,
            self.weight,
            self.grade,
            self.optical_size
        )

        if self.style_key not in Icon.shared_styles:
            self.css_class = f"material-icon-{len(Icon.shared_styles)}"
            Icon.shared_styles[self.style_key] = self.css_class
        else:
            self.css_class = Icon.shared_styles[self.style_key]

    def render_props(self) -> Dict[str, Any]:
        """Return properties for diffing. The icon name is now the text content."""
        return {
            'css_class': self.css_class,
            'data': self.icon.name # The text content of the <span>
        }

    def get_required_css_classes(self) -> Set[str]:
        return {self.css_class}

    @staticmethod
    def _get_widget_render_tag(widget: 'Widget') -> str:
        # Override the render tag for this specific widget type
        if isinstance(widget, Icon):
            return 'i' # Render as a span, not an <i> or <img>
        # Fallback to a central tag map if you have one
        return 'div'

    @staticmethod
    def generate_css_rule(style_key: Tuple, css_class: str) -> str:
        """Generates the CSS including the powerful font-variation-settings."""
        try:
            (fontFamily, size, color, fill, weight, grade, optical_size) = style_key

            # This is the magic property for variable fonts
            font_variation_settings = f"'FILL' {1 if fill else 0}, 'wght' {weight}, 'GRAD' {grade}, 'opsz' {optical_size}"

            return f"""
                .{css_class} {{
                    position: relative;
                    font-family: '{fontFamily}';
                    font-weight: normal;
                    font-style: normal;
                    font-size: {size}px;
                    line-height: 1;
                    letter-spacing: normal;
                    text-transform: none;
                    z-index: 100;
                    display: inline-block;
                    white-space: nowrap;
                    word-wrap: normal;
                    direction: ltr;
                    -webkit-font-smoothing: antialiased;
                    text-rendering: optimizeLegibility;
                    -moz-osx-font-smoothing: grayscale;
                    font-feature-settings: 'liga';
                    color: {color or 'inherit'};
                    font-variation-settings: {font_variation_settings};
                }}
            """
        except Exception as e:
            # ... error handling ...
            return f"/* Error generating rule for Icon .{css_class} */"

# IMPORTANT: In your reconciler's _get_widget_render_tag method, make sure it
# knows that an Icon should be a <span>.
# A good way is to call the widget's own static method if it exists.

# pythra/widgets.py
class VirtualListView(Widget):
    """
    A *virtual* scrollable list – renders only the rows that are visible.
    Compatible with reconciliation and JS viewport.
    """
    shared_styles: Dict[Tuple, str] = {}

    def __init__(
        self,
        item_count: int,
        item_builder: Callable[[int], Widget],
        key: Optional[Key] = None,
        estimated_height: int = 50,
        padding: Optional[EdgeInsets] = None,
        scroll_direction: str = Axis.VERTICAL,
        reverse: bool = False,
        physics: str = ScrollPhysics.ALWAYS_SCROLLABLE,
    ):
        super().__init__(key=key, children=[])  # children are virtual
        self.item_count = item_count
        self.item_builder = item_builder
        self.estimated_height = estimated_height
        self.padding = padding or EdgeInsets.all(0)
        self.scroll_direction = scroll_direction
        self.reverse = reverse
        self.physics = physics

        print("Item Count: ", self.item_count)

        # CSS key
        self.style_key = (
            make_hashable(self.padding),
            scroll_direction,
            reverse,
            physics,
            estimated_height,
        )
        if self.style_key not in VirtualListView.shared_styles:
            self.css_class = f"virtual-list-{len(VirtualListView.shared_styles)}"
            VirtualListView.shared_styles[self.style_key] = self.css_class
        else:
            self.css_class = VirtualListView.shared_styles[self.style_key]

    def render_props(self):
        return {
            "css_class": self.css_class,
            "item_count": self.item_count,
            "estimated_height": self.estimated_height,
            "scroll_direction": self.scroll_direction,
            "padding": self._get_render_safe_prop(self.padding),
            "reverse": self.reverse,
            "physics": self.physics,
        }

    def get_required_css_classes(self):
        return {self.css_class}

    @staticmethod
    def generate_css_rule(style_key, css_class):
        padding, direction, reverse, physics, _ = style_key
        flex_dir = "column" if direction == Axis.VERTICAL else "row"
        if reverse:
            flex_dir += "-reverse"
        overflow = "hidden" if physics == ScrollPhysics.NEVER_SCROLLABLE else "auto"
        pad = EdgeInsets(*padding).to_css_value() if padding else "0"
        return f"""
        .{css_class} {{
            display: flex;
            flex-direction: {flex_dir};
            overflow: {overflow};
            padding: {pad};
            box-sizing: border-box;
            position: relative;
        }}
        .{css_class} > .viewport {{
            flex: 1 1 auto;
            overflow-y: auto;
            overflow-x: hidden;
            position: relative;
        }}
        .{css_class} .phantom {{
            position: absolute;
            top: 0;
            left: 0;
            width: 1px;
            pointer-events: none;
            visibility: hidden;
        }}
        """

            
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
            self.padding, # Use helper or ensure EdgeInsets is hashable
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
            # overflow_style = ""
            # axis_to_scroll = 'y' if scrollDirection == Axis.VERTICAL else 'x'
            # if physics == ScrollPhysics.NEVER_SCROLLABLE:
            #     overflow_style = "overflow: hidden;"
            # elif physics == ScrollPhysics.CLAMPING:
            #      # Usually implies hidden, but let CSS default handle (might clip)
            #      overflow_style = f"overflow-{axis_to_scroll}: hidden;" # More specific? Or just overflow: hidden? Let's use specific.
            # elif physics == ScrollPhysics.ALWAYS_SCROLLABLE or physics == ScrollPhysics.BOUNCING:
            #      # Standard CSS uses 'auto' or 'scroll'. 'auto' is generally preferred.
            #      # 'bouncing' (-webkit-overflow-scrolling: touch;) is iOS specific, apply if needed.
            #      overflow_style = f"overflow-{axis_to_scroll}: auto;"
            #      if physics == ScrollPhysics.BOUNCING:
            #            overflow_style += " -webkit-overflow-scrolling: touch;" # Add iOS momentum

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
                 size_style = "flex-grow: 1; flex-basis: 0; width: 100%;" # Attempt to fill
                 # Need to handle potential conflict if both width/height 100% and overflow are set.
                 # Add min-height/min-width to prevent collapse?
                #  size_style += " min-height: 0; min-width: 0;"


            # Padding
            # Reconstruct EdgeInsets or use representation directly if simple
            # Assuming padding_repr is hashable and usable by EdgeInsets.to_css() if needed
            # For now, assume padding_repr IS the EdgeInsets object if it was hashable
            padding_obj = padding_repr
            padding_style = ""
            if isinstance(padding_obj, EdgeInsets):
                print(f"padding: {padding_repr};")
                padding_style = f"padding: {padding_obj.to_css_value()};"
            elif padding_repr: # Handle fallback if not EdgeInsets obj
                padding_style = f"padding: {padding_repr};" # Assumes it's already CSS string? Risky.
                print(f"padding: {padding_repr};")


            # Combine styles
            styles = (
                f"display: flex; "
                f"flex-direction: {flex_direction}; "
                f"{padding_style} "
                f"{size_style} "
                # "{overflow_style}"
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
                 print(padding_style)
            elif padding_repr:
                 padding_style = f"padding: {padding_repr};" # Fallback
                 print(padding_style)


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
    """A single fixed-height row that typically contains some text as well as a
    leading or trailing icon. Conforms to Material 3 list item specs."""
    shared_styles: Dict[Tuple, str] = {}

    def __init__(self,
                 key: Optional[Key] = None,
                 leading: Optional[Widget] = None,
                 title: Optional[Widget] = None,
                 subtitle: Optional[Widget] = None,
                 trailing: Optional[Widget] = None,
                 onTap: Optional[Callable] = None,
                 onTapName: Optional[str] = None,
                 onTapArg: Optional[List] = [],
                 enabled: bool = True,
                 selected: bool = False,
                 dense: bool = False,
                 selectedColor: Optional[str] = None,
                 selectedTileColor: Optional[str] = None,
                 contentPadding: Optional[EdgeInsets] = None):

        # --- THIS IS THE KEY CHANGE ---
        # The reconciler will now see leading, title, etc., as regular children.
        # The CSS will use selectors like `:first-child` and `:last-child` to style them.
        children = []
        if leading: children.append(leading)
        if title: children.append(title)
        if subtitle: children.append(subtitle)
        if trailing: children.append(trailing)
        super().__init__(key=key, children=children)

        self.onTap = onTap
        self.onTapName = onTapName if onTapName else (onTap.__name__ if onTap else None)
        self.onTapArg = onTapArg
        self.enabled = enabled
        self.selected = selected
        self.dense = dense
        self.selectedColor = selectedColor
        self.selectedTileColor = selectedTileColor
        self.contentPadding = contentPadding

        # --- CORRECTED STYLE KEY ---
        # Only include properties that define the base, shared style.
        # States like selected/enabled are handled by adding classes dynamically.
        self.style_key = (self.dense, make_hashable(self.contentPadding))

        if self.style_key not in ListTile.shared_styles:
            self.css_class = f"shared-listtile-{len(ListTile.shared_styles)}"
            ListTile.shared_styles[self.style_key] = self.css_class
        else:
            self.css_class = ListTile.shared_styles[self.style_key]

        # Combine base class with stateful classes for the current render.
        self.current_css_class = f"{self.css_class} {'selected' if self.selected else ''} {'disabled' if not self.enabled else ''}"
        # Add class to indicate if subtitle exists, for CSS styling
        if subtitle:
            self.current_css_class += " has-subtitle"

    def render_props(self) -> Dict[str, Any]:
        """Return properties for the Reconciler to use for patching."""
        props = {
            'css_class': self.current_css_class,
            'enabled': self.enabled,
            'onTapName': self.onTapName if self.enabled else None,
            'onTapArg' : self.onTapArg,
            'onTap' : self.onTap,
            # Pass colors as CSS variables for the .selected rule to use
            'style': {
                '--listtile-selected-fg': self.selectedColor,
                '--listtile-selected-bg': self.selectedTileColor
            } if self.selected else {}
        }
        return props

    def get_required_css_classes(self) -> Set[str]:
        return {self.css_class}

    @staticmethod
    def generate_css_rule(style_key: Tuple, css_class: str) -> str:
        """Static method to generate CSS for ListTile structure."""
        try:
            dense, padding_tuple = style_key
            # ... (the rest of your generate_css_rule logic is excellent) ...
            # The only change needed is to use structural selectors for children.

            # Example structural CSS:
            return f"""
                .{css_class} {{ /* Base styles */ }}
                .{css_class} > :first-child {{ /* Styles for Leading */ }}
                .{css_class} > :last-child {{ /* Styles for Trailing */ }}
                .{css_class} > :nth-child(2) {{ /* Styles for Title */ }}
                .{css_class}.has-subtitle > :nth-child(3) {{ /* Styles for Subtitle */ }}
                /* etc. */
            """
            # Your existing CSS Grid implementation is actually better than this.
            # Just keep it, it will work now that the key is fixed.
            # Your original generate_css_rule was very good, it just needed the key fixed.
            # Here it is again, confirmed to work with the new key.
            min_height = 48 if dense else 56
            padding_css = f"padding: {EdgeInsets(*padding_tuple).to_css_value()};" if padding_tuple else "padding: 8px 16px;"

            return f"""
                .{css_class} {{
                    display: grid;
                    grid-template-areas: "leading title trailing" "leading subtitle trailing";
                    grid-template-columns: auto 1fr auto;
                    align-items: center; width: 100%; min-height: {min_height}px;
                    gap: 0 16px; {padding_css} box-sizing: border-box;
                    transition: background-color .15s linear;
                }}
                .{css_class} > :nth-child(1) {{ grid-area: leading; }}
                .{css_class} > :nth-child(2) {{ grid-area: title; }}
                .{css_class}.has-subtitle > :nth-child(3) {{ grid-area: subtitle; }}
                .{css_class} > :last-child {{ grid-area: trailing; }}
                .{css_class}:not(.has-subtitle) > .listtile-title {{ align-self: center; }}
                .{css_class}.has-subtitle > .listtile-title {{ align-self: end; }}

                .{css_class}:not(.disabled) {{ cursor: pointer; }}
                .{css_class}.disabled {{ opacity: 0.38; pointer-events: none; }}
                .{css_class}.selected {{ background-color: {Colors.primaryContainer}; color: {Colors.onPrimaryContainer}; }}
            """

        except Exception as e:
            # ... error handling ...
            return f"/* Error generating rule for .{css_class} */"



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
    A widget that sizes its child to a specific aspect ratio.
    This is a rendering widget that creates a div with the `aspect-ratio` CSS property.
    """
    def __init__(self,
                 aspectRatio: float,
                 key: Optional[Key] = None,
                 child: Optional[Widget] = None):

        if aspectRatio <= 0:
             raise ValueError("aspectRatio must be positive")
        super().__init__(key=key, children=[child] if child else [])
        self.aspectRatio = aspectRatio

    def render_props(self) -> Dict[str, Any]:
        """Pass the aspect ratio for direct styling by the Reconciler."""
        return {'aspectRatio': self.aspectRatio}

    def get_required_css_classes(self) -> Set[str]:
        return set()

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





# The RoundedPolygon class can be removed from here, as its logic is now in JS.

class ClipPath(Widget):
    """
    A widget that renders a container and clips its child using a path.
    The path is defined by a list of points and an optional corner radius,
    and is made fully responsive by a client-side engine.
    """
    def __init__(self,
                 key: Optional[Key] = None,
                 child: Optional[Widget] = None,
                 points: List[Tuple[float, float]] = None,
                 radius: float = 0,
                 viewBox: Tuple[float, float] = (100, 100),
                 width: Optional[Union[str, int, float]] = '100%',
                 height: Optional[Union[str, int, float]] = '100%',
                 aspectRatio: Optional[float] = None,
                 ): # <-- NEW PARAMETER
        
        if not child: raise ValueError("ClipPath widget requires a child.")
        super().__init__(key=key, children=[child])
        
        self.points = points or []
        self.radius = radius
        # viewBox now only needs width and height of the blueprint
        self.viewBox = viewBox
        self.width = width
        self.height = height
        self.aspectRatio = aspectRatio # <-- STORE IT

    def render_props(self) -> Dict[str, Any]:
        """
        Passes its layout properties and the raw data needed for
        responsive clipping to the Reconciler.
        """
        width_css = f"{self.width}px" if isinstance(self.width, (int, float)) else self.width
        height_css = f"{self.height}px" if isinstance(self.height, (int, float)) else self.height
        
        # The Python side's only job is to serialize the raw data.
        return {
            'width': width_css,
            'height': height_css,
            'aspectRatio': self.aspectRatio, # <-- PASS IT TO PROPS
            'responsive_clip_path': {
                'viewBox': self.viewBox,
                'points': self.points,
                'radius': self.radius,
            }
        }

    def get_required_css_classes(self) -> Set[str]:
        # Styles are applied dynamically via JS, no shared class needed.
        return set()




class TextField(Widget):
    """
    A Material Design-inspired text input field that correctly handles focus
    during UI rebuilds. It uses a TextEditingController for state management

    and an InputDecoration class for styling.
    """
    shared_styles: Dict[Tuple, str] = {}

    def __init__(self,
                 # value: str,
                 # Deprecated:
                 # onChanged: Callable[[str], None],
                 key: Key, # A Key is MANDATORY for focus to be preserved
                 controller: TextEditingController,
                 decoration: InputDecoration = InputDecoration(),
                 leading: Optional[Icon]= None,
                 trailing: Optional[Icon]= None,
                 enabled: bool = True,
                 obscureText: bool = False, # For passwords
                 
                 ):
        
        super().__init__(key=key, children=[])

        if not isinstance(key, Key):
             raise TypeError("TextField requires a unique Key to preserve focus during rebuilds.")
        if not isinstance(controller, TextEditingController):
            raise TypeError("TextField requires a TextEditingController instance.")

        self.controller = controller
        self.decoration = decoration
        self.enabled = enabled
        self.obscureText = obscureText
        self.leading = leading

        # The name for the callback is now derived from the controller's object ID,
        # ensuring it's unique for each controller instance.
        self.onChangedName = f"ctrl_{id(self.controller)}"
        
        # The actual callback function is a lambda that updates the controller.
        # This is registered once with the API.
        self.onChanged = lambda new_value: setattr(self.controller, 'text', new_value)
        
        # --- CSS Class Management ---
        # The style key is now based entirely on the InputDecoration object.
        self.style_key = make_hashable(self.decoration)

        if self.style_key not in TextField.shared_styles:
            self.css_class = f"shared-textfield-{len(TextField.shared_styles)}"
            TextField.shared_styles[self.style_key] = self.css_class
        else:
            self.css_class = TextField.shared_styles[self.style_key]

        # Combine base class with dynamic state classes for the current render
        state_classes = []
        if not self.enabled:
            state_classes.append('disabled')
        if self.decoration and self.decoration.errorText:
            state_classes.append('error')

        self.current_css_class = f"{self.css_class} {' '.join(state_classes)} textfield-root-container"
        
        # --- Central Callback Registration ---
        # The framework's API only needs to know about this callback once.
        # This is a good place to register it.
        # Api.instance().register_callback(self.onChangedName, self.onChanged)

    def render_props(self) -> Dict[str, Any]:
        """Return properties needed by the Reconciler to generate HTML and JS."""
        return {
            'value': self.controller.text,
            'onChangedName': self.onChangedName,
            'onChanged': self.onChanged,
            'label': self.decoration.label,
            'leading': self.leading,
            'placeholder': self.decoration.hintText, # Use hintText as placeholder
            'errorText': '' if not self.decoration.errorText or None else self.decoration.errorText,
            'enabled': self.enabled,
            'obscureText': self.obscureText,
            'css_class': self.get_shared_css_class()#self.current_css_class,
        }
    
    
    # OVERRIDE THE NEW METHODS
    def get_static_css_classes(self) -> Set[str]:
        return {"textfield-root-container"}

    def get_shared_css_class(self) -> Optional[str]:
        return self.css_class

    def get_required_css_classes(self) -> Set[str]:
        static = self.get_static_css_classes()
        return {self.css_class}


    @staticmethod
    def _generate_html_stub(widget_instance: 'TextField', html_id: str, props: Dict) -> str:
        """
        Custom stub generator. It now ALWAYS includes the helper-text div,
        which will be shown or hidden by CSS.
        """
        container_id = html_id
        input_id = f"{html_id}_input"
        helper_text_id = f"{html_id}_helper" # Give the helper an ID for updates
        
        css_class = props.get('css_class', '')
        label_text = props.get('label', '')
        # Get the error text, default to an empty string
        helper_text = props.get('errorText', '') 
        
        on_input_handler = f"handleInput('{props.get('onChangedName', '')}', this.value)"
        input_type = "password" if props.get('obscureText', False) else "text"
        
        return f"""
        <div id="{container_id}" class="textfield-root-container {css_class.replace('textfield-root-container', '')}">
            <div class="textfield-container {css_class.replace('textfield-root-container', '')}">
                <input 
                    id="{input_id}" 
                    class="textfield-input {css_class.replace('textfield-root-container', '')}" 
                    type="{input_type}" 
                    value="{html.escape(str(props.get('value', '')), quote=True)}"
                    placeholder="{html.escape(str(props.get('placeholder', '')), quote=True)}"
                    oninput="{on_input_handler}"
                    {'disabled' if not props.get('enabled', True) else ''}
                >
                <label for="{input_id}" class="textfield-label {css_class.replace('textfield-root-container', '')}">{html.escape(label_text) if label_text else ''}</label>
                <div class="textfield-outline {css_class.replace('textfield-root-container', '')}"></div>
            </div>
            {f'<div id="{helper_text_id}" class="textfield-helper-text {css_class.replace('textfield-root-container', '')}">{ '' if not helper_text or None else html.escape(helper_text) }</div>'}
        </div>
        """

    @staticmethod
    def generate_css_rule(style_key: Tuple, css_class: str) -> str:
        """Generates the complex CSS for a Material Design-style text field."""
        # Reconstruct the InputDecoration object from the style_key tuple
        # This assumes make_hashable(decoration) and decoration.to_tuple() are consistent.
        try:
            decoration = InputDecoration(
                # Unpack the tuple in the EXACT same order as to_tuple()
                label=style_key[0], hintText=style_key[1], errorText=style_key[2],
                fillColor=style_key[3], focusColor=style_key[4], labelColor=style_key[5],
                errorColor=style_key[6],
                borderRadius=style_key[7],
                # Re-create BorderSide objects from their tuple representations
                border=BorderSide(*style_key[8]) if style_key[8] else None,
                focusedBorder=BorderSide(*style_key[9]) if style_key[9] else None,
                errorBorder=BorderSide(*style_key[10]) if style_key[10] else None,
                filled=style_key[11]
            )
        except (IndexError, TypeError) as e:
            print(f"Error unpacking style_key for TextField {css_class}. Using default decoration. Error: {e}")
            decoration = InputDecoration()

        # --- 2. Extract all style values from the decoration object ---
        fill_color = decoration.fillColor
        # print(f">>>>Fill Color {fill_color}<<<>>>{decoration.label}<<<")
        focus_color = decoration.focusColor
        label_color = decoration.labelColor
        error_color = decoration.errorColor
        
        # Normal border
        border_radius = decoration.borderRadius
        border_width = decoration.border.width
        border_style = decoration.border.style
        border_color = decoration.border.color
        
        # Focused border
        focused_border_width = decoration.focusedBorder.width
        focused_border_style = decoration.focusedBorder.style # Style might not change
        focused_border_color = decoration.focusedBorder.color
        
        # Error border
        error_border_width = decoration.errorBorder.width
        error_border_style = decoration.errorBorder.style
        error_border_color = decoration.errorBorder.color

        # --- 3. Generate CSS rules using the extracted variables ---
        return f"""
        /* === Styles for {css_class} === */


        .textfield-root-container.{css_class} {{
            display: flex; flex-direction: column; margin: 0px;
            border-radius: 4px;
            width: 100%;
        }}
        .textfield-root-container.{css_class} .textfield-container {{
            position: relative; padding-top: 0px;
        }}
        .textfield-root-container.{css_class} .textfield-input {{
            width: 100%; height: 34px; padding: 0px 8px; font-size: 14px;
            color: {Colors.hex("#D9D9D9")}; background-color: {fill_color};
            border-top: none;
            border-left: none;
            border-right: none;
            border-bottom:{border_width}px {border_style} {border_color}; outline: none; {border_radius} box-sizing: border-box;
            transition: background-color 0.2s;
        }}
        .textfield-root-container.{css_class} .textfield-label {{
            position: absolute; left: 16px; top: 16px; font-size: 16px;
            color: {label_color}; pointer-events: none;
            transform-origin: left top; transform: translateY(-50%);
            transition: transform 0.2s, color 0.2s;
        }}
        .textfield-root-container.{css_class} .textfield-outline {{
            position: absolute; bottom: 0; left: 0; right: 0;
            height: {border_width}px; background-color: {border_color};
            transition: background-color 0.2s, height 0.2s; display: none;
        }}
        .textfield-root-container.{css_class}  .textfield-helper-text {{
            padding: 4px 16px 0 16px; font-size: 12px; color: {label_color};
            min-height: 1.2em; transition: color 0.2s;
        }}
        .textfield-root-container.{css_class} .textfield-helper-text:empty {{
             display: none; 
        }}

        /* --- FOCUSED STATE (Scoped) --- */
        .textfield-root-container.{css_class} .textfield-input:focus {{
            border-top: none;
            border-left: none;
            border-right: none;
            border-bottom:{border_width}px {border_style} {Colors.hex("#FF94DA")};
        }}
        .textfield-root-container.{css_class} .textfield-input:focus ~ .textfield-label {{
            transform: translateY(-190%) scale(0.75);
            color: {focus_color};
            display: none;
        }}
        .textfield-root-container.{css_class}:focus-within .textfield-outline {{
            height: {focused_border_width}px;
            background-color: {focused_border_color};
        }}
        
        /* --- ERROR STATE (Scoped) --- */
        .textfield-root-container.{css_class}.error .textfield-label,
        .textfield-root-container.{css_class}.error:focus-within .textfield-label {{
            color: {error_color};
        }}
        .textfield-root-container.{css_class}.error .textfield-outline {{
            height: {error_border_width}px;
            background-color: {error_border_color};
        }}
        .textfield-root-container.{css_class}.error .textfield-helper-text {{
            color: {error_color};
        }}

        /* --- DISABLED STATE (Scoped) --- */
        .textfield-root-container.{css_class}.disabled .textfield-input {{
            background-color: {Colors.rgba(0,0,0,0.06)};
            color: {Colors.rgba(0,0,0,0.38)};
        }}
        .textfield-root-container.{css_class}.disabled .textfield-label,
        .textfield-root-container.{css_class}.disabled .textfield-helper-text {{
            color: {Colors.rgba(0,0,0,0.38)};
        }}
        .textfield-root-container.{css_class}.disabled .textfield-outline {{
            background-color: {Colors.rgba(0,0,0,0.12)};
        }}
        """


# In pythra/widgets.py

class Slider(Widget):
    """
    A Material Design slider that allows a user to select a value from a range.
    Accepts a SliderTheme for detailed styling.
    """
    shared_styles: Dict[Tuple, str] = {}

    def __init__(self,
                 key: Key,
                 controller: SliderController,
                 onChanged: Callable[[float], None] = None,
                 onChangeStart: Callable[[float], None] = None,
                 onChangeEnd: Callable[[float], None] = None,
                 min: float = 0.0,
                 max: float = 1.0,
                 divisions: Optional[int] = None,
                 # --- Direct style props (override theme) ---
                 activeColor: Optional[str] = None,
                 inactiveColor: Optional[str] = None,
                 thumbColor: Optional[str] = None,
                 # --- Theme ---
                 theme: Optional[SliderTheme] = None):

        super().__init__(key=key)

        if not isinstance(controller, SliderController):
            raise TypeError("Slider widget requires a SliderController instance.")
        
        # Initialize default theme if none provided
        theme = theme or SliderTheme()

        self.controller = controller
        self.onChanged = onChanged
        self.onChangeStart = onChangeStart
        self.onChangeEnd = onChangeEnd
        self.min = min
        self.max = max
        self.divisions = divisions

        # --- Style Precedence Logic ---
        # 1. Direct Prop > 2. Theme Prop > 3. Default
        self.activeColor = activeColor or theme.activeTrackColor or Colors.primary
        self.inactiveColor = inactiveColor or theme.inactiveTrackColor or Colors.surfaceVariant
        self.thumbColor = thumbColor or theme.thumbColor or Colors.primary
        self.overlayColor = theme.overlayColor or Colors.rgba(103, 80, 164, 0.15)
        self.trackHeight = theme.trackHeight
        self.thumbSize = theme.thumbSize
        self.thumbBorderWidth = theme.thumbBorderWidth
        self.overlaySize = theme.overlaySize

        # --- Callback Management (no change) ---
        self.on_drag_update_name = f"slider_update_{id(self.controller)}"
        Api.instance().register_callback(self.on_drag_update_name, self._handle_drag_update)

        # --- CSS Style Management ---
        # The style_key MUST now include all themeable properties
        self.style_key = (
            self.activeColor, self.inactiveColor, self.thumbColor,
            self.overlayColor, self.trackHeight, self.thumbSize,
            self.thumbBorderWidth, self.overlaySize
        )
        
        if self.style_key not in Slider.shared_styles:
            self.css_class = f"shared-slider-{len(Slider.shared_styles)}"
            Slider.shared_styles[self.style_key] = self.css_class
        else:
            self.css_class = Slider.shared_styles[self.style_key]

        self.drag_ended: bool = self.controller.isDragEnded

    def _handle_drag_update(self, new_value: float, drag_ended: bool):
        # This method remains the same
        self.controller.isDragEnded = drag_ended
        clamped_value = max(self.min, min(self.max, new_value))
        
        snapped_value = clamped_value
        if self.divisions is not None and self.divisions > 0:
            step = (self.max - self.min) / self.divisions
            snapped_value = self.min + round((clamped_value - self.min) / step) * step
            snapped_value = max(self.min, min(self.max, snapped_value))
            
        if self.onChanged:
            self.onChanged(snapped_value)

        if self.onChangeEnd and drag_ended:
            self.onChangeEnd(snapped_value)

    def render_props(self) -> Dict[str, Any]:
        # This method remains the same
        current_value = self.controller.value
        isDragEnded = self.controller.isDragEnded
        range_val = self.max - self.min
        percentage = ((current_value - self.min) / range_val) * 100 if range_val > 0 else 0

        return {
            "css_class": self.css_class,
            "init_slider": True,
            "type": "slider",
            "onDragName": self.on_drag_update_name,
            "onDrag": self._handle_drag_update,
            "isDragEnded" : isDragEnded,
            "slider_options": { "min": self.min, "max": self.max, "onDragName": self.on_drag_update_name, "isDragEnded" : isDragEnded },
            "style": { "--slider-percentage": f"{percentage}%" }
        }

    def get_required_css_classes(self) -> Set[str]:
        return {self.css_class}

    @staticmethod
    def _generate_html_stub(widget_instance: 'Slider', html_id: str, props: Dict) -> str:
        # This method remains the same
        css_class = props.get('css_class', '')
        style_prop = props.get('style', {})
        percentage_str = style_prop.get('--slider-percentage', '0%')
        style_attr = f'style="width: 100%; --slider-percentage: {percentage_str};"'
        
        return f"""
        <div id="{html_id}" class="slider-container {css_class}" {style_attr}>
            <div class="slider-track"></div>
            <div class="slider-track-active"></div>
            <div class="slider-thumb"></div>
        </div>
        """
        
    @staticmethod
    def generate_css_rule(style_key: Tuple, css_class: str) -> str:
        """Generates themed CSS for the slider's appearance and states."""
        # --- Unpack all theme properties from the style_key ---
        (active_color, inactive_color, thumb_color, overlay_color,
         track_height, thumb_size, thumb_border_width, overlay_size) = style_key
        
        # Calculate track border radius based on height
        track_radius = track_height / 2.0
        
        return f"""
        .{css_class}.slider-container {{
            position: relative; width: 100%; height: 20px;
            display: flex; align-items: center; cursor: pointer;
            -webkit-tap-highlight-color: transparent;
        }}
        .{css_class} .slider-track, .{css_class} .slider-track-active {{
            position: absolute; width: 100%; height: {track_height}px;
            border-radius: {track_radius}px; pointer-events: none;
        }}
        .{css_class} .slider-track {{ background-color: {inactive_color}; }}
        .{css_class} .slider-track-active {{
            background-color: {active_color}; width: var(--slider-percentage, 0%);
        }}
        .{css_class} .slider-thumb {{
            position: absolute; left: var(--slider-percentage, 0%);
            transform: translateX(-50%);
            width: {thumb_size}px;
            height: {thumb_size}px;
            background-color: {thumb_color};
            border-radius: 50%;
            border: {thumb_border_width}px solid {thumb_color};
            transition: transform 0.1s ease-out, box-shadow 0.1s ease-out;
            box-shadow: 0 1px 3px rgba(0,0,0,0.2);
            pointer-events: none;
        }}
        .{css_class}.slider-container:hover .slider-thumb {{ transform: translateX(-50%) scale(1.2); }}
        .{css_class}.slider-container.active .slider-thumb {{
            transform: translateX(-50%) scale(1.4);
            box-shadow: 0 0 0 {overlay_size}px {overlay_color};
        }}
        """# In pythra/widgets.py

class Slider(Widget):
    """
    A Material Design slider that allows a user to select a value from a range.
    Accepts a SliderTheme for detailed styling.
    """
    shared_styles: Dict[Tuple, str] = {}

    def __init__(self,
                 key: Key,
                 controller: SliderController,
                 onChanged: Callable[[float], None] = None,
                 onChangeStart: Callable[[float], None] = None,
                 onChangeEnd: Callable[[float], None] = None,
                 min: float = 0.0,
                 max: float = 1.0,
                 divisions: Optional[int] = None,
                 # --- Direct style props (override theme) ---
                 activeColor: Optional[str] = None,
                 inactiveColor: Optional[str] = None,
                 thumbColor: Optional[str] = None,
                 # --- Theme ---
                 theme: Optional[SliderTheme] = None):

        super().__init__(key=key)

        if not isinstance(controller, SliderController):
            raise TypeError("Slider widget requires a SliderController instance.")
        
        # Initialize default theme if none provided
        theme = theme or SliderTheme()

        self.controller = controller
        self.onChanged = onChanged
        self.onChangeStart = onChangeStart
        self.onChangeEnd = onChangeEnd
        self.min = min
        self.max = max
        self.divisions = divisions

        # --- Style Precedence Logic ---
        # 1. Direct Prop > 2. Theme Prop > 3. Default
        self.activeColor = activeColor or theme.activeTrackColor or Colors.primary
        self.inactiveColor = inactiveColor or theme.inactiveTrackColor or Colors.surfaceVariant
        self.thumbColor = thumbColor or theme.thumbColor or Colors.primary
        self.overlayColor = theme.overlayColor or Colors.rgba(103, 80, 164, 0.15)
        self.trackHeight = theme.trackHeight
        self.thumbSize = theme.thumbSize
        self.thumbBorderWidth = theme.thumbBorderWidth
        self.overlaySize = theme.overlaySize

        # --- Callback Management (no change) ---
        self.on_drag_update_name = f"slider_update_{id(self.controller)}"
        # Api.instance().register_callback(self.on_drag_update_name, self._handle_drag_update)

        # --- CSS Style Management ---
        # The style_key MUST now include all themeable properties
        self.style_key = (
            self.activeColor, self.inactiveColor, self.thumbColor,
            self.overlayColor, self.trackHeight, self.thumbSize,
            self.thumbBorderWidth, self.overlaySize
        )
        
        if self.style_key not in Slider.shared_styles:
            self.css_class = f"shared-slider-{len(Slider.shared_styles)}"
            Slider.shared_styles[self.style_key] = self.css_class
        else:
            self.css_class = Slider.shared_styles[self.style_key]

        self.drag_ended: bool = self.controller.isDragEnded

    def _handle_drag_update(self, new_value: float, drag_ended: bool):
        # This method remains the same
        self.controller.isDragEnded = drag_ended
        clamped_value = max(self.min, min(self.max, new_value))
        
        snapped_value = clamped_value
        if self.divisions is not None and self.divisions > 0:
            step = (self.max - self.min) / self.divisions
            snapped_value = self.min + round((clamped_value - self.min) / step) * step
            snapped_value = max(self.min, min(self.max, snapped_value))
            
        if self.onChanged:
            self.onChanged(snapped_value)

        if self.onChangeEnd and drag_ended:
            self.onChangeEnd(snapped_value)

    def render_props(self) -> Dict[str, Any]:
        # This method remains the same
        current_value = self.controller.value
        isDragEnded = self.controller.isDragEnded
        range_val = self.max - self.min
        percentage = ((current_value - self.min) / range_val) * 100 if range_val > 0 else 0

        return {
            "css_class": self.css_class,
            "init_slider": True,
            "type": "slider",
            "onDragName": self.on_drag_update_name,
            "onDrag": self._handle_drag_update,
            "isDragEnded" : isDragEnded,
            "slider_options": { "min": self.min, "max": self.max, "onDragName": self.on_drag_update_name, "isDragEnded" : isDragEnded },
            "style": { "--slider-percentage": f"{percentage}%" }
        }

    def get_required_css_classes(self) -> Set[str]:
        return {self.css_class}

    @staticmethod
    def _generate_html_stub(widget_instance: 'Slider', html_id: str, props: Dict) -> str:
        # This method remains the same
        css_class = props.get('css_class', '')
        style_prop = props.get('style', {})
        percentage_str = style_prop.get('--slider-percentage', '0%')
        style_attr = f'style="width: 100%; --slider-percentage: {percentage_str};"'
        
        return f"""
        <div id="{html_id}" class="slider-container {css_class}" {style_attr}>
            <div class="slider-track"></div>
            <div class="slider-track-active"></div>
            <div class="slider-thumb"></div>
        </div>
        """
        
    @staticmethod
    def generate_css_rule(style_key: Tuple, css_class: str) -> str:
        """Generates themed CSS for the slider's appearance and states."""
        # --- Unpack all theme properties from the style_key ---
        (active_color, inactive_color, thumb_color, overlay_color,
         track_height, thumb_size, thumb_border_width, overlay_size) = style_key
        
        # Calculate track border radius based on height
        track_radius = track_height / 2.0
        
        return f"""
        .{css_class}.slider-container {{
            position: relative; width: 100%; height: 20px;
            display: flex; align-items: center; cursor: pointer;
            -webkit-tap-highlight-color: transparent;
        }}
        .{css_class} .slider-track, .{css_class} .slider-track-active {{
            position: absolute; width: 100%; height: {track_height}px;
            border-radius: {track_radius}px; pointer-events: none;
        }}
        .{css_class} .slider-track {{ background-color: {inactive_color}; }}
        .{css_class} .slider-track-active {{
            background-color: {active_color}; width: var(--slider-percentage, 0%);
        }}
        .{css_class} .slider-thumb {{
            position: absolute; left: var(--slider-percentage, 0%);
            transform: translateX(-50%);
            width: {thumb_size}px;
            height: {thumb_size}px;
            background-color: {thumb_color};
            border-radius: 50%;
            border: {thumb_border_width}px solid {thumb_color};
            transition: transform 0.1s ease-out, box-shadow 0.1s ease-out;
            box-shadow: 0 1px 3px rgba(0,0,0,0.2);
            pointer-events: none;
        }}
        .{css_class}.slider-container:hover .slider-thumb {{ transform: translateX(-50%) scale(1.2); }}
        .{css_class}.slider-container.active .slider-thumb {{
            transform: translateX(-50%) scale(1.4);
            box-shadow: 0 0 0 {overlay_size}px {overlay_color};
        }}
        """



class Checkbox(Widget):
    """
    A Material Design checkbox that conforms to the framework's style-swapping logic.
    It treats its 'checked' and 'unchecked' states as two distinct visual styles,
    each with its own shared CSS class, allowing it to work with the existing
    core update mechanism.
    """
    shared_styles: Dict[Tuple, str] = {}

    def __init__(self,
                 key: Key,
                 value: bool,
                 onChanged: Callable[[bool], None],
                 activeColor: Optional[str] = None,
                 checkColor: Optional[str] = None,
                 inactiveColor: Optional[str] = None,
                 theme: Optional[CheckboxTheme] = None):

        super().__init__(key=key)

        if not isinstance(key, Key):
             raise TypeError("Checkbox requires a unique Key.")
        if onChanged is None:
            raise ValueError("Checkbox requires an onChanged callback.")

        theme = theme or CheckboxTheme()

        self.value = value
        self.onChanged = onChanged

        # --- Style Configuration ---
        self.activeColor = activeColor or theme.activeColor or Colors.primary
        self.checkColor = checkColor or theme.checkColor or Colors.onPrimary
        self.inactiveColor = inactiveColor or theme.inactiveColor or Colors.onSurfaceVariant
        self.splashColor = theme.splashColor or Colors.rgba(103, 80, 164, 0.15)
        self.size = theme.size
        self.strokeWidth = theme.strokeWidth
        self.splashRadius = theme.splashRadius

        # --- Callback setup that conforms to the Reconciler pattern ---
        self.onPressedName = f"checkbox_press_{self.key.value}"
        # The Reconciler will find the `onPressed` method below and register it.

        # --- STATEFUL STYLE KEY (The Core of the Solution) ---
        # The boolean 'value' is part of the key. This ensures that a checked
        # and unchecked checkbox get two different, unique shared CSS classes.
        self.style_key = (
            self.value, # <-- This is the key to making it work
            self.activeColor, self.checkColor, self.inactiveColor, self.splashColor,
            self.size, self.strokeWidth, self.splashRadius
        )

        if self.style_key not in Checkbox.shared_styles:
            self.css_class = f"shared-checkbox-{len(Checkbox.shared_styles)}"
            Checkbox.shared_styles[self.style_key] = self.css_class
        else:
            self.css_class = Checkbox.shared_styles[self.style_key]

    def onPressed(self):
        """ The framework's Reconciler will automatically find and register this method. """
        self.onChanged(not self.value)

    def render_props(self) -> Dict[str, Any]:
        """
        Passes the single, state-aware CSS class and the callback name to the reconciler.
        """
        return {
            "css_class": self.css_class,
            "onPressedName": self.onPressedName,
            "onPressed": self.onPressed,
        }

    def get_required_css_classes(self) -> Set[str]:
        return {self.css_class}

    @staticmethod
    def _generate_html_stub(widget_instance: 'Checkbox', html_id: str, props: Dict) -> str:
        """Generates the HTML stub. Now with .strip() to prevent whitespace issues."""
        css_class = props.get('css_class', '')
        on_click_handler = f"handleClick('{props.get('onPressedName', '')}')"

        return f"""
        <div id="{html_id}" class="checkbox-container {css_class}" onclick="{on_click_handler}">
            <svg class="checkbox-svg" viewBox="0 0 24 24">
                <path class="checkbox-checkmark" d="M1.73,12.91 8.1,19.28 22.79,4.59"/>
            </svg>
        </div>
        """.strip()

    @staticmethod
    def generate_css_rule(style_key: Tuple, css_class: str) -> str:
        """
        Generates a specific CSS rule for EITHER the checked OR unchecked state,
        based on the boolean value included in the style_key.
        """
        (is_checked, active_color, check_color, inactive_color, splash_color,
         size, stroke_width, splash_radius) = style_key

        if is_checked:
            background_color = active_color
            border_color = active_color
            checkmark_offset = 0
        else:
            background_color = 'transparent'
            border_color = inactive_color
            checkmark_offset = 29

        # We generate a unique animation name to avoid conflicts
        animation_name = f"checkbox-ripple-{css_class}"

        return f"""
        .{css_class}.checkbox-container {{
            position: relative;
            width: {size}px; height: {size}px;
            border: {stroke_width}px solid {border_color};
            border-radius: 4px;
            background-color: {background_color};
            cursor: pointer;
            display: inline-flex; align-items: center; justify-content: center;
            transition: background-color 0.15s ease-out, border-color 0.15s ease-out;
            -webkit-tap-highlight-color: transparent;
        }}
        .{css_class} .checkbox-svg {{
            width: 100%; height: 100%;
            fill: none;
            stroke: {check_color};
            stroke-width: {stroke_width + 1};
            stroke-linecap: round; stroke-linejoin: round;
        }}
        .{css_class} .checkbox-checkmark {{
            stroke-dasharray: 29;
            stroke-dashoffset: {checkmark_offset};
            transition: stroke-dashoffset 0.2s cubic-bezier(0.4, 0.0, 0.2, 1);
        }}
        .{css_class}.checkbox-container:active::before {{
            content: '';
            position: absolute; top: 50%; left: 50%;
            width: 0; height: 0;
            background-color: {splash_color};
            border-radius: 50%;
            transform: translate(-50%, -50%);
            animation: {animation_name} 0.4s ease-out;
        }}
        @keyframes {animation_name} {{
            from {{ width: 0; height: 0; opacity: 1; }}
            to {{ width: {splash_radius * 2}px; height: {splash_radius * 2}px; opacity: 0; }}
        }}
        """


# In pythra/widgets.py

# ... (keep all your other widget classes)

class Switch(Widget):
    """
    A Material Design switch that toggles a boolean state.

    This widget conforms to the framework's style-swapping logic by treating
    its 'on' and 'off' states as two distinct visual styles, each with its own
    shared CSS class.
    """
    shared_styles: Dict[Tuple, str] = {}

    def __init__(self,
                 key: Key,
                 value: bool,
                 onChanged: Callable[[bool], None],
                 activeColor: Optional[str] = None,
                 thumbColor: Optional[str] = None,
                 theme: Optional[SwitchTheme] = None):

        super().__init__(key=key)

        if not isinstance(key, Key):
             raise TypeError("Switch requires a unique Key.")
        if onChanged is None:
            raise ValueError("Switch requires an onChanged callback.")

        theme = theme or SwitchTheme()
        self.value = value
        self.onChanged = onChanged

        # --- Style Precedence: Direct Prop > Theme Prop > M3 Default ---
        self.activeTrackColor = activeColor or theme.activeTrackColor or Colors.primary
        self.inactiveTrackColor = theme.inactiveTrackColor or Colors.surfaceVariant
        self.activeThumbColor = theme.activeThumbColor or Colors.onPrimary
        self.thumbColor = thumbColor or theme.thumbColor or Colors.outline

        # --- Callback Conformance ---
        self.onPressedName = f"switch_press_{self.key.value}"
        # The Reconciler will find and register the `onPressed` method below.

        # --- STATEFUL STYLE KEY ---
        # The boolean 'value' is part of the key, generating a unique class
        # for the 'on' state and another for the 'off' state.
        self.style_key = (
            self.value,
            self.activeTrackColor,
            self.inactiveTrackColor,
            self.activeThumbColor,
            self.thumbColor,
        )

        if self.style_key not in Switch.shared_styles:
            self.css_class = f"shared-switch-{len(Switch.shared_styles)}"
            Switch.shared_styles[self.style_key] = self.css_class
        else:
            self.css_class = Switch.shared_styles[self.style_key]

    def onPressed(self):
        """The framework's Reconciler will automatically find and register this."""
        self.onChanged(not self.value)

    def render_props(self) -> Dict[str, Any]:
        """Passes the state-aware CSS class and callback name to the reconciler."""
        return {
            "css_class": self.css_class,
            "onPressedName": self.onPressedName,
            "onPressed": self.onPressed,
        }

    def get_required_css_classes(self) -> Set[str]:
        return {self.css_class}

    @staticmethod
    def _generate_html_stub(widget_instance: 'Switch', html_id: str, props: Dict) -> str:
        """Generates the HTML structure for the switch (track and thumb)."""
        css_class = props.get('css_class', '')
        on_click_handler = f"handleClick('{props.get('onPressedName', '')}')"

        return f"""
        <div id="{html_id}" class="switch-container {css_class}" onclick="{on_click_handler}">
            <div class="switch-track"></div>
            <div class="switch-thumb"></div>
        </div>
        """.strip()

    @staticmethod
    def generate_css_rule(style_key: Tuple, css_class: str) -> str:
        """
        Generates a specific CSS rule for EITHER the 'on' OR 'off' state,
        based on the boolean value included in the style_key.
        """
        (is_on, active_track_color, inactive_track_color,
         active_thumb_color, inactive_thumb_color) = style_key

        # --- Determine styles based on the is_on flag ---
        if is_on:
            track_color = active_track_color
            thumb_color = active_thumb_color
            thumb_transform = "translateX(24px)" # Position for 'on' state
        else:
            track_color = inactive_track_color
            thumb_color = inactive_thumb_color
            thumb_transform = "translateX(4px)"  # Position for 'off' state

        return f"""
        /* --- Style for {css_class} ('on' state: {is_on}) --- */
        .{css_class}.switch-container {{
            position: relative;
            width: 52px;
            height: 32px;
            border-radius: 16px;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            flex-shrink: 0;
            transition: background-color 0.2s ease-in-out;
            background-color: {track_color};
        }}
        .{css_class} .switch-thumb {{
            position: absolute;
            width: 24px;
            height: 24px;
            background-color: {thumb_color};
            border-radius: 50%;
            box-shadow: 0 1px 3px rgba(0,0,0,0.2);
            transition: transform 0.2s cubic-bezier(0.4, 0.0, 0.2, 1), background-color 0.2s ease-in-out;
            transform: {thumb_transform};
        }}
        """


# In pythra/widgets.py

# ... (keep all your other widget classes)

class Radio(Widget):
    """
    A Material Design radio button.

    Used to select one option from a set. A radio button's state is determined
    by comparing its `value` to a `groupValue`. When the radio button is tapped,
    it calls the `onChanged` callback with its `value`.
    """
    shared_styles: Dict[Tuple, str] = {}

    def __init__(self,
                 key: Key,
                 value: Any,  # The unique value this radio button represents
                 groupValue: Any,  # The currently selected value for the group
                 onChanged: Callable[[Any], None],
                 theme: Optional[RadioTheme] = None):

        super().__init__(key=key)

        if not isinstance(key, Key):
             raise TypeError("Radio requires a unique Key.")
        if onChanged is None:
            raise ValueError("Radio requires an onChanged callback.")

        theme = theme or RadioTheme()
        self.value = value
        self.groupValue = groupValue
        self.onChanged = onChanged

        # The radio button is selected if its value matches the group's value.
        self.isSelected = (self.value == self.groupValue)

        # --- Style Configuration ---
        self.activeColor = theme.fillColor or Colors.primary
        self.inactiveColor = Colors.onSurfaceVariant
        self.splashColor = theme.splashColor or Colors.rgba(103, 80, 164, 0.15)

        # --- Callback Conformance ---
        self.onPressedName = f"radio_press_{self.key.value}"
        # The Reconciler will find and register the `onPressed` method.

        # --- STATEFUL STYLE KEY ---
        # The selection state is the most crucial part of the style key.
        self.style_key = (
            self.isSelected,
            self.activeColor,
            self.inactiveColor,
            self.splashColor,
        )

        if self.style_key not in Radio.shared_styles:
            self.css_class = f"shared-radio-{len(Radio.shared_styles)}"
            Radio.shared_styles[self.style_key] = self.css_class
        else:
            self.css_class = Radio.shared_styles[self.style_key]

    def onPressed(self):
        """The Reconciler will find this and register it with the API."""
        # When pressed, it calls the parent's handler with its own unique value.
        self.onChanged(self.value)

    def render_props(self) -> Dict[str, Any]:
        """Passes the state-aware CSS class and callback name to the reconciler."""
        return {
            "css_class": self.css_class,
            "onPressedName": self.onPressedName,
        }

    def get_required_css_classes(self) -> Set[str]:
        return {self.css_class}

    @staticmethod
    def _generate_html_stub(widget_instance: 'Radio', html_id: str, props: Dict) -> str:
        """Generates the HTML structure: an outer circle and an inner dot."""
        css_class = props.get('css_class', '')
        on_click_handler = f"handleClick('{props.get('onPressedName', '')}')"

        return f"""
        <div id="{html_id}" class="radio-container {css_class}" onclick="{on_click_handler}">
            <div class="radio-dot"></div>
        </div>
        """.strip()

    @staticmethod
    def generate_css_rule(style_key: Tuple, css_class: str) -> str:
        """
        Generates a specific CSS rule for EITHER the 'selected' OR 'unselected'
        state, based on the boolean value in the style_key.
        """
        (is_selected, active_color, inactive_color, splash_color) = style_key

        if is_selected:
            border_color = active_color
            dot_bg_color = active_color
            dot_transform = "scale(1)"
        else:
            border_color = inactive_color
            dot_bg_color = active_color # Dot color is always active, just hidden
            dot_transform = "scale(0)"

        animation_name = f"radio-ripple-{css_class}"

        return f"""
        /* --- Style for {css_class} ('selected' state: {is_selected}) --- */
        .{css_class}.radio-container {{
            position: relative;
            width: 20px; height: 20px;
            border: 2px solid {border_color};
            border-radius: 50%;
            display: inline-flex;
            align-items: center; justify-content: center;
            cursor: pointer;
            transition: border-color 0.2s ease-in-out;
            -webkit-tap-highlight-color: transparent;
        }}
        .{css_class} .radio-dot {{
            width: 10px; height: 10px;
            background-color: {dot_bg_color};
            border-radius: 50%;
            transform: {dot_transform};
            transition: transform 0.2s cubic-bezier(0.4, 0.0, 0.2, 1);
        }}

        /* --- INTERACTION STATES (Splash/Ripple Effect) --- */
        .{css_class}.radio-container:active::before {{
            content: '';
            position: absolute; top: 50%; left: 50%;
            width: 0; height: 0;
            background-color: {splash_color};
            border-radius: 50%;
            transform: translate(-50%, -50%);
            animation: {animation_name} 0.4s ease-out;
        }}
        @keyframes {animation_name} {{
            from {{ width: 0; height: 0; opacity: 1; }}
            to {{ width: 40px; height: 40px; opacity: 0; }}
        }}
        """

# In pythra/widgets.py

class Dropdown(Widget):
    """
    A custom, stateless dropdown widget.

    Its state (selected value) is managed by a `DropdownController`.
    It renders pure HTML and is controlled by the dropdown.js engine.
    """
    shared_styles: Dict[Tuple, str] = {}

    def __init__(self,
                 key: Key,
                 controller: DropdownController,
                 items: List[Union[str, Tuple[str, Any]]],
                 onChanged: Callable[[Any], None],
                 hintText: str = "Select an option",
                 # --- Theme properties can be added here later ---
                 backgroundColor: str = Colors.surfaceContainerHighest,
                 textColor: str = Colors.onSurface,
                 borderColor: str = Colors.outline,
                 borderRadius: int = 4):

        super().__init__(key=key)

        if not isinstance(controller, DropdownController):
            raise TypeError("Dropdown requires a DropdownController instance.")

        self.controller = controller
        self.items = items
        self.onChanged = onChanged
        self.hintText = hintText
        
        # --- Style Properties ---
        self.backgroundColor = backgroundColor
        self.textColor = textColor
        self.borderColor = borderColor
        self.borderRadius = borderRadius

        # --- Callback Management ---
        self.on_changed_name = f"dropdown_change_{id(self.controller)}"
        # Note: We pass the user's `onChanged` function directly. The JS engine
        # will send the new value, and the framework will call this function.
        
        # --- CSS Style Management ---
        self.style_key = (self.backgroundColor, self.textColor, self.borderColor, self.borderRadius)
        
        if self.style_key not in Dropdown.shared_styles:
            self.css_class = f"shared-dropdown-{len(Dropdown.shared_styles)}"
            Dropdown.shared_styles[self.style_key] = self.css_class
        else:
            self.css_class = Dropdown.shared_styles[self.style_key]

    def _get_label_for_value(self, value: Any) -> str:
        """Finds the display label corresponding to a given value."""
        for item in self.items:
            if isinstance(item, tuple):
                label, item_value = item
                if item_value == value:
                    return label
            elif item == value: # Handle simple list of strings
                return item
        return self.hintText # Fallback if value not found

    def render_props(self) -> Dict[str, Any]:
        """Pass all necessary data to the reconciler and JS engine."""
        return {
            "css_class": self.css_class,
            "init_dropdown": True, # Flag for the JS initializer
            "dropdown_options": {
                "onChangedName": self.on_changed_name,
            },
            # This is the new, unified callback pattern
            "onChangedName": self.on_changed_name,
            "onChanged": self.onChanged,
        }

    def get_required_css_classes(self) -> Set[str]:
        return {self.css_class}

    @staticmethod
    def _generate_html_stub(widget_instance: 'Dropdown', html_id: str, props: Dict) -> str:
        """Generates the pure HTML structure for the dropdown."""
        css_class = props.get('css_class', '')
        controller = widget_instance.controller
        items = widget_instance.items
        
        current_label = widget_instance._get_label_for_value(controller.selectedValue)
        
        # Build the list of dropdown items (<li> elements)
        items_html = ""
        for item in items:
            if isinstance(item, tuple):
                label, value = item
                items_html += f'<li class="dropdown-item" data-value="{html.escape(str(value), quote=True)}">{html.escape(label)}</li>'
            else: # Simple list of strings
                items_html += f'<li class="dropdown-item" data-value="{html.escape(str(item), quote=True)}">{html.escape(item)}</li>'

        return f"""
        <div id="{html_id}" class="dropdown-container {css_class}">
            <div class="dropdown-value-container">
                <span>{html.escape(current_label)}</span>
                <svg class="dropdown-caret" viewBox="0 0 24 24"><path d="M7 10l5 5 5-5z"></path></svg>
            </div>
            <ul class="dropdown-menu">
                {items_html}
            </ul>
        </div>
        """
        
    @staticmethod
    def generate_css_rule(style_key: Tuple, css_class: str) -> str:
        """Generates the CSS for the dropdown's appearance and states."""
        bg_color, text_color, border_color, border_radius = style_key

        return f"""
        .{css_class}.dropdown-container {{
            position: relative;
            width: 100%;
            font-family: sans-serif;
        }}
        .{css_class} .dropdown-value-container {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 8px 12px;
            background-color: {bg_color};
            color: {text_color};
            border: 1px solid {border_color};
            border-radius: {border_radius}px;
            cursor: pointer;
            transition: border-color 0.2s;
        }}
        .{css_class}.open .dropdown-value-container {{
            border-color: {Colors.primary}; /* Highlight when open */
        }}
        .{css_class} .dropdown-caret {{
            width: 20px;
            height: 20px;
            fill: currentColor;
            transition: transform 0.2s ease-in-out;
        }}
        .{css_class}.open .dropdown-caret {{
            transform: rotate(180deg);
        }}
        .{css_class} .dropdown-menu {{
            position: absolute;
            top: calc(100% + 4px);
            left: 0;
            right: 0;
            background-color: {bg_color};
            border: 1px solid {border_color};
            border-radius: {border_radius}px;
            list-style: none;
            margin: 0;
            padding: 4px 0;
            z-index: 100;
            opacity: 0;
            visibility: hidden;
            transform: translateY(-10px);
            transition: opacity 0.2s, transform 0.2s, visibility 0.2s;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }}
        .{css_class}.open .dropdown-menu {{
            opacity: 1;
            visibility: visible;
            transform: translateY(0);
        }}
        .{css_class} .dropdown-item {{
            padding: 8px 12px;
            cursor: pointer;
            transition: background-color 0.2s;
        }}
        .{css_class} .dropdown-item:hover {{
            background-color: {Colors.rgba(103, 80, 164, 0.1)}; /* Hover color */
        }}
        """

# In pythra/widgets.py
# (Make sure to import TapDetails, PanUpdateDetails from your events file)


class GestureDetector(Widget):
    """
    A widget that detects gestures.

    This widget does not have a visual representation but instead tries to
    recognize gestures that are made on its child widget.
    """
    shared_styles: Dict[Tuple, str] = {}

    def __init__(self,
                 key: Key,
                 child: Widget,
                 onTap: Optional[Callable[[TapDetails], None]] = None,
                 onDoubleTap: Optional[Callable[[], None]] = None,
                 onLongPress: Optional[Callable[[], None]] = None,
                 onPanStart: Optional[Callable[[], None]] = None,
                 onPanUpdate: Optional[Callable[[PanUpdateDetails], None]] = None,
                 onPanEnd: Optional[Callable[[], None]] = None,
                 ):

        super().__init__(key=key, children=[child])
        
        self.child = child
        self.onTap = onTap
        self.onDoubleTap = onDoubleTap
        self.onLongPress = onLongPress
        self.onPanStart = onPanStart
        self.onPanUpdate = onPanUpdate
        self.onPanEnd = onPanEnd
        
        # --- Unique callback names for this instance ---
        instance_id = id(self)
        self.onTapName = f"gd_tap_{instance_id}" if onTap else None
        self.onDoubleTapName = f"gd_dbtap_{instance_id}" if onDoubleTap else None
        self.onLongPressName = f"gd_lpress_{instance_id}" if onLongPress else None
        self.onPanStartName = f"gd_pstart_{instance_id}" if onPanStart else None
        self.onPanUpdateName = f"gd_pupdate_{instance_id}" if onPanUpdate else None
        self.onPanEndName = f"gd_pend_{instance_id}" if onPanEnd else None

        # --- CSS Style Management ---
        # The style key depends on which gestures are active, to apply CSS like `cursor`.
        has_tap = bool(onTap or onDoubleTap)
        has_pan = bool(onPanStart or onPanUpdate or onPanEnd)
        self.style_key = (has_tap, has_pan)

        if self.style_key not in GestureDetector.shared_styles:
            self.css_class = f"shared-gesture-{len(GestureDetector.shared_styles)}"
            GestureDetector.shared_styles[self.style_key] = self.css_class
        else:
            self.css_class = GestureDetector.shared_styles[self.style_key]

    def render_props(self) -> Dict[str, Any]:
        """Pass all necessary data to the reconciler and JS engine."""
        return {
            "css_class": self.css_class,
            "init_gesture_detector": True,
            "gesture_options": {
                "onTapName": self.onTapName,
                "onDoubleTapName": self.onDoubleTapName,
                "onLongPressName": self.onLongPressName,
                "onPanStartName": self.onPanStartName,
                "onPanUpdateName": self.onPanUpdateName,
                "onPanEndName": self.onPanEndName,
            },
            # Pass the actual callback functions for the reconciler to register
            "onTap": self.onTap,
            "onTapName": self.onTapName,
            "onDoubleTap": self.onDoubleTap,
            "onLongPress": self.onLongPress,
            "onPanStart": self.onPanStart,
            "onPanUpdate": self.onPanUpdate,
            "onPanEnd": self.onPanEnd,
            "onDoubleTapName": self.onDoubleTapName,
            "onLongPressName": self.onLongPressName,
            "onPanStartName": self.onPanStartName,
            "onPanUpdateName": self.onPanUpdateName,
            "onPanEndName": self.onPanEndName,
        }

    def get_required_css_classes(self) -> Set[str]:
        return {self.css_class}

    @staticmethod
    def _generate_html_stub(widget_instance: 'GestureDetector', html_id: str, props: Dict) -> str:
        """A GestureDetector is just a div that wraps its child."""
        # The child's HTML will be generated and placed inside this div by the framework.
        return f'<div id="{html_id}" class="{props.get("css_class", "")}"></div>'

    @staticmethod
    def generate_css_rule(style_key: Tuple, css_class: str) -> str:
        """Generates CSS to make the gesture detector functional."""
        has_tap, has_pan = style_key
        
        styles = [
            # CRITICAL: This makes the wrapper invisible for layout purposes.
            # The child will be positioned as if the GestureDetector div isn't there.
            "display: contents;"
        ]
        
        # We need to apply interaction styles to the child element itself.
        child_styles = []
        if has_tap:
            child_styles.append("cursor: pointer;")
        if has_pan:
            # CRITICAL: These prevent unwanted browser behavior like text selection or page scrolling during a drag.
            child_styles.append("touch-action: none;")
            child_styles.append("user-select: none;")
            child_styles.append("-webkit-user-select: none;") # For Safari

        container_rule = f".{css_class} {{ {' '.join(styles)} }}"
        child_rule = f".{css_class} > * {{ {' '.join(child_styles)} }}"
        
        return f"{container_rule}\n{child_rule}"



class GradientBorderContainer(Widget):
    """
    A widget that wraps its child with an animated gradient border.

    It intelligently calculates its own border-radius based on the child's
    styling and the specified border width (padding).
    """
    shared_styles: Dict[Tuple, str] = {}

    def __init__(self,
                 key: Key,
                 child: Widget,
                 borderWidth: float = 6.0,
                 theme: Optional[GradientBorderTheme] = None):

        super().__init__(key=key, children=[child]) # Child is passed to base

        if not child:
            raise ValueError("GradientBorderContainer requires a child widget.")
            
        self.borderWidth = borderWidth
        self.theme = theme or GradientBorderTheme()

        self.style_key = self.theme.to_tuple()

        if self.style_key not in GradientBorderContainer.shared_styles:
            self.css_class = f"shared-gradient-border-{len(GradientBorderContainer.shared_styles)}"
            GradientBorderContainer.shared_styles[self.style_key] = self.css_class
        else:
            self.css_class = GradientBorderContainer.shared_styles[self.style_key]

    def render_props(self) -> Dict[str, Any]:
        child = self.get_children()[0]
        child_props = child.render_props()

        # --- Intelligent Radius Calculation ---
        child_radius_val = 0.0
        # Check for radius on a Container's decoration
        if isinstance(child, Container) and child.decoration and child.decoration.borderRadius:
            radius_prop = child.decoration.borderRadius
            if isinstance(radius_prop, (int, float)):
                child_radius_val = radius_prop
            elif isinstance(radius_prop, BorderRadius):
                child_radius_val = radius_prop.topLeft # Use one value for simplicity

        wrapper_radius = child_radius_val + self.borderWidth

        # Pass all calculated values as CSS custom properties
        return {
            'css_class': self.css_class,
            'style': {
                '--gradient-border-size': f"{self.borderWidth}px",
                '--gradient-border-radius': f"{wrapper_radius}px",
                '--gradient-child-radius': f"{child_radius_val}px",
            }
        }

    def get_required_css_classes(self) -> Set[str]:
        # The main class + we need to tell the reconciler to style the child
        return {self.css_class, f"{self.css_class}-child-override"}

    @staticmethod
    def _generate_html_stub(widget_instance: 'GradientBorderContainer', html_id: str, props: Dict) -> str:
        # The stub for the wrapper. The child's HTML will be inserted inside by the reconciler.
        style_prop = props.get('style', {})
        style_str = " ".join([f"{key}: {value};" for key, value in style_prop.items()])
        
        return f'<div id="{html_id}" class="{props.get("css_class", "")}" style="{style_str}"></div>'

    @staticmethod
    def generate_css_rule(style_key: Tuple, css_class: str) -> str:
        """Generates the CSS for the gradient container and its child."""
        # Check if we are generating the special child override rule
        if css_class.endswith("-child-override"):
            base_class = css_class.replace("-child-override", "")
            # This rule modifies the direct child of the gradient border container.
            # It forces the child's border-radius to match our calculated value.
            return f"""
            .{base_class} > * {{
                border-radius: var(--gradient-child-radius) !important;
            }}
            """

        # Otherwise, generate the main container rule
        (gradient_colors, direction, speed, timing) = style_key
        
        gradient_str = ", ".join(gradient_colors)

        return f"""
        @keyframes borderShift-{css_class} {{
            0% {{ background-position: 0% 50%; }}
            50% {{ background-position: 100% 50%; }}
            100% {{ background-position: 0% 50%; }}
        }}

        .{css_class} {{
            padding: var(--gradient-border-size);
            border-radius: var(--gradient-border-radius);
            background: linear-gradient({direction}, {gradient_str});
            background-size: 400% 400%;
            animation: borderShift-{css_class} {speed} {timing} infinite;
            /* Ensure it doesn't add extra layout space */
            display: inline-block;
            line-height: 0; /* Fix for extra space below inline elements */
        }}
        """


# In pythra/widgets.py

class GradientClipPathBorder(Widget):
    """
    A widget that wraps its child with an animated gradient border that
    perfectly matches the shape of a complex ClipPath.
    """
    shared_styles: Dict[Tuple, str] = {}

    def __init__(self,
                 key: Key,
                 child: Widget,
                 # ClipPath properties
                 points: List[Tuple[float, float]],
                 radius: float = 0,
                 viewBox: Tuple[float, float] = (100, 100),
                 # Border properties
                 borderWidth: float = 6.0,
                 theme: Optional[GradientBorderTheme] = None):

        super().__init__(key=key, children=[child])
        
        self.points = points
        self.radius = radius
        self.viewBox = viewBox
        self.borderWidth = borderWidth
        self.theme = theme or GradientBorderTheme()

        # CSS class is based on the gradient's theme
        self.style_key = self.theme.to_tuple()

        if self.style_key not in GradientClipPathBorder.shared_styles:
            self.css_class = f"shared-gradient-clip-{len(GradientClipPathBorder.shared_styles)}"
            GradientClipPathBorder.shared_styles[self.style_key] = self.css_class
        else:
            self.css_class = GradientClipPathBorder.shared_styles[self.style_key]

    def render_props(self) -> Dict[str, Any]:
        """Pass all geometric and theme data to the reconciler and JS engine."""
        return {
            "css_class": self.css_class,
            "init_gradient_clip_border": True,
            "gradient_clip_options": {
                "points": self.points,
                "radius": self.radius,
                "viewBox": self.viewBox,
                "borderWidth": self.borderWidth,
            }
        }

    def get_required_css_classes(self) -> Set[str]:
        return {self.css_class}

    @staticmethod
    def _generate_html_stub(widget_instance: 'GradientClipPathBorder', html_id: str, props: Dict) -> str:
        # The stub is just a container. The JS engine will add the background
        # and host divs. The reconciler will place the child inside.
        return f'<div id="{html_id}" class="gradient-clip-container {props.get("css_class", "")}"></div>'

    @staticmethod
    def generate_css_rule(style_key: Tuple, css_class: str) -> str:
        """Generates the CSS for the container and the gradient background."""
        (gradient_colors, direction, speed, timing) = style_key
        gradient_str = ", ".join(gradient_colors)

        return f"""
        @keyframes borderShift-{css_class} {{
            0% {{ background-position: 0% 50%; }}
            50% {{ background-position: 100% 50%; }}
            100% {{ background-position: 0% 50%; }}
        }}

        /* This is the main container, it acts as a grid to stack the layers */
        .{css_class}.gradient-clip-container {{
            display: grid;
            grid-template-areas: "stack";
        }}

        /* The background and content host are placed in the same grid cell */
        .{css_class} .gradient-clip-background,
        .{css_class} .gradient-clip-content-host {{
            grid-area: stack;
        }}

        /* Style the background layer with the animated gradient */
        .{css_class} .gradient-clip-background {{
            background: linear-gradient({direction}, {gradient_str});
            background-size: 400% 400%;
            animation: borderShift-{css_class} {speed} {timing} infinite;
        }}
        """