# framework/widgets.py
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
    def generate_css_rule(style_key: Tuple, css_class: str) -> str:
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


class TextButton(Widget):
    shared_styles = {}  # Stores unique style definitions for shared CSS

    def __init__(self, child, onPressed=None, style=None):
        super().__init__(widget_id=None)
        self.child = child
        self.onPressed = onPressed
        self.style = style or ButtonStyle()

        # Generate a unique style key for deduplication
        self.style_key = (
            self.style,
        )

        # Assign a shared class based on the style key
        if self.style_key not in TextButton.shared_styles:
            self.css_class = f"shared-textbutton-{len(TextButton.shared_styles)}"
            TextButton.shared_styles[self.style_key] = self.css_class
        else:
            self.css_class = TextButton.shared_styles[self.style_key]

        # Register the child widget with the framework
        self.add_child(self.child) if self.child else None

    def to_css(self):
        """Generate the shared CSS rules for text button styles."""
        css_rules = ""
        for style_key, css_class in TextButton.shared_styles.items():
            style, = style_key
            style_str = style.to_css() if style else ""

            css_rules += f"""
            .{css_class} {{
                {style_str}
            }}
            """

        return css_rules

    def to_html(self):
        self.to_js()
        """Generate the HTML for the text button."""
        button_id = self.widget_id()
        on_click_attr = f'onclick="handleClick(\'{self.onPressed.__name__}\')"' if self.onPressed else ''
        child_html = self.child.to_html() if self.child else ''
        return f"""
        <button id="{button_id}" class="{self.css_class}" {on_click_attr}>
            {child_html}
        </button>
        """

    def to_js(self):
        """Generate JavaScript for the button."""
        if self.onPressed:
            # Register the callback in the framework's API
            Api().register_callback(self.onPressed.__name__, self.onPressed)
        return ""


class ElevatedButton(Widget):
    shared_styles = {}  # Shared CSS for buttons

    def __init__(self, child, onPressed=None, style=None):
        super().__init__(widget_id=None)
        self.child = child
        self.onPressed = onPressed
        self.style = style or ButtonStyle()

        # Generate a unique style key for deduplication
        self.style_key = (
            self.style.backgroundColor,
            self.style.foregroundColor,
            self.style.overlayColor,
            self.style.shadowColor,
            self.style.elevation,
            self.style.padding,
            self.style.minimumSize,
            self.style.side,
            self.style.shape,
            self.style.textStyle,
            self.style.alignment,
            self.style.icon,
        )

        # Assign a shared CSS class based on the style key
        if self.style_key not in ElevatedButton.shared_styles:
            self.css_class = f"shared-elevatedbutton-{len(ElevatedButton.shared_styles)}"
            ElevatedButton.shared_styles[self.style_key] = self.css_class
        else:
            self.css_class = ElevatedButton.shared_styles[self.style_key]

        # Register the child widget
        self.add_child(self.child) if self.child else None

    def to_css(self):
        """Generate the shared CSS rules for ElevatedButton styles."""
        css_rules = ""
        for style_key, css_class in ElevatedButton.shared_styles.items():
            style = ButtonStyle(*style_key)  # Recreate ButtonStyle from the style key
            style_str = style.to_css() if style else ""

            css_rules += f"""
            .{css_class} {{
                {style_str}
            }}
            """
        return css_rules

    def to_html(self):
        self.to_js()
        """Generate the HTML for the ElevatedButton."""
        button_id = self.widget_id()
        on_click_attr = f'onclick="handleClick(\'{self.onPressed.__name__}\')"' if self.onPressed else ''
        child_html = self.child.to_html() if self.child else ''
        return f"""
        <button id="{button_id}" class="{self.css_class}" {on_click_attr}>
            {child_html}
        </button>
        """

    def to_js(self):
        """Generate JavaScript for the button."""
        if self.onPressed:
            Api().register_callback(self.onPressed.__name__, self.onPressed)
        return ""


class IconButton(Widget):
    shared_styles = {}  # Shared CSS for IconButton styles

    def __init__(self, icon, onPressed=None, iconSize=None, style=None):
        super().__init__(widget_id=None)
        self.child = icon
        self.onPressed = onPressed
        self.iconSize = iconSize or 16
        self.style = style or ButtonStyle()

        # Generate a unique style key for deduplication
        self.style_key = (
            self.style.backgroundColor,
            self.style.foregroundColor,
            self.style.overlayColor,
            self.style.shadowColor,
            self.style.elevation,
            self.style.padding,
            self.style.minimumSize,
            self.style.side,
            self.style.shape,
            self.style.textStyle,
            self.style.alignment,
            self.style.icon,
        )

        # Assign a shared CSS class based on the style key
        if self.style_key not in IconButton.shared_styles:
            self.css_class = f"shared-iconbutton-{len(IconButton.shared_styles)}"
            IconButton.shared_styles[self.style_key] = self.css_class
        else:
            self.css_class = IconButton.shared_styles[self.style_key]

        # Register the child widget
        self.add_child(self.child) if self.child else None

    def to_css(self):
        
        """Generate the shared CSS rules for IconButton styles."""
        css_rules = ""
        for style_key, css_class in IconButton.shared_styles.items():
            style = ButtonStyle(*style_key)  # Recreate ButtonStyle from the style key
            style_str = style.to_css() if style else ""

            css_rules += f"""
            .{css_class} {{
                {style_str}
                background-color: transparent; 
            }}
            """
        return css_rules

    def to_html(self):
        self.to_js()
        self.child.size = self.iconSize if self.iconSize and isinstance(self.child, Widget) else 16

        """Generate the HTML for the IconButton."""
        button_id = self.widget_id()
        on_click_attr = f'onclick="handleClick(\'{self.onPressed.__name__}\')"' if self.onPressed else ''
        child_html = self.child.to_html() if isinstance(self.child, Widget) else self.child

        return f"""
        <button id="{button_id}" class="{self.css_class}" {on_click_attr}>
            {child_html}
        </button>
        """

    def to_js(self):
        """Generate JavaScript for the button."""
        if self.onPressed:
            Api().register_callback(self.onPressed.__name__, self.onPressed)
        return ""


