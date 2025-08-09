# componetns/home.py

# --- Framework Imports ---
# Make sure to import ClipPath and the clipper base classes
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
import math  # For the StarClipper


class DropDownState(State):
    def __init__(self):
        super().__init__()
        self.visible = False
        self.values = ["Option 1", "Option 2", "Option 3"]
        self.currentOp = self.values[1]

    def openDropDown(self):
        self.visible = not self.visible
        print(self.visible)
        self.setState()

    def changeOp1(self):
        self.currentOp = self.values[0]
        print("Current option: ", self.currentOp)
        self.setState()
        self.openDropDown()

    def changeOp2(self):
        self.currentOp = self.values[1]
        print("Current option: ", self.currentOp)
        self.setState()
        self.openDropDown()

    def changeOp3(self):
        self.currentOp = self.values[2]
        print("Current option: ", self.currentOp)
        self.setState()
        self.openDropDown()

    def build(self):
        return Container(
            key=Key("dro_dow_cont_root"),
            padding=EdgeInsets.all(8),
            height="100vh",
            width="100vw",
            child=Column(
                key=Key("dro_dow_column_root"),
                children=[
                    Container(
                        key=Key("dro_dow_cont"),
                        padding=EdgeInsets.only(left=8),
                        height=30,
                        width=300,
                        child=Center(
                            key=Key("dro_dow_cont_center"),
                            child=Row(
                                key=Key("dro_dow_cont_row"),
                                # crossAxisAlignment=CrossAxisAlignment.CENTER,
                                mainAxisAlignment=MainAxisAlignment.SPACE_BETWEEN,
                                children=[
                                    Text(
                                        self.currentOp,
                                        key=Key("dro_dow_cont_current_txt"),
                                    ),
                                    TextButton(
                                        key=Key("dro_dow_cont_dro_dow_ico_btn"),
                                        child=Icon(
                                            Icons.arrow_drop_down_rounded,
                                            key=Key("dro_dow_cont_dro_dow_ico"),
                                        ),
                                        onPressed=self.openDropDown,
                                        style=ButtonStyle(
                                            backgroundColor=Colors.transparent,
                                        ),
                                    ),
                                ],
                            ),
                        ),
                        decoration=BoxDecoration(
                            color=Colors.lightpink,
                            borderRadius=BorderRadius.all(0),
                        ),
                    ),
                    Container(
                        key=Key("dro_dow_options_continer"),
                        width=300,
                        child=Column(
                            key=Key("dro_dow_options_column"),
                            crossAxisAlignment=CrossAxisAlignment.START,
                            children=[
                                TextButton(
                                    key=Key("dro_dow_option_1_btn"),
                                    child=Container(
                                        key=Key("dro_dow_option_1_cont"),
                                        padding=EdgeInsets.symmetric(horizontal=8),
                                        height=30,
                                        width=300,
                                        child=Center(
                                            key=Key("dro_dow_option_1_center"),
                                            child=Row(
                                                # crossAxisAlignment=CrossAxisAlignment.CENTER,
                                                mainAxisAlignment=MainAxisAlignment.SPACE_BETWEEN,
                                                children=[
                                                    Text(
                                                        self.values[0],
                                                        key=Key("dro_dow_option_1_txt"),
                                                    ),
                                                ],
                                            ),
                                        ),
                                        decoration=BoxDecoration(
                                            color=Colors.lightpink,
                                            borderRadius=BorderRadius.all(8),
                                        ),
                                    ),
                                    onPressed=self.changeOp1,
                                    style=ButtonStyle(
                                        backgroundColor=Colors.transparent,
                                        padding=EdgeInsets.all(0),
                                    ),
                                ),
                                TextButton(
                                    key=Key("dro_dow_option_2_btn"),
                                    child=Container(
                                        key=Key("dro_dow_option_2_cont"),
                                        padding=EdgeInsets.symmetric(horizontal=8),
                                        height=30,
                                        width=300,
                                        child=Center(
                                            key=Key("dro_dow_option_2_center"),
                                            child=Row(
                                                key=Key("dro_dow_option_2_row"),
                                                # crossAxisAlignment=CrossAxisAlignment.CENTER,
                                                mainAxisAlignment=MainAxisAlignment.SPACE_BETWEEN,
                                                children=[
                                                    Text(
                                                        self.values[1],
                                                        key=Key("dro_dow_option_2_txt"),
                                                    ),
                                                ],
                                            ),
                                        ),
                                        decoration=BoxDecoration(
                                            color=Colors.lightpink,
                                            borderRadius=BorderRadius.all(8),
                                        ),
                                    ),
                                    onPressed=self.changeOp2,
                                    style=ButtonStyle(
                                        backgroundColor=Colors.transparent,
                                        padding=EdgeInsets.all(0),
                                    ),
                                ),
                                TextButton(
                                    key=Key("dro_dow_option_3_btn"),
                                    child=Container(
                                        key=Key("dro_dow_option_3_cont"),
                                        padding=EdgeInsets.symmetric(horizontal=8),
                                        height=30,
                                        width=300,
                                        child=Center(
                                            key=Key("dro_dow_option_3_center"),
                                            child=Row(
                                                key=Key("dro_dow_option_3_row"),
                                                # crossAxisAlignment=CrossAxisAlignment.CENTER,
                                                mainAxisAlignment=MainAxisAlignment.SPACE_BETWEEN,
                                                children=[
                                                    Text(
                                                        self.values[2],
                                                        key=Key("dro_dow_option_3_txt"),
                                                    ),
                                                ],
                                            ),
                                        ),
                                        decoration=BoxDecoration(
                                            color=Colors.lightpink,
                                            borderRadius=BorderRadius.all(8),
                                        ),
                                    ),
                                    onPressed=self.changeOp3,
                                    style=ButtonStyle(
                                        backgroundColor=Colors.transparent,
                                        padding=EdgeInsets.all(0),
                                    ),
                                ),
                            ],
                        ),
                        decoration=BoxDecoration(
                            color=Colors.lightpink,
                            borderRadius=BorderRadius.all(0),
                        ),
                        visible=self.visible,
                    ),
                ],
            ),
        )


