from pythra import (
    Framework,
    State,
    StatefulWidget,
    Key,
    Widget,
    Icon,
    Container,
    Center,
    Column,
    Row,
    Text,
    ElevatedButton,
    Spacer,
    IconButton,
    SizedBox,
    Colors,
    EdgeInsets,
    MainAxisAlignment,
    CrossAxisAlignment,
    Image,
    AssetImage,
    FloatingActionButton,
    ButtonStyle,
    BoxDecoration,
    BoxShadow,
    Offset,
    BorderRadius,
    ListTile,
    Divider,
    Alignment,
    ClipPath,
    PathCommandWidget,
    MoveTo,
    LineTo,
    ClosePath,
    ArcTo,
    QuadraticCurveTo,
    create_rounded_polygon_path,
    AspectRatio,
    PolygonClipper,
    RoundedPolygon,
    TextField,
    Icons,
    Padding,
    TextStyle,
    TextButton,
    ListView,
    Scrollbar,
    ScrollbarTheme,
    TextEditingController,
    InputDecoration,
    BorderSide,
    GridView,  # <-- ADD THESE IMPORTS
)


from pythra import (
    # ... keep all your existing imports
    Framework, State, StatefulWidget, Key, Widget, Container, Row, Column, Text,
    Icon, Icons, TextButton, ButtonStyle, Colors, EdgeInsets,
    Alignment, BoxDecoration, BorderRadius, MainAxisAlignment, Stack,
    Positioned, Text, EdgeInsets, Alignment, Center,  # <-- Important for the overlay menu
)
from typing import List, Optional, Any, Callable

class Dropdown(StatefulWidget):
    """
    A configurable, self-contained dropdown menu widget.

    This widget displays the currently selected value. When tapped, it presents
    an overlay menu of options using a Stack. The parent widget controls the
    list of items and the current value, and is notified of changes via the
    onChanged callback.
    """
    def __init__(self,
                 key: Key,
                 items: List[Any],
                 value: Any,
                 onChanged: Callable[[Any], None],
                 hint: Optional[Widget] = None,
                 width: float = 300,
                 height: float = 40,
                 itemHeight: float = 40,
                 backgroundColor: str = Colors.surfaceContainer,
                 borderRadius: BorderRadius = BorderRadius.all(8),
                 elevation: float = 2.0, # For the dropdown menu's shadow
                 icon: Widget = Icon(Icons.arrow_drop_down_rounded),
                 ):
        
        super().__init__(key=key)
        
        # --- Configuration passed from the user ---
        self.items = items
        self.value = value
        self.onChanged = onChanged
        self.hint = hint or Text("Select an option")
        
        # --- Styling ---
        self.width = width
        self.height = height
        self.itemHeight = itemHeight
        self.backgroundColor = backgroundColor
        self.borderRadius = borderRadius
        self.elevation = elevation
        self.icon = icon

    def createState(self) -> 'State':
        return _DropdownState()

