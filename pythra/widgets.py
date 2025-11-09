# =============================================================================
# PYTHRA WIDGET LIBRARY - The "LEGO Blocks" for Building Your UI
# =============================================================================

"""
PyThra Widget Library

This is your "LEGO block collection" for building user interfaces! Every visual 
element in your app (buttons, text, images, layouts, etc.) is a widget defined here.

**What are widgets?**
Widgets are like LEGO blocks - individual pieces that you can combine to build 
complex user interfaces. Just like LEGO, each widget has:
- A specific purpose (button for clicking, text for displaying words)
- Properties you can customize (colors, sizes, text content)
- The ability to contain other widgets (like a box containing smaller pieces)

**Widget categories in this file:**
- **Layout Widgets**: Container, Column, Row (arrange other widgets)
- **Display Widgets**: Text, Image, Icon (show content to users)
- **Interactive Widgets**: Button, TextField (respond to user input)
- **Specialized Widgets**: Custom components for specific needs

**How to use widgets:**
```python
# Simple widget
Text("Hello World!")

# Widget with properties
Container(
    child=Text("I'm inside a box!"),
    color="blue",
    padding=EdgeInsets.all(20)
)

# Widgets containing other widgets
Column(children=[
    Text("First item"),
    Text("Second item"),
    Button(text="Click me!")
])
```
"""


import html
import json
from .api import Api
from .widgets_more import *
from .base import *
from .state import *
from .styles import *
from .icons import *
from .icons.base import IconData # Import the new data class
from .controllers import *
from .config import Config
import weakref
from typing import Any, Dict, List, Optional, Set, Tuple, Union, Callable


config = Config()
assets_dir = config.get('assets_dir', 'assets')
port = config.get('assets_server_port')
#Colors = Colors()



# =============================================================================
# CONTAINER WIDGET - The "Styled Box" That Holds Other Widgets
# =============================================================================

class Container(Widget):
    """
    The "Swiss Army Knife" of layout widgets - a styled box that can hold one child widget.
    
    **What is Container?**
    Think of Container like a gift box that you can customize:
    - You can change its size, color, and decorations
    - You can add padding (space inside the box)
    - You can add margins (space around the box)
    - You can put ONE item inside it (the child widget)
    
    **Real-world analogy:**
    Container is like a customizable picture frame:
    - The frame itself can be styled (color, border, size)
    - The picture goes inside (child widget)
    - You can add matting around the picture (padding)
    - You can position the frame on the wall (margins, alignment)
    
    **Common use cases:**
    - Adding background colors to widgets
    - Creating spacing around widgets (padding/margins)
    - Making widgets specific sizes (width/height)
    - Adding borders and shadows (decoration)
    - Creating animated gradient backgrounds
    
    **Example uses:**
    ```python
    # Simple colored box
    Container(
        child=Text("I'm in a blue box!"),
        color="blue",
        padding=EdgeInsets.all(20)
    )
    
    # Fancy styled container
    Container(
        child=Button("Click me"),
        decoration=BoxDecoration(
            color="white",
            borderRadius=BorderRadius.circular(10),
            boxShadow=[BoxShadow(color="gray", blur=5)]
        ),
        width=200,
        height=100
    )
    
    # Animated gradient background
    Container(
        child=Text("Fancy animated background!"),
        gradient=GradientTheme(
            gradientColors=["red", "blue", "green"],
            animationSpeed="3s"
        )
    )
    ```
    
    **Key parameters:**
    - child: The widget that goes inside the container
    - color: Simple background color
    - padding: Space inside the container around the child
    - margin: Space outside the container
    - width/height: Fixed dimensions
    - decoration: Advanced styling (borders, shadows, etc.)
    - gradient: Animated gradient backgrounds
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
                 gradient: Optional[GradientTheme] = None,
                 zAxisIndex: int = 0,
                 cssClass: Optional[Union[str, List[str]]] = None,
                 js_init = {},
                 ):
                  # <-- NEW PARAMETER

        super().__init__(key=key, children=[child] if child else [])

        self.padding = padding
        self.color = color
        self.decoration = decoration
        self.width = width
        self.height = height
        self.constraints = constraints
        self.margin = margin
        self.transform = transform
        self.alignment = alignment.to_css() if alignment else None
        self.clipBehavior = clipBehavior
        self.visible = visible
        self.gradient = gradient
        self.zAxisIndex = zAxisIndex
        self.js_init = js_init
        
        # Handle cssClass parameter - convert to list if string
        self.cssClass = cssClass if isinstance(cssClass, list) else [cssClass] if cssClass else []

        # --- UPDATED CSS Class Management ---
        # The style key includes gradient theme and cssClass.
        self.style_key = tuple(make_hashable(prop) for prop in (
            self.padding, self.color, self.decoration, self.width, self.height,
            self.constraints, self.margin, self.transform, self.alignment,
            self.clipBehavior, self.gradient, self.zAxisIndex, tuple(sorted(self.cssClass))
        ))

        if self.style_key not in Container.shared_styles:
            self.css_class = f"shared-container-{len(Container.shared_styles)}"
            Container.shared_styles[self.style_key] = self.css_class
        else:
            self.css_class = Container.shared_styles[self.style_key]

    def render_props(self) -> Dict[str, Any]:
        instance_styles = {}
        
        if not self.visible:
            instance_styles['display'] = 'none'

        # Combine the shared CSS class with any custom classes
        css_classes = [self.css_class] + [cls for cls in self.cssClass if cls]
        css_class = ' '.join(filter(None, css_classes))

        return {
            'css_class': css_class,
            'style': instance_styles,
            '_js_init': self.js_init
        }

    def get_required_css_classes(self) -> Set[str]:
        return {self.css_class}

    @staticmethod
    def generate_css_rule(style_key: Tuple, css_class: str) -> str:
        """
        Static method updated to generate CSS for solid colors OR animated gradients.
        """
        try:
            # 1. Unpack the style_key tuple, now with cssClass at the end
            (padding_tuple, color, decoration_tuple, width, height,
             constraints_tuple, margin_tuple, transform, alignment_tuple,
             clipBehavior, gradient_tuple, z_axis_index, css_classes_tuple) = style_key

            styles = ["box-sizing: border-box;"]
            extra_rules = [] # For storing @keyframes

            # if not visible:
            #     styles.append("display: none;")

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
                # print(alignment_tuple().to_css())
                # align_obj = Alignment(*alignment_tuple)
                styles.append(alignment_tuple)

            if transform: styles.append(f"transform: {transform};")

            if clipBehavior and hasattr(clipBehavior, 'to_css_overflow'):
                overflow_val = clipBehavior.to_css_overflow()
                if overflow_val: styles.append(f"overflow: {overflow_val};")

            if z_axis_index: styles.append(f"z-index: {z_axis_index};")
            
            # Assemble and return the final CSS rules.
            main_rule = f".{css_class} {{ {' '.join(filter(None, styles))} }}"
            
            # Prepend any extra rules (like @keyframes) to the main rule
            return "\n".join(extra_rules) + "\n" + main_rule

        except Exception as e:
            import traceback
            print(f"ERROR generating CSS for Container {css_class} with key {style_key}:")
            traceback.print_exc()
            return f"/* Error generating rule for .{css_class} */"




# =============================================================================
# TEXT WIDGET - The "Word Display" for Showing Text Content
# =============================================================================

class Text(Widget):
    """
    The fundamental "word display" widget - shows text content to your users!
    
    **What is Text widget?**
    Think of Text like a "smart label maker" that can display any text with custom styling.
    It's one of the most basic and important widgets - almost every app needs to show text!
    
    **Real-world analogy:**
    Text widget is like a "smart typewriter" that can:
    - Type any words you want (the data parameter)
    - Use different fonts, sizes, and colors (the style parameter)
    - Align text left, center, or right (textAlign parameter)
    - Handle text that's too long (overflow parameter)
    
    **Common use cases:**
    - Displaying labels ("Name:", "Email:", "Welcome!")
    - Showing user data (usernames, messages, descriptions)
    - Creating headings and titles
    - Displaying instructions or help text
    - Error messages and notifications
    
    **Examples:**
    ```python
    # Simple text
    Text("Hello, World!")
    
    # Styled text with custom appearance
    Text(
        "Important Notice",
        style=TextStyle(
            fontSize=24,
            fontWeight="bold",
            color="red"
        )
    )
    
    # Centered text
    Text(
        "This text is centered",
        textAlign="center"
    )
    
    # Text that shows "..." when too long
    Text(
        "This is a very long text that might not fit",
        overflow="ellipsis"
    )
    ```
    
    **Key parameters:**
    - **data**: The actual words to display (required)
    - **style**: How the text should look (font, size, color, etc.)
    - **textAlign**: Where to position the text ("left", "center", "right")
    - **overflow**: What to do if text is too long ("ellipsis" = "...", "clip" = cut off)
    
    **Performance feature:**
    Text widget is smart about styling - if multiple Text widgets use the same style,
    they share the same CSS class to keep your app running fast!
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


# =============================================================================
# TEXTBUTTON WIDGET - The "Simple Click Button" for Basic Actions
# =============================================================================

