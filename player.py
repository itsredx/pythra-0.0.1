# main.py

import sys
import time
import random
import string
from PySide6.QtCore import QTimer, QCoreApplication
from components.drawer import DrawerState, Drawer
from components.control import ControlsState, Controls

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


# --- Application State ---
class PlayerAppState(State):
    def __init__(self):
        super().__init__()
        self.items = [
            {"id": 1, "name": "Apple 🍎"},
            {"id": 2, "name": "Banana 🍌"},
            {"id": 3, "name": "Cherry 🍒"},
            {"id": 4, "name": "Apple 🍎"},
            {"id": 5, "name": "Shoma (feat. Yng Bun)"},
            {"id": 6, "name": "Banana 🍌"},
            {"id": 7, "name": "Cherry 🍒"},
            {"id": 8, "name": "Apple 🍎"},
            {"id": 9, "name": "Apple 🍎"},
            {"id": 10, "name": "Banana 🍌"},
            {"id": 11, "name": "Cherry 🍒"},
            {"id": 12, "name": "Apple 🍎"},
            {"id": 13, "name": "Apple 🍎"},
            {"id": 14, "name": "Banana 🍌"},
            {"id": 15, "name": "Cherry 🍒"},
            {"id": 16, "name": "Apple 🍎"},
            {"id": 17, "name": "Apple 🍎"},
            {"id": 18, "name": "Banana 🍌"},
            {"id": 19, "name": "Cherry 🍒"},
            {"id": 20, "name": "Apple 🍎"},
        ]
        self.password_controller = TextEditingController()
        self.password_controller.add_listener(self.on_username_updates)
        self.value_entered = False

    def on_username_updates(self):
        print(f"Listener notified! Username is now: {self.password_controller.text}")
        # We still need to call setState if a listener changes other parts of the UI
        # For simple text updates, this isn't necessary, but for validation it is.
        if len(self.password_controller.text) >= 1:
            self.value_entered = True
            print("Value in: ", self.value_entered)
            self.setState()  # Re-render to remove the error message

    # --- Build Method ---TODO SINGLECHILDSCROL
    def build(self) -> Widget:
        # print(f"\n--- Building PlayerApp UI ---")
        password_decoration = InputDecoration(
            hintText="Search",
            fillColor="#363636",  # Use a different color on focus
            border=BorderSide(width=1, color=Colors.grey),  # Thinner, grey border
            filled=True,
            focusColor=Colors.hex("#FF94DA"),
        )

        list_item_widgets = [
            Container(
                key=Key(f"List_item_{str(item['id'])}"),
                height=46,
                color=(
                    Colors.hex("#363636") if item["id"] % 2 != 0 else Colors.transparent
                ),
                padding=EdgeInsets.all(9),
                margin=EdgeInsets.only(
                    right=24,
                    top=2,
                    bottom=2,
                ),
                decoration=BoxDecoration(borderRadius=BorderRadius.all(4)),
                child=Row(
                    mainAxisAlignment=MainAxisAlignment.SPACE_BETWEEN,
                    children=[
                        SizedBox(width=20),
                        (
                            Icon(
                                icon=Icons.bar_chart_rounded,
                                size=12,
                                color=(
                                    Colors.hex("#FF94DA")
                                    if item["id"] == 5
                                    else Colors.hex("#D9D9D9")
                                ),
                            )
                            if item["id"] == 5
                            else SizedBox(width=16)
                        ),
                        SizedBox(width=20),
                        Container(
                            width=300,
                            child=Text(
                                item["name"],
                                style=TextStyle(
                                    color=(
                                        Colors.hex("#FF94DA")
                                        if item["id"] == 5
                                        else Colors.hex("#D9D9D9")
                                    ),
                                    fontSize=12.0,
                                    fontFamily="verdana",
                                ),
                            ),
                        ),
                        Container(
                            # color=Colors.green,
                            child=Row(
                                mainAxisAlignment=MainAxisAlignment.END,
                                children=[
                                    Container(
                                        width=150,
                                        height=28,
                                        child=Text(
                                            "Red X" if item["id"] == 5 else "Artist",
                                            style=TextStyle(
                                                color=(
                                                    Colors.hex("#FF94DA")
                                                    if item["id"] == 5
                                                    else Colors.hex("#D9D9D9")
                                                ),
                                                fontSize=12.0,
                                                fontFamily="verdana",
                                            ),
                                        ),
                                        alignment=Alignment.center(),
                                        color=(
                                            Colors.hex("#3535353e")
                                            if item["id"] == 1
                                            else Colors.transparent
                                        ),
                                        decoration=BoxDecoration(
                                            borderRadius=BorderRadius.all(4)
                                        ),
                                    ),
                                    SizedBox(width=90),
                                    Container(
                                        width=150,
                                        color=(
                                            Colors.hex("#3535353e")
                                            if item["id"] == 1
                                            else Colors.transparent
                                        ),
                                        height=28,
                                        child=Text(
                                            (
                                                "On the couch"
                                                if item["id"] == 5
                                                else "Album"
                                            ),
                                            style=TextStyle(
                                                color=(
                                                    Colors.hex("#FF94DA")
                                                    if item["id"] == 5
                                                    else Colors.hex("#D9D9D9")
                                                ),
                                                fontSize=12.0,
                                                fontFamily="verdana",
                                            ),
                                        ),
                                        alignment=Alignment.center(),
                                        decoration=BoxDecoration(
                                            borderRadius=BorderRadius.all(4)
                                        ),
                                    ),
                                    SizedBox(width=90),
                                    Container(
                                        width=100,
                                        child=Text(
                                            "RnB" if item["id"] == 5 else "Genre",
                                            style=TextStyle(
                                                color=(
                                                    Colors.hex("#FF94DA")
                                                    if item["id"] == 5
                                                    else Colors.hex("#D9D9D9")
                                                ),
                                                fontSize=12.0,
                                                fontFamily="verdana",
                                            ),
                                        ),
                                        alignment=Alignment.center(),
                                    ),
                                    SizedBox(width=90),
                                    Container(
                                        # color=Colors.blue,
                                        width=100,
                                        child=Text(
                                            "02:23" if item["id"] == 5 else "04:43",
                                            style=TextStyle(
                                                color=(
                                                    Colors.hex("#FF94DA")
                                                    if item["id"] == 5
                                                    else Colors.hex("#D9D9D9")
                                                ),
                                                fontSize=12.0,
                                                fontFamily="verdana",
                                            ),
                                        ),
                                        alignment=Alignment.center_right(),
                                    ),
                                ],
                            ),
                        ),
                    ],
                ),
            )
            for item in self.items
        ]

        return Container(
            height="100vh",
            width="100vw",
            padding=EdgeInsets.all(6),
            color=Colors.hex("#282828"),
            child=Row(
                crossAxisAlignment=CrossAxisAlignment.STRETCH,
                children=[
                    Container(
                        height="100%",
                        width=323,
                        # color= Colors.hex("#484848"),
                        decoration=BoxDecoration(
                            color=Colors.hex("#484848"),
                            borderRadius=BorderRadius.circular(18.0),
                        ),
                        child=Drawer(),
                    ),
                    SizedBox(
                        width=13,
                    ),
                    Container(
                        height="100%",
                        width=1190,
                        # color= Colors.hex("#484848"),
                        decoration=BoxDecoration(
                            color=Colors.transparent,
                            borderRadius=BorderRadius.circular(18.0),
                        ),
                        child=Column(
                            crossAxisAlignment=CrossAxisAlignment.STRETCH,
                            children=[
                                Container(
                                    height=100,
                                    width="100%",
                                    decoration=BoxDecoration(
                                        color=Colors.transparent,
                                        borderRadius=BorderRadius.circular(18.0),
                                    ),
                                    child=Column(
                                        mainAxisAlignment=MainAxisAlignment.END,
                                        crossAxisAlignment=CrossAxisAlignment.STRETCH,
                                        children=[
                                            Row(
                                                children=[
                                                    Container(
                                                        height=50,
                                                        width="100%",
                                                        padding=EdgeInsets.symmetric(
                                                            16
                                                        ),
                                                        color=Colors.transparent,
                                                        child=Row(
                                                            crossAxisAlignment=CrossAxisAlignment.START,
                                                            children=[
                                                                Text(
                                                                    "Music",
                                                                    key=Key(
                                                                        "music_header"
                                                                    ),
                                                                    style=TextStyle(
                                                                        color=Colors.hex(
                                                                            "#D9D9D9"
                                                                        ),
                                                                        fontSize=33.0,
                                                                        fontWeight=500,
                                                                        fontFamily="verdana",
                                                                    ),
                                                                ),
                                                                SizedBox(
                                                                    width=25,
                                                                ),
                                                                Container(
                                                                    child=Column(
                                                                        children=[
                                                                            SizedBox(
                                                                                height=10,
                                                                            ),
                                                                            TextButton(
                                                                                child=Text(
                                                                                    "Songs",
                                                                                    key=Key(
                                                                                        "Songs"
                                                                                    ),
                                                                                    style=TextStyle(
                                                                                        color=Colors.hex(
                                                                                            "#D9D9D9"
                                                                                        ),
                                                                                        fontSize=17.0,
                                                                                        fontFamily="verdana",
                                                                                    ),
                                                                                ),
                                                                                style=ButtonStyle(
                                                                                    backgroundColor=Colors.transparent,
                                                                                ),
                                                                            ),
                                                                            SizedBox(
                                                                                height=10,
                                                                            ),
                                                                            Image(
                                                                                AssetImage(
                                                                                    "selector.svg"
                                                                                ),
                                                                                width=16,
                                                                                height=3,
                                                                            ),
                                                                        ]
                                                                    )
                                                                ),
                                                                SizedBox(
                                                                    width=25,
                                                                ),
                                                                Container(
                                                                    child=Column(
                                                                        children=[
                                                                            SizedBox(
                                                                                height=10,
                                                                            ),
                                                                            TextButton(
                                                                                child=Text(
                                                                                    "Albums",
                                                                                    key=Key(
                                                                                        "Albums"
                                                                                    ),
                                                                                    style=TextStyle(
                                                                                        color=Colors.hex(
                                                                                            "#D9D9D9"
                                                                                        ),
                                                                                        fontSize=17.0,
                                                                                        fontFamily="verdana",
                                                                                    ),
                                                                                ),
                                                                                style=ButtonStyle(
                                                                                    backgroundColor=Colors.transparent,
                                                                                ),
                                                                            ),
                                                                        ]
                                                                    ),
                                                                ),
                                                                SizedBox(
                                                                    width=25,
                                                                ),
                                                                Container(
                                                                    child=Column(
                                                                        children=[
                                                                            SizedBox(
                                                                                height=10,
                                                                            ),
                                                                            TextButton(
                                                                                child=Text(
                                                                                    "Artists",
                                                                                    key=Key(
                                                                                        "Artists"
                                                                                    ),
                                                                                    style=TextStyle(
                                                                                        color=Colors.hex(
                                                                                            "#D9D9D9"
                                                                                        ),
                                                                                        fontSize=17.0,
                                                                                        fontFamily="verdana",
                                                                                    ),
                                                                                ),
                                                                                style=ButtonStyle(
                                                                                    backgroundColor=Colors.transparent,
                                                                                ),
                                                                            ),
                                                                        ]
                                                                    ),
                                                                ),
                                                            ],
                                                        ),
                                                    ),
                                                    Container(
                                                        height=14,
                                                        width=14,
                                                        margin=EdgeInsets.only(
                                                            top=-95,
                                                        ),
                                                        decoration=BoxDecoration(
                                                            color=Colors.lightgreen,
                                                            borderRadius=BorderRadius.circular(
                                                                4.0
                                                            ),
                                                        ),
                                                        child=ElevatedButton(
                                                            child=Container(
                                                                height=14,
                                                                width=14,
                                                                decoration=BoxDecoration(
                                                                    color=Colors.ash,
                                                                    borderRadius=BorderRadius.circular(
                                                                        4.0
                                                                    ),
                                                                ),
                                                            ),
                                                            style=ButtonStyle(
                                                                padding=EdgeInsets.all(
                                                                    0
                                                                ),
                                                                margin=EdgeInsets.all(
                                                                    0
                                                                ),
                                                                shape=BorderRadius.circular(
                                                                    4.0
                                                                ),
                                                                backgroundColor=Colors.lightgreen,
                                                            ),
                                                            onPressed=self.framework.minimize,
                                                        ),
                                                    ),
                                                    SizedBox(width=6),
                                                    Container(
                                                        height=14,
                                                        width=14,
                                                        margin=EdgeInsets.only(
                                                            top=-95,
                                                        ),
                                                        decoration=BoxDecoration(
                                                            color=Colors.error,
                                                            borderRadius=BorderRadius.circular(
                                                                4.0
                                                            ),
                                                        ),
                                                        child=ElevatedButton(
                                                            child=Container(
                                                                height=14,
                                                                width=14,
                                                                decoration=BoxDecoration(
                                                                    color=Colors.ash,
                                                                    borderRadius=BorderRadius.circular(
                                                                        4.0
                                                                    ),
                                                                ),
                                                            ),
                                                            style=ButtonStyle(
                                                                padding=EdgeInsets.all(
                                                                    0
                                                                ),
                                                                margin=EdgeInsets.all(
                                                                    0
                                                                ),
                                                                shape=BorderRadius.circular(
                                                                    4.0
                                                                ),
                                                                backgroundColor=Colors.error,
                                                            ),
                                                            onPressed=self.framework.close,
                                                        ),
                                                    ),
                                                ]
                                            )
                                        ],
                                    ),
                                ),
                                Container(
                                    key=Key("Artist_music_artwork_container_border"),
                                    height="-webkit-fill-available",
                                    width="100%",
                                    margin=EdgeInsets.only(
                                        top=-60,
                                    ),
                                    decoration=BoxDecoration(
                                        color=Colors.transparent,
                                        borderRadius=BorderRadius.circular(18.0),
                                    ),
                                    child=ClipPath(
                                        key=Key(
                                            "responsive_Artist_music_artwork_container"
                                        ),
                                        # width="50%",
                                        # aspectRatio=1.0,
                                        viewBox=(
                                            1190,
                                            608.24,
                                        ),  # Define the coordinate system of the path
                                        child=Container(
                                            width="100%",
                                            height="100%",
                                            padding=EdgeInsets.all(16),
                                            decoration=BoxDecoration(
                                                color=Colors.hex("#484848"),
                                            ),
                                            child=Container(
                                                width="100%",
                                                height="100%",
                                                color=Colors.transparent,
                                                child=Column(
                                                    children=[
                                                        Row(
                                                            mainAxisAlignment=MainAxisAlignment.END,
                                                            children=[
                                                                ElevatedButton(
                                                                    child=Row(
                                                                        children=[
                                                                            Icon(
                                                                                icon=Icons.create_new_folder_rounded,
                                                                                color=Colors.hex(
                                                                                    "#D9D9D9"
                                                                                ),
                                                                                size=16,
                                                                                fill=True,
                                                                                weight=700,
                                                                            ),
                                                                            SizedBox(
                                                                                width=6.0
                                                                            ),
                                                                            Text(
                                                                                "Add folder",
                                                                                style=TextStyle(
                                                                                    color=Colors.hex(
                                                                                        "#D9D9D9"
                                                                                    ),
                                                                                    fontSize=14.0,
                                                                                    fontFamily="verdana",
                                                                                ),
                                                                            ),
                                                                        ]
                                                                    ),
                                                                    style=ButtonStyle(
                                                                        backgroundColor=Colors.hex(
                                                                            "#353535"
                                                                        ),
                                                                        shape=BorderRadius.all(
                                                                            4
                                                                        ),
                                                                        padding=EdgeInsets.symmetric(
                                                                            horizontal=10,
                                                                            vertical=8,
                                                                        ),
                                                                        margin=EdgeInsets.all(
                                                                            0
                                                                        ),
                                                                        # maximumSize=(156.3, 33.6)
                                                                    ),
                                                                ),
                                                            ],
                                                        ),
                                                        SizedBox(height=50),
                                                        Row(
                                                            mainAxisAlignment=MainAxisAlignment.SPACE_BETWEEN,
                                                            children=[
                                                                ElevatedButton(
                                                                    child=Row(
                                                                        children=[
                                                                            Icon(
                                                                                icon=Icons.shuffle_rounded,
                                                                                color=Colors.hex(
                                                                                    "#353535"
                                                                                ),
                                                                                size=16,
                                                                                fill=True,
                                                                                weight=700,
                                                                            ),
                                                                            SizedBox(
                                                                                width=6.0
                                                                            ),
                                                                            Text(
                                                                                "Shuffle and play",
                                                                                style=TextStyle(
                                                                                    color=Colors.hex(
                                                                                        "#353535"
                                                                                    ),
                                                                                    fontSize=14.0,
                                                                                    fontFamily="verdana",
                                                                                ),
                                                                            ),
                                                                        ]
                                                                    ),
                                                                    style=ButtonStyle(
                                                                        backgroundColor=Colors.hex(
                                                                            "#FF94DA"
                                                                        ),
                                                                        shape=BorderRadius.all(
                                                                            4
                                                                        ),
                                                                        padding=EdgeInsets.symmetric(
                                                                            horizontal=10,
                                                                            vertical=8,
                                                                        ),
                                                                        margin=EdgeInsets.all(
                                                                            0
                                                                        ),
                                                                    ),
                                                                ),
                                                                Container(
                                                                    child=Row(
                                                                        children=[
                                                                            Text(
                                                                                "Sort by:",
                                                                                style=TextStyle(
                                                                                    color=Colors.hex(
                                                                                        "#D9D9D9"
                                                                                    ),
                                                                                    fontSize=14.0,
                                                                                    fontFamily="verdana",
                                                                                ),
                                                                            ),
                                                                            SizedBox(
                                                                                width=5
                                                                            ),
                                                                            TextButton(
                                                                                child=Text(
                                                                                    "Artists",
                                                                                    style=TextStyle(
                                                                                        color=Colors.hex(
                                                                                            "#FF94DA"
                                                                                        ),
                                                                                        fontSize=14.0,
                                                                                        fontFamily="verdana",
                                                                                    ),
                                                                                ),
                                                                                style=ButtonStyle(
                                                                                    backgroundColor=Colors.transparent,
                                                                                ),
                                                                            ),
                                                                            SizedBox(
                                                                                width=5
                                                                            ),
                                                                            ElevatedButton(
                                                                                child=Icon(
                                                                                    icon=Icons.arrow_drop_down_rounded,
                                                                                    color=Colors.hex(
                                                                                        "#D9D9D9"
                                                                                    ),
                                                                                    size=16,
                                                                                    fill=True,
                                                                                    weight=700,
                                                                                ),
                                                                                style=ButtonStyle(
                                                                                    padding=EdgeInsets.all(
                                                                                        0
                                                                                    ),
                                                                                    margin=EdgeInsets.all(
                                                                                        0
                                                                                    ),
                                                                                    shape=BorderRadius.circular(
                                                                                        4.0
                                                                                    ),
                                                                                    backgroundColor=Colors.transparent,
                                                                                    elevation=0,
                                                                                ),
                                                                            ),
                                                                        ]
                                                                    )
                                                                ),
                                                            ],
                                                        ),
                                                        SizedBox(height=30),
                                                        Row(
                                                            mainAxisAlignment=MainAxisAlignment.START,
                                                            children=[
                                                                TextButton(
                                                                    child=Text(
                                                                        "Juice WRLD",
                                                                        style=TextStyle(
                                                                            color=Colors.hex(
                                                                                "#FF94DA"
                                                                            ),
                                                                            fontSize=16.0,
                                                                            fontFamily="verdana",
                                                                        ),
                                                                    ),
                                                                    style=ButtonStyle(
                                                                        backgroundColor=Colors.transparent,
                                                                    ),
                                                                )
                                                            ],
                                                        ),
                                                        SizedBox(height=10),
                                                        Container(
                                                            height=470,
                                                            width="100%",
                                                            child=Scrollbar(
                                                                theme=ScrollbarTheme(
                                                                    width=14,
                                                                    thumbColor=Colors.hex(
                                                                        "#D9D9D9"
                                                                    ),
                                                                    trackColor=Colors.hex(
                                                                        "#3535353e"
                                                                    ),
                                                                    thumbHoverColor=Colors.hex(
                                                                        "#9c9b9b"
                                                                    ),
                                                                    radius=6,
                                                                ),
                                                                autoHide=False,
                                                                child=ListView(
                                                                    key=Key(
                                                                        "item_list_column"
                                                                    ),
                                                                    children=list_item_widgets,
                                                                ),
                                                            ),
                                                        ),
                                                        # SizedBox(height=10),
                                                    ]
                                                ),
                                            ),
                                        ),
                                        points=[
                                            (0, 70),
                                            (450, 70),
                                            (450, 0),
                                            (1190, 0),
                                            (1190, 608.24),
                                            (0, 608.24),
                                            # (0, 50),
                                        ],
                                        radius=18.0,
                                    ),
                                ),
                                SizedBox(
                                    height=13,
                                ),
                                Container(
                                    key=Key("Artist_music_artwork_container"),
                                    height=112,
                                    width="100%",
                                    # padding=EdgeInsets.all(9),
                                    decoration=BoxDecoration(
                                        color=Colors.hex("#484848"),
                                        borderRadius=BorderRadius.circular(18.0),
                                    ),
                                    child=Controls(),
                                ),
                            ],
                        ),
                    ),
                ],
            ),
        )


# --- App Definition & Runner (remain the same) ---
class PlayerApp(StatefulWidget):
    def createState(self) -> PlayerAppState:
        return PlayerAppState()


class Application:
    def __init__(self):
        self.framework = Framework.instance()
        self.my_app = PlayerApp(key=Key("test_app_root"))
        self.state_instance: Optional[PlayerAppState] = None

    # def schedule_tests(self):
    #     # ... (same test scheduling logic) ...
    #     pass  # Let's run manually for this test

    def run(self):
        self.framework.set_root(self.my_app)
        if isinstance(self.my_app, StatefulWidget):
            self.state_instance = self.my_app.get_state()
        self.framework.run()


if __name__ == "__main__":
    app_runner = Application()
    app_runner.run()