class FloatingActionButton(Widget):
    shared_styles = {}  # Shared CSS for FloatingActionButton styles

    def __init__(self, child=None, onPressed=None, key=None, style=None):
        super().__init__(widget_id=None)
        self.child = child
        self.onPressed = onPressed
        self.key = key
        self.style = style or ButtonStyle()

        # Generate a unique style key for deduplication
        self.style_key = (
            self.style.backgroundColor,
            self.style.foregroundColor,
            self.style.shadowColor,
            self.style.elevation,
            self.style.padding,
            self.style.shape,
        )

        # Assign a shared CSS class based on the style key
        if self.style_key not in FloatingActionButton.shared_styles:
            self.css_class = f"shared-fab-{len(FloatingActionButton.shared_styles)}"
            FloatingActionButton.shared_styles[self.style_key] = self.css_class
        else:
            self.css_class = FloatingActionButton.shared_styles[self.style_key]

        # Register the child widget
        self.add_child(self.child) if self.child else None

    def to_css(self):
        """Generate the shared CSS rules for FloatingActionButton styles."""
        css_rules = ""
        for style_key, css_class in FloatingActionButton.shared_styles.items():
            style = ButtonStyle(*style_key)  # Recreate ButtonStyle from the style key
            style_str = style.to_css() if style else ""

            css_rules += f"""
            .{css_class} {{
                {style_str}
                position: fixed;
                bottom: 16px;
                right: 16px;
                border-radius: 50%;
                width: 56px;
                height: 56px;
                display: flex;
                justify-content: center;
                align-items: center;
                box-shadow: 0 2px 10px rgba(0,0,0,0.2);
            }}
            """
        return css_rules

    def to_html(self):
        self.to_js()
        """Generate the HTML for the FloatingActionButton."""
        button_id = self.widget_id()
        on_click_attr = f'onclick="handleClick(\'{self.onPressed.__name__}\')"' if self.onPressed else ''
        child_html = self.child.to_html() if isinstance(self.child, Widget) else self.child or ""

        return f"""
        <button id="{button_id}" class="{self.css_class}" {on_click_attr}>
            {child_html}
        </button>
        """

    def to_js(self):
        """Generate JavaScript for the button."""
        if self.onPressed:
            Api().register_callback(self.onPressed.__name__, self.onPressed)
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
    shared_styles = {}  # Shared CSS for Row styles

    def __init__(self, children=None, key=None, mainAxisAlignment=MainAxisAlignment.START, mainAxisSize=MainAxisSize.MAX, crossAxisAlignment=CrossAxisAlignment.CENTER, textDirection=TextDirection.LTR, verticalDirection=VerticalDirection.DOWN, textBaseline=TextBaseline.alphabetic):
        super().__init__(widget_id=None)
        self.children = children or []
        self.key = key
        self.mainAxisAlignment = mainAxisAlignment
        self.mainAxisSize = mainAxisSize
        self.crossAxisAlignment = crossAxisAlignment
        self.textDirection = textDirection
        self.verticalDirection = verticalDirection
        self.textBaseline = textBaseline

        # Generate a unique style key for deduplication
        self.style_key = (
            self.mainAxisAlignment,
            self.mainAxisSize,
            self.crossAxisAlignment,
            self.textDirection,
            self.verticalDirection,
            self.textBaseline,
        )

        # Assign a shared CSS class based on the style key
        if self.style_key not in Row.shared_styles:
            self.css_class = f"shared-row-{len(Row.shared_styles)}"
            Row.shared_styles[self.style_key] = self.css_class
        else:
            self.css_class = Row.shared_styles[self.style_key]

        # Add children widgets
        for child in self.children:
            self.add_child(child) if child else None  # Register each child widget

    def to_css(self):
        """Generate the shared CSS rules for Row styles."""
        css_rules = ""
        for style_key, css_class in Row.shared_styles.items():
            (
                mainAxisAlignment,
                mainAxisSize,
                crossAxisAlignment,
                textDirection,
                verticalDirection,
                textBaseline,
            ) = style_key

            # Build CSS for the specific style key
            styles = (
                f"display: flex; "
                f"flex-direction: row; "
                f"justify-content: {mainAxisAlignment}; "
                f"align-items: {crossAxisAlignment}; "
                f"direction: {textDirection}; "
                f"vertical-align: {textBaseline};"
            )
            if mainAxisSize == 'min':
                styles += "width: auto;"
            elif mainAxisSize == 'max':
                styles += "width: 100%;"

            css_rules += f"""
            .{css_class} {{
                {styles}
            }}
            """
        return css_rules

    def to_html(self):
        """Generate HTML for the Row widget."""
        children_html = ''.join([child.to_html() for child in self.children])

        return f"<div id='{self.widget_id()}' class='{self.css_class}'>{children_html}</div>"
    

class Image(Widget):
    shared_styles = {}  # Shared CSS for Image styles

    def __init__(self, image, width=None, height=None, fit=ImageFit.CONTAIN, alignment='center'):
        super().__init__(widget_id=None)
        self.image = image
        self.width = width
        self.height = height
        self.fit = fit
        self.alignment = alignment

        # Generate a unique style key for deduplication
        self.style_key = (self.fit, self.width, self.height, self.alignment)

        # Assign a shared CSS class based on the style key
        if self.style_key not in Image.shared_styles:
            self.css_class = f"shared-image-{len(Image.shared_styles)}"
            Image.shared_styles[self.style_key] = self.css_class
        else:
            self.css_class = Image.shared_styles[self.style_key]

        # Register the image as a child widget
        self.add_child(self.image) if self.image else None

    def to_css(self):
        """Generate the shared CSS rules for Image styles."""
        css_rules = ""
        for style_key, css_class in Image.shared_styles.items():
            fit, width, height, alignment = style_key

            # Build CSS for the specific style key
            styles = (
                f"object-fit: {fit}; "
                f"width: {width}px; " if width else "" +
                f"height: {height}px; " if height else "" +
                f"display: flex; "
                f"justify-content: center; "
                f"align-items: {alignment};"
            )

            css_rules += f"""
            .{css_class} {{
                {styles}
            }}
            """
        return css_rules

    def to_html(self):
        """Generate HTML for the Image widget."""
        src = self.image.get_source()
        return f"<img id='{self.widget_id()}' src='{src}' class='{self.css_class}' />"

class AssetImage:
    
    def __init__(self, file_name):
        # Use the local server to serve assets
        self.src = f'http://localhost:{port}/{assets_dir}/{file_name}'

    def get_source(self):
        return self.src

class NetworkImage:
    def __init__(self, url):
        self.src = url

    def get_source(self):
        return self.src


class Icon(Widget):
    shared_styles = {}  # Shared CSS for Icon styles

    def __init__(self, icon_name=None, custom_icon=None, size=16, color=None):
        super().__init__(widget_id=None)
        self.icon_name = icon_name
        self.custom_icon = custom_icon
        self.size = size
        self.color = color

        # Generate a unique style key for deduplication
        self.style_key = (
                    self.size, 
                    self.color
            )

        # Assign a shared CSS class based on the style key
        if self.style_key not in Icon.shared_styles:
            # Assign a new shared class name for unique styles
            self.css_class = f"shared-icon-{len(Icon.shared_styles)}"
            Icon.shared_styles[self.style_key] = self.css_class
        else:
            # Reuse the existing class for identical styles
            self.css_class = Icon.shared_styles[self.style_key]

    def get_children(self):
        """Icon doesn't have children, so return an empty list."""
        return []

    def remove_all_children(self):
        """Icon has no children, so this is a no-op."""
        pass

    def to_css(self):
        """Generate the shared CSS rules for Icon styles."""
        css_rules = ""
        
        for style_key, css_class in Icon.shared_styles.items():
            size, color = style_key

            # Build CSS for the specific style key
            styles = (
                f"font-size: {size}px; "
                f"width: {self.size}px;"
                f"height: {self.size}px;"
                f"{f'color: {color};' if color else ''}"
            )

            css_rules += f"""
            .{self.css_class} {{
                {styles}
            }}
            """
        return css_rules

    def to_html(self):
        """Generate HTML for the Icon widget."""
        if self.custom_icon:
            # Handle custom icons as image sources
            src = AssetImage(self.custom_icon).get_source()
            return f"<img id='{self.widget_id()}' src='{src}' class='{self.css_class}' />"
        else:
            # Use a CDN for predefined icons, e.g., FontAwesome
            return f"<i id='{self.widget_id()}' class='fa fa-{self.icon_name} {self.css_class}'></i>"




