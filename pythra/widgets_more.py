# =============================================================================
# PYTHRA EXTENDED WIDGET LIBRARY - Advanced "LEGO Blocks" for Specialized UI
# =============================================================================

"""
PyThra Extended Widget Library (Part 2)

This is the "advanced toolkit" that extends the basic widget collection with more
specialized and complex widgets. While widgets.py contains the fundamental building
blocks, this file contains the "premium tools" for advanced UI construction.

**What's in this extended library?**
- **Layout Widgets**: Advanced containers and layout systems
- **Navigation Widgets**: Drawers, app bars, navigation components
- **Interactive Widgets**: Advanced form controls and input widgets
- **Display Widgets**: Specialized content display widgets
- **Material Design Widgets**: Components following Material Design guidelines
- **Custom Widgets**: PyThra-specific advanced components

**Think of it like:**
If widgets.py is your "basic toolbox" (hammer, screwdriver, wrench),
then widgets_more.py is your "power tools workshop" (table saw, router, advanced tools).

**Categories of widgets you'll find here:**
- Divider: Visual separators
- Drawer: Side panel navigation
- AppBar: Top navigation bars
- Scaffold: Main app structure framework
- Card: Material design cards
- ListTile: List item components
- And many more advanced components...

**When to use widgets from this file:**
- When you need more sophisticated UI components
- When building complex navigation systems
- When following Material Design patterns
- When the basic widgets aren't specialized enough for your needs
"""

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



# =============================================================================
# DIVIDER WIDGET - The "Visual Separator" for Organizing Content Sections
# =============================================================================

class Divider(Widget):
    """
    A simple visual separator line - like drawing a line between sections of content!
    
    **What is Divider?**
    Think of Divider as a "visual comma" or "line break" in your UI that helps separate
    different sections of content. It's like the lines you might draw on paper to
    separate different topics or sections.
    
    **Real-world analogy:**
    Divider is like the lines in a notebook:
    - Helps separate different sections of content
    - Makes content easier to read and organize
    - Provides visual breathing room
    - Usually subtle and not attention-grabbing
    
    **When to use Divider:**
    - Separating items in lists or menus
    - Dividing sections in forms or settings pages
    - Creating visual breaks in long content
    - Separating different types of content
    - Adding structure to dense layouts
    
    **When NOT to use Divider:**
    - Between every single element (creates visual clutter)
    - When spacing/padding would work better
    - In already well-structured layouts that don't need extra separation
    
    **Examples:**
    ```python
    # Simple divider between sections
    Column(children=[
        Text("Profile Settings"),
        Switch("Enable notifications"),
        Switch("Dark mode"),
        Divider(),  # Separates settings from account section
        Text("Account"),
        ListTile(title="Change password"),
        ListTile(title="Sign out")
    ])
    
    # Custom styled divider
    Divider(
        thickness=2.0,  # Thicker line
        color="#E0E0E0",  # Light gray
        indent=16,  # Space from left edge
        endIndent=16  # Space from right edge
    )
    
    # Divider with margin for more spacing
    Divider(
        margin=EdgeInsets.symmetric(vertical=16),  # Space above and below
        color=Colors.outline
    )
    ```
    
    **Key parameters:**
    - **thickness**: How thick the line is (default: 1 pixel)
    - **color**: Color of the divider line (default: subtle gray)
    - **indent**: Space from the left edge before the line starts
    - **endIndent**: Space from the right edge where the line ends
    - **margin**: Space around the entire divider (above and below)
    - **height**: Total height including any spacing (often controlled by margin instead)
    
    **Design tip:**
    Keep dividers subtle! They should organize content without being distracting.
    Use your app's theme colors for consistency.
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



# =============================================================================
# DRAWER WIDGET - The "Slide-Out Navigation Panel" for App Navigation
# =============================================================================

class Drawer(Widget):
    """
    The "slide-out navigation panel" that appears from the side of your app - like a hidden menu!
    
    **What is Drawer?**
    Think of Drawer as a "secret compartment" that slides out from the side of your app
    when users need to navigate. It's like having a filing cabinet drawer that pulls
    out to reveal organized navigation options, then slides back when not needed.
    
    **Real-world analogy:**
    Drawer is like a car's glove compartment or a desk drawer:
    - Usually hidden to save space
    - Slides out when you need access to its contents
    - Contains organized items (navigation links, user info, settings)
    - Can be closed to get back to the main content
    - Doesn't interfere with the main workspace when closed
    
    **When to use Drawer:**
    - Main app navigation (Home, Settings, Profile, About)
    - Secondary navigation that doesn't fit in the main UI
    - User account information and actions
    - App settings and preferences
    - Multi-section apps where users need to switch between areas
    
    **When NOT to use Drawer:**
    - For primary actions users need frequently (use buttons instead)
    - In simple apps with only a few screens (use bottom navigation or tabs)
    - For temporary actions (use dialogs or bottom sheets)
    
    **Examples:**
    ```python
    # Basic navigation drawer
    Drawer(
        child=Column(children=[
            # Header with user info
            Container(
                padding=EdgeInsets.all(16),
                child=Row(children=[
                    CircleAvatar("user.jpg"),
                    SizedBox(width=12),
                    Column(children=[
                        Text("John Doe", style=TextStyle(fontWeight="bold")),
                        Text("john@example.com", style=TextStyle(color="gray"))
                    ])
                ])
            ),
            Divider(),
            
            # Navigation items
            ListTile(leading=Icon("home"), title="Home", onTap=go_home),
            ListTile(leading=Icon("person"), title="Profile", onTap=go_profile),
            ListTile(leading=Icon("settings"), title="Settings", onTap=go_settings),
            Divider(),
            ListTile(leading=Icon("help"), title="Help", onTap=show_help),
            ListTile(leading=Icon("logout"), title="Sign Out", onTap=sign_out)
        ])
    )
    
    # Custom styled drawer
    Drawer(
        width=280,  # Wider than default
        backgroundColor=Colors.surface,
        elevation=4.0,  # More dramatic shadow
        child=Column(children=[
            # Custom header
            Container(
                height=200,
                decoration=BoxDecoration(
                    gradient=LinearGradient(["blue", "purple"])
                ),
                child=Center(child=Text("My App", style=TextStyle(color="white")))
            ),
            # Navigation content...
        ])
    )
    ```
    
    **Key parameters:**
    - **child**: The content inside the drawer (usually a Column with navigation items)
    - **width**: How wide the drawer should be (default: 304px following Material Design)
    - **backgroundColor**: Background color of the drawer
    - **elevation**: Shadow depth (how much it "floats" above the main content)
    - **shadowColor**: Color of the shadow
    - **padding**: Internal spacing around the drawer content
    
    **Navigation patterns:**
    Most drawers follow this structure:
    1. **Header**: User info, app logo, or branding
    2. **Main Navigation**: Primary app sections
    3. **Divider**: Visual separator
    4. **Secondary Actions**: Settings, help, sign out
    
    **Material Design tip:**
    Keep drawer content organized and prioritize the most important navigation
    items at the top. Users' eyes naturally scan from top to bottom!
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