class TextButton(Widget):
    """
    A simple, text-based button for basic user interactions - like a clickable label!
    
    **What is TextButton?**
    Think of TextButton like a "clickable text label" - it looks like regular text
    but responds when users click it. It's perfect for simple actions that don't
    need heavy visual emphasis.
    
    **Real-world analogy:**
    TextButton is like a "hyperlink" on a website:
    - Looks like regular text (but maybe colored differently)
    - Shows it's clickable when you hover over it
    - Performs an action when clicked
    - Doesn't have a big button background like "solid" buttons
    
    **When to use TextButton:**
    - Secondary actions ("Cancel", "Skip", "Learn More")
    - Navigation links ("Go to Settings", "View Details")
    - Less important actions that shouldn't dominate the screen
    - Actions in toolbars or menus
    
    **When NOT to use TextButton:**
    - Primary actions (use ElevatedButton instead)
    - Important actions that need emphasis
    - Destructive actions (like "Delete" - use colored buttons)
    
    **Examples:**
    ```python
    # Simple text button
    TextButton(
        child=Text("Cancel"),
        onPressed=lambda: print("Cancel clicked")
    )
    
    # Text button with custom styling
    TextButton(
        child=Text("Learn More"),
        onPressed=go_to_help_page,
        style=ButtonStyle(
            foregroundColor="blue",
            padding=EdgeInsets.all(16)
        )
    )
    
    # Text button with icon
    TextButton(
        child=Row(children=[
            Icon("info"),
            Text("Info")
        ]),
        onPressed=show_info
    )
    ```
    
    **Key parameters:**
    - **child**: What to show inside the button (usually Text, but can be any widget)
    - **onPressed**: Function to call when button is clicked
    - **style**: How the button should look (colors, padding, shape, etc.)
    - **onPressedName**: Custom name for the click handler (for debugging)
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
                # print(f"[TextButton] Registered callback '{self.onPressed_id}' on style creation.")

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
            hv_color = getattr(style_obj, 'hoverColor', 'rgba(0, 0, 0, 0.08)')
            ac_color = getattr(style_obj, 'activeColor', 'rgba(0, 0, 0, 0.12)')
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
            hover_bg_color = hv_color if hv_color else Colors.rgba(0,0,0,0.08) # Fallback dark overlay
            active_bg_color = ac_color if ac_color else Colors.rgba(0,0,0,0.12) # Fallback dark overlay
            try: # Try to make overlay from foreground color
                 # Basic check: Assume hex format #RRGGBB
                 if fg_color and fg_color.startswith('#') and len(fg_color) == 7:
                     r, g, b = int(fg_color[1:3], 16), int(fg_color[3:5], 16), int(fg_color[5:7], 16)
                     hover_bg_color = Colors.rgba(r, g, b, 0.50) # 8% opacity overlay
                     active_bg_color = Colors.rgba(r, g, b, 0.00) # 12% opacity overlay
            except: pass # Ignore errors, use fallback
  
            hover_rule = f".{css_class}:hover {{ background-color: {hover_bg_color};}}"
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

# =============================================================================
# ELEVATEDBUTTON WIDGET - The "Primary Action Button" with Emphasis
# =============================================================================

class ElevatedButton(Widget):
    """
    The "hero button" of your app - draws attention and emphasizes important actions!
    
    **What is ElevatedButton?**
    Think of ElevatedButton as the "main character" button that stands out from the crowd.
    It has a background color and a subtle shadow ("elevation") that makes it appear
    to "float" above the surface, giving it visual importance.
    
    **Real-world analogy:**
    ElevatedButton is like the "big red button" in important control rooms:
    - It stands out visually from everything else
    - It has a solid, substantial appearance
    - It clearly says "this is the main action you should take"
    - It has depth/shadow that makes it look "elevated" above other elements
    
    **When to use ElevatedButton:**
    - Primary actions ("Save", "Submit", "Continue", "Sign In")
    - Actions you want users to notice first
    - Important calls-to-action
    - The "main" button when you have multiple button options
    
    **When NOT to use ElevatedButton:**
    - Secondary actions (use TextButton or OutlinedButton)
    - When you have many buttons (only one should be "elevated")
    - Destructive actions (consider using colored buttons with warning colors)
    
    **Examples:**
    ```python
    # Simple elevated button with default styling
    ElevatedButton(
        child=Text("Save Changes"),
        onPressed=save_changes
    )
    
    # Custom styled elevated button
    ElevatedButton(
        child=Text("Sign In"),
        onPressed=sign_in,
        style=ButtonStyle(
            backgroundColor="#007AFF",  # iOS blue
            foregroundColor="white",
            elevation=4,  # More shadow for emphasis
            padding=EdgeInsets.symmetric(horizontal=24, vertical=12)
        )
    )
    
    # Elevated button with icon and text
    ElevatedButton(
        child=Row(children=[
            Icon("save", color="white"),
            SizedBox(width=8),
            Text("Save")
        ]),
        onPressed=save_data
    )
    ```
    
    **Key parameters:**
    - **child**: Content inside the button (usually Text, but can be Row with icon + text)
    - **onPressed**: Function to call when button is clicked
    - **style**: Appearance customization (colors, elevation, padding, shape, etc.)
    - **elevation**: How much "shadow/depth" the button has (higher = more dramatic)
    
    **Visual hierarchy tip:**
    Use only ONE ElevatedButton per screen/section to maintain clear visual hierarchy!
    """
    shared_styles: Dict[Tuple, str] = {}

    def __init__(self,
                 child: Widget,
                 key: Optional[Key] = None,
                 onPressed: Optional[Callable] = None,
                 onPressedName: Optional[str] = None,
                 style: Optional[ButtonStyle] = None,
                 tooltip: Optional[str] = None,
                 callbackArgs: Optional[List] = None):

        super().__init__(key=key, children=[child])
        self.child = child

        self.onPressed = onPressed
        self.onPressed_id = onPressedName if onPressedName else (onPressed.__name__ if onPressed else None)
        self.callbackArgs = callbackArgs
        self.tooltip = tooltip

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
            ElevatedButton.shared_styles[self.style_key] = self.css_class # type: ignore
            # Register callback - see note in TextButton about timing/location
            if self.onPressed and self.onPressed_id:
                Api().register_callback(self.onPressed_id, self.onPressed)
                # print(f"[ElevatedButton] Registered callback '{self.onPressed_id}' on style creation.")
        else:
            self.css_class = ElevatedButton.shared_styles[self.style_key] # type: ignore


    def render_props(self) -> Dict[str, Any]:
        """Return properties for diffing."""
        props = {
            # 'style_details': self.style.to_dict(), # Or specific props if needed
            'css_class': self.css_class,
            'tooltip': self.tooltip,
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
                (bgColor, fgColor, disBgColor, disFgColor, shadowColor, hoverColor, activeColor, elevation,
                 padding_tuple, margin_tuple, minSize_tuple, maxSize_tuple, side_tuple, shape_repr,
                 textStyle_tuple, alignment_tuple) = style_key
            except (ValueError, TypeError) as unpack_error:
                 # Handle cases where the key doesn't match the expected structure
                 print(f"Warning: Could not unpack style_key for ElevatedButton {css_class}. Using defaults. Key: {style_key}. Error: {unpack_error}")
                 # Set default values if unpacking fails
                 bgColor, fgColor, elevation = ('#6200ee', 'white', 2.0) # Basic defaults
                 padding_tuple, minSize_tuple, maxSize_tuple, side_tuple, shape_repr = (None,) * 5
                 textStyle_tuple, alignment_tuple, shadowColor, disBgColor, disFgColor = (None,) * 5

            # print("hoverColor: ", f"{'background-color: ' + str(hoverColor) + ';' if hoverColor else ''}" if hoverColor else None)

            # --- Base Button Styles ---
            base_styles_dict = {
                'display': 'inline-flex', # Use inline-flex to size with content but allow block behavior
                'align-items': 'center', # Vertically center icon/text
                'justify-content': 'center', # Horizontally center icon/text
                'padding': {EdgeInsets(*padding_tuple).to_css_value()} if padding_tuple else '8px 16px', # Default padding (M3 like)
                'margin': {EdgeInsets(*margin_tuple).to_css_value()} if margin_tuple else '4px', # Default margin # type: ignore
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

            if margin_tuple: # type: ignore
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
            hover_rule = f""".{css_class}:hover {{ 
                {hover_shadow_str} 
                {'background-color: ' + str(hoverColor) + ';' if hoverColor else ''}
                /* Add background overlay? */ 
                }}"""

            # Active state (M3: Lower/remove elevation)
            active_rule = f".{css_class}:active {{ box-shadow: none; background-color: {activeColor if activeColor else 'rgba(0, 0, 0, 0.12)'} }}"

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


# =============================================================================
# ICONBUTTON WIDGET - The "Icon-Only Button" for Compact Actions
# =============================================================================

class IconButton(Widget):
    """
    A compact button that shows only an icon - perfect for toolbars and space-saving interfaces!
    
    **What is IconButton?**
    Think of IconButton as the "compact action button" that shows only an icon instead of text.
    It's like having a "shortcut button" that uses universal symbols (icons) to communicate
    what action it performs, without taking up much space.
    
    **Real-world analogy:**
    IconButton is like the buttons on your TV remote or car dashboard:
    - Shows a simple, recognizable icon (play button, volume up, etc.)
    - Takes up minimal space
    - Instantly recognizable action
    - Usually has a subtle background or no background at all
    - Often includes a tooltip when you hover over it
    
    **When to use IconButton:**
    - Toolbars and app bars (save, edit, delete, share icons)
    - Navigation (back arrow, menu hamburger, search icon)
    - Secondary actions where space is limited
    - Actions that are universally understood through icons
    - Repeated actions in lists (favorite heart, more options)
    
    **When NOT to use IconButton:**
    - Primary actions (use ElevatedButton with text instead)
    - Actions that aren't clearly represented by an icon
    - When users might not understand the icon meaning
    - Complex actions that need explanation
    
    **Examples:**
    ```python
    # Simple icon button (like a "back" button)
    IconButton(
        icon=Icon("arrow_back"),
        onPressed=go_back
    )
    
    # Icon button with tooltip for clarity
    IconButton(
        icon=Icon("favorite", color="red"),
        onPressed=toggle_favorite,
        tooltip="Add to favorites"
    )
    
    # Custom styled icon button
    IconButton(
        icon=Icon("delete", color="white"),
        onPressed=delete_item,
        style=ButtonStyle(
            backgroundColor="red",
            padding=EdgeInsets.all(12)
        ),
        tooltip="Delete item"
    )
    
    # Icon button with custom size
    IconButton(
        icon=Icon("settings"),
        onPressed=open_settings,
        iconSize=32,  # Larger than default
        tooltip="Settings"
    )
    ```
    
    **Key parameters:**
    - **icon**: The Icon widget to display (required)
    - **onPressed**: Function to call when button is clicked
    - **iconSize**: Size of the icon in pixels (default: 24)
    - **tooltip**: Text that appears when user hovers (very important for accessibility!)
    - **style**: Visual customization (background color, padding, etc.)
    - **enabled**: Whether the button can be clicked (default: True)
    
    **Accessibility tip:**
    Always include a tooltip for IconButton to help users understand what it does!
    """
    # Class-level cache for mapping unique style definitions to a CSS class name.
    shared_styles: Dict[Tuple, str] = {}

    def __init__(self,
                 icon: Widget,  # The Icon widget is the required child
                 key: Optional[Key] = None,
                 onPressed: Optional[Callable] = None,
                 onPressedName: Optional[str] = None,
                 onPressedArgs: Optional[List] = [],
                 iconSize: Optional[int] = 24,  # Default M3 icon size
                 style: Optional[ButtonStyle] = None,
                 tooltip: Optional[str] = None,
                 enabled: bool = True,
                 cssClass: Optional[str] = ''):

        super().__init__(key=key, children=[icon])
        self.icon = icon

        self.onPressed = onPressed
        self.onPressed_id = onPressedName if onPressedName else (onPressed.__name__ if onPressed else None)
        self.onPressedArgs = onPressedArgs

        # Use a default ButtonStyle if none is provided. This ensures self.style is never None.
        self.style = style if isinstance(style, ButtonStyle) else ButtonStyle()
        self.iconSize = iconSize
        self.tooltip = tooltip
        self.enabled = enabled
        self.cssClass = cssClass

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
        disabled_class = 'disabled' if not self.enabled else ''
        self.current_css_class = f"{self.css_class} {self.cssClass} {disabled_class}".strip()

    def render_props(self) -> Dict[str, Any]:
        """Return properties for diffing by the Reconciler."""
        # The DOM element only needs its class, callback name, and tooltip.
        # All complex styling is handled by the generated CSS.
        props = {
            'css_class': self.current_css_class,
            'onPressedName': self.onPressed_id,
            'tooltip': self.tooltip,
            'enabled': self.enabled, # Pass enabled state for JS if needed
            'onPressedArgs': self.onPressedArgs,
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
            hv_color = getattr(style_obj, 'hoverColor', 'rgba(0, 0, 0, 0.08)')
            ac_color = getattr(style_obj, 'activeColor', 'rgba(0, 0, 0, 0.12)')
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
                # print("Shape obj value: ", BorderRadius(*shape_obj).to_css_value())
                if isinstance(shape_obj, BorderRadius):
                    # print("Shape obj value: ", shape_obj.to_css_value())
                    base_styles['border-radius'] = shape_obj.to_css_value()
                elif isinstance(shape_obj, (int, float)):
                    base_styles['border-radius'] = f"{max(0.0, shape_obj)}px"
                elif isinstance(shape_obj, tuple):
                    base_styles['border-radius'] = BorderRadius(*shape_obj).to_css_value()

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

            hover_rule = f".{css_class.rstrip()}:hover {{ background-color: {hv_color if hv_color else hover_bg_color}; }}"
            active_rule = f".{css_class.rstrip()}:active {{ background-color: {active_bg_color}; }}"
            active_rule_mod = f".{css_class.rstrip()}.active {{ background-color: {ac_color if ac_color else active_bg_color}; }}"

            # Disabled state (applied via .disabled class by reconciler)
            disabled_color = 'rgba(0, 0, 0, 0.38)' # M3 disabled content color .active {}
            disabled_rule = f".{css_class.rstrip()}.disabled {{ color: {disabled_color}; background-color: transparent; cursor: default; pointer-events: none; }}"

            return "\n".join([main_rule, icon_rule, hover_rule, active_rule, active_rule_mod, disabled_rule])

        except Exception as e:
            import traceback
            print(f"ERROR generating CSS for IconButton {css_class} with key {style_key}:")
            traceback.print_exc()
            return f"/* Error generating rule for .{css_class} */"

# =============================================================================
# FLOATING ACTION BUTTON - The "Quick Action" Button That Floats Above Everything
# =============================================================================

class FloatingActionButton(Widget):
    """
    The prominent "quick action" button that floats above your app's content - usually circular with an icon.
    
    **What is FloatingActionButton (FAB)?**
    Think of FAB as the "main action button" of your screen. It's a prominent, usually circular
    button that "floats" above other content and represents the primary action users can take.
    FABs are designed to catch attention and make the most important action easily accessible.
    
    **Real-world analogy:**
    Like the "emergency call" button in an elevator:
    - Prominently placed and easily visible
    - Clearly indicates the most important action
    - Always accessible regardless of what else is happening
    - Stands out from other controls
    
    **When to use FloatingActionButton:**
    - Primary action of a screen ("Add new item", "Compose message", "Create", "Call")
    - Actions users do frequently on that screen
    - When you want to make an action highly discoverable
    - Actions that create new content or initiate primary workflows
    
    **Common FAB examples by app type:**
    - Email app: "Compose new message" (pencil icon)
    - Notes app: "Create new note" (plus icon)
    - Shopping app: "Add to cart" (shopping cart icon)
    - Camera app: "Take photo" (camera icon)
    - Social media: "Create post" (plus or edit icon)
    
    **Material Design principles for FABs:**
    1. **One per screen**: Only use one FAB per screen for the primary action
    2. **Persistent**: Should be visible and accessible from the main content area
    3. **Prominent**: Uses contrasting colors to stand out from other content
    4. **Related to screen**: The action should be directly related to the current screen's content
    5. **Floating**: Positioned above other content with elevation/shadow
    
    **Examples:**
    ```python
    # Simple FAB with an icon
    FloatingActionButton(
        child=Icon("add"),  # Plus icon for "add new" action
        onPressed=create_new_item
    )
    
    # FAB with custom styling
    FloatingActionButton(
        child=Icon("edit"),
        onPressed=start_editing,
        style=ButtonStyle(
            backgroundColor=Colors.green,
            elevation=8,  # Higher shadow for more prominence
            shape=28  # Circular (radius = half of 56px default size)
        ),
        tooltip="Start editing"  # Helpful hint on hover
    )
    
    # FAB in a Scaffold (typical usage)
    Scaffold(
        appBar=AppBar(title=Text("My Notes")),
        body=NotesList(),
        floatingActionButton=FloatingActionButton(
            child=Icon("add"),
            onPressed=create_new_note
        )
    )
    ```
    
    **Key parameters:**
    - **child**: The content inside the button (usually an Icon)
    - **onPressed**: Function called when the button is tapped
    - **style**: ButtonStyle for customizing appearance (colors, size, shadows)
    - **tooltip**: Text shown when user hovers over the button (accessibility)
    - **key**: Optional unique identifier for this widget
    
    **Default styling:**
    - **Shape**: Circular (56px diameter by default)
    - **Elevation**: Floating above content with shadow
    - **Colors**: Uses theme's accent/primary colors
    - **Position**: Fixed in bottom-right corner (when used in Scaffold)
    - **Icon size**: 24px (standard Material Design icon size)
    
    **Accessibility notes:**
    1. Always include a tooltip for screen readers
    2. Use clear, recognizable icons
    3. Make sure the action is obvious from context
    4. Provide alternative ways to access the same function
    
    **Performance notes:**
    FABs are lightweight and efficient since they're typically just a button with an icon.
    The floating positioning and shadows are handled efficiently by CSS.
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
            FloatingActionButton.shared_styles[self.style_key] = self.css_class # type: ignore
            # Register callback (Move to Framework recommended)
            # if self.onPressed and self.onPressed_id:
            #     Api().register_callback(self.onPressed_id, self.onPressed)
        else:
            self.css_class = FloatingActionButton.shared_styles[self.style_key] # type: ignore

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
                (bgColor, fgColor, disBgColor, disFgColor, shadowColor, hoverColor, elevation,
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
                 if padding_tuple: # type: ignore
                     try: padding_obj = EdgeInsets(*padding_tuple); base_styles_dict['padding'] = padding_obj.to_css_value()
                     except: pass
                 # Override shape if provided in key
                 if shape_repr:
                     if isinstance(shape_repr, tuple) and len(shape_repr) == 4:
                          try: 
                            shape_obj = BorderRadius(*shape_repr) 
                            base_styles_dict['border-radius'] = shape_obj.to_css_value()
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
            ac_color = f"background-color: {hoverColor};" if hoverColor else ''
            active_rule = f".{css_class}:active {{ transform: scale(0.98); {ac_color}/* Example subtle press */ }}"

            # Disabled state (add .disabled class)
            disabled_bg = disBgColor or Colors.rgba(0,0,0,0.12) # type: ignore # M3 Disabled container approx
            disabled_fg = disFgColor or Colors.rgba(0,0,0,0.38) # type: ignore # M3 Disabled content approx
            disabled_rule = f".{css_class}.disabled {{ background-color: {disabled_bg}; color: {disabled_fg}; box-shadow: none; cursor: default; pointer-events: none; }}"


            return "\n".join([main_rule, icon_rule, hover_rule, active_rule, disabled_rule])

        except Exception as e:
            import traceback
            print(f"Error generating CSS for FloatingActionButton {css_class} with key {style_key}: {e}")
            traceback.print_exc()
            return f"/* Error generating rule for .{css_class} */"
    # Removed instance methods: to_html(), to_css(), to_js()



# =============================================================================
# SINGLECHILDSCROLLVIEW WIDGET - The "Scrollable Container" for Overflow Content
# =============================================================================

class SingleChildScrollView(Widget):
    """
    The "magical expanding container" that makes content scrollable when it's too big to fit!
    
    **What is SingleChildScrollView?**
    Think of SingleChildScrollView as a "smart window" that can show content larger than itself.
    When your content is too tall or too wide to fit in the available space, this widget
    adds scroll bars so users can scroll to see the rest.
    
    **Real-world analogy:**
    SingleChildScrollView is like a "scroll viewer" for ancient scrolls:
    - The scroll itself (child content) might be very long
    - The "viewing window" (container) shows only a portion at a time
    - You can scroll up/down (or left/right) to see different parts
    - The scroll bars appear when the content is larger than the window
    
    **When to use SingleChildScrollView:**
    - Long forms that might not fit on small screens
    - Text content that could be longer than the screen
    - Image galleries or content that might overflow
    - Any content where you're not sure if it will fit
    - When you have ONE child that might be too big (use ListView for multiple items)
    
    **When NOT to use SingleChildScrollView:**
    - For lists of many items (use ListView instead - it's much more efficient)
    - When content will definitely fit (adds unnecessary complexity)
    - For horizontal scrolling of many items (use horizontal ListView)
    
    **Examples:**
    ```python
    # Vertical scrolling for a long form
    SingleChildScrollView(
        child=Column(children=[
            TextField("Name"),
            TextField("Email"),
            TextField("Address"),
            # ... many more fields
            ElevatedButton(child=Text("Submit"), onPressed=submit)
        ])
    )
    
    # Horizontal scrolling for wide content
    SingleChildScrollView(
        scrollDirection=Axis.HORIZONTAL,
        child=Row(children=[
            Container(width=200, child=Text("Panel 1")),
            Container(width=200, child=Text("Panel 2")),
            Container(width=200, child=Text("Panel 3")),
            # ... more wide panels
        ])
    )
    
    # Scrollable content with padding
    SingleChildScrollView(
        padding=EdgeInsets.all(16),
        child=Text(
            "This is a very long text that will definitely not fit "
            "in a small container and will need to be scrollable..."
        )
    )
    ```
    
    **Key parameters:**
    - **child**: The content that might be too big to fit (required)
    - **scrollDirection**: Axis.VERTICAL (up/down) or Axis.HORIZONTAL (left/right)
    - **padding**: Space inside the scroll area around the content
    - **reverse**: If True, starts scrolled to the bottom/end instead of top/start
    - **physics**: Controls scroll behavior (bouncy, never scrollable, etc.)
    
    **Performance tip:**
    Only use this for single widgets! For lists of items, use ListView which is optimized
    to only render visible items and can handle thousands of items efficiently.
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


#=============================================================================
# GLOBAL SCROLLBAR STYLE - A "Set It and Forget It" Theme for Your App's Main Scrollbar
#=============================================================================

class GlobalScrollbarStyle(Widget):
    """
    A special, non-rendering widget that applies a custom scrollbar style
    to the entire application window (the `<body>` element's scrollbar).

    **What is GlobalScrollbarStyle?**
    This widget is a "theme setter" for the browser's default scrollbar. It doesn't draw anything
    on the screen itself, but instead injects a global CSS rule to make the main window scrollbar
    match your application's aesthetic. You place it once in your app, and it takes care of the rest.

    **Real-world analogy:**
    It's like choosing the frame style for all the windows in your house. You don't apply it to
    each pane of glass individually. Instead, you set a single rule ("all window frames will be
    brushed nickel"), and every window automatically follows that style, creating a consistent look.

    **When to use GlobalScrollbarStyle:**
    - When you want to customize the main browser scrollbar that appears when the whole page is longer than the screen.
    - To ensure a consistent visual theme across your entire application.
    - Place it **once** at the top level of your widget tree, often within your main `Scaffold` or root `Container`.

    **Examples:**
    ```python
    # Define a custom theme for the scrollbar
    my_scrollbar_theme = ScrollbarTheme(
        thumb_color=Colors.blue[300],
        track_color=Colors.grey[800],
        radius=4
    )
    
    # Place the GlobalScrollbarStyle widget at the top of your app
    Scaffold(
        appBar=AppBar(title=Text("My App")),
        body=Column(
            children=[
                GlobalScrollbarStyle(theme=my_scrollbar_theme),
                # ... rest of your app content
                LongContentThatCausesScrolling(),
            ]
        )
    )
    ```
    
    **Key parameters:**
    - **theme**: An optional `ScrollbarTheme` object to define the colors, size, and roundness of the scrollbar. If omitted, a default theme is used.
    - **key**: Optional unique identifier for this widget.
    
    **How it works:**
    Unlike other widgets, `GlobalScrollbarStyle` generates CSS that targets browser-specific pseudo-elements (`::-webkit-scrollbar` for Chrome/Safari, `scrollbar-color` for Firefox) instead of a specific CSS class. This allows it to style the browser's native UI component for scrolling.

    **Accessibility notes:**
    - Customizing scrollbars can improve visual consistency and readability, especially in dark themes.
    - Ensure that the contrast between the scrollbar thumb and track is sufficient for users with low vision.
    - This widget doesn't interfere with keyboard or screen reader scrolling functionality.

    **Performance notes:**
    - Extremely lightweight. It injects a single, small CSS rule once per theme.
    - Has zero impact on rendering performance as it is a non-visual widget.
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


# =============================================================================
# SCROLLBAR - A Highly-Customizable Scrollable Container
# =============================================================================

class Scrollbar(Widget):
    """
    A robust, customizable scrollbar widget that wraps its child, providing a
    consistent, themeable scrolling experience across all browsers using SimpleBar.js.

    **What is Scrollbar?**
    The `Scrollbar` widget is a container that makes its content scrollable if it overflows.
    It replaces the often inconsistent and operating-system-dependent native browser scrollbars
    with a sleek, modern, and fully themeable alternative that looks and feels the same everywhere.

    **Real-world analogy:**
    Think of it as a high-tech display case for a long, historical scroll. The case itself
    has a fixed size, but it includes a smooth, elegant track and handle that lets you
    effortlessly glide through the entire length of the scroll inside, no matter how long it is.

    **When to use Scrollbar:**
    - For scrollable lists, sidebars, or navigation menus.
    - In chat windows or logs where content grows over time.
    - Any container with dynamic content that might exceed its fixed dimensions.
    - When you need a high-performance scrollable area for thousands of items (using virtualization).

    **Examples:**
    ```python
    # 1. Simple scrollable column
    Scrollbar(
        height=300, # Fixed height
        child=Column(
            children=[Text(f"Item {i}") for i in range(100)]
        )
    )
    
    # 2. A scrollbar with a custom theme
    my_theme = ScrollbarTheme(
        thumb_color=Colors.amber,
        track_color="transparent",
        width=12
    )
    Scrollbar(
        height="100%", # Take full parent height
        theme=my_theme,
        child=MyLongContentWidget()
    )
    
    # 3. High-performance virtualized list (for thousands of items)
    Scrollbar(
        height=500,
        virtualization_options={
            'itemHeight': 30, # Height of each row
            'totalItems': 10000
        },
        child=MyItemRenderer() # Widget that renders a single row
    )
    ```

    **Key parameters:**
    - **child**: The single widget to be placed inside the scrollable container.
    - **theme**: An optional `ScrollbarTheme` to customize the scrollbar's appearance.
    - **width**: The width of the scrollable area (e.g., '100%', 300).
    - **height**: The height of the scrollable area (e.g., '100%', 500).
    - **autoHide**: (bool) If `True` (default), scrollbars fade out when not in use.
    - **virtualization_options**: A dictionary to enable high-performance virtual scrolling for very large lists. This drastically improves performance by only rendering visible items.

    **Default styling:**
    - Utilizes a subtle, modern default theme if no `ScrollbarTheme` is provided.
    - Scrollbars are overlaid on the content and only appear on hover or during scrolling.
    - Provides a consistent look and feel across Chrome, Firefox, Safari, and Edge.

    **Performance notes:**
    - Standard usage is very efficient, powered by the battle-tested SimpleBar.js library.
    - For lists with hundreds or thousands of items, **virtualization is essential**. By providing `virtualization_options`, you switch to a mode that only renders the DOM nodes currently in view, resulting in massive performance gains and instant scrolling, regardless of list size.
    """
    # A class-level cache to share CSS for identical themes.
    shared_styles: Dict[Tuple, str] = {}

    def __init__(self,
                 child: Widget,
                 key: Optional[Key] = None,
                 theme: Optional[ScrollbarTheme] = None,
                 width: Optional[Any] = '100%',
                 height: Optional[Any] = '100%',
                 autoHide: bool = True,
                 virtualization_options: Optional[Dict] = None 
                 ):
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
        self.virtualization_options = virtualization_options # <-- STORE IT

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
        props = {
            'css_class': self.css_class,
            'widget_instance': self,
        }
        
        # --- THIS IS THE CHANGE ---
        # Only initialize SimpleBar OR VirtualList, not both.
        # VirtualList will now handle the SimpleBar initialization internally.
        print("virtualization_options: ", self.virtualization_options)
        if self.virtualization_options:
            
            props['init_virtual_list'] = True
            props['virtual_list_options'] = self.virtualization_options
            # Pass simplebar options inside the vlist options
            props['virtual_list_options']['simplebarOptions'] = {'autoHide': self.autoHide}
        else:
            # For a non-virtualized scrollbar, do the normal initialization
            props['init_simplebar'] = True
            props['simplebar_options'] = {'autoHide': self.autoHide}
            props['attributes'] = {'data-simplebar': 'true'}
            
        return props
    
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


# =============================================================================
# COLUMN WIDGET - The "Vertical Stack" for Organizing Content Up-and-Down
# =============================================================================

class Column(Widget):
    """
    The "vertical stack organizer" - arranges multiple widgets in a top-to-bottom layout!
    
    **What is Column?**
    Think of Column as a "vertical filing cabinet" that stacks widgets on top of each other.
    It's one of the most fundamental layout widgets - you'll use it constantly to organize
    your app's content vertically (like a shopping list or form fields).
    
    **Real-world analogy:**
    Column is like stacking books on top of each other:
    - Each book (child widget) sits on top of the previous one
    - You can control how they align (all to the left, centered, etc.)
    - You can control spacing between them
    - The whole stack can be aligned within a larger bookshelf (container)
    
    **When to use Column:**
    - Organizing form fields vertically (Name, Email, Password fields)
    - Creating menus or lists of buttons
    - Stacking content like cards or tiles
    - Building the main layout structure of screens
    - Any time you need things arranged top-to-bottom
    
    **Key concepts:**
    - **Main Axis**: The vertical direction (top-to-bottom)
    - **Cross Axis**: The horizontal direction (left-to-right)
    - **Children**: The widgets you want to stack vertically
    
    **Examples:**
    ```python
    # Simple vertical list
    Column(children=[
        Text("Item 1"),
        Text("Item 2"),
        Text("Item 3")
    ])
    
    # Centered form layout
    Column(
        mainAxisAlignment=MainAxisAlignment.CENTER,  # Center vertically
        crossAxisAlignment=CrossAxisAlignment.CENTER,  # Center horizontally
        children=[
            Text("Welcome!", style=TextStyle(fontSize=24)),
            SizedBox(height=20),  # Spacing
            TextField("Username"),
            TextField("Password"),
            ElevatedButton(child=Text("Login"), onPressed=login)
        ]
    )
    
    # Spaced-out layout filling the screen
    Column(
        mainAxisAlignment=MainAxisAlignment.SPACE_BETWEEN,
        children=[
            Text("Header"),
            Text("Content in the middle"),
            Text("Footer")
        ]
    )
    ```
    
    **Key parameters:**
    - **children**: List of widgets to stack vertically (required)
    - **mainAxisAlignment**: How to arrange children along the main (vertical) axis:
      * START: Pack at the top
      * CENTER: Center in available space
      * END: Pack at the bottom
      * SPACE_BETWEEN: Spread out with equal space between
      * SPACE_AROUND: Spread out with space around each child
      * SPACE_EVENLY: Equal space between and around all children
    - **crossAxisAlignment**: How to align children along the cross (horizontal) axis:
      * START: Align to the left
      * CENTER: Center horizontally
      * END: Align to the right
      * STRETCH: Make each child fill the width
    - **mainAxisSize**: Whether to take up all available height (MAX) or just what's needed (MIN)
    
    **Layout tip:**
    Column is perfect for mobile-first design since phones are taller than they are wide!
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

# =============================================================================
# ROW WIDGET - The "Horizontal Stack" for Organizing Content Left-to-Right
# =============================================================================

class Row(Widget):
    """
    The "horizontal organizer" - arranges multiple widgets side-by-side in a left-to-right layout!
    
    **What is Row?**
    Think of Row as a "horizontal shelf" that places widgets next to each other from left to right.
    It's the horizontal companion to Column - while Column stacks things vertically,
    Row arranges them horizontally (like items on a bookshelf).
    
    **Real-world analogy:**
    Row is like arranging items on a shelf:
    - Each item (child widget) sits next to the previous one
    - You can control how they align vertically (top, center, bottom)
    - You can control spacing and distribution across the shelf
    - The whole arrangement fits within the shelf's width
    
    **When to use Row:**
    - Navigation bars with multiple buttons side-by-side
    - Tool bars with icons arranged horizontally  
    - Button groups (OK, Cancel, Apply)
    - Form fields that should be on the same line (First Name, Last Name)
    - Icon + text combinations
    - Any content that should be arranged left-to-right
    
    **Key concepts:**
    - **Main Axis**: The horizontal direction (left-to-right)
    - **Cross Axis**: The vertical direction (top-to-bottom)
    - **Children**: The widgets you want to arrange horizontally
    
    **Examples:**
    ```python
    # Simple horizontal layout
    Row(children=[
        Icon("home"),
        Text("Home"),
        Icon("settings")
    ])
    
    # Button group with spacing
    Row(
        mainAxisAlignment=MainAxisAlignment.SPACE_EVENLY,
        children=[
            TextButton(child=Text("Cancel"), onPressed=cancel),
            ElevatedButton(child=Text("Save"), onPressed=save),
            TextButton(child=Text("Help"), onPressed=show_help)
        ]
    )
    
    # Icon and text combination
    Row(
        crossAxisAlignment=CrossAxisAlignment.CENTER,  # Center vertically
        children=[
            Icon("person", size=24),
            SizedBox(width=8),  # Spacing
            Text("Profile")
        ]
    )
    
    # Form fields side-by-side
    Row(children=[
        Expanded(child=TextField("First Name")),
        SizedBox(width=16),
        Expanded(child=TextField("Last Name"))
    ])
    ```
    
    **Key parameters:**
    - **children**: List of widgets to arrange horizontally (required)
    - **mainAxisAlignment**: How to arrange children along the main (horizontal) axis:
      * START: Pack to the left
      * CENTER: Center in available space
      * END: Pack to the right
      * SPACE_BETWEEN: Spread out with equal space between
      * SPACE_AROUND: Spread out with space around each child
      * SPACE_EVENLY: Equal space between and around all children
    - **crossAxisAlignment**: How to align children along the cross (vertical) axis:
      * START: Align to the top
      * CENTER: Center vertically  
      * END: Align to the bottom
      * STRETCH: Make each child fill the height
      * BASELINE: Align text baselines (great for text + icon combinations)
    - **mainAxisSize**: Whether to take up all available width (MAX) or just what's needed (MIN)
    
    **Layout tip:**
    Use Expanded widget around Row children to control how they share the available width!
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

# =============================================================================
# IMAGE HELPER CLASSES - The "Image Source Managers" for Different Image Types
# =============================================================================

class AssetImage:
    """
    Points to an image file stored in your project's assets folder - like a "local photo reference"!
    
    **What is AssetImage?**
    Think of AssetImage as a "bookmark" that points to an image file stored locally in your
    project (like photos you've included with your app). It's like having a filing cabinet
    of images that ship with your application.
    
    **When to use AssetImage:**
    - App logos and branding images
    - Icons and graphics that are part of your app design
    - Default profile pictures or placeholder images
    - UI elements like backgrounds, patterns, decorations
    - Any image that doesn't change and ships with your app
    
    **Example usage:**
    ```python
    # Reference an image in your assets folder
    logo = AssetImage("logo.png")
    profile_pic = AssetImage("avatars/default-user.jpg")
    background = AssetImage("backgrounds/gradient-bg.png")
    ```
    """
    def __init__(self, file_name: str):
        # Basic check for leading slashes
        clean_file_name = file_name.lstrip('/')
        # TODO: Add more robust path joining and sanitization
        self.src = f'http://localhost:{port}/{clean_file_name}'
        # print("Asset image src: ", self.src)

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
    """
    Points to an image on the internet - like a "web link to a photo"!
    
    **What is NetworkImage?**
    Think of NetworkImage as a "web address" that tells your app where to find an image
    on the internet. It's like giving someone a URL to look at a photo online.
    
    **When to use NetworkImage:**
    - User profile pictures downloaded from social media or accounts
    - Product images from an online store or database
    - Photos from APIs or web services
    - Dynamic content that changes based on user data
    - Images stored on your server or cloud storage
    
    **Example usage:**
    ```python
    # Reference images from the web
    user_avatar = NetworkImage("https://api.example.com/users/123/avatar.jpg")
    product_photo = NetworkImage("https://store.example.com/products/456/image.png")
    weather_icon = NetworkImage(f"https://weather.com/icons/{weather_condition}.svg")
    ```
    
    **Important note:**
    NetworkImage requires an internet connection to load. Always have fallback
    AssetImage alternatives for offline scenarios!
    """
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

# =============================================================================
# IMAGE WIDGET - The "Picture Display" for Showing Photos and Graphics
# =============================================================================

class Image(Widget):
    """
    The "picture frame" of your app - displays images from files or the internet!
    
    **What is Image widget?**
    Think of Image as a "smart picture frame" that can display photos, logos, icons,
    or any visual content. It's like having a digital photo frame that can show
    images from your photo album (assets) or from the internet.
    
    **Real-world analogy:**
    Image widget is like a picture frame on your wall:
    - You can put different photos in it (change the image source)
    - You can resize the frame (width/height)
    - You can choose how the photo fits (crop, stretch, contain)
    - You can add rounded corners (borderRadius)
    - You can position the photo within the frame (alignment)
    
    **When to use Image:**
    - Displaying user profile pictures
    - Showing product photos in a store app
    - App logos and branding
    - Icons and decorative graphics
    - Backgrounds and visual elements
    - Photos from galleries or cameras
    
    **Examples:**
    ```python
    # Simple app logo
    Image(
        image=AssetImage("logo.png"),
        width=200,
        height=100
    )
    
    # User profile picture with rounded corners
    Image(
        image=NetworkImage(user.avatar_url),
        width=60,
        height=60,
        fit=ImageFit.COVER,  # Crop to fill the frame
        borderRadius=BorderRadius.circular(30)  # Perfect circle
    )
    
    # Product photo that scales nicely
    Image(
        image=NetworkImage(product.image_url),
        width="100%",  # Fill available width
        height=200,
        fit=ImageFit.CONTAIN,  # Show entire image without cropping
        alignment="center"
    )
    
    # Background image
    Image(
        image=AssetImage("backgrounds/gradient.jpg"),
        width="100%",
        height="100vh",  # Full screen height
        fit=ImageFit.COVER  # Fill entire area, crop if needed
    )
    ```
    
    **Key parameters:**
    - **image**: The image source (AssetImage for local files, NetworkImage for web images)
    - **width**: How wide the image should be (pixels or percentages like "100%")
    - **height**: How tall the image should be
    - **fit**: How the image should fit in the space:
      * CONTAIN: Show entire image, add letterboxes if needed
      * COVER: Fill entire space, crop if needed
      * FILL: Stretch image to fit exactly (may distort)
      * FIT_WIDTH: Scale to fit width, height adjusts
      * FIT_HEIGHT: Scale to fit height, width adjusts
    - **alignment**: Where to position the image ("center", "top", "bottom left", etc.)
    - **borderRadius**: Rounded corners for the image
    
    **Image fit guide:**
    - Use CONTAIN for logos (never crop, always show full image)
    - Use COVER for backgrounds and avatars (fill space, cropping is OK)
    - Use FILL only when aspect ratio doesn't matter
    
    **Performance tip:**
    Always specify width and height to prevent layout jumps while images load!
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




# =============================================================================
# ICON WIDGET - The "Symbol Display" for Showing Vector Icons
# =============================================================================

class Icon(Widget):
    """
    The "symbol display" that shows scalable vector icons - like digital hieroglyphics!
    
    **What is Icon widget?**
    Think of Icon as a "universal symbol display" that can show any icon from a huge
    library of symbols (like Material Icons). It's like having access to thousands
    of perfectly designed symbols that scale to any size without getting blurry.
    
    **Real-world analogy:**
    Icon widget is like the symbols on road signs or computer keyboards:
    - Universally recognizable symbols (home, search, settings, etc.)
    - Always crisp and clear at any size (vector-based, not pixels)
    - Convey meaning quickly without words
    - Consistent styling across your entire app
    - Take up minimal space but communicate effectively
    
    **When to use Icon:**
    - Navigation buttons (home, back, menu)
    - Action buttons (search, edit, delete, save)
    - Status indicators (favorite heart, notification bell)
    - User interface elements (close X, dropdown arrow)
    - Decorative elements that enhance usability
    
    **Examples:**
    ```python
    # Simple icon with default size
    Icon(Icons.home)
    
    # Colored icon with custom size
    Icon(
        Icons.favorite,
        color="red",
        size=32
    )
    
    # Icon with Material Design 3 variable font features
    Icon(
        Icons.settings,
        size=24,
        color=Colors.primary,
        fill=True,          # Filled version of the icon
        weight=500,         # Medium weight
        grade=0            # Standard grade
    )
    
    # Icon in a button context
    IconButton(
        icon=Icon(Icons.notification, color="blue"),
        onPressed=show_notifications
    )
    ```
    
    **Key parameters:**
    - **icon**: The icon to display (use Icons.name like Icons.home, Icons.search)
    - **size**: Size in pixels (default: 24)
    - **color**: Icon color (inherits from parent if not specified)
    
    **Advanced Material Design 3 parameters:**
    - **fill**: True for filled version, False for outlined (default: False)
    - **weight**: Font weight from 100-700 (default: 400)
    - **grade**: Visual emphasis from -50 to 200 (default: 0)
    - **optical_size**: Optimizes for different sizes (default: matches size)
    
    **Material Design 3 Icon Variants:**
    ```python
    # Outlined (default)
    Icon(Icons.favorite)  # ♡
    
    # Filled
    Icon(Icons.favorite, fill=True)  # ♥
    
    # Different weights
    Icon(Icons.home, weight=300)  # Lighter
    Icon(Icons.home, weight=700)  # Bolder
    ```
    
    **Icon library:**
    PyThra includes thousands of Material Design icons. Common ones:
    - Icons.home, Icons.search, Icons.menu
    - Icons.favorite, Icons.star, Icons.thumb_up  
    - Icons.edit, Icons.delete, Icons.add
    - Icons.arrow_back, Icons.arrow_forward
    - Icons.person, Icons.settings, Icons.help
    
    **Performance tip:**
    Icons are vector-based and super lightweight - use them liberally!
    They're much more efficient than image files for simple symbols.
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
                 optical_size: Optional[int] = 24,
                 cssClass: Optional[str] = '',
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
        self.cssClass = cssClass

        is_color_static = not bool(self.cssClass)

        # The style key now includes all font variation settings
        self.style_key = (
            self.icon.fontFamily,
            self.size,
            self.fill,
            self.weight,
            self.grade,
            self.optical_size,
            self.color if is_color_static else None, # Include color only if static
        )

        if self.style_key not in Icon.shared_styles:
            self.css_class = f"material-icon-{len(Icon.shared_styles)}"
            Icon.shared_styles[self.style_key] = self.css_class
        else:
            self.css_class = Icon.shared_styles[self.style_key]

        self.current_css_class = f"{self.css_class} {self.cssClass}".strip()        

    def render_props(self) -> Dict[str, Any]:
        """Return properties for diffing. The icon name is now the text content."""
        props = {
            'css_class': self.current_css_class,
            'data': self.icon.name, # The text content of the <span>
        }
        if self.cssClass:
            props['color'] = self.color
        return props

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
            (fontFamily, size, fill, weight, grade, optical_size, static_color) = style_key

            # This is the magic property for variable fonts
            font_variation_settings = f"'FILL' {1 if fill else 0}, 'wght' {weight}, 'GRAD' {grade}, 'opsz' {optical_size}"

            # --- THE FIX ---
            # Only include the color property in the CSS rule if it was passed in the key.
            color_rule = f"color: {static_color or 'inherit'};" if static_color is not None else ""


            return f"""
                .{css_class} {{
                    position: relative;
                    font-family: '{fontFamily}';
                    font-weight: normal;
                    font-style: normal;
                    font-size: {size}px;
                    {color_rule}
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
                    font-variation-settings: {font_variation_settings};
                }}
            """
        except Exception as e:
            # ... error handling ...
            return f"/* Error generating rule for Icon .{css_class} */"

# IMPORTANT: In your reconciler's _get_widget_render_tag method, make sure it
# knows that an Icon should be a <span>.
# A good way is to call the widget's own static method if it exists.


# =============================================================================
# VIRTUAL LIST VIEW STATE (Internal Class)
# =============================================================================
class _VirtualListViewState(State):
    """
    The internal state management and logic for the `VirtualListView` widget.

    **Role of this class:**
    This class is the "engine" behind `VirtualListView`. It is not used directly by developers
    building an application. Instead, it handles the complex stateful logic required for
    virtualization to work, including:
    
    1.  **Lifecycle Management**: Sets up necessary components when the list is created
        (`initState`) and cleans up when it's removed (`dispose`).
    2.  **JavaScript Interop**: Manages the bridge between the Python backend and the
        JavaScript virtualization library running in the browser.
    3.  **On-Demand Item Building**: Responds to requests from the JavaScript frontend to build
        the HTML and CSS for items as they are about to be scrolled into view.
    4.  **Controller Integration**: Connects to the `VirtualListController` so that external
        code can command the list to refresh.
    5.  **Widget Construction**: Builds the final `Scrollbar` widget that hosts the JavaScript
        virtualization component.
    
    **Key Methods and Logic Flow:**

    - **`initState()`**:
        - Runs once when the `VirtualListView` is first added to the widget tree.
        - **Registers a callback** (`build_item_for_js`) with the API. This gives the
          JavaScript frontend a named function it can call to request new list items.
        - **Pre-renders initial items**: To ensure the list appears instantly without a
          flicker, it builds the first screen's worth of items ahead of time.
        - **Prepares `_virtualization_options`**: Bundles all the necessary data
          (total item count, item size, builder name, initial items) into a dictionary
          that will be passed to the JavaScript component.

    - **`build_item_for_js(index)`**:
        - This is the core on-demand building function. It is **called from JavaScript**
          whenever the virtualizer needs the content for a specific `index`.
        - It takes the requested `index`, calls the developer's `itemBuilder` function to
          get the corresponding widget, and performs a partial reconciliation on it.
        - This reconciliation generates the `html`, `css`, and `callbacks` for that single
          item without affecting the main application state.
        - It returns this payload in a dictionary, which the JavaScript side then injects
          into the DOM.

    - **`refresh_js(indices)`**:
        - This method is the Python-to-JavaScript command channel.
        - It is called by the `VirtualListController` when a developer wants to update the list.
        - It constructs and executes a snippet of JavaScript that tells the frontend
          virtualization instance to either refresh all its items or just a specific set of
          items, triggering new calls to `build_item_for_js` as needed.

    - **`build()`**:
        - This standard state method is called during every rebuild.
        - Its only job is to construct the visible part of the widget tree: a `Scrollbar`
          widget configured with the `virtualization_options` that were prepared in `initState`.
          This effectively hands off the rendering of the list's content to the JavaScript
          virtualizer.
    
    - **`dispose()`**:
        - Runs when the `VirtualListView` is permanently removed.
        - It detaches from the `VirtualListController` to prevent memory leaks and dangling
          references.
    """
    def __init__(self):
        """
        The constructor should ONLY call its parent and declare variables.
        It should NOT access the widget.
        """
        super().__init__()
        self.item_builder_name = None
        self._virtualization_options = None

    def initState(self):
        """
        This method runs AFTER the state is linked to the widget.
        This is the correct place to access self.get_widget() and perform setup.
        """
        widget = self.get_widget()
        if not widget: return

        # Attach the state to the controller provided by the widget
        if widget.controller: # type: ignore
            widget.controller._attach(self) # type: ignore

        # --- MOVE ALL SETUP LOGIC HERE ---
        self.item_builder_name = f"vlist_item_builder_{widget.key.value}" # type: ignore
        Api().register_callback(self.item_builder_name, self.build_item_for_js)

        # Pre-render the initial items once during initialization.
        initial_items_html = {}
        initial_item_count = min(widget.initialItemCount, widget.itemCount) # type: ignore
        for i in range(initial_item_count):
            initial_items_html[i] = self.build_item_for_js(i)
        
        self._virtualization_options = {
            "itemCount": widget.itemCount, # type: ignore
            "itemExtent": widget.itemExtent, # type: ignore
            "itemBuilderName": self.item_builder_name,
            "initialItems": initial_items_html
        }

        # --- END OF MOVED LOGIC ---

    
    def dispose(self):
        # Clean up the controller link to prevent memory leaks
        widget = self.get_widget()
        if widget and widget.controller: # type: ignore
            widget.controller._detach() # type: ignore
        super().dispose()


    def refresh_js(self, indices: Optional[List[int]] = None):
        """
        Called by the controller to command the JS engine to refresh.
        Can do a full refresh (indices=None) or a targeted item refresh.
        """
        widget = self.get_widget()
        if not (self.framework and self.framework.window and widget):
            return

        instance_name = f"{widget.key.value}_vlist" # type: ignore
        
        if indices is None:
            print(f"Python: Commanding JS instance '{instance_name}' to perform a FULL refresh.")
            js_command = f"window._pythra_instances['{instance_name}']?.refreshAll();"
        else:
            print(f"Python: Commanding JS instance '{instance_name}' to refresh items at indices: {indices}")
            indices_json = json.dumps(indices)
            js_command = f"window._pythra_instances['{instance_name}']?.refreshItems({indices_json});"

        self.framework.window.evaluate_js(self.framework.id, js_command)


    def build_item_for_js(self, index: int) -> Dict[str, Any]:
        """
        This method is called by the API.
        """
        widget = self.get_widget()
        # The check for widget and framework is still good practice here.
        if not widget or not self.framework:
            return {"html": "<div>Error</div>", "css": "", "callbacks": {}}
            
        widget_to_build = widget.itemBuilder(index) # type: ignore
        built_tree = self.framework._build_widget_tree(widget_to_build)
        
        main_context_map = self.framework.reconciler.get_map_for_context("main")
        result = self.framework.reconciler.reconcile(
            previous_map=main_context_map,
            new_widget_root=built_tree,
            parent_html_id='__limbo__',
            is_partial_reconciliation=True
        )
        
        main_context_map.update(result.new_rendered_map)
        
        root_key = built_tree.get_unique_id() if built_tree else None
        html_string = self.framework._generate_html_from_map(root_key, result.new_rendered_map)
        css_string = self.framework._generate_css_from_details(result.active_css_details)
        callbacks = result.registered_callbacks
        
        for name, func in callbacks.items():
            self.framework.api.register_callback(name, func)

        return {
            "html": html_string,
            "css": css_string,
            "callback_names": list(callbacks.keys())
        }


    def build(self) -> Widget:
        """
        Builds the Scrollbar using the options generated during initState.
        """
        # print("virtualization_options: ", self._virtualization_options)
        widget = self.get_widget()
        if not widget:
            print('!!widget is not found!! vlist')
            # Return a placeholder if the widget is somehow gone
            return Container(width=0, height=0)


        # The options are now guaranteed to exist because initState ran first.
        return Scrollbar(
            key=widget.key, 
            width=widget.width, # type: ignore
            height=widget.height, # type: ignore
            theme=widget.theme, # type: ignore
            child=Container(key=Key(f"{widget.key.value}_content"), alignment=Alignment.center()), # type: ignore
            virtualization_options=self._virtualization_options
        )

# =============================================================================
# VIRTUAL LIST VIEW - The High-Performance List for "Infinite" Scrolling
# =============================================================================

class VirtualListView(StatefulWidget):
    """
    A highly-performant, scrollable list that only renders the items currently
    visible on screen. It is the essential choice for lists containing hundreds,
    thousands, or even millions of items.

    **What is VirtualListView?**
    VirtualListView is a "smart" list. Instead of creating all of its item widgets at once
    (which would crash the browser for large lists), it only builds and renders the handful
    of items that can fit in the visible area. As the user scrolls, it efficiently recycles
    the containers, swapping content in and out on the fly.

    **Real-world analogy:**
    Imagine a smart, infinitely long bookshelf viewer. Instead of trying to load every book
    in the library at once, the viewer only renders the books on the single shelf you are
    currently looking at. As you move the viewer up or down (scroll), it instantly loads
    the next shelf's books while unloading the ones that are no longer visible. This allows
    you to browse a massive library with instant performance.

    **When to use VirtualListView:**
    - **ALWAYS** for long lists (more than 50-100 items).
    - Displaying large datasets: social media feeds, contact lists, log files, financial data tables.
    - When a standard `ListView` becomes slow, janky, or consumes too much memory.
    - Any time you need a smooth "infinite scroll" experience.

    **Key Concepts:**
    1.  **Virtualization**: The core technique. Only visible items exist in the DOM, keeping the app fast and lightweight.
    2.  **`itemBuilder`**: A function you provide that acts as a factory. The list calls it on-demand with an `index` to get the widget for that specific item.
    3.  **`itemExtent`**: The fixed height (for vertical lists) of each item. This is **crucial** for the virtualization logic to calculate which items should be visible and where to position the scrollbar. All items *must* have the same size.
    4.  **`VirtualListController`**: An object you create to programmatically control the list, such as forcing it to refresh its data.

    **Examples:**
    ```python
    # Controller to manage the list
    list_controller = VirtualListController()

    # The builder function that creates a widget for a given index
    def user_card_builder(index: int):
        return ListTile(
            leading=Icon("person"),
            title=Text(f"User Number {index + 1}"),
            subtitle=Text("This is a virtualized list item.")
        )

    # The VirtualListView widget itself
    VirtualListView(
        key=Key("my-user-list"),
        controller=list_controller,
        itemCount=10000,          # Total number of items in our dataset
        itemBuilder=user_card_builder, # The function to build each item
        itemExtent=72             # The fixed height of each ListTile
    )

    # Later, to refresh the list after data changes:
    # list_controller.refresh()
    ```

    **Key parameters:**
    - **key**: A **required** unique `Key` to identify this stateful widget.
    - **controller**: A **required** `VirtualListController` instance to manage the list.
    - **itemCount**: The total number of items in the list.
    - **itemBuilder**: A function that takes an `int` (index) and returns a `Widget`.
    - **itemExtent**: The fixed size (usually height) in pixels of each item.
    - **theme**: An optional `ScrollbarTheme` for the scrollbar's appearance.
    - **width**, **height**: The dimensions of the scrollable container.

    **Performance notes:**
    This is the definitive solution for performance with large lists. Its memory and CPU usage
    remain flat and low, regardless of whether `itemCount` is 100 or 1,000,000, because it
    only ever renders a small, constant number of DOM elements.
    """
    def __init__(self,
                 key: Key,
                 controller: VirtualListController, # <-- Requires a controller
                 itemCount: int,
                 itemBuilder: Callable[[int], Widget],
                 itemExtent: float,
                 # --- REMOVE data_version ---
                 initialItemCount: int = 20,
                 theme: Optional[ScrollbarTheme] = None,
                 width: Optional[Any] = '100%',
                 height: Optional[Any] = '100%'):

        self.controller = controller
        self.itemCount = itemCount
        self.itemBuilder = itemBuilder
        self.itemExtent = itemExtent
        self.initialItemCount = initialItemCount
        self.theme = theme
        self.width = width
        self.height = height
        super().__init__(key=key)

    def createState(self) -> _VirtualListViewState:
        return _VirtualListViewState()


# =============================================================================
# LIST VIEW - The Simple, Standard Scrollable List
# =============================================================================
class ListView(Widget):
    """
    A standard scrollable list that arranges its children linearly and renders
    them all at once.

    **What is ListView?**
    ListView is the fundamental widget for displaying a scrollable collection of items.
    You provide it with a complete `List` of child widgets, and it lays them out in a
    column or row, adding a scrollbar if they overflow the container's bounds.
    It's simple and effective for a limited number of items.

    **Real-world analogy:**
    Think of a physical scroll of parchment. The entire text (all the child widgets) is
    written on the scroll from top to bottom. To see different parts, you simply roll it
    up or down. The whole content is always present, just not all visible at once.

    **When to use ListView:**
    - For lists with a **small, manageable number of items** (e.g., less than ~50).
    - Settings menus, navigation drawers, or short lists of options.
    - When items have variable heights, which is difficult for `VirtualListView`.
    - When the simplicity of passing a `children` list is preferred over an `itemBuilder`.

    **When NOT to use ListView:**
    - For long lists. It renders **all** children into the DOM immediately, which will
      cause severe performance degradation and high memory usage as the list grows.
      **Use `VirtualListView` for large datasets.**

    **Examples:**
    ```python
    # A simple vertical list of settings
    ListView(
        padding=EdgeInsets.symmetric(vertical=8),
        children=[
            ListTile(title=Text("Wi-Fi"), leading=Icon("wifi")),
            ListTile(title=Text("Bluetooth"), leading=Icon("bluetooth")),
            ListTile(title=Text("Display"), leading=Icon("desktop_windows")),
        ]
    )

    # A horizontal list of cards
    Container(
        height=150,
        child=ListView(
            scrollDirection=Axis.HORIZONTAL,
            children=[
                Card(child=Text("Item 1"), width=100),
                Card(child=Text("Item 2"), width=100),
                Card(child=Text("Item 3"), width=100),
            ]
        )
    )
    ```

    **Key parameters:**
    - **children**: A `List` of `Widget`s to display in the scrollable area.
    - **padding**: `EdgeInsets` to create space between the container's edge and the content.
    - **scrollDirection**: `Axis.VERTICAL` (default) or `Axis.HORIZONTAL`.
    - **reverse**: (bool) If `True`, scrolls from bottom-to-top or right-to-left.
    - **shrinkWrap**: (bool) If `True`, the list's size will be determined by its content. If `False` (default), it will expand to fill the available space provided by its parent.

    **Performance notes:**
    `ListView` is very efficient for small lists. However, its performance scales linearly
    with the number of children. For lists of more than a few dozen items, the cost of
    building, laying out, and painting every widget can lead to a slow UI.
    **Always profile and switch to `VirtualListView` if performance suffers.**
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


# =============================================================================
# GRID VIEW - The Scrollable Grid for Photo Galleries, Products, and More
# =============================================================================
class GridView(Widget):
    """"
    A scrollable, 2D array of widgets arranged in a grid layout. Ideal for
    presenting items of a similar type, like images or cards.

    **What is GridView?**
    `GridView` is a widget that arranges its children in a scrollable two-dimensional grid.
    You specify how many columns (or rows) you want, and it automatically handles the
    layout, spacing, and aspect ratio of the items to create a clean, organized grid.

    **Real-world analogy:**
    It's like a perfectly organized photo album or a collector's display case for trading cards.
    Each item has its own designated slot, arranged in neat rows and columns. If you have
    more items than can fit on one page, you can simply scroll to see the rest, but the
    organized structure remains consistent.

    **When to use GridView:**
    - Photo galleries or image pickers.
    - Product listings in an e-commerce app.
    - Dashboards with multiple stat cards.
    - App launchers or menu selections with icons.
    - Any time you need to display a collection of items in a uniform grid.

    **Examples:**
    ```python
    # 1. A simple 3-column photo gallery
    GridView(
        crossAxisCount=3,      # 3 columns
        mainAxisSpacing=8,     # 8px vertical space between items
        crossAxisSpacing=8,    # 8px horizontal space between items
        padding=EdgeInsets.all(8),
        children=[
            Image(src="photo1.jpg"),
            Image(src="photo2.jpg"),
            Image(src="photo3.jpg"),
            Image(src="photo4.jpg"),
            Image(src="photo5.jpg"),
            Image(src="photo6.jpg"),
        ]
    )

    # 2. A grid of square product cards with a 2-column layout
    GridView(
        crossAxisCount=2,
        mainAxisSpacing=16,
        crossAxisSpacing=16,
        childAspectRatio=1.0, # Ensures items are perfect squares
        children=[
            ProductCard(product=p) for p in my_products
        ]
    )
    ```

    **Key parameters:**
    - **children**: A `List` of `Widget`s to display in the grid.
    - **crossAxisCount**: The number of items in the cross-axis. For a vertical-scrolling grid, this is the number of columns. For a horizontal-scrolling grid, this is the number of rows.
    - **mainAxisSpacing**: The spacing between items along the direction of scrolling (e.g., vertical gap).
    - **crossAxisSpacing**: The spacing between items perpendicular to the direction of scrolling (e.g., horizontal gap).
    - **childAspectRatio**: The ratio of the cross-axis size to the main-axis size for each child. For example, `1.0` creates squares, `16/9` creates widescreen rectangles.
    - **padding**: `EdgeInsets` to create space around the entire grid.
    - **scrollDirection**: `Axis.VERTICAL` (default) or `Axis.HORIZONTAL`.

    **Performance notes:**
    Like `ListView`, the standard `GridView` renders all of its children at once. This is perfectly fine for dozens of items, but it can cause performance issues with hundreds or thousands of items. For very large grids, a virtualized version (`VirtualGridView`, if available) would be necessary to maintain a smooth user experience.
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

# =============================================================================
# STACK - The Widget for Layering and Positioning
# =============================================================================
class Stack(Widget):
    """
    A widget that layers its children on top of each other, allowing for
    complex layouts with overlapping elements. It creates a positioning context
    for its descendants.

    **What is Stack?**
    `Stack` allows you to place widgets on top of one another, like stacking papers on a desk.
    By default, they are all aligned to the top-left corner, but you can use the `Positioned`
    widget on any child to precisely place it relative to the Stack's edges (top, right,
    bottom, left).

    **Real-world analogy:**
    It's like a bulletin board or a collage. You start with the board (the `Stack`). Then you
    can pin a large background image that fills the whole board. On top of that, you can pin a
    note in the top-right corner, a photo in the center, and a title at the bottom. Each item
    is placed independently on the z-axis (depth).

    **When to use Stack:**
    - Placing a text label or badge over an icon (e.g., a notification count).
    - Displaying text or buttons over a background image.
    - Creating custom UI elements that involve overlapping shapes or controls.
    - Building complex layouts where elements need to be anchored to different corners of a container.

    **Examples:**
    ```python
    # 1. A simple badge on an icon
    Stack(
        children=[
            Icon("mail", size=32),
            Positioned(
                top=0,
                right=0,
                child=Container(
                    padding=EdgeInsets.all(2),
                    decoration=BoxDecoration(color=Colors.red, shape=BoxShape.CIRCLE),
                    child=Text("3", style=TextStyle(color=Colors.white, fontSize=10))
                )
            )
        ]
    )

    # 2. Text centered over a background image
    Stack(
        fit=StackFit.expand, # Makes Stack fill its parent
        children=[
            Image(src="background.jpg", fit=BoxFit.COVER),
            Center(
                child=Text("Welcome!", style=TextStyle(fontSize=48, color=Colors.white))
            )
        ]
    )
    ```

    **Key parameters:**
    - **children**: A `List` of `Widget`s to layer. The last widget in the list is the topmost one.
    - **alignment**: How to align children that are *not* wrapped in a `Positioned` widget. Defaults to top-left.
    - **fit**: How the `Stack` should size itself. `StackFit.loose` (default) makes it size to its non-positioned children. `StackFit.expand` makes it expand to fill its parent.
    - **clipBehavior**: Determines if children that extend beyond the `Stack`'s bounds are clipped (hidden) or visible. `HARD_EDGE` (default) will clip them.

    **Using with `Positioned`:**
    The true power of `Stack` is unlocked with the `Positioned` widget. Wrap any child of a `Stack` in `Positioned` and provide properties like `top`, `bottom`, `left`, or `right` to anchor it to the stack's edges.
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


# =============================================================================
# POSITIONED - The Widget That Pins a Child Within a Stack
# =============================================================================
class Positioned(Widget):
    """
    Controls the position of a child widget within a `Stack`. It only works
    when it is a direct descendant of a `Stack`.

    **What is Positioned?**
    `Positioned` is a special wrapper widget that doesn't draw anything itself. Instead,
    it tells its parent `Stack` exactly where to place its single child. You can "pin" the
    child to any combination of the `Stack`'s edges (top, right, bottom, left) or give it a
    specific width and height.

    **Real-world analogy:**
    Think of the `Stack` as a bulletin board. The `Positioned` widget is the thumbtack.
    You use the thumbtack (`Positioned`) to pin your item (`child`) to a specific spot on the
    board, for example, "0 inches from the top and 0 inches from the right" to place it
    in the top-right corner. Without a `Positioned` wrapper, children are just piled up at
    the `Stack`'s default alignment point (usually the top-left).

    **When to use Positioned:**
    - **Exclusively** as a direct child of a `Stack` widget.
    - To precisely anchor a widget to the corners or edges of a container.
    - To stretch a widget to fill the `Stack` by setting opposing anchors (e.g., `left=0`, `right=0`).
    - To create overlapping UI elements like badges, floating buttons, or labels on top of images.

    **Examples:**
    ```python
    Stack(
        children=[
            # A background container
            Container(color=Colors.blue_grey, width=200, height=200),

            # Pinned to the top-left corner
            Positioned(
                top=10,
                left=10,
                child=Text("Top Left")
            ),

            # Pinned to the bottom-right corner
            Positioned(
                bottom=10,
                right=10,
                child=Text("Bottom Right")
            ),
            
            # Stretched horizontally, centered vertically
            Positioned(
                left=20,
                right=20,
                top=90, # (200 / 2) - (20 / 2) -> center of stack - half of height
                height=20,
                child=Container(color=Colors.amber, child=Center(child=Text("Stretched")))
            )
        ]
    )
    ```

    **Key parameters:**
    - **child**: The single `Widget` to be positioned. This is required.
    - **top**: The distance in pixels from the top edge of the `Stack`.
    - **right**: The distance in pixels from the right edge of the `Stack`.
    - **bottom**: The distance in pixels from the bottom edge of the `Stack`.
    - **left**: The distance in pixels from the left edge of the `Stack`.
    - **width**: The explicit width of the child widget.
    - **height**: The explicit height of the child widget.

    **Layout behavior:**
    - You can combine anchors. For instance, setting `left`, `top`, and `right` will determine the widget's position and its width implicitly.
    - If you provide opposing anchors (e.g., `top` and `bottom`) along with a `height`, the `height` takes precedence.
    - If you provide opposing anchors without a size (e.g., `left=10`, `right=10`), the child will stretch to fill the space between those anchors.
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
        self.top = top or 0
        self.right = right or 0
        self.bottom = bottom or 0
        self.left = left or 0
        self.width = width or 0
        self.height = height or 0

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
# In pythra/widgets.py

# =============================================================================
# EXPANDED WIDGET - The "Space Filler" for Flexible Layout Children
# =============================================================================

class Expanded(Widget):
    """
    The "greedy space grabber" that makes its child take up all available space in a Row or Column!
    
    **What is Expanded?**
    Think of Expanded as a "space-hungry wrapper" that tells its child widget:
    "take up as much space as you can get!" It's like having a balloon that inflates
    to fill all available space in a container.
    
    **Real-world analogy:**
    Expanded is like the adjustable shelves in a bookcase:
    - You have a fixed bookcase (Row or Column)
    - Some shelves are fixed size (regular widgets)
    - Some shelves expand to use leftover space (Expanded widgets)
    - If you have multiple expanding shelves, they share the space fairly
    
    **When to use Expanded:**
    - Making one widget take up remaining space in a Row/Column
    - Creating responsive layouts that adapt to screen size
    - Distributing space proportionally between multiple widgets
    - Making text or content areas flexible
    
    **Common use cases:**
    - Search bar that takes up remaining width in a header
    - Content area that fills space between header and footer
    - Flexible columns in a data table
    - Responsive button groups
    
    **Examples:**
    ```python
    # Make middle widget take up remaining space
    Row(children=[
        Icon(Icons.menu),           # Fixed size
        Expanded(                   # Takes remaining space
            child=TextField("Search...")
        ),
        Icon(Icons.search)          # Fixed size
    ])
    
    # Distribute space proportionally between multiple widgets
    Row(children=[
        Expanded(                   # Gets 1/3 of available space
            flex=1,
            child=Container(color="red", child=Text("1"))
        ),
        Expanded(                   # Gets 2/3 of available space
            flex=2, 
            child=Container(color="blue", child=Text("2"))
        )
    ])
    
    # Content that fills vertical space
    Column(children=[
        Text("Header"),             # Fixed height
        Expanded(                   # Fills remaining height
            child=SingleChildScrollView(
                child=Text("Long content...")
            )
        ),
        Text("Footer")              # Fixed height
    ])
    
    # Responsive form layout
    Row(children=[
        Expanded(child=TextField("First Name")),
        SizedBox(width=16),  # Fixed spacing
        Expanded(child=TextField("Last Name"))
    ])
    ```
    
    **Key parameters:**
    - **child**: The widget that will be expanded (required)
    - **flex**: How much space to take relative to other Expanded widgets (default: 1)
    
    **Flex explained:**
    - flex=1: Takes 1 "unit" of available space
    - flex=2: Takes 2 "units" of available space
    - If you have two Expanded widgets with flex=1 each, they split space 50/50
    - If you have flex=1 and flex=2, they split space 33/67
    
    **Important notes:**
    1. **Only works inside Row/Column**: Expanded must be a direct child of Row or Column
    2. **Flexible vs Fixed**: Mix Expanded with fixed-size widgets for responsive designs
    3. **Overflow prevention**: Expanded prevents overflow by making content fit available space
    4. **Nesting**: You can put Row/Column inside Expanded for complex layouts
    
    **Layout tip:**
    Use Expanded to create layouts that look good on both phones and tablets!
    """
    def __init__(self,
                 child: Widget,
                 key: Optional[Key] = None,
                 flex: int = 1):

        if not child:
             raise ValueError("Expanded widget requires a child.")
        super().__init__(key=key, children=[child])
        
        self.flex = max(0, flex)

    def render_props(self) -> Dict[str, Any]:
        """
        Passes flex properties to the reconciler. These will be applied
        as inline styles to the wrapper div around the child.
        """
        # We will apply these styles to the direct child's container.
        # This requires the reconciler to be aware of this special case.
        # A cleaner way is to let the parent (Column/Row) handle it.
        # Let's try a different approach. The widget that is returned
        # should have these props.
        
        # The Expanded widget itself will become the flex item.
        # Its child will be a regular child.
        return {
            'style': {
                'flexGrow': self.flex,
                'flexShrink': 1, # Allow shrinking by default
                'flexBasis': '0%', # Start from a basis of 0 to allow full growth
                # The following are crucial for flex children to have a "world" to expand into
                'minWidth': '100%',
                'minHeight': 0,
                # Ensure the expanded container can itself be a flex container for its child
                'display': 'flex',
                'flexDirection': 'column' # Assume child should stack vertically
            }
        }

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
# =============================================================================
# SIZEDBOX WIDGET - The "Invisible Spacer" for Precise Layout Control
# =============================================================================

class SizedBox(Widget):
    """
    The "invisible spacer" that creates precise gaps and spacing in your layouts!
    
    **What is SizedBox?**
    Think of SizedBox as an "invisible box" that takes up exact space without showing anything.
    It's like using an empty picture frame as a spacer - it reserves space but doesn't
    display any content. Perfect for creating precise gaps between widgets.
    
    **Real-world analogy:**
    SizedBox is like the spacers used in printing or carpentry:
    - Invisible to the end user but crucial for proper spacing
    - Has exact measurements (width and height)
    - Creates consistent gaps between elements
    - Helps align things properly
    
    **When to use SizedBox:**
    - Creating fixed spacing between widgets
    - Adding padding-like space without using Container
    - Making widgets take up exact dimensions
    - Creating breathing room in dense layouts
    - Separating groups of related content
    
    **Common use cases:**
    - Space between buttons in a Row
    - Vertical spacing between sections in a Column
    - Fixed-size placeholders
    - Consistent margins and gaps
    
    **Examples:**
    ```python
    # Horizontal spacing between buttons
    Row(children=[
        ElevatedButton(child=Text("Save"), onPressed=save),
        SizedBox(width=16),  # 16 pixels of horizontal space
        TextButton(child=Text("Cancel"), onPressed=cancel)
    ])
    
    # Vertical spacing between form sections
    Column(children=[
        Text("Personal Information"),
        TextField("Name"),
        TextField("Email"),
        SizedBox(height=32),  # 32 pixels of vertical space
        Text("Address"),
        TextField("Street"),
        TextField("City")
    ])
    
    # Fixed size placeholder or spacer
    SizedBox(
        width=200,
        height=100  # Empty 200x100 pixel rectangle
    )
    
    # Just width (height adjusts to content)
    SizedBox(width=300, child=Text("This text is in a 300px wide box"))
    
    # Just height (width adjusts to content)
    SizedBox(height=50, child=Icon(Icons.star))
    ```
    
    **Key parameters:**
    - **width**: Fixed width in pixels (or CSS units like "100%")
    - **height**: Fixed height in pixels (or CSS units)
    - **child**: Optional widget to put inside the sized box
    
    **Spacing patterns:**
    ```python
    # Common spacing values (following 8px grid system)
    SizedBox(width=8)    # Tiny gap
    SizedBox(width=16)   # Small gap
    SizedBox(width=24)   # Medium gap
    SizedBox(width=32)   # Large gap
    SizedBox(width=48)   # Extra large gap
    ```
    
    **SizedBox vs Container vs Padding:**
    - **SizedBox**: Just creates space, no styling
    - **Container**: Can create space AND style (background, borders, etc.)
    - **Padding**: Adds space around a widget's content
    
    **When to use each:**
    - Use SizedBox for simple spacing between widgets
    - Use Container when you need background color or borders
    - Use Padding when you want space around a widget's content
    
    **Performance tip:**
    SizedBox is very lightweight - use it liberally for spacing!
    It's more efficient than Container for simple spacing needs.
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

# =============================================================================
# APPBAR WIDGET - The "top navigation bar" for Precise Layout Control
# =============================================================================

class AppBar(Widget):
    """
    The "top navigation bar" of your app — a horizontal bar at the top that
    typically contains a leading icon (like a back button or menu), a title,
    and optional action buttons (such as search, share, settings). It can also
    host an additional bottom section (like a TabBar).

    What is AppBar?
    Think of AppBar as the app's header. It anchors navigation, branding (title),
    and common actions in a predictable place at the top of the screen.

    Real-world analogy:
    - Like the title bar of a desktop application window that shows the app name,
      a back button, and a few quick actions on the right.

    When to use AppBar:
    - On most app screens to show context (page title) and quick actions
    - As a place to include a navigation (menu) button or back button
    - To host a TabBar or other content in the "bottom" area

    Typical layout structure:
    [ leading ]  [            title            ]  [ actions ... ]
    [                    bottom (optional)                     ]

    Key parameters:
    - leading: Optional widget placed at the far left (e.g., IconButton for menu/back)
    - title: The central label or any widget representing the page title
    - actions: List of widgets aligned to the right (e.g., IconButtons)
    - bottom: Optional widget displayed below the toolbar row (e.g., TabBar)
    - backgroundColor: AppBar background color (theme surface/primary is common)
    - foregroundColor: Default text/icon color used inside the AppBar
    - elevation: Adds shadow for depth; higher values appear more elevated
    - shadowColor: Color of the elevation shadow
    - centerTitle: If True, centers the title; otherwise it aligns left by default
    - titleSpacing: Horizontal padding surrounding the title
    - toolbarHeight: Height of the main toolbar row (commonly around 56px)
    - leadingWidth: Custom width to reserve for the leading area
    - pinned: If True, uses sticky positioning so it remains visible while scrolling

    Examples:
    Basic app bar with a title
    ```python
    AppBar(
        title=Text("Home"),
    )
    ```

    App bar with a menu button, centered title, and actions
    ```python
    AppBar(
        leading=IconButton(icon=Icon("menu"), onPressed=open_drawer),
        title=Text("Dashboard"),
        centerTitle=True,
        actions=[
            IconButton(icon=Icon("search"), onPressed=do_search),
            IconButton(icon=Icon("more_vert"), onPressed=open_menu),
        ],
    )
    ```

    App bar with a bottom TabBar
    ```python
    AppBar(
        title=Text("Library"),
        bottom=TabBar(tabs=[Text("Books"), Text("Authors"), Text("Genres")])
    )
    ```

    Notes and tips:
    1) Keep titles short to avoid truncation; AppBar automatically ellipsizes long text
    2) Use pinned=True for layouts with long, scrollable bodies so the AppBar stays in view
    3) Prefer consistent leading actions (e.g., back vs menu) for better UX
    4) The Reconciler adds internal wrapper elements like .appbar-toolbar-row and
       slot wrappers like .appbar-leading, .appbar-title, .appbar-actions, .appbar-bottom
       which are styled by the generated CSS for predictable layout.
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