class ListView(Widget):
    shared_styles = {}  # Shared CSS for ListView configurations

    def __init__(self, children, padding=None, scrollDirection=Axis.VERTICAL, reverse=False, primary=True, physics=ScrollPhysics.ALWAYS_SCROLLABLE, shrinkWrap=False, itemExtent=None, cacheExtent=None, semanticChildCount=None):
        super().__init__(widget_id=None)
        self.children = children
        self.padding = padding or EdgeInsets.all(0)
        self.scrollDirection = scrollDirection
        self.reverse = reverse
        self.primary = primary
        self.physics = physics
        self.shrinkWrap = shrinkWrap
        self.itemExtent = itemExtent
        self.cacheExtent = cacheExtent
        self.semanticChildCount = semanticChildCount

        # Add children widgets to the tree
        for child in self.children:
            self.add_child(child) if child else None

        # Generate a unique style key
        self.style_key = (
            self.padding.to_css(),
            self.scrollDirection,
            self.reverse,
            self.primary,
            self.physics,
            self.itemExtent,
            self.cacheExtent,
        )

        # Assign a shared CSS class based on the style key
        if self.style_key not in ListView.shared_styles:
            self.css_class = f"shared-listview-{len(ListView.shared_styles)}"
            ListView.shared_styles[self.style_key] = self.css_class
        else:
            self.css_class = ListView.shared_styles[self.style_key]

    def to_css(self):
        """Generate shared CSS rules for ListView."""
        css_rules = ""
        for style_key, css_class in ListView.shared_styles.items():
            (padding, scrollDirection, reverse, primary, physics, itemExtent, cacheExtent) = style_key

            # Convert style attributes to CSS
            scroll_direction_style = "flex-direction: column;" if scrollDirection == Axis.VERTICAL else "flex-direction: row;"
            reverse_style = "flex-direction: column-reverse;" if reverse else ""
            primary_style = (
                "overflow-y: auto;" if scrollDirection == Axis.VERTICAL and primary
                else "overflow-x: auto;" if scrollDirection == Axis.HORIZONTAL and primary
                else ""
            )
            padding_style = f"padding: {padding};"
            physics_style = ""
            if physics == ScrollPhysics.BOUNCING:
                physics_style = "overflow: scroll; -webkit-overflow-scrolling: touch;"
            elif physics == ScrollPhysics.CLAMPING:
                physics_style = "overflow: hidden;"
            item_extent_style = f"flex-basis: {itemExtent}px;" if itemExtent else ""
            cache_extent_style = f"scroll-margin-top: {cacheExtent}px;" if cacheExtent else ""

            # Build the full CSS rule
            css_rules += f"""
            .{css_class} {{
                display: flex;
                {scroll_direction_style}
                {reverse_style}
                {primary_style}
                {padding_style}
                {physics_style}
                {cache_extent_style}
                height: 100%;
                width: 100%;
            }}
            """
        return css_rules

    def to_html(self):
        """Generate HTML for ListView."""
        children_html = ''.join(
            [f"<div style='flex: none; {f'flex-basis: {self.itemExtent}px;' if self.itemExtent else ''}'>{child.to_html()}</div>" for child in self.children]
        )
        semantic_child_count_attr = f"aria-setsize='{self.semanticChildCount}'" if self.semanticChildCount else ""

        return f"""
        <div id="{self.widget_id()}" class="{self.css_class}" {semantic_child_count_attr}>
            {children_html}
        </div>
        """


class GridView(Widget):
    shared_styles = {}  # Shared CSS for GridView configurations

    def __init__(self, children, padding=None, scrollDirection=Axis.VERTICAL, reverse=False, primary=True, physics=ScrollPhysics.ALWAYS_SCROLLABLE, shrinkWrap=False, crossAxisCount=2, mainAxisSpacing=0, crossAxisSpacing=0, childAspectRatio=1.0):
        super().__init__(widget_id=None)
        self.children = children
        self.padding = padding or EdgeInsets.all(0)
        self.scrollDirection = scrollDirection
        self.reverse = reverse
        self.primary = primary
        self.physics = physics
        self.shrinkWrap = shrinkWrap
        self.crossAxisCount = crossAxisCount
        self.mainAxisSpacing = mainAxisSpacing
        self.crossAxisSpacing = crossAxisSpacing
        self.childAspectRatio = childAspectRatio

        # Add children to the widget tree
        for child in self.children:
            self.add_child(child) if child else None

        # Generate unique style key for shared CSS
        self.style_key = (
            self.padding.to_css(),
            self.scrollDirection,
            self.reverse,
            self.primary,
            self.physics,
            self.crossAxisCount,
            self.mainAxisSpacing,
            self.crossAxisSpacing,
            self.childAspectRatio,
        )

        # Assign shared CSS class
        if self.style_key not in GridView.shared_styles:
            self.css_class = f"shared-gridview-{len(GridView.shared_styles)}"
            GridView.shared_styles[self.style_key] = self.css_class
        else:
            self.css_class = GridView.shared_styles[self.style_key]

    def to_css(self):
        """Generate shared CSS rules for GridView."""
        css_rules = ""
        for style_key, css_class in GridView.shared_styles.items():
            (
                padding, scrollDirection, reverse, primary, physics,
                crossAxisCount, mainAxisSpacing, crossAxisSpacing, childAspectRatio
            ) = style_key

            # Convert attributes to CSS
            scroll_direction_style = "flex-direction: column;" if scrollDirection == Axis.VERTICAL else "flex-direction: row;"
            reverse_style = "flex-direction: column-reverse;" if reverse else ""
            primary_style = (
                "overflow-y: auto;" if scrollDirection == Axis.VERTICAL and primary
                else "overflow-x: auto;" if scrollDirection == Axis.HORIZONTAL and primary
                else ""
            )
            padding_style = f"padding: {padding};"
            physics_style = ""
            if physics == ScrollPhysics.BOUNCING:
                physics_style = "overflow: scroll; -webkit-overflow-scrolling: touch;"
            elif physics == ScrollPhysics.CLAMPING:
                physics_style = "overflow: hidden;"
            grid_template_columns = f"repeat({crossAxisCount}, 1fr);"
            grid_gap = f"{mainAxisSpacing}px {crossAxisSpacing}px;"

            css_rules += f"""
            .{css_class} {{
                display: flex;
                {scroll_direction_style}
                {reverse_style}
                {primary_style}
                {padding_style}
                {physics_style}
                height: 100%;
                width: 100%;
            }}
            .{css_class} .grid-container {{
                display: grid;
                grid-template-columns: {grid_template_columns}
                gap: {grid_gap};
                width: 100%;
            }}
            .{css_class} .grid-item {{
                flex: 1;
                aspect-ratio: {childAspectRatio};
            }}
            """
        return css_rules

    def to_html(self):
        """Generate HTML for GridView."""
        children_html = ''.join(
            [f"<div class='grid-item'>{child.to_html()}</div>" for child in self.children]
        )
        return f"""
        <div id="{self.widget_id()}" class="{self.css_class}" role="grid">
            <div class="grid-container">
                {children_html}
            </div>
        </div>
        """

          