# =============================================================================
# END DRAWER - The Slide-out Panel from the Right Edge
# =============================================================================
class EndDrawer(Widget):
    """
    Represents a Material Design navigation drawer that slides in from the end
    (right side in left-to-right locales) of the screen. It is typically used
    within a `Scaffold`.

    **What is EndDrawer?**
    The `EndDrawer` is a content panel that is hidden by default and can be revealed by the
    user, typically by swiping from the right edge of the screen or tapping an icon in the
    `AppBar`. It's functionally identical to a `Drawer` but appears from the opposite side.
    It is often used for secondary actions, filters, or profile information.

    **Real-world analogy:**
    It's like a pull-out spice rack or a sliding pantry built into the side of a kitchen
    cabinet. It's neatly tucked away until you need it, and then it slides out to reveal
    its contents, providing extra functionality without cluttering the main workspace.

    **When to use EndDrawer:**
    - To provide access to secondary navigation or actions.
    - To display filtering options for a list of content.
    - For profile details, notifications, or a shopping cart summary.
    - When you already have a primary `Drawer` on the left and need another panel.

    **Usage with `Scaffold`:**
    The `EndDrawer` is almost exclusively used in the `endDrawer` property of a `Scaffold`
    widget. The `Scaffold` is responsible for handling the logic to open, close, and animate
    the drawer, as well as managing the scrim (the dark overlay) that appears over the main content.

    **Examples:**
    ```python
    # Define the content for the EndDrawer
    my_end_drawer_content = EndDrawer(
        child=ListView(
            children=[
                ListTile(title=Text("Filter by Date")),
                ListTile(title=Text("Filter by Category")),
                Divider(),
                ListTile(title=Text("Sort Ascending")),
            ]
        )
    )

    # Place it in a Scaffold
    Scaffold(
        appBar=AppBar(
            title=Text("My App"),
            # An action button in the AppBar is often used to open the EndDrawer
        ),
        body=Center(child=Text("Main Content")),
        endDrawer=my_end_drawer_content
    )

    # To open the drawer programmatically, you would use a ScaffoldKey/ScaffoldState.
    # scaffoldKey.currentState.openEndDrawer()
    ```

    **Key parameters:**
    - **child**: The `Widget` that defines the content displayed inside the drawer. This is required.
    - **width**: The width of the drawer when it is open. Defaults to the Material Design standard of 304px.
    - **backgroundColor**: The background color of the drawer panel.
    - **padding**: `EdgeInsets` to apply padding around the child content.
    - **elevation** & **shadowColor**: These properties control the shadow that gives the drawer a sense of depth, although the `Scaffold` is what actually renders it.

    **Note on State:**
    You do not control the visibility of the `EndDrawer` directly with a boolean flag. The `Scaffold` manages its open/closed state internally. You interact with it programmatically through a `ScaffoldState` object.
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


# =============================================================================
# BOTTOM SHEET - The Contextual Panel That Slides Up from the Bottom
# =============================================================================
class BottomSheet(Widget):
    """
    A Material Design panel that slides up from the bottom edge of the screen to
    reveal more content. It is typically used to present a set of contextual
    choices or a simple task related to the current screen.

    **What is BottomSheet?**
    A Bottom Sheet is a temporary surface that anchors to the bottom of the screen. It's an
    alternative to menus or dialogs and is primarily used on mobile. There are two main types:
    - **Modal Bottom Sheets**: These are the most common. They appear over the main UI, which
      is obscured by a scrim (dark overlay). The user must interact with the sheet (e.g.,
      make a choice or dismiss it) before they can interact with the rest of the app.
    - **Persistent Bottom Sheets**: (Not covered by this implementation) These are integrated
      with the app content and are not modal.

    **Real-world analogy:**
    It's like pulling open the bottom drawer of a desk to quickly grab a tool. The drawer
    slides out, presenting a specific set of items. You pick what you need, close the drawer,
    and your main workspace is clear again. The drawer's contents are directly related to the
    task you were doing at your desk.

    **When to use BottomSheet:**
    - To offer a set of choices after a user action (e.g., a "Share via..." panel).
    - To present a simple, self-contained task, like composing a short reply.
    - As a more modern, mobile-friendly alternative to a simple dialog or menu.
    - When you need to provide more context or richer controls than a simple menu allows.

    **Usage:**
    The visibility of a `BottomSheet` is controlled by the parent state, often within a `Scaffold`.
    You would typically have a state variable like `_is_sheet_open` and a function that shows it by
    calling `setState`.

    **Examples:**
    ```python
    # Define the content for the BottomSheet
    my_bottom_sheet = BottomSheet(
        child=ListView(
            children=[
                ListTile(leading=Icon("photo"), title=Text("Share to Gallery")),
                ListTile(leading=Icon("chat"), title=Text("Share to Chat App")),
                ListTile(leading=Icon("link"), title=Text("Copy Link")),
            ]
        )
    )

    # In a parent stateful widget's build method:
    # (Simplified logic, usually used with Scaffold's bottomSheet property)

    # if self.state.is_sheet_open:
    #     return Stack(
    #         children=[
    #             MyMainScreen(), # Main app content
    #             my_bottom_sheet
    #         ]
    #     )
    # else:
    #     return MyMainScreen()
    ```

    **Key parameters:**
    - **child**: The `Widget` that defines the content displayed inside the sheet. Required.
    - **maxHeight**: The maximum height the sheet can have, often a percentage of the screen height (e.g., "60%"). This prevents it from covering the entire screen.
    - **backgroundColor**: The background color of the sheet.
    - **borderTopRadius**: Controls the roundness of the top corners, a key part of its Material Design look.
    - **showDragHandle**: (bool) If `True`, displays the small horizontal bar at the top that indicates the sheet can be dragged.
    - **onDismissed**: A callback function that is called when the user dismisses the sheet (e.g., by tapping the scrim or swiping down).

    **Note on State:**
    Similar to a `Drawer`, the state (open/closed) of a `BottomSheet` is managed externally by its parent. You don't set an `is_open` property directly on the widget itself.
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



# =============================================================================
# SNACKBAR ACTION - The Action Button Inside a SnackBar
# =============================================================================
class SnackBarAction(Widget):
    """
    Represents an optional action button displayed at the end of a `SnackBar`.
    This widget is a configuration object used to define the action's behavior
    and appearance.

    **What is SnackBarAction?**
    A `SnackBarAction` defines a clickable button, usually with a short text label
    like "Undo", "Retry", or "Dismiss", that appears within a `SnackBar`. It provides
    the user with an immediate way to respond to the notification they just received.
    This widget is not used by itself; it is passed to the `action` property of a `SnackBar`.

    **Real-world analogy:**
    It's like the "Snooze" button on an alarm clock. The alarm itself is the notification
    (the `SnackBar` message), and the "Snooze" button (`SnackBarAction`) is the immediate,
    contextual action you can take in response to it.

    **When to use SnackBarAction:**
    - To provide an "Undo" option after an action like deleting an item or sending a message.
    - To allow the user to "Retry" a failed operation.
    - To give a quick way to "Dismiss" a persistent notification.

    **Examples:**
    ```python
    # Define a function to be called when the action is pressed
    def undo_delete():
        print("Undo action was triggered!")

    # Create the SnackBarAction, passing the label and the function
    my_action = SnackBarAction(
        label=Text("UNDO"),
        onPressed=undo_delete
    )

    # Now, use this action when creating the SnackBar
    SnackBar(
        content=Text("Item deleted."),
        action=my_action
    )
    ```

    **Key parameters:**
    - **label**: The `Widget` (almost always a `Text` widget) to display as the button's content. Required.
    - **onPressed**: The callback function to execute when the user taps the action button.
    - **textColor**: The color of the label text. Material Design guidelines recommend a highly
      contrasting color (Inverse Primary) to make it stand out against the dark `SnackBar` background.

    **Note on Styling:**
    The styling of the `SnackBarAction` is heavily guided by Material Design principles to ensure it looks
    like a button and has adequate touch targets. You primarily control the label text and its color.
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

# =============================================================================
# SNACKBAR - A Brief, Temporary Notification at the Bottom of the Screen
# =============================================================================
class SnackBar(Widget):
    """
    A lightweight, temporary notification that provides brief feedback about an
    operation. It appears at the bottom of the screen, displays a message, and
    can optionally include an action.

    **What is SnackBar?**
    A `SnackBar` is a pop-up message used for "transient" notifications. It informs the user
    of something that happened (or is happening) without interrupting their workflow. It
    appears for a few seconds and then disappears automatically. It should not contain
    critical information that requires a user's immediate action to proceed.

    **Real-world analogy:**
    It's like the toast popping out of a toaster. It appears briefly to signal that a
    process is complete, gets your attention, and then you can either ignore it or take
    an action (like grabbing the toast). It doesn't block you from doing other things
    in the kitchen.

    **When to use SnackBar:**
    - After an action is completed (e.g., "Message sent", "Profile updated", "Item added to cart").
    - To confirm a user's action, especially if it's reversible (e.g., "Conversation archived").
    - To provide system status updates (e.g., "Connected", "Offline").

    **Usage:**
    The visibility of a `SnackBar` is typically managed by a controller or state manager,
    often associated with a `Scaffold`. You don't manage an `is_open` flag on the `SnackBar`
    itself. Instead, you would call a function like `scaffoldKey.currentState.showSnackBar(...)`
    to make it appear.

    **Examples:**
    ```python
    # A simple SnackBar with just a message
    simple_snackbar = SnackBar(
        content=Text("Your profile has been saved.")
    )

    # A SnackBar with an "Undo" action
    undo_snackbar = SnackBar(
        content=Text("Email has been deleted."),
        action=SnackBarAction(
            label=Text("UNDO"),
            onPressed=handle_undo_action
        ),
        duration=5000 # Show for 5 seconds
    )

    # To show it (conceptual example):
    # scaffoldState.showSnackBar(simple_snackbar)
    ```

    **Key parameters:**
    - **content**: The main message to display, usually a `Text` widget. Required.
    - **action**: An optional `SnackBarAction` widget to display a button.
    - **duration**: The time in milliseconds that the `SnackBar` will be visible before
      it automatically disappears. Defaults to 4000 (4 seconds).
    - **backgroundColor**: The background color of the `SnackBar` container. Material Design
      recommends a dark, high-contrast color (Inverse Surface).
    - **textColor**: The color of the main content text. Material Design recommends a light
      color that is readable on the dark background (Inverse On Surface).
    - **shapeRadius**: The roundness of the corners.
    - **elevation**: The z-axis elevation, which controls the shadow's prominence.
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



# =============================================================================
# CENTER WIDGET - The "Perfect Centering Machine" for Layout Alignment
# =============================================================================

