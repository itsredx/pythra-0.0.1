# main.py

import sys
import time
import random
import string
from PySide6.QtCore import QTimer, QCoreApplication

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
    ScrollbarTheme,  # <-- ADD THESE IMPORTS
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
            {"id": 5, "name": "Apple 🍎"},
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

    # --- Build Method ---TODO SINGLECHILDSCROL
    def build(self) -> Widget:
        print(f"\n--- Building PlayerApp UI ---")

        list_item_widgets = [
            Container(
                key=Key(f"List_item_{str(item['id'])}"),
                color= Colors.lightpink if item['id']% 2 != 0 else Colors.transparent, 
                padding=EdgeInsets.all(6),
                margin=EdgeInsets.only(right=24),
                child=Row(
                    children=[
                        Text(item["name"]),
                    ]
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
                    ),
                    SizedBox(
                        width=13,
                    ),
                    Container(
                        height="100%",
                        width="100%",
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
                                            Container(
                                                height=50,
                                                width="100%",
                                                padding=EdgeInsets.symmetric(16),
                                                color=Colors.transparent,
                                                child=Row(
                                                    crossAxisAlignment=CrossAxisAlignment.START,
                                                    children=[
                                                        Text(
                                                            "Music",
                                                            key=Key("music_header"),
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
                                        ],
                                    ),
                                ),
                                Container(
                                    key=Key("body_path"),
                                    height="-webkit-fill-available",
                                    width="100%",
                                    margin=EdgeInsets.only(
                                        top=-70,
                                    ),
                                    decoration=BoxDecoration(
                                        color=Colors.transparent,
                                        borderRadius=BorderRadius.circular(18.0),
                                    ),
                                    child=ClipPath(
                                        key=Key("responsive_star_clip"),
                                        # width="50%",
                                        # aspectRatio=1.0,
                                        viewBox=(
                                            1248.7,
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
                                                            mainAxisAlignment=MainAxisAlignment.START,
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
                                                            ],
                                                        ),
                                                        SizedBox(height=30),
                                                        Row(
                                                            mainAxisAlignment=MainAxisAlignment.START,
                                                            children=[
                                                                Text(
                                                                    "Juice WRLD",
                                                                    style=TextStyle(
                                                                        color=Colors.hex(
                                                                            "#FF94DA"
                                                                        ),
                                                                        fontSize=16.0,
                                                                        fontFamily="verdana",
                                                                    ),
                                                                )
                                                            ],
                                                        ),
                                                        SizedBox(height=10),
                                                        Container(
                                                            height=500,
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
                                                    ]
                                                ),
                                            ),
                                        ),
                                        points=[
                                            (0, 70),
                                            (450, 70),
                                            (450, 0),
                                            (1248.7, 0),
                                            (1248.7, 608.24),
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
                                    key=Key("Control_container"),
                                    height=112,
                                    width="100%",
                                    decoration=BoxDecoration(
                                        color=Colors.hex("#484848"),
                                        borderRadius=BorderRadius.circular(18.0),
                                    ),
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