class Stack(Widget):
    def __init__(self, children, alignment=Alignment.top_left(), textDirection=TextDirection.LTR, fit=StackFit.loose, clipBehavior=ClipBehavior.NONE, overflow=Overflow.VISIBLE, key=None):
        super().__init__(widget_id=None)
        self.children = children
        self.alignment = alignment
        self.textDirection = textDirection
        self.fit = fit
        self.clipBehavior = clipBehavior
        self.overflow = overflow
        self.key = key

        # Loop over self.children and add them to the widget tree
        for child in self.children:
            self.add_child(child)  if child else None # Use the add_child method to manage parent-child relationships


    def to_html(self):
        alignment_style = self.alignment.to_css()
        text_direction_style = f"direction: {self.textDirection};"
        fit_style = "width: 100%; height: 100%;" if self.fit == StackFit.expand else ""
        clip_style = ""
        if self.clipBehavior == ClipBehavior.HARD_EDGE:
            clip_style = "overflow: hidden;"
        elif self.clipBehavior == ClipBehavior.ANTI_ALIAS or self.clipBehavior == ClipBehavior.ANTI_ALIAS_WITH_SAVE_LAYER:
            clip_style = "overflow: hidden; clip-path: inset(0% round 0.5%);"

        overflow_style = f"overflow: {self.overflow.value};"

        children_html = ''.join([child.to_html() for child in self.children])

        return f"""
        <div id="{self.widget_id()}" style="position: relative; {alignment_style} {text_direction_style} {fit_style} {clip_style} {overflow_style}">
            {children_html}
        </div>
        """
        
class Positioned(Widget):
    def __init__(self, child, top=None, right=None, bottom=None, left=None):
        super().__init__(widget_id=None)
        self.child = child
        self.top = top
        self.right = right
        self.bottom = bottom
        self.left = left


        self.add_child(self.child) if self.child else None # Use the add_child method to manage parent-child relationships

    


    def to_html(self):
        top_style = f"top: {self.top}px;" if self.top is not None else ""
        right_style = f"right: {self.right}px;" if self.right is not None else ""
        bottom_style = f"bottom: {self.bottom}px;" if self.bottom is not None else ""
        left_style = f"left: {self.left}px;" if self.left is not None else ""

        return f"""
        <div id='{self.widget_id()}' style="position: absolute; {top_style} {right_style} {bottom_style} {left_style}">
            {self.child.to_html()}
        </div>
        """
        

class Expanded(Widget):
    def __init__(self, child, flex=1, key=None):
        super().__init__(widget_id=None)
        self.child = child
        self.flex = flex
        self.key = key


        self.add_child(self.child) if self.child else None# Register the child widget with the framework



    def to_html(self):
        return f"<div id='{self.widget_id()}' style='flex: {self.flex};'>{self.child.to_html()}</div>"



class Spacer(Widget):
    def __init__(self, flex=1, key=None):
        super().__init__(widget_id=None)
        self.flex = flex
        self.key = key
    
    def get_children(self):
        return []  # SizedBox doesn't have children, so return an empty list

    def remove_all_children(self):
        pass


    def widget_id(self):
        return 'spacer'


    def to_html(self):
        return f"<div id='{self.widget_id()}' style='flex: {self.flex};'></div>"
        
class SizedBox(Widget):
    def __init__(self, height=0, width=0):
        super().__init__(widget_id=None)
        self.height = height
        self.width = width

    def get_children(self):
        return []  # SizedBox doesn't have children, so return an empty list

    def remove_all_children(self):
        pass

    def widget_id(self):
        return 'sizedBox'

    def to_html(self):
        return f"<div id='{self.widget_id()}' style='height: {self.height}px; width: {self.width}px;'></div>"

class AppBar(Widget):
    def __init__(self, title=None, actions=None, leading=None, backgroundColor=None, elevation=None, centerTitle=None, titleSpacing=None, pinned=False, bottom=None, shadowColor=Colors.rgba(0,0,0,0.2)):
        super().__init__(widget_id=None)
        self.title = title
        self.actions = actions or []
        self.leading = leading
        self.backgroundColor = backgroundColor
        self.elevation = elevation
        self.centerTitle = centerTitle
        self.titleSpacing = titleSpacing
        self.shadowColor = shadowColor
        self.pinned = pinned
        self.bottom = bottom
        
        self.add_child(self.title) if self.title else None
        self.add_child(self.leading) if self.leading else None

        for action in self.actions:
            self.add_child(action) if action else None
    



    def to_html(self):
        pinned_style = 'position: fixed; width: 100%;' if self.pinned else 'position: relative;'
        app_bar_style = ""
        if self.backgroundColor:
            app_bar_style += f"background-color: {self.backgroundColor};"
        if self.elevation:
            app_bar_style += f"box-shadow: 0 {self.elevation}px 5px {self.shadowColor};"
        
        # Define height and ensure it affects layout
        app_bar_style += f"box-shadow: 0 6px 5px rgba(0, 0, 0, 0.2); height: 56px; display: flex; align-items: center; position: relative; z-index: 1;"

        leading_html = self.leading.to_html() if self.leading else ""
        title_html = self.title.to_html() if self.title else ""
        center_title = self.centerTitle.to_html() if self.centerTitle else ""
        actions_html = ''.join([action.to_html() for action in self.actions])

        bottom_html = self.bottom.to_html() if self.bottom else ""

        leading_css = f'margin-left: 16px;' if self.leading else ""
        action_css = f'margin-right: 16px;' if self.actions else ""
        title_spacing = self.titleSpacing if self.titleSpacing else 10

        return f"""
        <div id="{self.widget_id()}" class="app-bar" style="{app_bar_style}">
            <div style="{leading_css}">{leading_html}</div>
            <div style="flex: 1; margin-left: {title_spacing}px;">{title_html}</div>
            <div style="flex: 1; text-align: center;">{center_title}</div>
            <div style="{action_css}">{actions_html}</div>
            {bottom_html}
        </div>
        """


class BottomNavigationBar(Widget):
    def __init__(self, 
                 items, 
                 onTap=None, 
                 currentIndex=0, 
                 fixedColor=None, 
                 backgroundColor= Colors.white , 
                 elevation=10, 
                 iconSize=30, 
                 selectedFontSize=18, 
                 unselectedFontSize=14, 
                 selectedItemColor= Colors.blue , 
                 unselectedItemColor= Colors.grey ,
                 showSelectedLabels=True, 
                 showUnselectedLabels=False, 
                 landscapeLayout="centered"):
        super().__init__(widget_id=None)
        self.items = items
        self.onTap = onTap
        self.currentIndex = currentIndex
        self.fixedColor = fixedColor
        self.backgroundColor = backgroundColor
        self.elevation = elevation
        self.iconSize = iconSize
        self.selectedFontSize = selectedFontSize
        self.unselectedFontSize = unselectedFontSize
        self.selectedItemColor = selectedItemColor
        self.unselectedItemColor = unselectedItemColor
        self.showSelectedLabels = showSelectedLabels
        self.showUnselectedLabels = showUnselectedLabels
        self.landscapeLayout = landscapeLayout

        self.api = Api()
        self.onTapName = self.onTap.__name__ if self.onTap else ''



        for item in self.items:
            self.add_child(item) if item else None


    def to_html(self):
        self.api.register_callback(self.onTapName, self.onTap)
        items_html = ''
        for index, item in enumerate(self.items):
            selected = index == self.currentIndex
            color = self.selectedItemColor if selected else self.unselectedItemColor
            font_size = self.selectedFontSize if selected else self.unselectedFontSize

            item.icon.size = self.iconSize
            

            item_html = item.to_html(selected=selected, showSelectedLabels = self.showSelectedLabels, showUnselectedLabels= self.showUnselectedLabels, fixedColor=self.fixedColor)
            item_style = f"color: {color}; font-size: {font_size}px; cursor: pointer; flex: 1;"
            items_html += f"<div onclick='handleClickOnTap(\"{self.onTapName}\", {index})' style='{item_style}'>{item_html}</div>"

        return f"""
        <div id="{self.widget_id()}" class="bottom-nav" id="bottomNav">
            {items_html}
        </div>
        """