class Center(Widget):
    """
    The "perfect centering machine" that puts its child widget exactly in the middle!
    
    **What is Center?**
    Think of Center as a "bullseye target" that always places its child widget
    at the exact center - both horizontally and vertically. It's like having
    a magnetic center point that pulls your content to the middle.
    
    **Real-world analogy:**
    Center is like the centering mechanism on a pottery wheel:
    - No matter what shape or size your clay (child widget), it centers it perfectly
    - Works both horizontally (left-right) and vertically (up-down)
    - Takes up the full available space to have room to center within
    - The centered item stays in the middle even if the wheel (container) changes size
    
    **When to use Center:**
    - Loading screens with spinners in the middle
    - Welcome messages or logos
    - Empty state illustrations
    - Modal dialog content
    - Any content that should be perfectly centered
    
    **Common use cases:**
    - App splash screens
    - "No data" placeholder screens
    - Centered buttons or call-to-action elements
    - Profile pictures in circular containers
    - Error messages and status displays
    
    **Examples:**
    ```python
    # Simple centered text
    Center(
        child=Text("Welcome to MyApp!")
    )
    
    # Centered loading spinner
    Center(
        child=CircularProgressIndicator()
    )
    
    # Centered login form
    Center(
        child=Container(
            width=300,
            padding=EdgeInsets.all(24),
            child=Column(children=[
                Text("Sign In"),
                TextField("Username"),
                TextField("Password"),
                ElevatedButton(child=Text("Login"), onPressed=login)
            ])
        )
    )
    
    # Centered icon with message
    Center(
        child=Column(
            mainAxisSize=MainAxisSize.MIN,  # Don't take full height
            children=[
                Icon(Icons.check_circle, size=64, color="green"),
                SizedBox(height=16),
                Text("Success!")
            ]
        )
    )
    ```
    
    **Key parameters:**
    - **child**: The widget to center (required)
    
    **How it works:**
    Center uses CSS Flexbox to achieve perfect centering:
    - Sets `justify-content: center` (horizontal centering)
    - Sets `align-items: center` (vertical centering)
    - Takes up full available width and height to center within
    
    **Center vs other alignment widgets:**
    - **Center**: Perfect center alignment (both horizontal and vertical)
    - **Align**: More flexible positioning (top-left, bottom-right, etc.)
    - **Padding**: Adds space around content but doesn't center
    - **Container with alignment**: Can center within a specific sized container
    
    **Layout tips:**
    1. **Content size**: Use `MainAxisSize.MIN` in Column/Row children to prevent them from taking full space
    2. **Nested centering**: You can put Center inside other layout widgets
    3. **Responsive**: Center automatically adjusts when screen size changes
    4. **Multiple items**: To center multiple items, wrap them in Column or Row first
    
    **Perfect for:**
    - Landing pages and welcome screens
    - Loading states and progress indicators
    - Empty states and placeholder content
    - Modal dialogs and popups
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



# =============================================================================
# PLACEHOLDER - A Visual "To-Do" Note for Your UI Layout
# =============================================================================
class Placeholder(Widget):
    """
    A widget that draws a simple box with a dashed border, useful for indicating
    where content will eventually be placed during development. It can also be used
    to conditionally display a child widget.

    **What is Placeholder?**
    The `Placeholder` widget is a visual tool for developers. It acts as a temporary
    stand-in for a widget that you haven't built yet or for content that will be loaded
    dynamically. It helps you visualize your UI layout and structure before all the
    final components are ready.

    **Real-world analogy:**
    It's like using a sticky note or drawing a box on a whiteboard to block out space for a
    photo or a chart in a presentation you're designing. It says, "Something important will
    go here," allowing you to build the rest of the layout around it.

    **When to use Placeholder:**
    - **During development**: To block out sections of your UI for widgets you plan to build later.
    - **Dynamic Content**: As a temporary display while waiting for data to load from a network request.
    - **Conditional UI**: To show a placeholder when a certain condition is not met (e.g., "Add an item to see your list").
    - **Layout Debugging**: To quickly fill space and understand how your layout widgets (like `Row`, `Column`, `Flex`) are distributing space.

    **Two Modes of Operation:**
    1.  **Placeholder Mode (no child)**: If you don't provide a `child` widget, it will render a dashed box with specified dimensions and optional text.
    2.  **Pass-through Mode (with child)**: If you provide a `child` widget, the `Placeholder` simply renders the child, acting as a transparent wrapper. This is useful for easily swapping between a real widget and a placeholder.

    **Examples:**
    ```python
    # 1. A simple 200x150 placeholder box for a future image gallery
    Placeholder(
        width=200,
        height=150,
        fallbackText="Image Gallery"
    )

    # 2. Using Placeholder while data is loading
    def build(self):
        if self.state.is_loading:
            return Placeholder(height=300, fallbackText="Loading user profile...")
        else:
            return UserProfileCard(user=self.state.user)

    # 3. Using the pass-through mode
    # This will just render the Text widget, not the placeholder box.
    Placeholder(
        child=Text("This is a real widget.")
    )
    ```

    **Key parameters:**
    - **child**: An optional `Widget` to display. If provided, the placeholder box itself is not rendered.
    - **width**, **height**: The dimensions of the placeholder box.
    - **color**: The color of the dashed border and the fallback text.
    - **strokeWidth**: The thickness of the dashed border.
    - **fallbackText**: The text to display inside the placeholder box.
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


# =============================================================================
# PADDING - A Simple Way to Add Space Around a Widget
# =============================================================================
class Padding(Widget):
    """
    A widget that insets its child by a given amount of padding, creating empty
    space around it.

    **What is Padding?**
    `Padding` is a simple but essential layout widget. It wraps another widget (`child`)
    and adds a specified amount of empty space on its top, right, bottom, and/or left
    sides. It doesn't have any visual appearance itself; it only affects the position
    and layout of its child.

    **Real-world analogy:**
    It's like the matting in a picture frame. The matting creates a blank space between
    the photo (`child`) and the frame's edge, giving the photo breathing room and making
    the composition look better. The matting itself isn't the main content, but it's
    crucial for the overall presentation.

    **When to use Padding:**
    - To create space between a widget and its parent's borders.
    - To add space between adjacent widgets in a `Row` or `Column`.
    - To create consistent spacing throughout your app's UI.

    **Examples:**
    ```python
    # 1. Add 16 pixels of padding on all sides of a Text widget
    Padding(
        padding=EdgeInsets.all(16),
        child=Text("This text has breathing room.")
    )

    # 2. Add different padding on the horizontal and vertical sides
    Padding(
        padding=EdgeInsets.symmetric(horizontal=24, vertical=12),
        child=Button(label=Text("Padded Button"))
    )

    # 3. Add padding only to the top
    Padding(
        padding=EdgeInsets.only(top=32),
        child=Text("This is pushed down from the top.")
    )
    ```

    **Key parameters:**
    - **padding**: An `EdgeInsets` object that defines the amount of space to add. This is required. `EdgeInsets` provides convenient constructors like `all()`, `symmetric()`, and `only()` to specify the padding values.
    - **child**: The `Widget` to be inset.
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


# =============================================================================
# ALIGN - A Widget to Position a Child Within Itself
# =============================================================================
class Align(Widget):
    """
    A widget that aligns its child within itself. It acts as a parent container
    that positions a single child according to a specified `Alignment`.

    **What is Align?**
    `Align` creates a container and places its `child` at a specific point within that
    container's boundaries. By default, the `Align` widget will try to be as big as
    possible (like a `Container` without explicit dimensions). You can then position
    the child at the `center`, `topLeft`, `bottomRight`, or any other `Alignment` point.

    **Real-world analogy:**
    Think of a large, blank wall as the `Align` widget. You have a single small painting (`child`)
    to hang on it. The `Alignment` object tells you exactly where to put the nail: dead center,
    in the top-left corner, or exactly 25% from the top and 75% from the left.

    **When to use Align:**
    - To position a single child within a larger area.
    - When you need to place a widget in a corner or at the center of its parent.
    - As a simpler alternative to a `Stack` when you only have one child to position.

    **Difference from `Center`:**
    The `Center` widget is just a convenient shorthand for `Align(alignment=Alignment.center)`.
    `Align` is more flexible and allows you to specify any alignment, not just the center.

    **Examples:**
    ```python
    # A 200x200 container with a small box aligned to the bottom right
    Container(
        width=200,
        height=200,
        color=Colors.blue_grey,
        child=Align(
            alignment=Alignment.bottomRight,
            child=Container(width=50, height=50, color=Colors.cyan)
        )
    )

    # Aligning a FloatingActionButton to the top center of its container
    Align(
        alignment=Alignment.topCenter,
        child=FloatingActionButton(child=Icon("add"))
    )

    # Using a fractional alignment (25% from top, 75% from left)
    Align(
        alignment=Alignment(0.25, 0.75),
        child=Text("Custom Position")
    )
    ```

    **Key parameters:**
    - **alignment**: An `Alignment` object that specifies where to position the child. This is required. `Alignment` provides presets like `topLeft`, `center`, `bottomRight`, etc., or you can create a custom fractional alignment.
    - **child**: The `Widget` to be aligned.
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