# =============================================================================
# BOTTOM NAVIGATION BAR ITEM - A Single "Tab" in the Bottom Navigation Bar
# =============================================================================
class BottomNavigationBarItem(Widget):
    """
    Represents the configuration for a single item (an icon and a label) within a
    `BottomNavigationBar`. This widget is not meant to be used on its own.

    **What is BottomNavigationBarItem?**
    Think of this widget not as a visual component you place anywhere, but as a "blueprint"
    or a data object. You create a list of these blueprints to tell a `BottomNavigationBar`
    what its tabs should look like and what they should contain. The parent `BottomNavigationBar`
    is responsible for actually building the visual item and managing its state (e.g., whether it's selected).

    **Real-world analogy:**
    It's like a tab on a manila file folder. The tab itself just holds a label ("Invoices", "Clients").
    It only becomes a functional, clickable navigation element when it's attached to the folder and
    placed inside the file cabinet (the `BottomNavigationBar`). You define the tab's content, but
    the cabinet handles its position and appearance.

    **When to use BottomNavigationBarItem:**
    - **Exclusively** inside the `items` list when creating a `BottomNavigationBar`.
    - To define the icon and label for each top-level destination in your app.

    **Examples:**
    ```python
    # Note: This is how you define an item.
    # You would then place this object inside the `items` list of a BottomNavigationBar.

    # An item for a "Home" screen
    BottomNavigationBarItem(
        icon=Icon("home"),
        label=Text("Home")
    )

    # An item for a "Profile" screen
    BottomNavigationBarItem(
        icon=Icon("person"),
        label=Text("Profile")
    )
    ```

    **Key parameters (What you should provide):**
    - **icon**: The `Icon` widget to display. This is required.
    - **label**: The `Text` widget to display below the icon.
    - **key**: An optional `Key` for reconciliation if the items might be reordered.

    **Important Note on Styling and State:**
    You do **not** manually set properties like `selected`, `selectedColor`, or `unselectedColor`.
    The parent `BottomNavigationBar` widget automatically controls these properties based on its
    own `currentIndex` and styling parameters. It injects the correct state and styles into
    each item during the build process, ensuring a consistent and centrally managed look and feel.
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
        selected_class = 'selected' if self.selected else ''
        self.css_class = f"{self.base_css_class} {selected_class}".strip()

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


# =============================================================================
# BOTTOM NAVIGATION BAR - The Main Navigation Hub at the Bottom of the Screen
# =============================================================================
class BottomNavigationBar(Widget):
    """
    A material design navigation bar that is displayed at the bottom of an app,
    providing navigation between top-level views.

    **What is BottomNavigationBar?**
    This is the persistent bar at the bottom of the screen that allows users to
    switch between a small number of primary destinations in an app (typically 3-5).
    It is stateful; it needs to know which item is currently selected (`currentIndex`)
    and needs a way to report back when a new item is tapped (`onTap`).

    **Real-world analogy:**
    It's like the main dashboard controls or gear shift in a car (Park, Drive, Neutral, Reverse).
    It's always visible, easily accessible, and lets you switch between the fundamental
    operating modes of the vehicle. You can only be in one gear at a time, and selecting
    a new one changes the entire state of the car.

    **When to use BottomNavigationBar:**
    - For top-level navigation between the main sections of your application.
    - When you have between three and five primary destinations.
    - To provide persistent, ergonomic navigation on mobile devices.

    **State Management Pattern:**
    The `BottomNavigationBar` is a "controlled component." Its parent `StatefulWidget` must:
    1.  Hold the current index in its own state (e.g., `self.current_index = 0`).
    2.  Pass this index to the `BottomNavigationBar(currentIndex=self.current_index)`.
    3.  Provide an `onTap` callback function that updates the state (e.g., `self.setState({"current_index": new_index})`).

    **Examples:**
    ```python
    # This would typically be inside the build method of a StatefulWidget
    class MyMainScreen(StatefulWidget):
        def createState(self):
            return _MyMainScreenState()

    class _MyMainScreenState(State):
        def __init__(self):
            super().__init__()
            self.current_index = 0 # 1. Hold state

        def on_item_tapped(self, index):
            self.setState({"current_index": index}) # 3. Update state

        def build(self):
            return Scaffold(
                # ... body changes based on self.current_index
                bottomNavigationBar=BottomNavigationBar(
                    currentIndex=self.current_index, # 2. Pass state
                    onTap=self.on_item_tapped,
                    items=[
                        BottomNavigationBarItem(icon=Icon("home"), label=Text("Home")),
                        BottomNavigationBarItem(icon=Icon("search"), label=Text("Search")),
                        BottomNavigationBarItem(icon=Icon("person"), label=Text("Profile")),
                    ]
                )
            )
    ```

    **Key parameters:**
    - **items**: A `List` of `BottomNavigationBarItem` objects that define the content of each tab.
    - **currentIndex**: The index of the item that is currently selected.
    - **onTap**: A callback function that is invoked with the index of the tapped item.
    - **backgroundColor**: The background color of the navigation bar.
    - **selectedItemColor**: The color of the icon and label of the selected item.
    - **unselectedItemColor**: The color of the icon and label of the unselected items.
    - **elevation**: The z-axis elevation of the bar, which controls its shadow.
    - **height**: The height of the navigation bar container.
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
            item_rules = BottomNavigationBarItem.generate_css_rule(None, "bnb-item") # type: ignore # Use base class name

            return f"{container_rule}\n{item_rules}" # Combine container and item rules

        except Exception as e:
            print(f"Error generating CSS for BottomNavigationBar {css_class} with key {style_key}: {e}")
            return f"/* Error generating rule for .{css_class} */"

    # Removed instance methods: to_html(), to_css()