class _DropdownState(State):
    """Manages the internal state (i.e., open/closed) of the Dropdown."""

    def initState(self):
        self.is_open = False

    def _toggle_dropdown(self):
        """Opens or closes the dropdown menu."""
        self.is_open = not self.is_open
        self.setState()

    def _handle_item_tap(self, selected_item: Any):
        """
        Handles when a user selects an item from the menu.
        """
        widget = self.get_widget()
        
        # 1. Call the user-provided onChanged callback
        if widget.onChanged:
            widget.onChanged(selected_item[0])
            
        # 2. Close the dropdown
        self.is_open = False
        
        # 3. Trigger a rebuild to reflect the closed state
        #    and the new value passed down from the parent.
        self.setState()

    def _build_item(self, item: Any) -> Widget:
        """Helper method to build a single row in the dropdown menu."""
        widget = self.get_widget()
        
        return TextButton(
            key=Key(f"dropdown_item_{item}"),
            onPressed=self._handle_item_tap,
            onPressedArgs=[item],
            style=ButtonStyle(
                padding=EdgeInsets.symmetric(horizontal=16),
                backgroundColor=Colors.transparent
            ),
            child=Container(
                height=widget.itemHeight,
                alignment=Alignment.center_left(),
                child=Text(str(item)) # Display the string representation of the item
            )
        )

    def build(self) -> Widget:
        widget: Dropdown = self.get_widget()

        # Determine what text to show in the main button
        display_content = widget.hint
        if widget.value is not None:
            display_content = Text(str(widget.value), key=Key(f"txt_{str(widget.value)}"))
            print("display content: ", display_content)

        # The main, always-visible dropdown button
        dropdown_button = Container(
            key=Key("dropdown_button_container"),
            width=widget.width,
            height=widget.height,
            decoration=BoxDecoration(
                color=widget.backgroundColor,
                borderRadius=widget.borderRadius,
                boxShadow=[BoxShadow(offset=Offset(0,1), blurRadius=2)] if widget.elevation > 0 else None
            ),
            child=TextButton(
                key=Key("dropdown_button"),
                onPressed=self._toggle_dropdown,
                style=ButtonStyle(padding=EdgeInsets.symmetric(horizontal=16)),
                child=Row(
                    mainAxisAlignment=MainAxisAlignment.SPACE_BETWEEN,
                    children=[
                        display_content,
                        widget.icon,
                    ]
                )
            )
        )

        # The overlay menu, which is only built when the dropdown is open
        dropdown_menu = None
        if self.is_open:
            menu_items = [self._build_item(item) for item in widget.items]
            
            # Use Positioned to place the menu below the button within the Stack
            dropdown_menu = Positioned(
                key=Key("dropdown_menu_positioned"),
                top=widget.height + 4, # Position below the button with a small gap
                left=0,
                child=Container(
                    width=widget.width,
                    decoration=BoxDecoration(
                        color=widget.backgroundColor,
                        borderRadius=widget.borderRadius,
                        boxShadow=[BoxShadow(offset=Offset(0, widget.elevation), blurRadius=widget.elevation * 2)]
                    ),
                    child=Column(children=menu_items)
                )
            )

        # A full-screen, transparent scrim that closes the menu when clicked
        scrim = None
        if self.is_open:
            scrim = Positioned(
                key=Key("dropdown_scrim"),
                top=0, left=0, right=0, bottom=0,
                child=TextButton(
                    onPressed=self._toggle_dropdown,
                    child=Container(width="100vw", height="100vh", color=Colors.transparent)
                )
            )

        # The final build uses a Stack to layer the button, scrim, and menu
        stack_children = [
            dropdown_button,
        ]
        if scrim:
            stack_children.append(scrim)
        if dropdown_menu:
            stack_children.append(dropdown_menu)

        # The Stack itself is wrapped in a Container to give it a defined size
        return Container(
            key=Key("dropdown_stack_wrapper"),
            width=widget.width,
            height=widget.height, # The wrapper's height is just the button's height
            child=Stack(
                key=Key("dropdown_stack"),
                children=stack_children
            )
        )


# In your main application file

# --- Framework Imports ---

# --- Component Imports ---
# Assuming the Dropdown class is in a file named 'dropdown' in this directory
# from dropdown import Dropdown 

# --- Application State ---

class MyAppState(State):
    def initState(self):
        """Initialize the application's state."""
        self.cities = ["Tokyo", "New York", "Paris", "London", "Sydney"]
        self.selected_city = "Paris"  # The initial selected value

    def on_city_changed(self, new_city):
        """Callback for the Dropdown, updates state and triggers a rebuild."""
        print(f"City changed to: {new_city}")
        self.selected_city = new_city
        self.setState()

    def build(self) -> Widget:
        """Build the UI."""
        return Container(
            width="100vw",
            height="100vh",
            color=Colors.background,
            alignment=Alignment.center(),
            child=Column(
                children=[
                    Text(f"Your selected city is: {self.selected_city}"),
                    SizedBox(height=20),
                    
                    # --- Using the new Dropdown widget ---
                    Dropdown(
                        key=Key("city_dropdown"),
                        items=self.cities,
                        value=self.selected_city,
                        onChanged=self.on_city_changed,
                        hint=Text("Please select a city"),
                        width=250,
                    )
                ]
            )
        )

class MyApp(StatefulWidget):
    def createState(self) -> MyAppState:
        return MyAppState()


class MainAppState(State):
    def __init__(self):
        super().__init__()
        self.app = MyApp(key=Key("my_app_root"))

    def build(self):
        return self.app


class MainApp(StatefulWidget):
    def createState(self) -> MainAppState:
        return MainAppState()

# --- Run the Application ---
if __name__ == "__main__":
    app = Framework.instance()
    app.set_root(MainApp(key=Key("my_main_app_root")))
    app.run(title="Reusable Dropdown Test")