# =============================================================================
# ASPECT RATIO - The Widget That Enforces a Proportional Shape
# =============================================================================
class AspectRatio(Widget):
    """
    A widget that attempts to size its child to a specific aspect ratio.

    **What is AspectRatio?**
    The `AspectRatio` widget is a simple container that forces its child to have a
    specific proportional shape. The aspect ratio is defined as the ratio of width
    to height (e.g., 16/9 for a widescreen video). The widget will try to find the
    largest possible size for its child within the available constraints while
    maintaining the specified ratio.

    **Real-world analogy:**
    It's like a picture frame designed for a specific photo format, such as a
    widescreen (16:9) frame or a square (1:1) frame for an Instagram photo. No matter
    how you resize the frame itself, the opening inside for the photo always maintains
    its intended shape.

    **When to use AspectRatio:**
    - To display images or videos that must maintain their original proportions.
    - To create square containers for profile pictures or icons.
    - In grid layouts to ensure all grid items have a uniform shape.
    - Any time you need a widget to have a width that is a multiple of its height, or vice versa.

    **Examples:**
    ```python
    # 1. A container for a widescreen video (16:9 ratio)
    AspectRatio(
        aspectRatio=16/9,
        child=Container(
            color=Colors.black,
            child=Center(child=Text("Video Player", style=TextStyle(color=Colors.white)))
        )
    )

    # 2. A perfect square for a profile image
    AspectRatio(
        aspectRatio=1.0,
        child=Image(
            src="profile_pic.jpg",
            fit=BoxFit.COVER # Ensures the image fills the square
        )
    )
    ```

    **Key parameters:**
    - **aspectRatio**: A `float` representing the ratio of width to height. This is required.
    - **child**: The `Widget` to be sized.

    **Layout behavior:**
    - The `AspectRatio` widget first tries to fit its parent's constraints.
    - Then, it determines one dimension (e.g., width) and calculates the other dimension (height) based on the `aspectRatio` to size its child.
    - For example, if it's given an infinite height but a fixed width of 320px, and the `aspectRatio` is 16/9, the child's height will be calculated as 320 / (16/9) = 180px.
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

# =============================================================================
# FITTED BOX - The Widget That Scales and Fits its Child
# =============================================================================
class FittedBox(Widget):
    """
    Scales and positions its child within itself according to a specified fit,
    ensuring the child fits neatly within the available space.

    **What is FittedBox?**
    A `FittedBox` takes a child widget of any size and scales it up or down to fit
    within the `FittedBox`'s own boundaries. You can control how the scaling and
    positioning happens using the `fit` and `alignment` properties.

    **Real-world analogy:**
    It's like the "Scale to Fit" or "Fill Page" options when you print a photo. The
    printer paper is the `FittedBox` and your photo is the `child`. You can choose to:
    - **`BoxFit.contain`**: Shrink the photo so the whole thing is visible, even if it leaves empty space on the paper.
    - **`BoxFit.cover`**: Zoom in on the photo so it completely covers the paper, even if some of the photo gets cropped.
    - **`BoxFit.fill`**: Stretch or squash the photo to match the paper's dimensions exactly, which might distort it.
    - And several other options.

    **When to use FittedBox:**
    - When you have a widget (like an image or a complex `Row` of text) that might be too large for its container, and you want it to shrink gracefully instead of overflowing.
    - To make a child widget expand to fill all available space, potentially cropping it.
    - In responsive layouts where you need content to adapt to different container sizes without breaking the layout.

    **Examples:**
    ```python
    # A 100x100 box where an image is scaled down to be fully visible inside
    Container(
        width=100,
        height=100,
        color=Colors.grey,
        child=FittedBox(
            fit=BoxFit.CONTAIN,
            child=Image(src="a_very_large_image.jpg")
        )
    )

    # A title that will shrink its font size to fit on a single line
    Container(
        width=200,
        height=50,
        child=FittedBox(
            fit=BoxFit.FIT_WIDTH,
            child=Text("This is a very long title that might overflow")
        )
    )
    ```

    **Key parameters:**
    - **child**: The `Widget` to be scaled and positioned.
    - **fit**: A `BoxFit` value that determines how the child is inscribed into the box. Common values are `CONTAIN`, `COVER`, `FILL`, `FIT_WIDTH`, and `FIT_HEIGHT`.
    - **alignment**: An `Alignment` object that controls how the child is positioned within the box if there's any empty space (e.g., when using `BoxFit.contain`).
    - **clipBehavior**: Determines whether to clip the child if it overflows the box's bounds (e.g., when using `BoxFit.cover`).
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

# =============================================================================
# FRACTIONALLY SIZED BOX - The "Percentage-Based" Sizing Widget
# =============================================================================
class FractionallySizedBox(Widget):
    """
    A widget that sizes its child to a fraction of the total available space,
    making it useful for creating responsive, proportional layouts.

    **What is FractionallySizedBox?**
    `FractionallySizedBox` is a layout widget that tells its child to be a certain
    percentage of its parent's width and/or height. It first lets its parent determine
    the available space, and then it calculates its child's size based on the given
    `widthFactor` and `heightFactor`.

    **Real-world analogy:**
    It's like giving instructions on a blueprint: "This window should take up exactly
    50% of the wall's width and 30% of its height." Regardless of whether the final wall
    is large or small, the window will always maintain those proportions relative to it.

    **When to use FractionallySizedBox:**
    - To create responsive UI elements that scale with the screen size.
    - To make a widget occupy a specific percentage of its parent's area.
    - To create proportional columns or rows without using a more complex `Flex` widget.
    - To center a box that is, for example, 80% of the screen's width.

    **Examples:**
    ```python
    # Center a card that takes up 90% of the available width
    FractionallySizedBox(
        widthFactor=0.9,
        child=Card(
            child=Padding(
                padding=EdgeInsets.all(16),
                child=Text("This card scales with the screen width.")
            )
        )
    )

    # Place a banner at the bottom that is 100% of the width and 20% of the height
    Align(
        alignment=Alignment.bottomCenter,
        child=FractionallySizedBox(
            widthFactor=1.0,
            heightFactor=0.2,
            child=Container(
                color=Colors.blue,
                child=Center(child=Text("Banner Ad"))
            )
        )
    )
    ```

    **Key parameters:**
    - **widthFactor**: The fraction (from 0.0 to 1.0 and beyond) of the available width the child should occupy.
    - **heightFactor**: The fraction of the available height the child should occupy.
    - **alignment**: An `Alignment` object that controls how the child is positioned within the full space if the factors are less than 1.0. Defaults to `center`.
    - **child**: The `Widget` to be sized.
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

# =============================================================================
# FLEX - The Master Widget for One-Dimensional Layouts
# =============================================================================
class Flex(Widget):
    """
    A powerful and efficient widget that displays its children in a one-dimensional
    array. This is the underlying engine for `Row` and `Column` and can be used
    directly for more complex or dynamic layouts.

    **What is Flex?**
    `Flex` is a low-level layout primitive that gives you precise control over how a
    series of child widgets are arranged and spaced along a single axis (either
    horizontally or vertically). It's the foundation of modern web and app layout,
    providing a robust system for distributing space and aligning items. The `Row`
    and `Column` widgets are just convenient wrappers around `Flex`.

    **Real-world analogy:**
    Think of arranging books on a bookshelf. `Flex` is the bookshelf itself.
    - **`direction`**: Are you stacking the books side-by-side (`HORIZONTAL`) or on top of each other (`VERTICAL`)?
    - **`mainAxisAlignment`**: After placing the books, are they all pushed to the `start` of the shelf, centered in the `middle`, or spread out `evenly`?
    - **`crossAxisAlignment`**: Are the books all aligned to the `front` edge of the shelf, the `back` edge, or centered in the middle of its depth?

    **When to use Flex (instead of Row/Column):**
    - When you need to programmatically change the layout direction from horizontal to vertical (e.g., for responsive design).
    - When creating a custom layout widget where you want to expose all flexbox properties directly.
    - In most everyday situations, using the more readable `Row` and `Column` widgets is preferred.

    **Examples:**
    ```python
    # A layout that is a Row on wide screens and a Column on narrow screens
    def build(self, context):
        is_wide_screen = context.mediaQuery.size.width > 600
        layout_direction = Axis.HORIZONTAL if is_wide_screen else Axis.VERTICAL

        return Flex(
            direction=layout_direction,
            mainAxisAlignment=MainAxisAlignment.SPACE_AROUND,
            children=[
                Icon(Icons.home),
                Icon(Icons.search),
                Icon(Icons.settings),
            ]
        )
    ```

    **Key parameters:**
    - **children**: A `List` of `Widget`s to display.
    - **direction**: The axis along which the children are placed. `Axis.HORIZONTAL` for a row-like layout, `Axis.VERTICAL` for a column-like layout.
    - **mainAxisAlignment**: How the children should be placed along the main axis (`direction`). Options include `START`, `CENTER`, `END`, `SPACE_BETWEEN`, `SPACE_AROUND`, `SPACE_EVENLY`.
    - **crossAxisAlignment**: How the children should be placed along the axis perpendicular to the `direction`. Options include `START`, `CENTER`, `END`, `STRETCH`.
    - **padding**: Optional `EdgeInsets` to create space around the flex container.
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