class BottomNavigationBarItem(Widget):
    def __init__(self, icon, label):
        
        super().__init__(widget_id=None)
        self.icon = icon
        self.label = label


        self.add_child(self.icon) if self.icon else None
        self.add_child(self.label) if self.label else None
    


    def to_html(self, selected=False, showSelectedLabels=True, showUnselectedLabels=False, iconSize=30, fixedColor=None):
        # Set the color to fixedColor if provided, otherwise use default behavior
        color = fixedColor if fixedColor else None
        self.icon.color = color
        
        icon_html = self.icon.to_html()
        should_show_label = (selected and showSelectedLabels) or (not selected and showUnselectedLabels)
        should_color_label = (fixedColor and selected) or (not fixedColor and selected)
        label_color = fixedColor if should_color_label else '#aaa'
        label = self.label
        #label.style()
        label_html = f"<div style='color: {label_color};'>{self.label.to_html()}</div>" if should_show_label else ''

        return f"<div id='{self.widget_id()}' style='text-align: center; '>{icon_html}{label_html}</div>"

class Scaffold(Widget):
    def __init__(self, 
                 appBar=None, 
                 body=None, 
                 floatingActionButton=None, 
                 bottomNavigationBar=None, 
                 drawer=None, 
                 endDrawer=None, 
                 bottomSheet=None, 
                 persistentFooterButtons=None,
                 snackBar=None,
                 backgroundColor=Colors.white,
                 resizeToAvoidBottomInset=True,
                 extendBody=False,
                 extendBodyBehindAppBar=False,
                 drawerDragStartBehavior=None,
                 drawerEdgeDragWidth=None,
                 drawerEnableOpenDragGesture=True,
                 endDrawerEnableOpenDragGesture=True,
                 drawerScrimColor=Colors.rgba(0, 0, 0, 0.5),
                 onDrawerChanged=None,
                 onEndDrawerChanged=None,
                 persistentFooterAlignment=MainAxisAlignment.CENTER,
                 primary=True,
                 key=None):
        super().__init__(widget_id=None)
        self.appBar = appBar
        self.body = body
        self.floatingActionButton = floatingActionButton
        self.bottomNavigationBar = bottomNavigationBar
        self.drawer = drawer
        self.endDrawer = endDrawer
        self.bottomSheet = bottomSheet
        self.persistentFooterButtons = persistentFooterButtons
        self.snackBar = snackBar
        self.backgroundColor = backgroundColor
        self.resizeToAvoidBottomInset = resizeToAvoidBottomInset
        self.extendBody = extendBody
        self.extendBodyBehindAppBar = extendBodyBehindAppBar
        self.drawerDragStartBehavior = drawerDragStartBehavior
        self.drawerEdgeDragWidth = drawerEdgeDragWidth
        self.drawerEnableOpenDragGesture = drawerEnableOpenDragGesture
        self.endDrawerEnableOpenDragGesture = endDrawerEnableOpenDragGesture
        self.drawerScrimColor = drawerScrimColor
        self.onDrawerChanged = onDrawerChanged
        self.onEndDrawerChanged = onEndDrawerChanged
        self.persistentFooterAlignment = persistentFooterAlignment
        self.primary = primary
        self.key = key


        children = [
            self.appBar, 
            self.body, 
            self.floatingActionButton,
            self.bottomNavigationBar,
            self.drawer,
            self.endDrawer,
            self.bottomSheet,
            self.snackBar
            ]

        for child in children:
            self.add_child(child) if child else None
        


    def to_html(self):
        appBar_html = self.appBar.to_html() if self.appBar else ""
        body_html = self.body.to_html() if self.body else ""
        # body_id = self.body._id if self.body else "" # Not used in JS currently
        floating_action_button_html = self.floatingActionButton.to_html() if self.floatingActionButton else ""
        bottom_navigation_bar_html = self.bottomNavigationBar.to_html() if self.bottomNavigationBar else "" # Ensure this renders id="bottomNav"
        drawer_html = self.drawer.to_html() if self.drawer else ""
        end_drawer_html = self.endDrawer.to_html() if self.endDrawer else ""
        bottom_sheet_html = self.bottomSheet.to_html() if self.bottomSheet else ""
        snack_bar_html = self.snackBar.to_html() if self.snackBar else ""
        footer_buttons_html = ''.join([button.to_html() for button in (self.persistentFooterButtons or [])])

        # Styles are better handled in CSS, but keep if needed for specific overrides
        background_color_style = f"background-color: {self.backgroundColor};"
        # These style calculations are complex and might be better handled purely in CSS flexbox/grid
        # extend_body_style = "position: absolute; top: 56; bottom: 0; left: 0; right: 0;" if self.extendBody or self.extendBodyBehindAppBar else ""
        # body_margin_top = "margin-top: 0px;" if self.appBar and not self.extendBodyBehindAppBar else ""


        return f"""
        <div id="{self.widget_id()}" class="body" style="{background_color_style}">
            {appBar_html} 
            <div class="drawer left" id="leftDrawer">
                {drawer_html}
            </div>

            <div class="drawer right" id="rightDrawer">
                {end_drawer_html}
            </div>

            <div class="content" id="content">
                {body_html}
            </div>

            {floating_action_button_html}
            {bottom_sheet_html}
            {snack_bar_html}
            <div style="position: absolute; bottom: 0; width: 100%; display: flex; justify-content: {self.persistentFooterAlignment};">
                {footer_buttons_html}
            </div>
            <div id="bottomNav" class="bottom-nav">
            {bottom_navigation_bar_html} 
            </div>
        </div>
        """
        

class Body(Widget):
    def __init__(self, child=None):
        super().__init__(widget_id=None)
        self.child = child
        self.id = self.widget_id()

        self.add_child(self.child) if self.child else None # Register the child widget with the framework
        
    def id(self):
        #print("Body: ", self.widget_id())
        return self.widget_id()

    def to_html(self):
        child_html = self.child.to_html() if self.child else ''
        
        return f"{child_html}"



class Divider(Widget):
    def __init__(self, height=1, margin=EdgeInsets.symmetric(8,0), color=Colors.hex('#ccc'), border=BorderStyle.NONE):
        super().__init__(widget_id=None)
        self.height = height
        self.margin = margin
        self.color = color
        self.border = border

    def get_children(self):
        return []  # SizedBox doesn't have children, so return an empty list

    def remove_all_children(self):
        pass

    


    def to_html(self):
        return f"""
        <hr  id="{self.widget_id()}" style="height: {self.height}px; background-color: {self.color}; border: {self.border}; margin: {self.margin.to_css()};">
        """

