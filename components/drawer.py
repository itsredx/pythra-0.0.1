# componetns/drawer.py

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
    BorderSide,  # <-- ADD THESE IMPORTS
)
import math  # For the StarClipper


class DrawerState(State):
    def __init__(self):
        super().__init__()

        self.search_controller = TextEditingController()
        self.search_controller.add_listener(self.on_search_updates)
        self.value_entered = False

    def on_search_updates(self):
        print(f"Listener notified! Username is now: {self.search_controller.text}")
        # We still need to call setState if a listener changes other parts of the UI
        # For simple text updates, this isn't necessary, but for validation it is.
        if len(self.search_controller.text) >= 1:
            self.value_entered = True
            print("Value in: ", self.value_entered)
            # self.setState() # Re-render to remove the error message

    def build(self) -> Widget:
        # print(f"\n--- Building Drawer UI ---")

        search_field_decoration = InputDecoration(
            hintText="Search",
            fillColor="#363636",  # Use a different color on focus
            border=BorderSide(width=1, color=Colors.grey),  # Thinner, grey border
            filled=True,
            focusColor=Colors.hex("#FF94DA"),
        )
        return Container(
            width=323,
            height=822,
            padding=EdgeInsets.all(14),
            child=Column(
                mainAxisAlignment=MainAxisAlignment.SPACE_BETWEEN,
                crossAxisAlignment=CrossAxisAlignment.START,
                children=[
                    Container(
                        child=Column(
                            crossAxisAlignment=CrossAxisAlignment.START,
                            children=[
                                Row(
                                    crossAxisAlignment=CrossAxisAlignment.CENTER,
                                    children=[
                                        Icon(
                                            Icons.arrow_back_ios_rounded,
                                            size=16,
                                            color=Colors.hex("#d9d9d955"),
                                        ),
                                        SizedBox(width=12),
                                        Icon(
                                            icon=Icons.play_music_rounded,
                                            size=22,
                                            color=Colors.hex("#D9D9D9"),
                                        ),
                                        SizedBox(width=12),
                                        Text(
                                            "Music Player",
                                            style=TextStyle(
                                                color=Colors.hex("#D9D9D9"),
                                                fontSize=12.0,
                                                fontFamily="verdana",
                                            ),
                                        ),
                                    ],
                                ),
                                SizedBox(height=15),
                                TextField(
                                    key=Key("password_field"),  # Another unique key
                                    controller=self.search_controller,
                                    decoration=search_field_decoration,
                                    # enabled= False,
                                    # obscureText= True,
                                    # You would add a property to make this a password type input
                                ),
                                Container(
                                    margin=EdgeInsets.only(top=-26, left=262, right=12),
                                    child=Icon(
                                        icon=Icons.search_rounded,
                                        size=16,
                                        color=Colors.hex("#D9D9D9"),
                                    ),
                                ),
                                (
                                    Container(
                                        margin=EdgeInsets.only(top=-20, left=238),
                                        child=Icon(
                                            icon=Icons.close_rounded,
                                            size=16,
                                            color=Colors.hex("#D9D9D9"),
                                        ),
                                    )
                                    if self.value_entered
                                    else SizedBox(width=0)
                                ),
                                SizedBox(height=12),
                                ElevatedButton(
                                    child=Container(
                                        width="100%",
                                        height=36,
                                        padding=EdgeInsets.only(
                                            top=6, left=12, right=12, bottom=6
                                        ),
                                        child=Row(
                                            mainAxisAlignment=MainAxisAlignment.START,
                                            children=[
                                                Icon(
                                                    icon=Icons.home_rounded,
                                                    size=22,
                                                    color=Colors.hex("#D9D9D9"),
                                                ),
                                                SizedBox(width=16),
                                                Text(
                                                    "Home",
                                                    style=TextStyle(
                                                        color=Colors.hex("#D9D9D9"),
                                                        fontSize=16.0,
                                                        fontFamily="verdana",
                                                    ),
                                                ),
                                            ],
                                        ),
                                    ),
                                    style=ButtonStyle(
                                        padding=EdgeInsets.all(0),
                                        margin=EdgeInsets.all(0),
                                        shape=BorderRadius.circular(4.0),
                                        backgroundColor=Colors.transparent,
                                        elevation=0,
                                        maximumSize=(290, 36),
                                        minimumSize=(290, 36),
                                    ),
                                ),
                                SizedBox(height=4),
                                ElevatedButton(
                                    child=Container(
                                        width="100%",
                                        height=36,
                                        padding=EdgeInsets.only(
                                            top=6, left=12, right=12, bottom=6
                                        ),
                                        decoration=BoxDecoration(
                                            color=Colors.hex("#363636"),
                                            borderRadius=BorderRadius.all(4),
                                        ),
                                        child=Row(
                                            mainAxisAlignment=MainAxisAlignment.START,
                                            children=[
                                                Container(
                                                    margin=EdgeInsets.only(
                                                        left=-12, right=9
                                                    ),
                                                    child=Image(
                                                        AssetImage("selector-.svg"),
                                                        width=3,
                                                        height=20,
                                                    ),
                                                ),
                                                Icon(
                                                    icon=Icons.library_music_rounded,
                                                    size=22,
                                                    color=Colors.hex("#D9D9D9"),
                                                ),
                                                SizedBox(width=16),
                                                Text(
                                                    "Music library",
                                                    style=TextStyle(
                                                        color=Colors.hex("#D9D9D9"),
                                                        fontSize=16.0,
                                                        fontFamily="verdana",
                                                    ),
                                                ),
                                            ],
                                        ),
                                    ),
                                    style=ButtonStyle(
                                        padding=EdgeInsets.all(0),
                                        margin=EdgeInsets.all(0),
                                        shape=BorderRadius.circular(4.0),
                                        backgroundColor=Colors.transparent,
                                        elevation=0,
                                        maximumSize=(290, 36),
                                        minimumSize=(290, 36),
                                    ),
                                ),
                                SizedBox(height=14),
                                Container(
                                    height=2,
                                    width="100%",
                                    color=Colors.hex("#7C7C7C"),
                                ),
                                SizedBox(height=12),
                                ElevatedButton(
                                    child=Container(
                                        width="100%",
                                        height=36,
                                        padding=EdgeInsets.only(
                                            top=6, left=12, right=12, bottom=6
                                        ),
                                        child=Row(
                                            mainAxisAlignment=MainAxisAlignment.START,
                                            children=[
                                                Icon(
                                                    icon=Icons.queue_music_rounded,
                                                    size=22,
                                                    color=Colors.hex("#D9D9D9"),
                                                ),
                                                SizedBox(width=16),
                                                Text(
                                                    "Play queue",
                                                    style=TextStyle(
                                                        color=Colors.hex("#D9D9D9"),
                                                        fontSize=16.0,
                                                        fontFamily="verdana",
                                                    ),
                                                ),
                                            ],
                                        ),
                                    ),
                                    style=ButtonStyle(
                                        padding=EdgeInsets.all(0),
                                        margin=EdgeInsets.all(0),
                                        shape=BorderRadius.circular(4.0),
                                        backgroundColor=Colors.transparent,
                                        elevation=0,
                                        maximumSize=(290, 36),
                                        minimumSize=(290, 36),
                                    ),
                                ),
                                SizedBox(height=4),
                                ElevatedButton(
                                    child=Container(
                                        width="100%",
                                        height=36,
                                        padding=EdgeInsets.only(
                                            top=6, left=12, right=12, bottom=6
                                        ),
                                        child=Row(
                                            mainAxisAlignment=MainAxisAlignment.SPACE_BETWEEN,
                                            children=[
                                                Row(
                                                    mainAxisAlignment=MainAxisAlignment.START,
                                                    children=[
                                                        Icon(
                                                            icon=Icons.playlist_play_rounded,
                                                            size=22,
                                                            color=Colors.hex("#D9D9D9"),
                                                        ),
                                                        SizedBox(width=16),
                                                        Text(
                                                            "Playlists",
                                                            style=TextStyle(
                                                                color=Colors.hex(
                                                                    "#D9D9D9"
                                                                ),
                                                                fontSize=16.0,
                                                                fontFamily="verdana",
                                                            ),
                                                        ),
                                                    ],
                                                ),
                                                Icon(
                                                    icon=Icons.arrow_drop_down_rounded,
                                                    color=Colors.hex("#D9D9D9"),
                                                    size=16,
                                                    fill=True,
                                                    weight=700,
                                                ),
                                            ],
                                        ),
                                    ),
                                    style=ButtonStyle(
                                        padding=EdgeInsets.all(0),
                                        margin=EdgeInsets.all(0),
                                        shape=BorderRadius.circular(4.0),
                                        backgroundColor=Colors.transparent,
                                        elevation=0,
                                        maximumSize=(290, 36),
                                        minimumSize=(290, 36),
                                    ),
                                ),
                            ],
                        ),
                    ),
                    Container(
                        child=Column(
                            crossAxisAlignment=CrossAxisAlignment.START,
                            children=[
                                ElevatedButton(
                                    Container(
                                        width="100%",
                                        height=36,
                                        padding=EdgeInsets.only(
                                            top=6, left=12, right=12, bottom=6
                                        ),
                                        child=Row(
                                            mainAxisAlignment=MainAxisAlignment.START,
                                            children=[
                                                Icon(
                                                    icon=Icons.settings_rounded,
                                                    size=22,
                                                    color=Colors.hex("#D9D9D9"),
                                                ),
                                                SizedBox(width=16),
                                                Text(
                                                    "Settings",
                                                    style=TextStyle(
                                                        color=Colors.hex("#D9D9D9"),
                                                        fontSize=16.0,
                                                        fontFamily="verdana",
                                                    ),
                                                ),
                                            ],
                                        ),
                                    ),
                                    style=ButtonStyle(
                                        padding=EdgeInsets.all(0),
                                        margin=EdgeInsets.all(0),
                                        shape=BorderRadius.circular(4.0),
                                        backgroundColor=Colors.transparent,
                                        elevation=0,
                                        maximumSize=(290, 36),
                                        minimumSize=(290, 36),
                                    ),
                                ),
                                SizedBox(height=4),
                                Container(
                                    height=344.5,
                                    width=291,
                                    decoration=BoxDecoration(
                                        color=Colors.transparent,
                                        borderRadius=BorderRadius.all(4),
                                    ),
                                    child=ClipPath(
                                        viewBox=(
                                            290,
                                            347,
                                        ),
                                        points=[
                                            (0, 343),
                                            (72, 343),
                                            (72, 290),
                                            (290, 290),
                                            (290, 0),
                                            (0, 0),
                                            # (0, 50),
                                        ],
                                        radius=15.0,
                                        child=Container(
                                            width="100%",
                                            height="100%",
                                            padding=EdgeInsets.all(5),
                                            decoration=BoxDecoration(
                                                color=Colors.gradient(
                                                    "to bottom", Colors.red, Colors.blue
                                                ),
                                            ),
                                            child=ClipPath(
                                                viewBox=(
                                                    280,
                                                    337,
                                                ),
                                                points=[
                                                    (0, 333),
                                                    (62, 333),
                                                    (62, 280),
                                                    (280, 280),
                                                    (280, 0),
                                                    (0, 0),
                                                    # (0, 50),
                                                ],
                                                radius=10.0,
                                                child=Container(
                                                    width="100%",
                                                    height=330,
                                                    padding=EdgeInsets.all(9),
                                                    decoration=BoxDecoration(
                                                        color=Colors.hex("#363636"),
                                                    ),
                                                    child=Column(
                                                        mainAxisAlignment=MainAxisAlignment.SPACE_BETWEEN,
                                                        crossAxisAlignment=CrossAxisAlignment.START,
                                                        children=[
                                                            Container(
                                                                width=262,
                                                                height=262,
                                                                # padding=EdgeInsets.all(5),
                                                                child=Image(
                                                                    AssetImage(
                                                                        "artwork.jpeg"
                                                                    ),
                                                                    width=261,
                                                                    height=261,
                                                                    borderRadius=BorderRadius.all(
                                                                        6
                                                                    ),
                                                                ),
                                                            ),
                                                            # SizedBox(height=9),
                                                            Image(
                                                                AssetImage(
                                                                    "avatar.jpg"
                                                                ),
                                                                width=42,
                                                                height=42,
                                                                borderRadius=BorderRadius.all(
                                                                    5
                                                                ),
                                                            ),
                                                        ],
                                                    ),
                                                ),
                                            ),
                                        ),
                                    ),
                                ),
                                Container(
                                    width="100%",
                                    margin=EdgeInsets.only(top=-46),
                                    child=Row(
                                        mainAxisAlignment=MainAxisAlignment.END,
                                        children=[
                                            Container(
                                                height=41,
                                                width=207,
                                                padding=EdgeInsets.symmetric(8, 4),
                                                decoration=BoxDecoration(
                                                    color=Colors.hex("#363636"),
                                                    borderRadius=BorderRadius.circular(
                                                        5.863
                                                    ),
                                                ),
                                                child=Column(
                                                    mainAxisAlignment=MainAxisAlignment.SPACE_BETWEEN,
                                                    crossAxisAlignment=CrossAxisAlignment.START,
                                                    children=[
                                                        Text(
                                                            "Shoma (feat. Yng Bun)",
                                                            style=TextStyle(
                                                                color=(
                                                                    Colors.hex(
                                                                        "#D9D9D9"
                                                                    )
                                                                ),
                                                                fontSize=14.0,
                                                                fontFamily="verdana",
                                                            ),
                                                        ),
                                                        Text(
                                                            "Red X",
                                                            style=TextStyle(
                                                                color=(
                                                                    Colors.hex(
                                                                        "#D9D9D9"
                                                                    )
                                                                ),
                                                                fontSize=11.0,
                                                                fontFamily="verdana",
                                                            ),
                                                        ),
                                                    ],
                                                ),
                                            ),
                                        ],
                                    ),
                                ),
                            ],
                        )
                    ),
                ],
            ),
        )


class Drawer(StatefulWidget):
    def createState(self) -> DrawerState:
        return DrawerState()