# =============================================================================
# WRAP - The Layout for "Line-Breaking" Content
# =============================================================================
class Wrap(Widget):
    """
    A layout widget that arranges its children in horizontal or vertical "runs".
    `Wrap` is similar to a `Row` or `Column` but will automatically wrap its
    children to the next line if there isn't enough space on the current one.

    **What is Wrap?**
    `Wrap` is a flexible layout that prevents its children from overflowing. When a `Row`
    runs out of horizontal space, its content gets clipped or pushes other elements
    out of the way. When a `Wrap` runs out of space, it simply moves the next child
    down to a new line, creating another "run". This is essential for building
    responsive UIs that look good on any screen size.

    **Real-world analogy:**
    It's like writing words on a piece of paper. You write words one after another
    (like items in a `Row`). When you reach the right margin, you don't keep writing
    off the edge of the page; you naturally "wrap" to the beginning of the next line.
    The `Wrap` widget does the same thing for widgets.

    **When to use Wrap:**
    - Displaying a list of tags, chips, or categories.
    - Creating a photo gallery with variable-sized images.
    - Any time you have a variable number of items in a `Row`-like layout and you don't want them to overflow.
    - Building responsive forms or toolbars that reflow on smaller screens.

    **Examples:**
    ```python
    # A collection of user-interest "chips" that will wrap onto multiple lines
    Wrap(
        spacing=8.0,      # Horizontal gap between chips
        runSpacing=4.0,   # Vertical gap between lines of chips
        children=[
            Chip(label=Text("Photography")),
            Chip(label=Text("Travel")),
            Chip(label=Text("Cooking")),
            Chip(label=Text("Technology")),
            Chip(label=Text("Music")),
            Chip(label=Text("Software Development")),
        ]
    )
    ```

    **Key parameters:**
    - **children**: A `List` of `Widget`s to display.
    - **direction**: The primary axis of the runs. `Axis.HORIZONTAL` (default) means children are laid out left-to-right and wrap to new lines vertically.
    - **spacing**: The amount of empty space to place between children along the main axis (e.g., horizontal gap).
    - **runSpacing**: The amount of empty space to place between the runs themselves (e.g., vertical gap).
    - **alignment**: How the children are aligned within a single run (e.g., `MainAxisAlignment.START`).
    - **runAlignment**: How the runs themselves are aligned within the `Wrap` (e.g., `MainAxisAlignment.CENTER`).
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

# =============================================================================
# DIALOG - The Modal Pop-up for Critical Information and Actions
# =============================================================================
class Dialog(Widget):
    """
    A Material Design dialog that appears over the main application content,
    requiring user interaction. It's used to present critical information or
    ask for a decision.

    **What is Dialog?**
    A dialog is a modal window that interrupts the user's workflow to deliver
    important information or request a choice. When a dialog is active, the
    background content is typically obscured by a scrim (a dark overlay),
    preventing interaction until the dialog is dismissed.

    **Real-world analogy:**
    It's like a bank teller asking you, "Are you sure you want to withdraw this amount?"
    before completing a transaction. They stop the normal process, present you with a
    clear choice, and wait for your explicit confirmation ("Yes" or "No") before
    proceeding. You cannot continue with anything else until you've answered.

    **When to use Dialog:**
    - **Confirmation:** Ask users to confirm a significant action (e.g., "Delete item?", "Discard draft?").
    - **Alerts:** Inform users about a critical situation that requires acknowledgement (e.g., "Connection Lost").
    - **Choices:** Present a set of simple, related options that the user must choose from.
    - **Simple Forms:** Gather a small amount of information, like a username and password.

    **Usage Pattern (External State Control):**
    The visibility of a `Dialog` is not controlled by an internal property. Instead, its parent `StatefulWidget` manages its visibility.
    1.  A state variable (e.g., `_show_dialog = False`) determines if the dialog should be in the widget tree.
    2.  An event (like a button press) calls `setState` to set `_show_dialog = True`, causing the dialog to be built and appear.
    3.  An action button *inside* the dialog (e.g., "OK" or "Cancel") calls a method that uses `setState` to set `_show_dialog = False`, dismissing it.

    **Examples:**
    ```python
    # This is a conceptual example of how a stateful parent would manage the dialog.

    class MyScreenState(State):
        def __init__(self):
            super().__init__()
            self._show_confirm_dialog = False

        def _show_dialog(self):
            self.setState({"_show_confirm_dialog": True})

        def _hide_dialog(self):
            self.setState({"_show_confirm_dialog": False})

        def build(self):
            dialog = Dialog(
                title=Text("Confirm Deletion"),
                content=Text("Are you sure you want to delete this file? This action cannot be undone."),
                actions=[
                    TextButton(label=Text("CANCEL"), onPressed=self._hide_dialog),
                    Button(label=Text("DELETE"), onPressed=self._delete_file_and_hide_dialog),
                ]
            )

            return Stack(
                children=[
                    # Main screen content
                    Scaffold(body=Button(label=Text("Delete File"), onPressed=self._show_dialog)),
                    # Conditionally render the dialog on top
                    dialog if self._show_confirm_dialog else Container(),
                ]
            )
    ```

    **Key parameters:**
    - **title**: The `Widget` (usually `Text`) displayed at the top of the dialog.
    - **content**: The main body of the dialog, providing more detail.
    - **actions**: A `List` of `Widget`s (usually `Button`s or `TextButton`s) displayed at the bottom, allowing the user to respond.
    - **icon**: An optional `Icon` widget displayed above the title.
    - **backgroundColor**: The color of the dialog's surface.
    - **shape**: The `BorderRadius` of the dialog's corners.
    - **barrierColor**: The color of the scrim that overlays the background content.
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





# =============================================================================
# CLIP PATH - The Widget for Creating Custom, Responsive Shapes
# =============================================================================
class ClipPath(Widget):
    """
    A widget that clips its child to a custom, non-rectangular shape. The shape
    is defined by a list of points on a "design canvas" (`viewBox`) and is made
    fully responsive by a client-side engine.

    **What is ClipPath?**
    `ClipPath` is a powerful decorative widget that allows you to break free from
    rectangular layouts. You define a polygon shape, and this widget will use that
    shape to "cut out" its child, hiding any parts of the child that fall outside
    the shape. The key feature is its responsiveness: the custom shape automatically
    scales and adapts to the widget's size.

    **Real-world analogy:**
    It's like a magical, resizing cookie cutter. You design the cutter's shape once
    (the `points` on the `viewBox`). Then you can use it on any size sheet of dough
    (the `child` widget), and the cutter will automatically scale itself to create a
    proportionally correct shape every time.

    **When to use ClipPath:**
    - To create hero banners with angled or curved edges.
    - For uniquely shaped containers, buttons, or image holders (e.g., hexagons, chevrons, speech bubbles).
    - To add dynamic and visually interesting decorative elements to your background.
    - For creating complex overlapping UI with non-rectangular boundaries.

    **Key Concepts:**
    - **`viewBox`**: This is your "design canvas" or "blueprint" size (e.g., 100x100).
    - **`points`**: This is a list of `(x, y)` coordinates on your `viewBox` canvas that define the vertices of your polygon shape. For example, `(0, 0)` is the top-left corner and `(100, 50)` is the middle-right edge of a 100x100 viewBox.
    - The client-side engine takes these blueprint coordinates and calculates a responsive SVG `clip-path` for the final rendered widget.

    **Examples:**
    ```python
    # Creating a downward-pointing chevron shape clipping an image
    ClipPath(
        # The design canvas is 100 units wide and 50 units high
        viewBox=(100, 50),
        # Points defining the chevron shape on the canvas
        points=[(0, 0), (50, 50), (100, 0)],
        # Apply a corner radius to smooth the points
        radius=5,
        child=Image(
            src="landscape.jpg",
            fit=BoxFit.COVER
        )
    )
    ```

    **Key parameters:**
    - **child**: The `Widget` to be clipped. This is required.
    - **points**: A `List` of `(x, y)` tuples defining the vertices of your clipping shape.
    - **viewBox**: A `(width, height)` tuple defining the coordinate system for your `points`.
    - **radius**: A `float` value to create rounded corners on the clipping path.
    - **width**, **height**, **aspectRatio**: Standard sizing properties that control the size of the `ClipPath` container itself.
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



# =============================================================================
# LIST TILE - The Building Block of Lists
# =============================================================================
class ListTile(Widget):
    """
    A single fixed-height row that conforms to Material Design list item specs.
    It's a versatile and fundamental widget for creating structured list entries
    with optional leading and trailing icons or widgets.

    **What is ListTile?**
    `ListTile` is a highly structured and opinionated widget that provides a
    pre-defined layout for a row in a list. It has designated "slots" for
    a `leading` widget (like an icon or avatar), a `title`, a `subtitle`, and a
    `trailing` widget (like another icon or a switch). This structure ensures
    consistency and adheres to Material Design guidelines.

    **Real-world analogy:**
    It's like an entry in a modern phone's contact list. Each entry has a
    consistent structure:
    - A contact photo on the left (`leading`).
    - The person's name (`title`).
    - Their phone number or email below the name (`subtitle`).
    - A call or message icon on the right (`trailing`).
    `ListTile` provides the blueprint for creating such structured rows.

    **When to use ListTile:**
    - As the primary child of a `ListView` for displaying rows of data.
    - To create items in a `Drawer` for navigation.
    - For building rows in a settings menu (e.g., an icon, setting name, and a `Switch`).
    - Any time you need a standardized, single-line list item with optional icons.

    **Examples:**
    ```python
    # 1. A simple ListTile used for navigation
    ListView(
        children=[
            ListTile(
                leading=Icon("inbox"),
                title=Text("Inbox"),
                onTap=lambda: navigate_to("inbox")
            ),
            ListTile(
                leading=Icon("send"),
                title=Text("Sent"),
                onTap=lambda: navigate_to("sent")
            )
        ]
    )

    # 2. A more complex ListTile with all slots filled
    ListTile(
        leading=CircleAvatar(child=Text("A")),
        title=Text("Alice"),
        subtitle=Text("alice@example.com"),
        trailing=Icon("phone"),
        selected=True, # Highlight this tile
        onTap=start_call
    )

    # 3. A ListTile for a setting with a Switch
    ListTile(
        title=Text("Enable Notifications"),
        trailing=Switch(value=is_notifications_enabled, onChanged=toggle_notifications),
        onTap=toggle_notifications # Allow tapping the whole row
    )
    ```

    **Key parameters:**
    - **leading**: The widget to display at the beginning of the tile (left side).
    - **title**: The primary content, typically `Text`.
    - **subtitle**: Additional content displayed below the title, typically `Text`.
    - **trailing**: The widget to display at the end of the tile (right side).
    - **onTap**: The callback function to execute when the tile is tapped.
    - **selected**: (bool) If `True`, the tile is rendered with a highlighted background to indicate it's selected.
    - **enabled**: (bool) If `False`, the tile is visually de-emphasized and will not respond to taps.
    - **dense**: (bool) If `True`, renders a more compact version of the tile with less vertical height.

    **Layout and Styling:**
    `ListTile` uses a CSS Grid layout internally to position its `leading`, `title`, `subtitle`,
    and `trailing` children. State changes (like `selected` or `disabled`) are handled by
    dynamically adding CSS classes, allowing for efficient and clean styling.
    """
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
        selected_class = 'selected' if self.selected else ''
        disabled_class = 'disabled' if not self.enabled else ''
        self.current_css_class = f"{self.css_class} {selected_class} {disabled_class}".strip()
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



# =============================================================================
# SLIDER - The Control for Selecting a Value from a Range
# =============================================================================
class Slider(Widget):
    """
    A Material Design slider that allows a user to select a value from a
    continuous or discrete range by dragging a thumb along a track.

    **What is Slider?**
    A `Slider` is an interactive component that represents a range of values. Users
    can drag the slider's "thumb" to select a specific value. It can be continuous,
    allowing selection of any value in the range, or discrete (using `divisions`),
    snapping the thumb to predefined steps.

    **Real-world analogy:**
    It's like the volume control on a stereo, the brightness setting on your screen,
    or a fader on a professional audio mixing board. It provides an intuitive, visual
    way to adjust a value between a minimum and maximum limit.

    **When to use Slider:**
    - For settings that reflect a range of intensities, such as volume, brightness, or color saturation.
    - To select a value where the relative position is more important than the exact number (e.g., font size).
    - In filters to define a range of values (e.g., price, distance).
    - For scrubbing through media playback like a video or audio track.

    **State Management Pattern (Controller):**
    The `Slider` is a "controlled component," meaning it does not manage its own value.
    Its parent `StatefulWidget` is responsible for its state.
    1.  Create a `SliderController` in the parent state and hold onto it.
    2.  Pass this `controller` to the `Slider` widget.
    3.  Use the `onChanged` callback to receive updates from the slider as the user drags it.
    4.  Inside `onChanged`, call `setState` in the parent to update the application's state, which in turn will update the `SliderController`'s value, causing the UI to reflect the change.

    **Examples:**
    ```python
    # Inside a StatefulWidget's State class
    class _MySettingsPageState(State):
        def __init__(self):
            super().__init__()
            # 1. Create and hold the controller
            self.volume_controller = SliderController(value=0.5)

        # 3. Define the callback
        def on_volume_changed(self, new_value):
            # 4. Update the state
            self.setState({}) # Rebuild to reflect the new value
            self.volume_controller.value = new_value
            print(f"New volume: {new_value}")

        def build(self):
            return Column(children=[
                Text(f"Volume: {self.volume_controller.value:.2f}"),
                # A continuous slider
                Slider(
                    key=Key("volume_slider"),
                    controller=self.volume_controller, # 2. Pass the controller
                    onChanged=self.on_volume_changed,
                    min=0.0,
                    max=1.0
                ),
                # A discrete slider for star ratings (0 to 5)
                Slider(
                    key=Key("rating_slider"),
                    controller=self.rating_controller,
                    onChanged=self.on_rating_changed,
                    min=0,
                    max=5,
                    divisions=5 # Creates 5 steps
                )
            ])
    ```

    **Key parameters:**
    - **key**: A **required** `Key` for this stateful widget.
    - **controller**: A **required** `SliderController` instance that holds the current value of the slider.
    - **onChanged**: A callback function that fires continuously as the thumb is dragged, providing the new value.
    - **onChangeEnd**: A callback that fires only when the user releases the thumb.
    - **min**, **max**: The minimum and maximum values of the slider's range.
    - **divisions**: If set to an integer, the slider becomes discrete, snapping to a number of evenly spaced intervals.
    - **theme**: A `SliderTheme` object for comprehensive styling of the track, thumb, and overlay.
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
        print(f'HANDLE DRAG TRIGGERD WITH VALUE: {new_value}')
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