class Drawer(Widget):

    _instance = None  # Class-level attribute to store the single instance

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            # If an instance doesn't exist, create one
            cls._instance = super(Drawer, cls).__new__(cls)
        return cls._instance  # Return the singleton instance

    def __init__(self, child, width=250, divider=None, borderRight= BorderSide(width=0.1, style=BorderStyle.SOLID), elevation='', padding=EdgeInsets.all(20), backgroundColor=Colors.white):
        # Only initialize the instance once
        if not hasattr(self, 'initialized'):
            super().__init__(widget_id=None)
            self.child = child
            self.width = width
            self.padding = padding
            self.borderRight = borderRight
            self.elevation = elevation
            self.divider = divider
            self.backgroundColor = backgroundColor
            self.is_open = False
            self.add_child(self.child) if self.child else None
            self.initialized = True  # Mark the instance as initialized


        self.add_child(self.child) if self.child else None# Register the child widget with the framework
    


    def to_html(self):
        
        divider = self.divider.to_html() if self.divider else ''
        drawer_width = self.width + self.padding.to_int_horizontal() + self.borderRight.to_int()
        border = self.borderRight.border_to_css() if self.borderRight else ''
        drawer_width = '0px' if self.is_open else f'-{drawer_width}' 
        print(self.width ,drawer_width, self.is_open)

        return f"""
        <div id="{self.widget_id()}" style="width: {self.width}px; padding: {self.padding.to_css()}; height: 100%; background: {self.backgroundColor}; box-shadow:{self.elevation}; overflow-y: auto; border-right: {border};">
            {self.child.to_html()}{divider}
        </div>
        """

    def toggle(self, bool=False):
        self.is_open = bool # Update Python state if needed elsewhere
        framework = self._framework_ref()
        if framework and framework.window:
            print(f"Calling JS: toggleDrawer('left'), Target Window ID: {framework.id}") # Debug
            framework.window.evaluate_js(
                framework.id,
                f"toggleDrawer('left');" # Ensure side is correctly passed if needed later ('right')
            )
        else:
             print("Framework or window not available for Drawer toggle JS call.")

        # Return value doesn't seem used, but keep if needed
        # return self.is_open



class EndDrawer(Widget):
    _instance = None  # Class-level attribute to store the single instance

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            # If an instance doesn't exist, create one
            cls._instance = super(EndDrawer, cls).__new__(cls)
        return cls._instance  # Return the singleton instance

    def __init__(self, child, width=250, divider=None, borderLeft= BorderSide(width=0.1, style=BorderStyle.SOLID), elevation='', padding=EdgeInsets.all(20), backgroundColor=Colors.white):
        # Only initialize the instance once
        if not hasattr(self, 'initialized'):
            super().__init__(widget_id=None)
            self.child = child
            self.width = width
            self.padding = padding
            self.borderLeft = borderLeft
            self.elevation = elevation
            self.divider = divider
            self.backgroundColor = backgroundColor
            self.is_open = False
            self.initialized = True  # Mark the instance as initialized


        self.add_child(self.child) if self.child else None# Register the child widget with the framework
    


    def to_html(self):
        divider = self.divider.to_html() if self.divider else ''
        end_drawer_width = self.width + self.padding.to_int_horizontal() + self.borderLeft.to_int()
        end_drawer_width = '0px' if self.is_open else end_drawer_width
        border = self.borderLeft.border_to_css() if self.borderLeft else ''
        return f"""
        <div id="{self.widget_id()}" style="width: {self.width}px; padding: {self.padding.to_css()}; height: 100%; background: {self.backgroundColor}; overflow-y: auto; box-shadow:{self.elevation}; border-left: {border};">
            {self.child.to_html()}{divider}
        </div>
        """

    def toggle(self, bool=False):
        self.is_open = bool # Update Python state if needed elsewhere
        framework = self._framework_ref()
        if framework and framework.window:
            print(f"Calling JS: toggleDrawer('left'), Target Window ID: {framework.id}") # Debug
            framework.window.evaluate_js(
                framework.id,
                f"toggleDrawer('right');" # Ensure side is correctly passed if needed later ('right')
            )
        else:
             print("Framework or window not available for Drawer toggle JS call.")

        # Return value doesn't seem used, but keep if needed
        # return self.is_open



class BottomSheet(Widget):
    _instance = None  # Class-level attribute to store the single instance

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            # If an instance doesn't exist, create one
            cls._instance = super(BottomSheet, cls).__new__(cls)
        return cls._instance  # Return the singleton instance
        
    def __init__(self, child, height=300, backgroundColor=Colors.white, elevation='', padding=EdgeInsets.all(20), enableDrag=True):
         # Only initialize the instance once
        if not hasattr(self, 'initialized'):
            super().__init__(widget_id=None)
            self.child = child
            self.height = height
            self.backgroundColor = backgroundColor
            self.elevation = elevation
            self.padding = padding
            self.enableDrag = enableDrag
            self.is_open = False
            self.show_barrier = False
            self.barrier_color = Colors.rgba(0, 0, 0, 0.5) # Modal barrier color (overlay)
            self.initialized = True  # Mark the instance as initialized



            self.add_child(self.child) if self.child else None# Register the child widget with the framework


    def to_html(self):
        # Barrier for background dimming (optional)
        barrier_html = f'<div style="position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; background-color: {self.barrier_color}; z-index: 899;"></div>' if self.is_open else ''
        barrier_html = barrier_html if self.show_barrier else ''
        drag_behavior = 'cursor: grab;' if self.enableDrag else ''
        translate = '0px' if self.is_open else '100%'
        return f"""
        {barrier_html} 
        <div id="{self.widget_id()}" style="position: fixed; left: 0; bottom: 0; z-index: 900; width: 100%; height: {self.height}px; padding: {self.padding.to_css()}; background-color: {self.backgroundColor}; box-shadow:{self.elevation}; transform: translateY({translate}); transition: transform 0.3s ease; {drag_behavior}">
            {self.child.to_html()}
        </div>
        """


    def toggle(self, bool=False):
        self.is_open = bool
        
        return self.is_open

class Center(Widget):
    def __init__(self, child):
        super().__init__(widget_id=None)
        self.child = child



        self.add_child(self.child) if self.child else None# Register the child widget with the framework    


    def to_html(self):
        return f"""
        <div id="{self.widget_id()}" style="display: flex; justify-content: center; align-items: center; height: 100%;">
            {self.child.to_html()}
        </div>
        """



class ListTile(Widget):
    def __init__(self, leading=None, title=None, subtitle=None, onTap=None):
        super().__init__(widget_id=None)
        self.leading = leading
        self.title = title
        self.subtitle = subtitle
        self.onTap = onTap

        self.api = Api()
        self.onTapName = self.onTap.__name__ if self.onTap else ''



        children = [
            self.leading,
            self.title,
            self.subtitle
        ]

        for child in children:
            self.add_child(child) if child else None# Register the child widget with the framework

    def to_html(self):
        self.api.register_callback(self.onTapName, self.onTap)

        leading_html = self.leading.to_html() if self.leading else ""
        title_html = self.title.to_html() if self.title else ""
        subtitle_html = self.subtitle.to_html() if self.subtitle else ""
        onClick = f'onclick="handleClick(\'{self.onTapName}\')"' if self.onTap else ""

        return f"""
        <div id="{self.widget_id()}" class="list-tile" style="display: flex; align-items: center; padding: 10px; cursor: pointer;" {onClick}>
            <div style="margin-right: 10px;">{leading_html}</div>
            <div>
                <div>{title_html}</div>
                <div style="color: grey;">{subtitle_html}</div>
            </div>
        </div>
        """




