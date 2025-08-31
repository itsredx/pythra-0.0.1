# pythra/widgets_more.py
import uuid
import yaml
import os
import html
import json
from .api import Api
from .base import *
from .state import *
from .styles import *
from .icons import *
from .icons.base import IconData # Import the new data class
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
                .{css_class} {{ /* Base styles */ cursor: pointer;}}
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
                    cursor: pointer;
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
                 trackRadius: Optional[BorderRadius] = None,
                 thumbColor: Optional[str] = None,
                 thumbBorderColor: Optional[str] = None,
                 thumbBorderRadius: Optional[BorderRadius] = None,
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
        self.trackRadius = trackRadius.to_css_value() if trackRadius else f"{self.trackHeight / 2}px"
        self.thumbSize = theme.thumbSize
        self.thumbBorderWidth = theme.thumbBorderWidth
        self.thumbBorderColor = thumbBorderColor or theme.thumbBorderColor or Colors.surfaceVariant
        self.thumbBorderRadius = thumbBorderRadius.to_css_value() if thumbBorderRadius else "50%"
        self.overlaySize = theme.overlaySize

        print("thumbBorderRadius: ", self.thumbBorderRadius)

        # --- Callback Management (no change) ---
        self.on_drag_update_name = f"slider_update_{id(self.controller)}"
        # Api.instance().register_callback(self.on_drag_update_name, self._handle_drag_update)

        # --- CSS Style Management ---
        # The style_key MUST now include all themeable properties
        self.style_key = (
            self.activeColor, self.inactiveColor, self.thumbColor,
            self.overlayColor, self.trackHeight, self.trackRadius, self.thumbSize,
            self.thumbBorderWidth, self.thumbBorderColor, self.thumbBorderRadius, self.overlaySize
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
         track_height, track_radius, thumb_size, thumb_border_width, thumb_border_color, thumb_border_radius, overlay_size) = style_key
        
        # Calculate track border radius based on height
        # track_radius = track_height / 2.0
        
        return f"""
        .{css_class}.slider-container {{
            position: relative; width: 100%; height: 20px;
            display: flex; align-items: center; cursor: pointer;
            -webkit-tap-highlight-color: transparent;
        }}
        .{css_class} .slider-track, .{css_class} .slider-track-active {{
            position: absolute; width: 100%; height: {track_height}px;
            border-radius: {track_radius}; pointer-events: none;
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
            border-radius: {thumb_border_radius};
            border: {thumb_border_width}px solid {thumb_border_color};
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
                 borderRadius: int = 4,
                 theme: Optional[DropdownTheme] = None,
                 ):

        super().__init__(key=key)

        if not isinstance(controller, DropdownController):
            raise TypeError("Dropdown requires a DropdownController instance.")

        self.controller = controller
        self.items = items
        self.theme = theme or DropdownTheme()
        self.onChanged = onChanged
        self.hintText = hintText
        
        # --- Style Properties ---
        self.backgroundColor = self.theme.backgroundColor or backgroundColor
        self.textColor = self.theme.textColor or textColor 
        self.borderColor = self.theme.borderColor or borderColor
        self.borderRadius = self.theme.borderRadius or borderRadius
        self.width = f"{self.theme.width}px" if isinstance(self.theme.width, (int, float)) else f"{self.theme.width}"
        self.borderWidth = self.theme.borderWidth or 1
        self.fontSize = self.theme.fontSize
        self.padding = self.theme.padding.to_css_value() or "8px 12px"
        self.dropdownColor = self.theme.dropdownColor
        self.dropdownTextColor = self.theme.dropdownTextColor
        self.selectedItemColor = self.theme.selectedItemColor
        self.selectedItemShape = self.theme.selectedItemShape
        self.dropdownMargin = self.theme.dropdownMargin.to_css_value()
        self.itemPadding = self.theme.itemPadding

        # --- Callback Management ---
        self.on_changed_name = f"dropdown_change_{id(self.controller)}"
        # Note: We pass the user's `onChanged` function directly. The JS engine
        # will send the new value, and the framework will call this function.
        
        # --- CSS Style Management ---
        self.style_key = (self.backgroundColor, self.textColor, self.borderColor, self.borderRadius,
                            self.width, self.borderWidth, self.fontSize, self.padding, self.dropdownColor, 
                            self.dropdownTextColor, self.selectedItemColor, self.selectedItemShape, 
                            self.dropdownMargin, self.itemPadding)
        
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
        (bg_color, text_color, border_color, border_radius, width, border_width, font_size, padding, dropdown_color, 
                            dropdown_text_color, selected_item_color, selected_item_shape, 
                            dropdown_margin, item_padding) = style_key

        return f"""
        .{css_class}.dropdown-container {{
            position: relative;
            width: {width};
            font-family: sans-serif;
        }}
        .{css_class} .dropdown-value-container {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: {padding};
            background-color: {bg_color};
            color: {text_color};
            border: {border_width}px solid {border_color};
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
            top: 100%;
            left: 0;
            right: 0;
            background-color: {dropdown_color};
            color: {dropdown_text_color},
            border: 1px solid {border_color};
            border-radius: {border_radius}px;
            list-style: none;
            margin: {dropdown_margin};
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