# =============================================================================
# CHECKBOX WIDGET - The "Toggle Choice Box" for Binary Options
# =============================================================================

class Checkbox(Widget):
    """
    The "digital checkbox" for yes/no, on/off, true/false choices - like checking items off a list!
    
    **What is Checkbox?**
    Think of Checkbox as a "digital version" of the checkboxes you see on forms and surveys.
    Users can click it to toggle between checked (☑) and unchecked (☐) states.
    It's perfect for binary choices, options, and settings.
    
    **Real-world analogy:**
    Checkbox is like the checkboxes on a restaurant order form:
    - Each item can be either selected or not selected
    - You can see at a glance what's been chosen (checkmark appears)
    - Clicking toggles between checked and unchecked
    - Each checkbox is independent (unlike radio buttons)
    - Used for "yes/no" type questions
    
    **When to use Checkbox:**
    - Settings that can be enabled/disabled
    - Features users can opt in/out of
    - Terms and conditions acceptance
    - Multi-select options (user can pick several)
    - Todo list items that can be marked complete
    
    **When NOT to use Checkbox:**
    - Single choice from multiple options (use RadioButton instead)
    - Actions that happen immediately (use Switch instead)
    - Navigation choices (use buttons or links)
    
    **Examples:**
    ```python
    # Simple settings checkbox
    notifications_enabled = True
    Checkbox(
        key=Key("notifications"),
        value=notifications_enabled,
        onChanged=lambda new_value: set_notifications(new_value)
    )
    
    # Checkbox with custom colors
    Checkbox(
        key=Key("terms_accepted"),
        value=terms_accepted,
        activeColor="green",     # Color when checked
        checkColor="white",     # Color of the checkmark
        inactiveColor="gray",   # Color when unchecked
        onChanged=lambda value: accept_terms(value)
    )
    
    # Checkbox in a list of options
    Column(children=[
        Text("Select your preferences:"),
        Checkbox(
            key=Key("email_updates"),
            value=email_updates,
            onChanged=toggle_email_updates
        ),
        Text("Email updates"),
        Checkbox(
            key=Key("push_notifications"), 
            value=push_notifications,
            onChanged=toggle_push_notifications
        ),
        Text("Push notifications")
    ])
    
    # Todo list checkbox
    CheckboxListTile(
        title=Text("Buy groceries"),
        value=task.completed,
        onChanged=lambda completed: mark_task_complete(task.id, completed)
    )
    ```
    
    **Key parameters:**
    - **key**: REQUIRED! Unique identifier for the checkbox
    - **value**: Current state (True = checked, False = unchecked)
    - **onChanged**: Function called when user clicks (gets the new value)
    - **activeColor**: Color when checked (default: theme primary color)
    - **checkColor**: Color of the checkmark symbol (default: white)
    - **inactiveColor**: Color when unchecked (default: gray)
    
    **State management pattern:**
    Checkbox follows the "controlled component" pattern:
    ```python
    # Your app manages the state
    is_enabled = False
    
    def toggle_setting(new_value):
        global is_enabled
        is_enabled = new_value
        # Update your app state here
    
    # Checkbox displays the state and notifies you of changes
    Checkbox(
        key=Key("setting"),
        value=is_enabled,      # Current state
        onChanged=toggle_setting  # Called when clicked
    )
    ```
    
    **Checkbox vs Switch vs RadioButton:**
    - **Checkbox**: Independent yes/no choices (can select multiple)
    - **Switch**: Immediate on/off actions (like toggling WiFi)
    - **RadioButton**: One choice from many options (mutually exclusive)
    
    **Accessibility tip:**
    Always pair checkboxes with descriptive labels or wrap them in
    CheckboxListTile for better usability!
    
    **Material Design:**
    This checkbox follows Material Design 3 guidelines with proper
    animations, ripple effects, and theming support.
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

# =============================================================================
# SWITCH WIDGET - The "Digital Toggle Switch" for Instant On/Off Actions
# =============================================================================

class Switch(Widget):
    """
    The "digital light switch" for instant on/off actions - like flipping a real switch!
    
    **What is Switch?**
    Think of Switch as a "digital version" of a physical light switch or power button.
    It toggles between ON and OFF states with a sliding animation, providing immediate
    feedback for actions that take effect instantly.
    
    **Real-world analogy:**
    Switch is like the light switches in your home:
    - Flip it one way = ON (lights turn on immediately)
    - Flip it the other way = OFF (lights turn off immediately)
    - The position clearly shows the current state
    - The action happens instantly when you flip it
    - Has a satisfying physical movement (sliding animation)
    
    **When to use Switch:**
    - Settings that take effect immediately (WiFi on/off, Dark mode, etc.)
    - Features that users want to enable/disable quickly
    - System controls (Bluetooth, Location, Notifications)
    - Preferences that apply right away
    - Any on/off action where users expect instant results
    
    **When NOT to use Switch:**
    - Choices that need confirmation (use Checkbox instead)
    - Actions that require saving (use Checkbox + Save button)
    - Multiple related options (use Checkbox group)
    - Navigation choices (use buttons or links)
    
    **Switch vs Checkbox:**
    - **Switch**: Immediate actions ("Turn on WiFi now")
    - **Checkbox**: Selections for later ("Include WiFi in backup")
    
    **Examples:**
    ```python
    # WiFi toggle switch
    wifi_enabled = True
    Switch(
        key=Key("wifi_switch"),
        value=wifi_enabled,
        onChanged=lambda enabled: toggle_wifi(enabled)
    )
    
    # Dark mode switch with custom colors
    Switch(
        key=Key("dark_mode"),
        value=is_dark_mode,
        activeColor="purple",      # Track color when ON
        thumbColor="white",       # Thumb (slider) color
        onChanged=lambda enabled: set_dark_mode(enabled)
    )
    
    # Notification switch in settings
    ListTile(
        leading=Icon(Icons.notifications),
        title=Text("Push Notifications"),
        trailing=Switch(
            key=Key("notifications"),
            value=notifications_enabled,
            onChanged=lambda enabled: {
                set_notifications(enabled),
                show_toast("Notifications " + ("enabled" if enabled else "disabled"))
            }
        )
    )
    
    # Settings group with multiple switches
    Column(children=[
        Text("Privacy Settings"),
        SwitchListTile(
            title="Location Services",
            value=location_enabled,
            onChanged=toggle_location
        ),
        SwitchListTile(
            title="Analytics",
            value=analytics_enabled, 
            onChanged=toggle_analytics
        ),
        SwitchListTile(
            title="Crash Reporting",
            value=crash_reporting_enabled,
            onChanged=toggle_crash_reporting
        )
    ])
    ```
    
    **Key parameters:**
    - **key**: REQUIRED! Unique identifier for the switch
    - **value**: Current state (True = ON, False = OFF)
    - **onChanged**: Function called when user toggles (gets the new value)
    - **activeColor**: Color of the track when ON (default: theme primary)
    - **thumbColor**: Color of the sliding thumb/knob
    
    **State management pattern:**
    Switch follows the "controlled component" pattern:
    ```python
    # Your app manages the state
    is_enabled = False
    
    def handle_toggle(new_state):
        global is_enabled
        is_enabled = new_state
        # Apply the change immediately
        apply_setting(new_state)
    
    # Switch shows current state and handles changes
    Switch(
        key=Key("setting"),
        value=is_enabled,        # What to display
        onChanged=handle_toggle  # What to do when toggled
    )
    ```
    
    **Animation and feedback:**
    Switch provides visual feedback with:
    - Smooth sliding animation between states
    - Color changes (track and thumb)
    - Haptic feedback on supported devices
    - Clear visual state indication
    
    **Accessibility:**
    - Screen readers announce "Switch, on" or "Switch, off"
    - Can be activated with keyboard (Space or Enter)
    - High contrast support for visibility
    - Proper touch target size for easy tapping
    
    **Material Design compliance:**
    Follows Material Design 3 guidelines with proper colors, animations,
    and interaction patterns for consistency across your app.
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



