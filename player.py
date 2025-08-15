# main.py
from pathlib import Path

import sys
import time
import random
import string
from PySide6.QtCore import QTimer, QCoreApplication
from components.drawer import Drawer
from components.tab_controller import *
from components.control import Controls
from components.home import HomePage
from components.music_list import MusicListBody
from media_scanner import scan_media_library
from song_utils import group_songs

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
    BorderSide,
    VirtualListView,
    GradientTheme,
    Axis,  # <-- ADD THESE IMPORTS
)
import math  # For the StarClipper

def on_tab_selected(index: int):

    pass




# --- Application State ---
class PlayerAppState(State):
    def __init__(self):
        super().__init__()
        # self.search_controller = TextEditingController()
        # self.search_controller.add_listener(self.on_search_updates)
        self.value_entered = False
        self.currentIndex = 0
        self.music_list_body = MusicListBody(
            key=Key("my_music_list_body")
        )
        self.home_page_body = HomePage(key=Key("my_home_page_body"))
        self.control_widget = Controls(key=Key("my_control_widget_with_slider"))
        self.drawer_widget = Drawer(
            key=Key("drawer_root"), onTabSelected=on_tab_selected
        )

    def on_tab_home_page(self):
        # if self.currentIndex != 1:
        self.currentIndex = 1
        print("currentIndex: ", self.currentIndex)
        self.setState()

    def on_tab_music_list(self):
        # if self.currentIndex != 0:
        self.currentIndex = 0
        self.setState()

    # --- Build Method ---TODO SINGLECHILDSCROL
    def build(self) -> Widget:
        # print(f"\n--- Building PlayerApp UI ---")
        # content = [self.music_list_body, self.home_page_body]

        # body_content = content[self.currentIndex]

        return Container(
            key=Key("player_app_root_container"),
            height="100vh",
            width="100vw",
            padding=EdgeInsets.all(6),
            color=Colors.hex("#282828"),
            child=Row(
                key=Key("player_app_root_row"),
                crossAxisAlignment=CrossAxisAlignment.STRETCH,
                children=[
                    Container(
                        key=Key("drawer_root_holder"),
                        height="100%",
                        width=323,
                        # color= Colors.hex("#484848"),
                        decoration=BoxDecoration(
                            color=Colors.hex("#484848"),
                            borderRadius=BorderRadius.circular(18.0),
                        ),
                        child=self.drawer_widget,
                    ),
                    SizedBox(
                        key=Key("player_app_root_gap"),
                        width=10,
                    ),
                    Container(
                        height="90vh",
                        child=Column(
                            children=[
                                Row(children=[
                                    ElevatedButton(
                                    child=Text("Switch", key=Key("player_app_root_home_switch_txt"),),
                                    key=Key("player_app_root_home_switch"),
                                    onPressed=self.on_tab_home_page,
                                ),
                                ElevatedButton(
                                    child=Text("Switch", key=Key("player_app_root_music_switch_txt"),),
                                    key=Key("player_app_root_music_switch"),
                                    onPressed=self.on_tab_music_list,
                                ),
                                ]),
                                
                                Container(
                                    child=self.music_list_body,
                                    key=Key("player_app_root_music_list"),
                                    visible = True if self.currentIndex == 0 else False,
                                ),
                                Container(
                                    child=self.home_page_body,
                                    key=Key("player_app_root_home_page"),
                                    visible = True if self.currentIndex == 1 else False,
                                ),  # self.music_list_body,
                                Container(
                                    key=Key("controls_holder"),
                                    height=112,
                                    width="100%",
                                    # padding=EdgeInsets.all(9),
                                    decoration=BoxDecoration(
                                        color=Colors.hex("#484848"),
                                        borderRadius=BorderRadius.circular(18.0),
                                    ),
                                    child=self.control_widget,  # Controls(),
                                ),
                            ]
                        ),
                    ),
                ],
            ),
        )


# --- App Definition & Runner (remain the same) ---
class PlayerApp(StatefulWidget):
    def createState(self) -> PlayerAppState:
        return PlayerAppState()


class mainAppState(State):
    def __init__(self):
        super().__init__()

    def build(self) -> Widget:
        return PlayerApp(key=Key("player_app_root_with_state"))


class mainApp(StatefulWidget):
    def createState(self) -> mainAppState:
        return mainAppState()


class Application:
    def __init__(self):
        self.framework = Framework.instance()
        self.my_app = mainApp(key=Key("main_app_root_with_state"))
        self.state_instance: Optional[mainAppState] = None

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