class SnackBar(Widget):
    _instance = None  # Class-level attribute to store the single instance

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            # If an instance doesn't exist, create one
            cls._instance = super(SnackBar, cls).__new__(cls)
        return cls._instance  # Return the singleton instance


    def __init__(self, content, action=None, duration=3000, backgroundColor=Colors.grey, padding=EdgeInsets.symmetric(horizontal=24, vertical=16)):
         # Only initialize the instance once
        if not hasattr(self, 'initialized'):    
            super().__init__(widget_id=None)
            self.content = content
            self.action = action
            self.duration = duration
            self.backgroundColor = backgroundColor
            self.padding = padding
            self.is_open = False
            self.initialized = True  # Mark the instance as initialized
            self.current_id = None


            children = [
                self.content,
                self.action,
            ]
        
            for child in children:
                self.add_child(child) if child else None# Register the child widget with the framework

    def to_html(self):
        self.current_id = self.widget_id()
        action_html = self.action.to_html() if self.action else ""
        display_style = "flex" if self.is_open else "none"
        return f"""
        <div id="{self.current_id}" 
        style="display: {display_style}; 
        position: absolute; 
        bottom: 20px; 
        left: 50%; 
        transform: translateX(-50%);
        width: calc(100% - 48px); 
        padding: {self.padding.to_css()}; 
        background-color: {self.backgroundColor}; 
        box-shadow: 0px -2px 10px rgba(0, 0, 0, 0.3);
        border-radius: 4px; 
        z-index: 999; 
        justify-content: space-between; 
        align-items: center;">
            <div>{self.content.to_html()}</div>
            {action_html}
        </div>
        """

    def get_id(self):
        return self.current_id

    def toggle(self, bool=False):
        self.is_open = bool
        
        return self.is_open

class SnackBarAction(Widget):
    _instance = None  # Class-level attribute to store the single instance

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            # If an instance doesn't exist, create one
            cls._instance = super(SnackBarAction, cls).__new__(cls)
        return cls._instance  # Return the singleton instance


    def __init__(self, label, onPressed, textColor=Colors.blue):
        # Only initialize the instance once
        if not hasattr(self, 'initialized'): 
            super().__init__(widget_id=None)
            self.label = label
            self.onPressed = onPressed
            self.textColor = textColor

            self.api = Api()
            self.onPressedName = self.onPressed.__name__ if self.onPressed else ''

            self.add_child(self.label) if self.label else None

    

    def to_html(self):
        self.api.register_callback(self.onPressedName, self.onPressed)

        return f"""
        <button id="{self.widget_id()}" 
        onclick="handleClick(\'{self.onPressedName}\')" 
        style="background: none; 
        border: none; 
        color: {self.textColor}; 
        font-size: 14px; 
        cursor: pointer;">
            {self.label.to_html()}
        </button>
        """


class Placeholder(Widget):
    def __init__(self, 
                 color=Colors.gray, 
                 stroke_width=2, 
                 height=100, 
                 width=100, 
                 child=None):
        super().__init__(widget_id=None)
        self.color = color
        self.stroke_width = stroke_width
        self.height = height
        self.width = width
        self.child = child

        if self.child:
            self.add_child(self.child)

    def to_html(self):
        if self.child:
            return self.child.to_html()
        else:
            return f"""
            <div id="{self.widget_id()}" style="
                height: {self.height}px;
                width: {self.width}px;
                border: {self.stroke_width}px dashed {self.color};
                display: flex;
                justify-content: center;
                align-items: center;
            ">
                <p style="
                color: {self.color};
                 font-size: 12px;
                 ">Placeholder</p>
            </div>
            """

class Padding(Widget):
    def __init__(self, padding=EdgeInsets.all(10), child=None):
        super().__init__(widget_id=None)
        self.padding = padding
        self.child = child

        if self.child:
            self.add_child(self.child)

    def to_html(self):
        child_html = self.child.to_html() if self.child else ''
        return f"""
        <div id="{self.widget_id()}" 
        style="padding: {self.padding.to_css()};">
            {child_html}
        </div>
        """

class Align(Widget):
    def __init__(self, alignment=Alignment.center(), child=None):
        super().__init__(widget_id=None)
        self.alignment = alignment
        self.child = child

        if self.child:
            self.add_child(self.child)

    def to_html(self):
        child_html = self.child.to_html() if self.child else ''
        return f"""
        <div id="{self.widget_id()}" 
        style="display: flex; 
        justify-content: {self.alignment.horizontal}; 
        align-items: {self.alignment.vertical}; 
        height: 100%; 
        width: 100%;">
            {child_html}
        </div>
        """


class AspectRatio(Widget):
    def __init__(self, aspect_ratio, child=None):
        super().__init__(widget_id=None)
        self.aspect_ratio = aspect_ratio
        self.child = child

        if self.child:
            self.add_child(self.child)

    def to_html(self):
        child_html = self.child.to_html() if self.child else ''
        
        # Aspect ratio calculation for CSS: padding-bottom is used to maintain aspect ratio
        padding_bottom = 100 / self.aspect_ratio

        return f"""
        <div id="{self.widget_id()}" 
        style="position: relative; 
        width: 100%; 
        padding-bottom: {padding_bottom}%; 
        height: 0; overflow: hidden;">
            <div style="position: absolute; 
            top: 0; left: 0; width: 100%; height: 100%;">
                {child_html}
            </div>
        </div>
        """

class FittedBox(Widget):
    def __init__(self, fit=BoxFit.CONTAIN, alignment=Alignment.center(), child=None):
        super().__init__(widget_id=None)
        self.fit = fit
        self.alignment = alignment
        self.child = child

        if self.child:
            self.add_child(self.child)

    def to_html(self):
        alignment_css = self.alignment.to_css()
        child_html = self.child.to_html() if self.child else ''

        # Using BoxFit values directly
        object_fit = self.fit

        return f"""
        <div id="{self.widget_id()}" 
        style="width: 100%; height: 100%; {alignment_css};">
            <div style="flex: 0 0 auto; object-fit: {object_fit};">
                {child_html}
            </div>
        </div>
        """

class FractionallySizedBox(Widget):
    def __init__(self, widthFactor=None, heightFactor=None, alignment=Alignment.center(), child=None):
        super().__init__(widget_id=None)
        self.widthFactor = widthFactor
        self.heightFactor = heightFactor
        self.alignment = alignment
        self.child = child

        if self.child:
            self.add_child(self.child)

    def to_html(self):
        alignment_css = self.alignment.to_css()

        # Calculate the width and height percentages based on the factors
        width = f"{self.widthFactor * 100}%" if self.widthFactor is not None else 'auto'
        height = f"{self.heightFactor * 100}%" if self.heightFactor is not None else 'auto'
        
        child_html = self.child.to_html() if self.child else ''

        return f"""
        <div id="{self.widget_id()}" 
        style="display: flex; 
        {alignment_css}; 
        width: 100%; height: 100%;">
            <div style="width: {width}; height: {height};">
                {child_html}
            </div>
        </div>
        """


class Flex(Widget):
    def __init__(self, 
                 direction=Axis.HORIZONTAL, 
                 mainAxisAlignment=MainAxisAlignment.START, 
                 crossAxisAlignment=CrossAxisAlignment.START, 
                 children=None, 
                 padding=None):
        super().__init__()
        self.direction = direction
        self.mainAxisAlignment = mainAxisAlignment
        self.crossAxisAlignment = crossAxisAlignment
        self.children = children if children is not None else []
        self.padding = padding if padding is not None else EdgeInsets.all(0)

        if self.children:
            for child in self.children:
                self.add_child(child)
        
    def to_html(self):
        direction_css = 'row' if self.direction == Axis.HORIZONTAL else 'column'
        
        # CSS for main axis and cross axis alignment
        justify_content = self.mainAxisAlignment
        align_items = self.crossAxisAlignment
        
        # Add padding to the Flex container
        padding_css = self.padding.to_css()
        
        # Generate the CSS for the Flex container
        container_css = f"""display: flex; 
        flex-direction: {direction_css}; 
        justify-content: {justify_content}; 
        align-items: {align_items}; 
        padding: {padding_css};"""
        
        # Build HTML for each child
        children_html = ''.join([child.render() for child in self.children])
        
        return f'<div style="{container_css}">{children_html}</div>'