# =============================================================================
# SCAFFOLD WIDGET - The "page layout frame" for Precise Layout Control
# =============================================================================

class Scaffold(Widget):
    """
    The "page layout frame" for your screen. Scaffold organizes the major
    structural regions of a Material-style app page and makes them work
    together: AppBar at the top, a scrollable Body in the middle, an optional
    BottomNavigationBar at the bottom, and overlay elements like Drawers,
    FloatingActionButtons (FAB), SnackBars, and BottomSheets.

    What is Scaffold?
    Think of Scaffold as the building's framework: it defines where the
    roof (AppBar), main room (Body), and floor (BottomNavigationBar) go, and
    provides hooks for doors (Drawers) and quick actions (FAB).

    Real-world analogy:
    - A house layout: a fixed roof (AppBar), a main living area (Body),
      a hallway at the bottom (BottomNavigationBar), and sliding doors (Drawers)
      that can overlay the space when opened.

    Key content slots (all optional unless noted):
    - appBar: Top bar for navigation, title, and actions (use AppBar)
    - body: The primary content area (scrollable by default)
    - floatingActionButton: Prominent action button overlayed on the body
    - bottomNavigationBar: Bottom navigation or persistent control bar
    - drawer / endDrawer: Left/right slide-in panels for navigation or utilities
    - bottomSheet: Persistent or modal panel anchored to the bottom
    - persistentFooterButtons: Buttons that remain visible near the bottom
    - snackBar: Temporary message overlay typically used for feedback

    Styling and behavior:
    - backgroundColor: Base background (Material3 Surface role by default)
    - extendBody: If True, the body can extend behind the bottom navigation
    - extendBodyBehindAppBar: If True, the body can extend behind the app bar
    - drawerScrimColor: The translucent overlay color shown behind an open drawer

    Typical usage:
    ```python
    Scaffold(
        appBar=AppBar(title=Text("Home"), pinned=True),
        body=SingleChildScrollView(
            child=Column(children=[
                Text("Welcome!"),
                SizedBox(height=16),
                Text("Here is your dashboard."),
            ])
        ),
        floatingActionButton=IconButton(icon=Icon("add"), onPressed=create_item),
        bottomNavigationBar=BottomNavigationBar(items=[
            BottomNavigationBarItem(icon=Icon("home"), label=Text("Home")),
            BottomNavigationBarItem(icon=Icon("search"), label=Text("Search")),
            BottomNavigationBarItem(icon=Icon("person"), label=Text("Profile")),
        ]),
        drawer=Drawer(children=[Text("Item 1"), Text("Item 2")])
    )
    ```

    Notes and tips:
    1) The body area scrolls internally; Scaffold itself uses a CSS grid to
       maintain a stable header/body/footer layout.
    2) extendBody and extendBodyBehindAppBar control whether content appears
       behind the bottom nav or app bar; remember to add padding in your body
       content or rely on the Scaffold’s automatic padding when not extended.
    3) Drawers are positioned with smooth transitions and a scrim layer; the
       scrim color can be tuned with drawerScrimColor.
    4) The Reconciler creates wrapper elements like .scaffold-appbar,
       .scaffold-body, .scaffold-bottomnav, .scaffold-drawer-left/right, and
       .scaffold-scrim which are styled by generated CSS to ensure correct
       placement and interaction.
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




# =============================================================================
# TEXTFIELD WIDGET - The "Text Input Box" for User Data Entry
# =============================================================================

class TextField(Widget):
    """
    The "text input box" where users can type and edit text - like a digital notepad field!
    
    **What is TextField?**
    Think of TextField as a "smart text box" that users can click on and type into.
    It's like having a form field on a website, but with beautiful Material Design
    styling and advanced features like floating labels and error messages.
    
    **Real-world analogy:**
    TextField is like a form you fill out at a doctor's office:
    - Has a label telling you what to write ("Name:", "Email:", etc.)
    - Has a box where you write your answer
    - Shows helpful hints (placeholder text)
    - Can show error messages if you make a mistake ("Email format invalid")
    - Can be disabled when you're not allowed to edit
    - Remembers what you typed even if the page refreshes
    
    **When to use TextField:**
    - User registration forms (name, email, password)
    - Search boxes and input fields
    - Settings that users can customize
    - Comments, messages, and text content
    - Any place where users need to enter text
    
    **Examples:**
    ```python
    # Basic text input
    name_controller = TextEditingController()
    TextField(
        key=Key("name_field"),
        controller=name_controller,
        decoration=InputDecoration(
            label="Full Name",
            hintText="Enter your full name"
        )
    )
    
    # Email field with validation
    email_controller = TextEditingController()
    TextField(
        key=Key("email_field"),
        controller=email_controller,
        decoration=InputDecoration(
            label="Email Address",
            hintText="you@example.com",
            errorText="Please enter a valid email" if not valid_email else None
        )
    )
    
    # Password field (hidden text)
    password_controller = TextEditingController()
    TextField(
        key=Key("password_field"),
        controller=password_controller,
        obscureText=True,  # Hides the text with dots
        decoration=InputDecoration(
            label="Password",
            hintText="At least 8 characters"
        )
    )
    
    # Disabled field (read-only)
    TextField(
        key=Key("readonly_field"),
        controller=readonly_controller,
        enabled=False,  # User can't edit
        decoration=InputDecoration(
            label="User ID",
            hintText="Auto-generated"
        )
    )
    ```
    
    **Key parameters:**
    - **key**: REQUIRED! Unique identifier to maintain focus during UI updates
    - **controller**: TextEditingController that manages the text content and changes
    - **decoration**: InputDecoration that controls appearance (label, hints, colors, borders)
    - **obscureText**: True to hide text (for passwords)
    - **enabled**: False to make it read-only
    
    **Controller pattern:**
    TextField uses a "controller" to manage its content:
    ```python
    # Create a controller
    controller = TextEditingController()
    
    # Use it in TextField
    TextField(key=Key("my_field"), controller=controller, ...)
    
    # Read the value
    user_input = controller.text
    
    # Set the value programmatically
    controller.text = "New value"
    ```
    
    **Input decoration:**
    Customize appearance with InputDecoration:
    - **label**: The floating label text
    - **hintText**: Placeholder text when empty
    - **errorText**: Error message (makes field red)
    - **fillColor**: Background color
    - **border**: Custom border styling
    
    **Important notes:**
    1. **Always use a Key!** This prevents focus loss during UI rebuilds
    2. **Use controllers** to manage text content and get notified of changes
    3. **Validate input** and show errors using decoration.errorText
    4. **Consider accessibility** with proper labels and hints
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
            TextField.shared_styles[self.style_key] = self.css_class # type: ignore
        else:
            self.css_class = TextField.shared_styles[self.style_key] # type: ignore

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
                    {('disabled' if not props.get('enabled', True) else '').strip()}
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