# =============================================================================
# RADIO - The "Select One" Button
# =============================================================================
class Radio(Widget):
    """
    A Material Design radio button, used to select one exclusive option from a set.

    **What is a Radio button?**
    Radio buttons are used when a user must select exactly one choice from a list of
    mutually exclusive options. Tapping on an unselected radio button selects it, and
    simultaneously deselects any other radio button in the same group that was
-   previously selected.

    **Real-world analogy:**
    It's like the buttons on an old car radio for selecting a station preset.
    Pressing one button (e.g., "Preset 1") automatically un-presses any other
    preset button that was active. You can only listen to one station at a time.

    **State Management Pattern (Group Value):**
    The state of a `Radio` button is "controlled" by its parent `StatefulWidget`.
    1.  The parent state holds the currently selected value for the entire group
        (e.g., `self.selected_option = "Option A"`). This is the `groupValue`.
    2.  Each `Radio` widget in the group is created with its own unique `value`
        (e.g., `"Option A"`, `"Option B"`).
    3.  Each `Radio` compares its own `value` to the `groupValue` from the parent.
        If they match, it displays as selected.
    4.  An `onChanged` callback is provided to all radio buttons. When a user taps
        a radio button, it calls `onChanged` with its own unique `value`.
    5.  The parent's `onChanged` handler then calls `setState`, updating the `groupValue`
        to the new value, which causes the UI to rebuild and reflect the new selection.

    **Examples:**
    ```python
    # Inside a StatefulWidget's State class
    class MyFormState(State):
        def __init__(self):
            super().__init__()
            # 1. Hold the group's selected value in the parent state
            self.delivery_option = "standard"

        # 4. Define the callback
        def on_option_changed(self, new_value):
            # 5. Update the state
            self.setState({"delivery_option": new_value})

        def build(self):
            return Column(
                children=[
                    Text("Select Delivery Option:"),
                    ListTile(
                        title=Text("Standard (5-7 days)"),
                        leading=Radio(
                            key=Key("radio_standard"),
                            value="standard", # 2. This radio's unique value
                            groupValue=self.delivery_option, # 3. Compare with group value
                            onChanged=self.on_option_changed
                        ),
                        onTap=lambda: self.on_option_changed("standard")
                    ),
                    ListTile(
                        title=Text("Express (1-2 days)"),
                        leading=Radio(
                            key=Key("radio_express"),
                            value="express",
                            groupValue=self.delivery_option,
                            onChanged=self.on_option_changed
                        ),
                        onTap=lambda: self.on_option_changed("express")
                    ),
                ]
            )
    ```

    **Key parameters:**
    - **key**: A **required**, unique `Key` for the radio button.
    - **value**: The unique value that this specific radio button represents. When this radio is selected, the `groupValue` will become this `value`.
    - **groupValue**: The currently selected value for the entire group of radio buttons.
    - **onChanged**: A callback function that is invoked with the radio's `value` when it is tapped.
    - **theme**: An optional `RadioTheme` to customize the colors and appearance.
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

# =============================================================================
# DROPDOWN - The Classic "Select from a List" Control
# =============================================================================
class Dropdown(Widget):
    """
    A Material Design dropdown button that displays a list of choices when tapped,
    allowing the user to select one.

    **What is a Dropdown?**
    A `Dropdown` (also known as a select or spinner) is a compact button that, when
    tapped, reveals a menu of options. It displays the currently selected option or a
    `hintText` if nothing is selected. It's an essential form element for choosing
    from a moderate number of items.

    **Real-world analogy:**
    It's like a drop-down menu on a website, such as a country selector in a shipping
    form. You see the current choice (e.g., "United States"), and clicking it reveals a
    scrollable list of all other available countries to choose from.

    **State Management Pattern (Controller):**
    Like the `Slider`, the `Dropdown` is a "controlled component."
    1.  Create and hold a `DropdownController` in the parent `StatefulWidget`'s state. This controller stores the `selectedValue`.
    2.  Pass this `controller` to the `Dropdown` widget.
    3.  Provide an `onChanged` callback. When the user selects a new item from the menu, this function is called with the new value.
    4.  In your `onChanged` handler, call `setState` and update the `DropdownController`'s `selectedValue` to reflect the user's choice.

    **Examples:**
    ```python
    # Inside a StatefulWidget's State class
    class MyFormState(State):
        def __init__(self):
            super().__init__()
            # 1. Create and hold the controller. Can be initialized with a value.
            self.category_controller = DropdownController(selectedValue="tech")

        # 3. Define the callback
        def on_category_changed(self, new_value):
            print(f"New category selected: {new_value}")
            # 4. Update the state and controller
            self.category_controller.selectedValue = new_value
            self.setState({})

        def build(self):
            return Dropdown(
                key=Key("category_dropdown"),
                controller=self.category_controller, # 2. Pass the controller
                onChanged=self.on_category_changed,
                hintText="Select a category",
                items=[
                    ("Technology", "tech"), # Tuple of (Display Label, Value)
                    ("Lifestyle", "life"),
                    ("Finance", "fin"),
                ]
            )
    ```

    **Key parameters:**
    - **key**: A **required**, unique `Key` for the dropdown.
    - **controller**: A **required** `DropdownController` that manages the selected value.
    - **items**: A `List` of options to display in the menu. Each item can be a simple `str` (where the label and value are the same) or a `Tuple` of `(label, value)`.
    - **onChanged**: The callback function that is invoked with the new `value` when an item is selected.
    - **hintText**: The placeholder text to display when no value is selected.
    - **theme**: An optional `DropdownTheme` for detailed styling of the button and the menu.
    """
    shared_styles: Dict[Tuple, str] = {}

    def __init__(self,
                 key: Key,
                 controller: DropdownController,
                 items: List[Union[str, Tuple[str, Any]]],
                 onChanged: Callable[[Any], None],
                 hintText: str = "Select an option",
                 dropDirection: Union[VerticalDirection, str] = VerticalDirection.DOWN,
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
        self.dropDirection = dropDirection
        
        # --- Style Properties ---
        self.backgroundColor = self.theme.backgroundColor or backgroundColor
        self.textColor = self.theme.textColor or textColor 
        self.borderColor = self.theme.borderColor or borderColor
        self.borderRadius = self.theme.borderRadius or borderRadius
        self.hoverColor = self.theme.hoverColor or Colors.rgba(0, 0, 0, 0.08)
        self.dropdownHoverColor = self.theme.dropdownHoverColor or Colors.rgba(0, 0, 0, 0.08)
        self.itemHoverColor = self.theme.itemHoverColor or Colors.rgba(103, 80, 164, 0.1)
        self.width = f"{self.theme.width}px" if isinstance(self.theme.width, (int, float)) else f"{self.theme.width}"
        self.dropDownHeight = f"{self.theme.dropDownHeight}px" if isinstance(self.theme.dropDownHeight, (int, float)) else f"{self.theme.dropDownHeight}"
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
        self.style_key = (self.backgroundColor, self.textColor, self.borderColor, self.borderRadius, self.hoverColor, self.dropdownHoverColor,
                            self.itemHoverColor, self.width, self.dropDownHeight, self.borderWidth, self.fontSize, self.padding, self.dropdownColor, 
                            self.dropdownTextColor, self.selectedItemColor, self.selectedItemShape, 
                            self.dropdownMargin, self.itemPadding, self.dropDirection)
        
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
        (bg_color, text_color, border_color, border_radius, hover_color, dropdown_hover_color, item_hover_color, width, drop_down_height, border_width, font_size, padding, dropdown_color, 
                            dropdown_text_color, selected_item_color, selected_item_shape, 
                            dropdown_margin, item_padding, drop_direction) = style_key

        to_top_height = f"-{int(drop_down_height.replace('px', '').replace('%', '').replace('vh', '')) + 50}px"

        return f"""
        .{css_class}.dropdown-container {{
            position: relative;
            width: {width};
            heifht: auto; //TODO
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
            {'transform: rotate(180deg);' if drop_direction.lower() == 'up' else ''}
            transition: transform 0.2s ease-in-out;
        }}
        .{css_class}.open .dropdown-caret {{
            transform: rotate({'180deg' if drop_direction.lower() == 'down' else '0deg'});
        }}
        .{css_class} .dropdown-menu {{
            position: absolute;
            top: 100%;
            left: 0;
            right: 0;
            height: {drop_down_height};
            background-color: {dropdown_color};
            color: {dropdown_text_color};
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
            overflow-y: auto;
        }}
        .{css_class}.open .dropdown-menu {{
            opacity: 1;
            visibility: visible;
            transform: translateY({0 if drop_direction.lower() == 'down' else to_top_height});
        }}
        .{css_class} .dropdown-item {{
            padding: 8px 12px;
            cursor: pointer;
            transition: background-color 0.2s;
        }}
        .{css_class} .dropdown-item:hover {{
            background-color: {item_hover_color}; /* Hover color */
        }}
        .{css_class} .dropdown-value-container:hover {{
            background-color: {hover_color}; /* Hover color */
        }}
        .{css_class} .dropdown-menu:hover {{
            background-color: {dropdown_hover_color}; /* Hover color */
        }}
        """



# =============================================================================
# GESTURE DETECTOR - The "Sense of Touch" for Your Widgets
# =============================================================================
class GestureDetector(Widget):
    """
    An invisible widget that detects gestures made on its child, such as taps,
    drags, and long presses, without providing any visual feedback.

    **What is GestureDetector?**
    `GestureDetector` is a special-purpose widget that wraps your interactive
    components. It doesn't draw anything on the screen; its only job is to listen for
    user input events (like mouse clicks or touch events) on its child widget and
    invoke the appropriate callback functions you provide.

    **Real-world analogy:**
    It's like putting a touch-sensitive layer over a physical object. The object
    itself (`child`) doesn't change, but the layer can now detect when you tap it,
    how long you press it, or if you drag your finger across it, and then it can
    trigger an electronic response.

    **When to use GestureDetector:**
    - To make a non-interactive widget, like a `Container` or `Image`, tappable.
    - To add complex interactions like double-taps or long-presses to a widget.
    - For creating custom draggable elements, like sliders, knobs, or resizable panels.
    - When you need to capture raw pointer events for custom painting or animations.

    **Important Note on `Button`s:**
    You should generally not wrap a `Button` or `FloatingActionButton` with a `GestureDetector`,
    as those widgets have their own built-in gesture detection (`onPressed`). Using a
    `GestureDetector` on them can lead to conflicting behavior. Use it for widgets
    that are not inherently interactive.

    **Examples:**
    ```python
    # 1. Making a Card tappable and double-tappable
    GestureDetector(
        key=Key("interactive_card"),
        onTap=lambda details: print(f"Card tapped at position: {details.localPosition}"),
        onDoubleTap=lambda: print("Card double-tapped!"),
        child=Card(
            child=Padding(padding=EdgeInsets.all(16), child=Text("Tap Me!"))
        )
    )

    # 2. A draggable container
    class DraggableBoxState(State):
        def __init__(self):
            super().__init__()
            self.offset = Offset(0, 0) # Store the position

        def on_pan_update(self, details: PanUpdateDetails):
            # Update the offset by the amount the user dragged
            self.setState({"offset": self.offset + details.delta})

        def build(self):
            return Positioned(
                left=self.offset.dx,
                top=self.offset.dy,
                child=GestureDetector(
                    key=Key("draggable_box"),
                    onPanUpdate=self.on_pan_update,
                    child=Container(width=100, height=100, color=Colors.blue)
                )
            )
    ```

    **Key parameters (Callbacks):**
    - **child**: The `Widget` that will be the target of the gestures.
    - **onTap**: Called when the user completes a brief tap. Provides `TapDetails` with the position.
    - **onDoubleTap**: Called when the user taps the same location twice in quick succession.
    - **onLongPress**: Called when the user holds their finger or mouse down for an extended period.
    - **onPanStart**, **onPanUpdate**, **onPanEnd**: A sequence of callbacks that fire when the user initiates, moves, and releases a drag gesture. `onPanUpdate` provides `PanUpdateDetails` with the delta (change in position).
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