class DropDown(StatefulWidget):
    def createState(self) -> DropDownState:
        return DropDownState()


class myAppState(State):
    def __init__(self):
        super().__init__()
        self.dropdown = DropDown(key=Key("dro_dow_widget"))

    def build(self):
        return Container(key=Key("dro_dow_widget_root_cont"), child=self.dropdown)


class myApp(StatefulWidget):
    def createState(self) -> myAppState:
        return myAppState()


if __name__ == "__main__":
    app = Framework.instance()
    app.set_root(myApp(key=Key("my_app_root")))
    app.run(title="Dropdown Test")


# components/dropdown.py

from pythra import (
    State,
    StatefulWidget,
    StatelessWidget,
    Key,
    Widget,
    Icon,
    Container,
    Column,
    Row,
    Text,
    TextButton,
    SizedBox,
    Colors,
    EdgeInsets,
    MainAxisAlignment,
    BoxDecoration,
    BorderRadius,
    Alignment,
    Stack,
    Positioned,
    Icons,
    ButtonStyle,
)
from typing import List, Optional, Callable, Any, Generic, TypeVar

# A Generic TypeVar allows us to create strongly-typed Dropdowns
T = TypeVar('T')

class DropdownMenuItem(StatelessWidget, Generic[T]):
    """
    Represents a single item in a Dropdown menu.
    """
    def __init__(self,
                 key: Optional[Key] = None,
                 value: Optional[T] = None,
                 child: Widget = None,
                 onTap: Optional[Callable] = None):
        super().__init__(key=key)
        self.value = value
        self.child = child
        self.onTap = onTap # The parent Dropdown will provide this

    def build(self) -> Widget:
        """Renders the menu item as a clickable button."""
        return TextButton(
            onPressed=self.onTap,
            style=ButtonStyle(
                padding=EdgeInsets.all(0),
                backgroundColor=Colors.transparent
            ),
            child=Container(
                width="100%",
                height=40,
                padding=EdgeInsets.symmetric(horizontal=16),
                alignment=Alignment.center_left(),
                child=self.child
            )
        )

class Dropdown(StatefulWidget, Generic[T]):
    """
    A Material Design-inspired dropdown button that displays a menu of items.
    """
    def __init__(self,
                 key: Key,
                 items: List[DropdownMenuItem[T]],
                 value: Optional[T],
                 onChanged: Callable[[T], None],
                 hint: Optional[Widget] = None,
                 width: float = 300):
        super().__init__(key=key)
        self.items = items
        self.value = value
        self.onChanged = onChanged
        self.hint = hint
        self.width = width

    def createState(self):
        return _DropdownState()

class _DropdownState(State, Generic[T]):
    
    def initState(self):
        self._is_open = False

    def _toggle_dropdown(self):
        self.setState(lambda: setattr(self, '_is_open', not self._is_open))

    def _handle_item_tap(self, new_value: T):
        widget = self.get_widget()
        if widget.value != new_value:
            widget.onChanged(new_value)
        # Always close the dropdown after an item is tapped
        self.setState(lambda: setattr(self, '_is_open', False))

    def build(self) -> Widget:
        widget = self.get_widget()

        # Find the widget to display for the currently selected value.
        selected_item_widget = widget.hint or Text("")
        for item in widget.items:
            if item.value == widget.value:
                selected_item_widget = item.child
                break

        # Build the list of menu items, injecting the onTap handler.
        menu_items = []
        for item in widget.items:
            menu_items.append(
                DropdownMenuItem(
                    key=item.key or Key(str(item.value)),
                    value=item.value,
                    child=item.child,
                    onTap=lambda v=item.value: self._handle_item_tap(v)
                )
            )

        # The core layout using a Stack
        return Container(
            width=widget.width,
            child=Stack(
                children=[
                    # --- Layer 1: The Main Dropdown Button ---
                    TextButton(
                        onPressed=self._toggle_dropdown,
                        style=ButtonStyle(padding=EdgeInsets.all(0)),
                        child=Container(
                            height=40,
                            padding=EdgeInsets.symmetric(horizontal=12),
                            decoration=BoxDecoration(
                                color=Colors.hex("#EADDFF"), # M3 Surface Container
                                borderRadius=BorderRadius.all(4)
                            ),
                            child=Row(
                                mainAxisAlignment=MainAxisAlignment.SPACE_BETWEEN,
                                children=[
                                    selected_item_widget,
                                    Icon(Icons.arrow_drop_down_rounded),
                                ]
                            )
                        )
                    ),
                    
                    # --- Layer 2: The Options Menu (Positioned and Toggled) ---
                    Positioned(
                        top=45, # Position it just below the main button
                        left=0,
                        right=0,
                        child=Container(
                            visible=self._is_open,
                            decoration=BoxDecoration(
                                color=Colors.hex("#F3EDF7"), # M3 Surface Container High
                                borderRadius=BorderRadius.all(4),
                                boxShadow=[BoxShadow(offset=Offset(0, 4), blurRadius=8, color=Colors.rgba(0,0,0,0.1))]
                            ),
                            child=Column(
                                children=menu_items
                            )
                        )
                    )
                ]
            )
        )