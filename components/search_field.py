

# You can create a new file, e.g., components/search_field.py, or add this to main.py
from pythra import (
    Framework,
    State,
    StatefulWidget,
    Key,
    Widget,
    Icon,
    Container,
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
    VirtualListView,
    Axis,  # <-- ADD THESE IMPORTS
)



class SearchComponent(StatefulWidget):
    """A self-contained component for the search text field."""
    def __init__(self, key: Key):
        super().__init__(key=key)

    def createState(self):
        return _SearchComponentState()

class _SearchComponentState(State):
    def __init__(self):
        super().__init__()
        self.search_controller = TextEditingController()
        self.is_field_populated = False
        # The decoration is now part of this component's state
        self.search_field_decoration = InputDecoration(
            hintText="Search",
            fillColor="#363636",
            border=BorderSide(width=1, color=Colors.grey),
            filled=True,
            focusColor=Colors.hex("#FF94DA"),
        )

    def initState(self):
        """Called once when the state is initialized."""
        # It's good practice to add listeners in initState
        self.search_controller.add_listener(self.on_search_updated)

    def on_search_updated(self):
        """Listener that updates the internal state of THIS component."""
        new_value = self.search_controller.text != ""
        # print("New Value: ", self.search_controller.text, " ", new_value)
        if self.is_field_populated != new_value:
            self.is_field_populated = new_value
            # This setState call is now LOCAL. It only rebuilds the SearchComponent.
            self.setState()

    def clear_search(self):
        # print("clearing")
        self.search_controller.clear()
        # self.setState()
        # print("data after clear: ", self.search_controller.text)
        # The listener will automatically handle the state update.

    def search(self):
        print(f"searching for: {self.search_controller.text}")

    def build(self) -> Widget:
        # This build method is tiny and fast!
        return Column(
            key=Key("search_component_root_col"),
            crossAxisAlignment = CrossAxisAlignment.STRETCH,
            children=[
                TextField(
                    key=Key("search_field_input"),
                    controller=self.search_controller,
                    decoration=self.search_field_decoration,
                ),
                Container(
                    key=Key("search_icons_container"),
                    margin=EdgeInsets.only(top=-26, left=260, right=12),
                    child=Row(
                        key=Key("search_icons_row"),
                        mainAxisAlignment=MainAxisAlignment.END,
                        children=[
                            (
                                ElevatedButton(
                                    key=Key("clear_search_button"), # Stable key
                                    child=Icon(key=Key("clear_icon"), icon=Icons.close_rounded, color=Colors.hex("#D9D9D9"), size=16),
                                    onPressed=self.clear_search,
                                    style=ButtonStyle(padding=EdgeInsets.all(0), margin=EdgeInsets.only(left=-38, right=22), backgroundColor=Colors.transparent, elevation=0)
                                )
                                if self.is_field_populated
                                else SizedBox(key=Key("clear_button_placeholder")) # Stable key for the "else" case
                            ),
                            ElevatedButton(
                                    key=Key("search_icon_button"), # Stable key
                                    child=Icon(key=Key("search_icon"), icon=Icons.search_rounded, color=Colors.hex("#D9D9D9"), size=16),
                                    onPressed=self.search,
                                    style=ButtonStyle(padding=EdgeInsets.all(0), margin=EdgeInsets.all(0),backgroundColor=Colors.transparent, elevation=0)
                                )
                            
                        ]
                    )
                ),
            ]
        )