# =============================================================================
# GRADIENT BORDER CONTAINER - The "Animated Glowing Border" Widget
# =============================================================================
class GradientBorderContainer(Widget):
    """
    A decorative widget that wraps its child with an animated, glowing gradient
    border. It intelligently adapts its border radius to match the child's own
    corner rounding.

    **What is GradientBorderContainer?**
    This widget is a pure "eye candy" component. It draws a border around its child
    that is not a solid color, but rather a smooth, multi-color gradient. Furthermore,
    this gradient is animated, typically shifting its colors along the border's path
    to create a subtle, shimmering, or glowing effect.

    **Real-world analogy:**
    It's like framing a picture with a neon sign or a string of color-changing LED
    lights. The frame itself becomes a dynamic, attention-grabbing element that
    enhances the content within.

    **When to use GradientBorderContainer:**
    - To highlight an important or "featured" card in a list.
    - To create a visually appealing, premium-looking button or container.
    - As a decorative frame for user avatars or profile pictures.
    - To draw attention to an element that is currently active or selected.

    **Intelligent Radius Calculation:**
    A key feature of this widget is its ability to automatically detect the
    `borderRadius` of its direct `child` (if it's a `Container` with a `BoxDecoration`).
    It then calculates the correct outer radius for itself to ensure the border
    perfectly and evenly wraps the child, no matter the corner rounding.

    **Examples:**
    ```python
    # A standard Card with an animated gradient border
    GradientBorderContainer(
        key=Key("featured_card"),
        borderWidth=4,
        # A theme can define the gradient colors, speed, etc.
        theme=GradientBorderTheme(
            colors=[Colors.pink, Colors.purple, Colors.cyan],
            direction="to right"
        ),
        child=Card(
            decoration=BoxDecoration(borderRadius=BorderRadius.all(12)),
            child=ListTile(title=Text("Featured Item"))
        )
    )

    # A circular avatar with a glowing border
    GradientBorderContainer(
        key=Key("glowing_avatar"),
        borderWidth=3,
        child=CircleAvatar(
            radius=40,
            child=Text("A")
        )
    )
    ```

    **Key parameters:**
    - **key**: A **required** `Key` for the widget.
    - **child**: The `Widget` to be wrapped with the gradient border. This is required.
    - **borderWidth**: The thickness of the gradient border in pixels.
    - **theme**: A `GradientBorderTheme` object that controls the `colors`, `direction`, `speed`, and animation `timing` of the gradient.
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


# =============================================================================
# GRADIENT CLIP PATH BORDER - The Animated Border for Custom Shapes
# =============================================================================
class GradientClipPathBorder(Widget):
    """
    A sophisticated decorative widget that wraps its child with an animated gradient
    border, where the border's shape is defined by a custom, responsive `ClipPath`.

    **What is GradientClipPathBorder?**
    This widget is the ultimate combination of custom shaping and decorative flair. It
    merges the animated, multi-color border effect of `GradientBorderContainer` with
    the powerful, non-rectangular shaping of `ClipPath`. The result is a child widget
    that appears to be framed by a glowing, animated border that perfectly follows
    any custom polygon shape you define.

    **Real-world analogy:**
    Imagine creating a custom-shaped neon sign (e.g., in the shape of a star or an
    arrow). The unique shape of the glass tubing is the `ClipPath`. The glowing,
    color-shifting gas inside the tube is the animated gradient border. This widget
    allows you to create that precise, custom-shaped "glow" around any other widget.

    **When to use GradientClipPathBorder:**
    - To create highly stylized, "premium" UI elements that need to stand out.
    - For hero banners or containers with angled or curved edges that you want to highlight with an active, glowing border.
    - To create uniquely shaped buttons (like hexagons or chevrons) that have an animated border on hover or when selected.
    - When you want to draw maximum attention to a featured item that is already using a `ClipPath` for its shape.

    **How it Works (Behind the Scenes):**
    This widget uses an advanced layering and clipping technique handled by a JavaScript engine:
    1.  It creates a stack of two layers: a background layer and a content layer for your `child`.
    2.  The background layer is styled with the animated gradient.
    3.  Based on your `points`, `viewBox`, and `borderWidth`, the engine calculates two responsive SVG `clip-path`s.
    4.  The **outer path** is applied to the gradient background layer.
    5.  A slightly smaller, **inset path** is applied to the content layer that hosts your `child`.
    6.  The visual difference between these two stacked, clipped layers is what you see as the perfectly shaped, animated border.

    **Examples:**
    ```python
    # An image inside a hexagonal container with a glowing, animated border.
    GradientClipPathBorder(
        key=Key("hex_avatar_border"),
        # The geometric definition of the hexagon on a 100x100 canvas
        viewBox=(100, 100),
        points=[(50, 0), (100, 25), (100, 75), (50, 100), (0, 75), (0, 25)],
        radius=8, # Smooth the corners of the hexagon
        borderWidth=5,
        theme=GradientBorderTheme(
            colors=[Colors.cyan, Colors.purple, Colors.pink],
            speed="3s"
        ),
        # The child widget that will be clipped and framed
        child=Image(
            src="profile_pic.jpg",
            fit=BoxFit.COVER
        )
    )
    ```

    **Key parameters:**
    - **key**: A **required** `Key` for the widget.
    - **child**: The `Widget` to be framed and clipped. This is required.
    - **points**: A `List` of `(x, y)` tuples defining the vertices of the custom shape on the `viewBox`.
    - **viewBox**: A `(width, height)` tuple that defines the coordinate system or "blueprint" for your `points`.
    - **radius**: A `float` value that creates rounded corners on your custom shape.
    - **borderWidth**: The thickness of the animated gradient border in pixels.
    - **theme**: A `GradientBorderTheme` object that controls the `colors`, `direction`, `speed`, and animation `timing` of the gradient.
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