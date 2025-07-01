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
    TextButton,  # <-- ADD THESE IMPORTS
)
import math  # For the StarClipper


# --- Application State ---
class PlayerAppState(State):
    def __init__(self):
        super().__init__()

    # --- Build Method ---TODO SINGLECHILDSCROL
    def build(self) -> Widget:
        print(f"\n--- Building PlayerApp UI ---")

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
                                                padding=EdgeInsets.symmetric(35),
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
                                    height="100%",
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
                                            733.24,
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
                                            ),
                                        ),
                                        points=[
                                            (0, 70),
                                            (450, 70),
                                            (450, 0),
                                            (1248.7, 0),
                                            (1248.7, 733.24),
                                            (0, 733.24),
                                            # (0, 50),
                                        ],
                                        radius=18.0,
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