class Wrap(Widget):
    def __init__(self, 
                 direction=Axis.HORIZONTAL, 
                 alignment=MainAxisAlignment.START, 
                 crossAxisAlignment=CrossAxisAlignment.START,
                 runAlignment=MainAxisAlignment.START,
                 spacing=0,
                 runSpacing=0,
                 clipBehavior=ClipBehavior.NONE,
                 children=None):
        self.direction = direction
        self.alignment = alignment
        self.crossAxisAlignment = crossAxisAlignment
        self.runAlignment = runAlignment
        self.spacing = spacing
        self.runSpacing = runSpacing
        self.clipBehavior = clipBehavior
        self.children = children or []


        if self.children:
            for child in self.children:
                self.add_child(child)
    
   

    def to_html(self):
        styles = []
        # Flex properties for wrapping
        flex_direction = 'row' if self.direction == Axis.HORIZONTAL else 'column'
        styles.append(f"display: flex; flex-wrap: wrap; flex-direction: {flex_direction};")
        
        # Main Axis Alignment
        styles.append(f"justify-content: {self.alignment};")
        
        # Cross Axis Alignment
        styles.append(f"align-items: {self.crossAxisAlignment};")
        
        # Run Alignment (applies to multi-row or multi-column layout)
        # In CSS, justify-content applies similarly to the "runAlignment"
        styles.append(f"align-content: {self.runAlignment};")
        
        # Spacing (gap between items)
        styles.append(f"gap: {self.spacing}px;")
        
        # Run Spacing (spacing between lines or rows of items)
        # CSS does not directly support run-spacing, so we may have to adjust for this manually later
        styles.append(f"row-gap: {self.runSpacing}px;" if self.direction == Axis.HORIZONTAL else f"column-gap: {self.runSpacing}px;")
        
        # Clip Behavior
        if self.clipBehavior:
            overflow_css = "overflow: hidden;" if self.clipBehavior != ClipBehavior.NONE else ""
            styles.append(overflow_css)
        
        css = " ".join(styles)
        children_html = "".join([child.to_html() for child in self.children])
        return f'<div style="{css}">{children_html}</div>'



class Dialog(Widget):

    _instance = None  # Class-level attribute to store the single instance

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            # If an instance doesn't exist, create one
            cls._instance = super(Dialog, cls).__new__(cls)
        return cls._instance  # Return the singleton instance

    def __init__(self,
                 title=None,
                 content=None,
                 actions=None,
                 title_alignment=TextAlign.center(),  # Allows title alignment customization
                 title_padding=EdgeInsets.all(10),  # Padding around the title
                 content_padding=EdgeInsets.all(5),  # Padding around the content
                 dialog_shape=BorderRadius.all(10),  # Custom shape (border radius)
                 elevation=8,  # Shadow depth for elevation
                 background_color=Colors.hex("#fff"),  # Background color
                 barrier_color=Colors.rgba(0, 0, 0, 0.5),  # Modal barrier color (overlay)
                 padding=EdgeInsets.all(20)):  # Padding inside the dialog

        # Only initialize the instance once
        if not hasattr(self, 'initialized'):
            super().__init__(widget_id=None)
            self.title = title
            self.content = content
            self.actions = actions or []
            self.title_alignment = title_alignment
            self.title_padding = title_padding
            self.content_padding = content_padding
            self.dialog_shape = dialog_shape
            self.elevation = elevation
            self.background_color = background_color
            self.barrier_color = barrier_color
            self.padding = padding

            if self.content:
                self.add_child(self.content)
                self.add_child(self.title)
            for action in self.actions:
                self.add_child(action)

            self.initialized = True  # Mark the instance as initialized

    def to_html(self):
        # Title HTML
        title_html = f'<div style="text-align: {self.title_alignment.to_css()}; padding: {self.title_padding.to_css()};">{self.title.to_html()}</div>' if self.title else ""
        
        # Content HTML
        content_html = f'<div style="padding: {self.content_padding.to_css()}; margin-top: 4px;">{self.content.to_html()}</div>' if self.content else ""
        
        # Actions (buttons, etc.)
        actions_html = "".join([action.to_html() for action in self.actions])

        # Calculate box-shadow based on elevation for the dialog
        box_shadow = f"0 {self.elevation}px {self.elevation * 2}px rgba(0, 0, 0, 0.2)"
        
        # Dialog CSS
        dialog_css = (
            f"{self.dialog_shape.to_css()}"  # Dialog shape (border-radius)
            f"background-color: {self.background_color};"
            f"padding: {self.padding.to_css()};"
            f"position: fixed; top: 50%; left: 50%;"
            f"transform: translate(-50%, -50%);"
            f"box-shadow: {box_shadow};"  # Elevation (shadow)
            f"max-width: 330px; min-width: 180px;"
            f"z-index: 1000;"
        )

        # Barrier for background dimming (optional)
        barrier_html = f'''<div style="position: fixed; 
        top: 0; left: 0; width: 100vw; 
        height: 100vh; background-color: {self.barrier_color}; 
        z-index: 999;"></div>'''

        # Full dialog HTML
        return f'''
        {barrier_html}  <!-- Barrier to block interaction outside the dialog -->
        <div style="{dialog_css}">
            {title_html}
            {content_html}
            <div class="dialog-actions" 
            style="margin-top: 20px;">
            {actions_html}
            </div>
        </div>
        '''



"""
class Dialog(Widget):

    _instance = None  # Class-level attribute to store the single instance

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            # If an instance doesn't exist, create one
            cls._instance = super(Dialog, cls).__new__(cls)
        return cls._instance  # Return the singleton instance
    def __init__(
            self,
            title=None, 
            content=None, 
            actions=None, 
            ):
         # Only initialize the instance once
        if not hasattr(self, 'initialized'):    
            super().__init__(widget_id=None)
            self.title = title
            self.content = content
            self.actions = actions or []
            self.color = color=Colors.hex("#fff")
            self.border = BorderSide(color=Colors.hex("#000"), style=BorderStyle.SOLID, width=1, borderRadius=5)
            self.initialized = True  # Mark the instance as initialized

            if self.content:
                self.add_child(self.content)
                self.add_child(self.title)
            for action in self.actions:
                self.add_child(action)

    def css(self):
        
        
        # Additional CSS for modal display
        modal_css = (
            f"{self.border.to_css()}"
            f"background-color: {self.color};"
            "padding: 15px;"
            "position: fixed; "
            "top: 50%; left: 50%; "
            "transform: translate(-50%, -50%); "
            "box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2); "
            "z-index: 1000;"
        )
        
        return f"{modal_css}"

    def to_html(self):
        # Title HTML
        title_html = self.title.to_html() if self.title else ""
        
        # Content HTML
        content_html = f'<div style="margin-top: 4px;">{self.content.to_html()}</div>' if self.content else ""
        
        # Actions (buttons, etc.)
        actions_html = "".join([action.to_html() for action in self.actions])

        # Full dialog HTML
        dialog_css = self.css()
        return f'''
        <div style="{dialog_css}">
            {title_html}
            {content_html}
            <div class="dialog-actions">{actions_html}</div>
        </div>
        '''


"""
