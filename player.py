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

        self.search_controller = TextEditingController()
        self.search_controller.add_listener(self.on_search_updates)
        self.value_entered = False

    def on_search_updates(self):
        print(f"Listener notified! Username is now: {self.search_controller.text}")
        # We still need to call setState if a listener changes other parts of the UI
        # For simple text updates, this isn't necessary, but for validation it is.
        if self.search_controller.text:
            self.value_entered = True
            print("Value in: ", self.value_entered)
            self.setState()  # Re-render to remove the error message
        else:
            self.value_entered = False
            print("Value in: ", self.value_entered)
            self.setState()

    def clear_search(self):
        self.search_controller.clear()
        self.setState()

    # --- Build Method ---TODO SINGLECHILDSCROL
    def build(self) -> Widget:
        # print(f"\n--- Building PlayerApp UI ---")

        search_field_decoration = InputDecoration(
            hintText="Search",
            fillColor="#363636",  # Use a different color on focus
            border=BorderSide(width=1, color=Colors.grey),  # Thinner, grey border
            filled=True,
            focusColor=Colors.hex("#FF94DA"),
        )

        list_item_widgets = [
            ElevatedButton(
                child=Container(
                    key=Key(f"List_item_{str(item['id'])}"),
                    height=46,
                    color=(
                        Colors.hex("#363636")
                        if item["id"] % 2 != 0
                        else Colors.transparent
                    ),
                    padding=EdgeInsets.all(9),
                    margin=EdgeInsets.all(0),
                    decoration=BoxDecoration(borderRadius=BorderRadius.all(8)),
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
                                                (
                                                    "Red X"
                                                    if item["id"] == 5
                                                    else "Artist"
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
                                                    # textAlign=TextAlign.left()
                                                ),
                                            ),
                                            alignment=Alignment.center_left(),
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
                                        SizedBox(width=80),
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
                ),
                style=ButtonStyle(
                    padding=EdgeInsets.only(
                        right=24,
                        top=2,
                        bottom=2,
                    ),
                    margin=EdgeInsets.only(top=2, bottom=2),
                    shape=BorderRadius.all(8.0),
                    backgroundColor=Colors.transparent,
                    elevation=0,
                    # maximumSize=(290, 36),
                    # minimumSize=(290, 36),
                ),
            )
            for item in self.items
        ]

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
                        child=Container(
                            key=Key("main_drawer_content_container"),
                            width=323,
                            height=822,
                            padding=EdgeInsets.all(14),
                            child=Column(
                                key=Key("main_drawer_content_column"),
                                mainAxisAlignment=MainAxisAlignment.SPACE_BETWEEN,
                                crossAxisAlignment=CrossAxisAlignment.START,
                                children=[
                                    Container(
                                        key=Key("top_drawer_content_container"),
                                        child=Column(
                                            key=Key("top_rawer_content_column"),
                                            crossAxisAlignment=CrossAxisAlignment.START,
                                            children=[
                                                Row(
                                                    key=Key("Title_row"),
                                                    crossAxisAlignment=CrossAxisAlignment.CENTER,
                                                    children=[
                                                        Icon(
                                                            Icons.arrow_back_ios_rounded,
                                                            size=16,
                                                            color=Colors.hex(
                                                                "#d9d9d955"
                                                            ),
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
                                                                color=Colors.hex(
                                                                    "#D9D9D9"
                                                                ),
                                                                fontSize=12.0,
                                                                fontFamily="verdana",
                                                            ),
                                                        ),
                                                    ],
                                                ),
                                                SizedBox(
                                                    key=Key("search_field_margin"),
                                                    height=15,
                                                ),
                                                TextField(
                                                    key=Key(
                                                        "search_field"
                                                    ),  # Another unique key
                                                    controller=self.search_controller,
                                                    decoration=search_field_decoration,
                                                    # enabled= False,
                                                    # obscureText= True,
                                                    # You would add a property to make this a password type input
                                                ),
                                                Container(
                                                    key=Key("search_icon_container"),
                                                    margin=EdgeInsets.only(
                                                        top=-26, left=262, right=12
                                                    ),
                                                    child=Icon(
                                                        key=Key("search_icon"),
                                                        icon=Icons.search_rounded,
                                                        size=16,
                                                        color=Colors.hex("#D9D9D9"),
                                                    ),
                                                ),
                                                (
                                                    Container(
                                                        key=Key("clear_icon_container"),
                                                        margin=EdgeInsets.only(
                                                            top=-20, left=238
                                                        ),
                                                        child=ElevatedButton(
                                                            key=Key("clear_btn"),
                                                            child=Icon(
                                                                key=Key("clear_icon"),
                                                                icon=Icons.close_rounded,
                                                                size=16,
                                                                color=Colors.hex(
                                                                    "#D9D9D9"
                                                                ),
                                                            ),
                                                            onPressed=self.clear_search,
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
                                                    )
                                                    if self.value_entered
                                                    else SizedBox(
                                                        key=Key(
                                                            "clear_icon_placeholder"
                                                        ),
                                                        width=0,
                                                    )
                                                ),
                                                #
                                                SizedBox(
                                                    key=Key(
                                                        "how_text_icon_container_margin"
                                                    ),
                                                    height=12,
                                                ),
                                                ElevatedButton(
                                                    key=Key(
                                                        "how_text_icon_elevated_btn"
                                                    ),
                                                    child=Container(
                                                        key=Key(
                                                            "how_text_icon_container"
                                                        ),
                                                        width="100%",
                                                        height=36,
                                                        padding=EdgeInsets.only(
                                                            top=6,
                                                            left=12,
                                                            right=12,
                                                            bottom=6,
                                                        ),
                                                        child=Row(
                                                            key=Key(
                                                                "home_text_icon_row"
                                                            ),
                                                            mainAxisAlignment=MainAxisAlignment.START,
                                                            children=[
                                                                Icon(
                                                                    icon=Icons.home_rounded,
                                                                    key=Key(
                                                                        "home_icon"
                                                                    ),
                                                                    size=22,
                                                                    color=Colors.hex(
                                                                        "#D9D9D9"
                                                                    ),
                                                                ),
                                                                SizedBox(width=16),
                                                                Text(
                                                                    "Home",
                                                                    key=Key(
                                                                        "Home_text"
                                                                    ),
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
                                                    ),
                                                    style=ButtonStyle(
                                                        padding=EdgeInsets.all(0),
                                                        margin=EdgeInsets.all(0),
                                                        shape=BorderRadius.circular(
                                                            4.0
                                                        ),
                                                        backgroundColor=Colors.transparent,
                                                        elevation=0,
                                                        maximumSize=(290, 36),
                                                        minimumSize=(290, 36),
                                                    ),
                                                ),
                                                SizedBox(
                                                    key=Key(
                                                        "Music_library_text_icon_selector_margin"
                                                    ),
                                                    height=4,
                                                ),
                                                ElevatedButton(
                                                    key=Key(
                                                        "Music_library_text_icon_selector_elevated_btn"
                                                    ),
                                                    child=Container(
                                                        key=Key(
                                                            "Music_library_text_icon_selector_container"
                                                        ),
                                                        width="100%",
                                                        height=36,
                                                        padding=EdgeInsets.only(
                                                            top=6,
                                                            left=12,
                                                            right=12,
                                                            bottom=6,
                                                        ),
                                                        decoration=BoxDecoration(
                                                            color=Colors.hex("#363636"),
                                                            borderRadius=BorderRadius.all(
                                                                4
                                                            ),
                                                        ),
                                                        child=Row(
                                                            key=Key(
                                                                "Music_library_text_icon_selector_row"
                                                            ),
                                                            mainAxisAlignment=MainAxisAlignment.START,
                                                            children=[
                                                                Container(
                                                                    key=Key(
                                                                        "Music_library_image_selector"
                                                                    ),
                                                                    margin=EdgeInsets.only(
                                                                        left=-12,
                                                                        right=9,
                                                                    ),
                                                                    child=Image(
                                                                        AssetImage(
                                                                            "selector-.svg"
                                                                        ),
                                                                        key=Key(
                                                                            "Music_library_selctor_identifier"
                                                                        ),
                                                                        width=3,
                                                                        height=20,
                                                                    ),
                                                                ),
                                                                Icon(
                                                                    icon=Icons.library_music_rounded,
                                                                    key=Key(
                                                                        "Music_library_icon"
                                                                    ),
                                                                    size=22,
                                                                    color=Colors.hex(
                                                                        "#D9D9D9"
                                                                    ),
                                                                ),
                                                                SizedBox(width=16),
                                                                Text(
                                                                    "Music library",
                                                                    key=Key(
                                                                        "Music_library_text"
                                                                    ),
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
                                                    ),
                                                    style=ButtonStyle(
                                                        padding=EdgeInsets.all(0),
                                                        margin=EdgeInsets.all(0),
                                                        shape=BorderRadius.circular(
                                                            4.0
                                                        ),
                                                        backgroundColor=Colors.transparent,
                                                        elevation=0,
                                                        maximumSize=(290, 36),
                                                        minimumSize=(290, 36),
                                                    ),
                                                ),
                                                SizedBox(
                                                    key=Key("drawer_divider_margin"),
                                                    height=14,
                                                ),
                                                Container(
                                                    key=Key("drawer_divider"),
                                                    height=2,
                                                    width="100%",
                                                    color=Colors.hex("#7C7C7C"),
                                                ),
                                                SizedBox(height=12),
                                                ElevatedButton(
                                                    key=Key(
                                                        "Play_queue_text_icon_elevated_btn"
                                                    ),
                                                    child=Container(
                                                        key=Key(
                                                            "Play_queue_text_icon_container"
                                                        ),
                                                        width="100%",
                                                        height=36,
                                                        padding=EdgeInsets.only(
                                                            top=6,
                                                            left=12,
                                                            right=12,
                                                            bottom=6,
                                                        ),
                                                        child=Row(
                                                            key=Key(
                                                                "Play_queue_text_icon_row"
                                                            ),
                                                            mainAxisAlignment=MainAxisAlignment.START,
                                                            children=[
                                                                Icon(
                                                                    icon=Icons.queue_music_rounded,
                                                                    key=Key(
                                                                        "Play_queue_icon"
                                                                    ),
                                                                    size=22,
                                                                    color=Colors.hex(
                                                                        "#D9D9D9"
                                                                    ),
                                                                ),
                                                                SizedBox(width=16),
                                                                Text(
                                                                    "Play queue",
                                                                    key=Key(
                                                                        "Play_queue_text"
                                                                    ),
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
                                                    ),
                                                    style=ButtonStyle(
                                                        padding=EdgeInsets.all(0),
                                                        margin=EdgeInsets.all(0),
                                                        shape=BorderRadius.circular(
                                                            4.0
                                                        ),
                                                        backgroundColor=Colors.transparent,
                                                        elevation=0,
                                                        maximumSize=(290, 36),
                                                        minimumSize=(290, 36),
                                                    ),
                                                ),
                                                SizedBox(
                                                    key=Key(
                                                        "playlist_and_icons_margin_4"
                                                    ),
                                                    height=4,
                                                ),
                                                ElevatedButton(
                                                    key=Key(
                                                        "playlist_and_icons_elevated_button"
                                                    ),
                                                    child=Container(
                                                        key=Key(
                                                            "playlist_and_icons_container"
                                                        ),
                                                        width="100%",
                                                        height=36,
                                                        padding=EdgeInsets.only(
                                                            top=6,
                                                            left=12,
                                                            right=12,
                                                            bottom=6,
                                                        ),
                                                        child=Row(
                                                            key=Key(
                                                                "playlist_and_icons_root_row"
                                                            ),
                                                            mainAxisAlignment=MainAxisAlignment.SPACE_BETWEEN,
                                                            children=[
                                                                Row(
                                                                    key=Key(
                                                                        "playlist_and_icons_row"
                                                                    ),
                                                                    mainAxisAlignment=MainAxisAlignment.START,
                                                                    children=[
                                                                        Icon(
                                                                            icon=Icons.playlist_play_rounded,
                                                                            key=Key(
                                                                                "playlist_icon_btn"
                                                                            ),
                                                                            size=22,
                                                                            color=Colors.hex(
                                                                                "#D9D9D9"
                                                                            ),
                                                                        ),
                                                                        SizedBox(
                                                                            width=16
                                                                        ),
                                                                        Text(
                                                                            "Playlists",
                                                                            key=Key(
                                                                                "playlist_btn_text"
                                                                            ),
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
                                                                    key=Key(
                                                                        "playlist_dropdown_icon"
                                                                    ),
                                                                    color=Colors.hex(
                                                                        "#D9D9D9"
                                                                    ),
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
                                                        shape=BorderRadius.circular(
                                                            4.0
                                                        ),
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
                                        key=Key(
                                            "settings_btn_and_playing_status_container"
                                        ),
                                        child=Column(
                                            key=Key(
                                                "settings_btn_and_playing_status_column"
                                            ),
                                            crossAxisAlignment=CrossAxisAlignment.START,
                                            children=[
                                                ElevatedButton(
                                                    key=Key("settings_btn"),
                                                    child=Container(
                                                        key=Key(
                                                            "settings_btn_iner_container"
                                                        ),
                                                        width="100%",
                                                        height=36,
                                                        padding=EdgeInsets.only(
                                                            top=6,
                                                            left=12,
                                                            right=12,
                                                            bottom=6,
                                                        ),
                                                        child=Row(
                                                            key=Key("settings_row_btn"),
                                                            mainAxisAlignment=MainAxisAlignment.START,
                                                            children=[
                                                                Icon(
                                                                    key=Key(
                                                                        "settings_icon_btn"
                                                                    ),
                                                                    icon=Icons.settings_rounded,
                                                                    size=22,
                                                                    color=Colors.hex(
                                                                        "#D9D9D9"
                                                                    ),
                                                                ),
                                                                SizedBox(width=16),
                                                                Text(
                                                                    "Settings",
                                                                    key=Key(
                                                                        "settings_text_btn"
                                                                    ),
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
                                                    ),
                                                    style=ButtonStyle(
                                                        padding=EdgeInsets.all(0),
                                                        margin=EdgeInsets.all(0),
                                                        shape=BorderRadius.circular(
                                                            4.0
                                                        ),
                                                        backgroundColor=Colors.transparent,
                                                        elevation=0,
                                                        maximumSize=(290, 36),
                                                        minimumSize=(290, 36),
                                                    ),
                                                ),
                                                SizedBox(
                                                    key=Key(
                                                        "playing_status_margin_under_settins"
                                                    ),
                                                    height=4,
                                                ),
                                                Container(
                                                    key=Key(
                                                        "playing_status_image_artist_path_container"
                                                    ),
                                                    height=344.5,
                                                    width=291,
                                                    decoration=BoxDecoration(
                                                        color=Colors.transparent,
                                                        borderRadius=BorderRadius.all(
                                                            4
                                                        ),
                                                    ),
                                                    child=ClipPath(
                                                        key=Key("Image_path_border"),
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
                                                            key=Key(
                                                                "Image_path_border_container"
                                                            ),
                                                            width="100%",
                                                            height="100%",
                                                            padding=EdgeInsets.all(5),
                                                            decoration=BoxDecoration(
                                                                color=Colors.gradient(
                                                                    "to bottom",
                                                                    Colors.red,
                                                                    Colors.blue,
                                                                ),
                                                            ),
                                                            child=ClipPath(
                                                                key=Key(
                                                                    "Image_path_content_path"
                                                                ),
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
                                                                    key=Key(
                                                                        "Image_path_content_container"
                                                                    ),
                                                                    width="100%",
                                                                    height=330,
                                                                    padding=EdgeInsets.all(
                                                                        9
                                                                    ),
                                                                    decoration=BoxDecoration(
                                                                        color=Colors.hex(
                                                                            "#363636"
                                                                        ),
                                                                    ),
                                                                    child=Column(
                                                                        key=Key(
                                                                            "Image_content_root_column"
                                                                        ),
                                                                        mainAxisAlignment=MainAxisAlignment.SPACE_BETWEEN,
                                                                        crossAxisAlignment=CrossAxisAlignment.START,
                                                                        children=[
                                                                            Container(
                                                                                key=Key(
                                                                                    "Song_artwork_mage_container"
                                                                                ),
                                                                                width=262,
                                                                                height=262,
                                                                                # padding=EdgeInsets.all(5),
                                                                                child=Image(
                                                                                    AssetImage(
                                                                                        "artwork.jpeg"
                                                                                    ),
                                                                                    key=Key(
                                                                                        "Song_artwork_mage"
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
                                                                                key=Key(
                                                                                    "Song_artist_mage"
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
                                                    key=Key(
                                                        "playing_status_root_container_in_path"
                                                    ),
                                                    width="100%",
                                                    margin=EdgeInsets.only(top=-46),
                                                    child=Row(
                                                        key=Key(
                                                            "playing_status_row_in_path"
                                                        ),
                                                        mainAxisAlignment=MainAxisAlignment.END,
                                                        children=[
                                                            Container(
                                                                key=Key(
                                                                    "playing_status_container_in_path"
                                                                ),
                                                                height=41,
                                                                width=207,
                                                                padding=EdgeInsets.symmetric(
                                                                    8, 4
                                                                ),
                                                                decoration=BoxDecoration(
                                                                    color=Colors.hex(
                                                                        "#363636"
                                                                    ),
                                                                    borderRadius=BorderRadius.circular(
                                                                        5.863
                                                                    ),
                                                                ),
                                                                child=Column(
                                                                    key=Key(
                                                                        "playing_status_column_in_path"
                                                                    ),
                                                                    mainAxisAlignment=MainAxisAlignment.SPACE_BETWEEN,
                                                                    crossAxisAlignment=CrossAxisAlignment.START,
                                                                    children=[
                                                                        Text(
                                                                            "Shoma (feat. Yng Bun)",
                                                                            key=Key(
                                                                                "song_name_in_path"
                                                                            ),
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
                                                                            key=Key(
                                                                                "artist_name_in_path"
                                                                            ),
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
                                        ),
                                    ),
                                ],
                            ),
                        ),
                        # child=Drawer(key=Key("drawer_root")),
                    ),
                    SizedBox(
                        key=Key("player_app_root_gap"),
                        width=13,
                    ),
                    Container(
                        key=Key("body_content_root_column"),
                        height="100%",
                        width=1190,
                        # color= Colors.hex("#484848"),
                        decoration=BoxDecoration(
                            color=Colors.transparent,
                            borderRadius=BorderRadius.circular(18.0),
                        ),
                        child=Column(
                            key=Key("body_content_column"),
                            crossAxisAlignment=CrossAxisAlignment.STRETCH,
                            children=[
                                Container(
                                    key=Key("body_content_container"),
                                    height=100,
                                    width="100%",
                                    decoration=BoxDecoration(
                                        color=Colors.transparent,
                                        borderRadius=BorderRadius.circular(18.0),
                                    ),
                                    child=Column(
                                        key=Key("music_header_title_content_column"),
                                        mainAxisAlignment=MainAxisAlignment.END,
                                        crossAxisAlignment=CrossAxisAlignment.STRETCH,
                                        children=[
                                            Row(
                                                key=Key(
                                                    "music_header_title_content_row"
                                                ),
                                                children=[
                                                    Container(
                                                        key=Key(
                                                            "music_header_title_content_container"
                                                        ),
                                                        height=50,
                                                        width="100%",
                                                        padding=EdgeInsets.symmetric(
                                                            16
                                                        ),
                                                        color=Colors.transparent,
                                                        child=Row(
                                                            key=Key(
                                                                "music_header_title_row"
                                                            ),
                                                            crossAxisAlignment=CrossAxisAlignment.START,
                                                            children=[
                                                                Text(
                                                                    "Music",
                                                                    key=Key(
                                                                        "music_header_title"
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
                                                                    key=Key(
                                                                        "Songs_text_in_header_root_container_margin"
                                                                    ),
                                                                    width=25,
                                                                ),
                                                                Container(
                                                                    key=Key(
                                                                        "Songs_text_in_header_root_container"
                                                                    ),
                                                                    child=Column(
                                                                        key=Key(
                                                                            "Songs_text_in_header_content_column"
                                                                        ),
                                                                        children=[
                                                                            SizedBox(
                                                                                key=Key(
                                                                                    "Songs_text_btn_margin"
                                                                                ),
                                                                                height=10,
                                                                            ),
                                                                            TextButton(
                                                                                key=Key(
                                                                                    "Songs_text_btn_in_header"
                                                                                ),
                                                                                child=Text(
                                                                                    "Songs",
                                                                                    key=Key(
                                                                                        "Songs_text_in_header"
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
                                                                                key=Key(
                                                                                    "Heder_page_selector_identifier"
                                                                                ),
                                                                                width=16,
                                                                                height=3,
                                                                            ),
                                                                        ],
                                                                    ),
                                                                ),
                                                                SizedBox(
                                                                    key=Key(
                                                                        "Albums_text_btn_in_header_root_container_margin"
                                                                    ),
                                                                    width=25,
                                                                ),
                                                                Container(
                                                                    key=Key(
                                                                        "Albums_text_btn_in_header_root_container"
                                                                    ),
                                                                    child=Column(
                                                                        key=Key(
                                                                            "Albums_text_btn_in_header_content_column"
                                                                        ),
                                                                        children=[
                                                                            SizedBox(
                                                                                key=Key(
                                                                                    "Albums_text_btn_in_header_margin"
                                                                                ),
                                                                                height=10,
                                                                            ),
                                                                            TextButton(
                                                                                key=Key(
                                                                                    "Albums_text_btn_in_header"
                                                                                ),
                                                                                child=Text(
                                                                                    "Albums",
                                                                                    key=Key(
                                                                                        "Albums_text_in_header"
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
                                                                        ],
                                                                    ),
                                                                ),
                                                                SizedBox(
                                                                    key=Key(
                                                                        "Artists_root_container_margin"
                                                                    ),
                                                                    width=25,
                                                                ),
                                                                Container(
                                                                    key=Key(
                                                                        "Artists_root_container"
                                                                    ),
                                                                    child=Column(
                                                                        key=Key(
                                                                            "Artists_content_column"
                                                                        ),
                                                                        children=[
                                                                            SizedBox(
                                                                                key=Key(
                                                                                    "Artists_margin"
                                                                                ),
                                                                                height=10,
                                                                            ),
                                                                            TextButton(
                                                                                key=Key(
                                                                                    "Artists_text_btn_in_header"
                                                                                ),
                                                                                child=Text(
                                                                                    "Artists",
                                                                                    key=Key(
                                                                                        "Artists_text_in_header"
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
                                                                        ],
                                                                    ),
                                                                ),
                                                            ],
                                                        ),
                                                    ),
                                                    Container(
                                                        key=Key(
                                                            "minimize_root_container_btn"
                                                        ),
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
                                                            key=Key(
                                                                "minimize_elevated_btn"
                                                            ),
                                                            child=Container(
                                                                key=Key(
                                                                    "minimize_container_btn"
                                                                ),
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
                                                    SizedBox(
                                                        key=Key(
                                                            "close_container_padding"
                                                        ),
                                                        width=6,
                                                    ),
                                                    Container(
                                                        key=Key(
                                                            "close_root_container_btn"
                                                        ),
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
                                                            key=Key(
                                                                "close_elevated_btn"
                                                            ),
                                                            child=Container(
                                                                key=Key(
                                                                    "close_container_btn"
                                                                ),
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
                                                ],
                                            )
                                        ],
                                    ),
                                ),
                                Container(
                                    key=Key("responsive_body_path_containerroot"),
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
                                        key=Key("responsive_body_path"),
                                        # width="50%",
                                        # aspectRatio=1.0,
                                        viewBox=(
                                            1190,
                                            608.24,
                                        ),  # Define the coordinate system of the path
                                        child=Container(
                                            key=Key("responsive_body_path_container"),
                                            width="100%",
                                            height="100%",
                                            padding=EdgeInsets.all(16),
                                            decoration=BoxDecoration(
                                                color=Colors.hex("#484848"),
                                            ),
                                            child=Container(
                                                key=Key(
                                                    "responsive_body_path_content_container"
                                                ),
                                                width="100%",
                                                height="100%",
                                                color=Colors.transparent,
                                                child=Column(
                                                    key=Key(
                                                        "responsive_body_path_content_column"
                                                    ),
                                                    children=[
                                                        Row(
                                                            key=Key(
                                                                "responsive_body_path_content_row"
                                                            ),
                                                            mainAxisAlignment=MainAxisAlignment.END,
                                                            children=[
                                                                ElevatedButton(
                                                                    key=Key(
                                                                        "add_folder_elevated_btn"
                                                                    ),
                                                                    child=Row(
                                                                        key=Key(
                                                                            "add_folder_elevated_btn_row"
                                                                        ),
                                                                        children=[
                                                                            Icon(
                                                                                icon=Icons.create_new_folder_rounded,
                                                                                key=Key(
                                                                                    "add_folder_elevated_btn_icon"
                                                                                ),
                                                                                color=Colors.hex(
                                                                                    "#D9D9D9"
                                                                                ),
                                                                                size=16,
                                                                                fill=True,
                                                                                weight=700,
                                                                            ),
                                                                            SizedBox(
                                                                                key=Key(
                                                                                    "add_folder_padding"
                                                                                ),
                                                                                width=6.0,
                                                                            ),
                                                                            Text(
                                                                                "Add folder",
                                                                                key=Key(
                                                                                    "add_folder_elevated_btn_text"
                                                                                ),
                                                                                style=TextStyle(
                                                                                    color=Colors.hex(
                                                                                        "#D9D9D9"
                                                                                    ),
                                                                                    fontSize=14.0,
                                                                                    fontFamily="verdana",
                                                                                ),
                                                                            ),
                                                                        ],
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
                                                        SizedBox(
                                                            key=Key(
                                                                "shuffle_and_play_content_row_top_padding"
                                                            ),
                                                            height=50,
                                                        ),
                                                        Row(
                                                            key=Key(
                                                                "shuffle_and_play_content_row"
                                                            ),
                                                            mainAxisAlignment=MainAxisAlignment.SPACE_BETWEEN,
                                                            children=[
                                                                ElevatedButton(
                                                                    key=Key(
                                                                        "shuffle_and_play_elevated_btn"
                                                                    ),
                                                                    child=Row(
                                                                        key=Key(
                                                                            "shuffle_and_play_elevated_btn_row"
                                                                        ),
                                                                        children=[
                                                                            Icon(
                                                                                key=Key(
                                                                                    "shuffle_and_play_icon"
                                                                                ),
                                                                                icon=Icons.shuffle_rounded,
                                                                                color=Colors.hex(
                                                                                    "#353535"
                                                                                ),
                                                                                size=16,
                                                                                fill=True,
                                                                                weight=700,
                                                                            ),
                                                                            SizedBox(
                                                                                key=Key(
                                                                                    "shuffle_and_play_top_padding"
                                                                                ),
                                                                                width=6.0,
                                                                            ),
                                                                            Text(
                                                                                "Shuffle and play",
                                                                                key=Key(
                                                                                    "shuffle_and_play_text"
                                                                                ),
                                                                                style=TextStyle(
                                                                                    color=Colors.hex(
                                                                                        "#353535"
                                                                                    ),
                                                                                    fontSize=14.0,
                                                                                    fontFamily="verdana",
                                                                                ),
                                                                            ),
                                                                        ],
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
                                                                    key=Key(
                                                                        "sort_by_content_container"
                                                                    ),
                                                                    child=Row(
                                                                        key=Key(
                                                                            "sort_by_content_row"
                                                                        ),
                                                                        children=[
                                                                            Text(
                                                                                "Sort by:",
                                                                                key=Key(
                                                                                    "sort_by_text"
                                                                                ),
                                                                                style=TextStyle(
                                                                                    color=Colors.hex(
                                                                                        "#D9D9D9"
                                                                                    ),
                                                                                    fontSize=14.0,
                                                                                    fontFamily="verdana",
                                                                                ),
                                                                            ),
                                                                            SizedBox(
                                                                                key=Key(
                                                                                    "dropdown_top_padding"
                                                                                ),
                                                                                width=5,
                                                                            ),
                                                                            TextButton(
                                                                                key=Key(
                                                                                    "Dropdown_text_btn"
                                                                                ),
                                                                                child=Text(
                                                                                    "Artists",
                                                                                    key=Key(
                                                                                        "sort_by_dropdown_text"
                                                                                    ),
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
                                                                                key=Key(
                                                                                    "drop_down_icon_elevated_btn"
                                                                                ),
                                                                                child=Icon(
                                                                                    icon=Icons.arrow_drop_down_rounded,
                                                                                    key=Key(
                                                                                        "drop_down_icon"
                                                                                    ),
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
                                                                        ],
                                                                    ),
                                                                ),
                                                            ],
                                                        ),
                                                        SizedBox(
                                                            key=Key(
                                                                "sort_identifier_padding"
                                                            ),
                                                            height=30,
                                                        ),
                                                        Row(
                                                            key=Key(
                                                                "sort_identifier_row"
                                                            ),
                                                            mainAxisAlignment=MainAxisAlignment.START,
                                                            children=[
                                                                TextButton(
                                                                    key=Key(
                                                                        "sort_identifier_text_btn"
                                                                    ),
                                                                    child=Text(
                                                                        "Juice WRLD",
                                                                        key=Key(
                                                                            "sort_identifier_text"
                                                                        ),
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
                                                        SizedBox(
                                                            key=Key("list_top_padding"),
                                                            height=10,
                                                        ),
                                                        Container(
                                                            key=Key(
                                                                "list_container_path"
                                                            ),
                                                            height=470,
                                                            width="100%",
                                                            child=Scrollbar(
                                                                key=Key(
                                                                    "scrollbar_body_list"
                                                                ),
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
                                                    ],
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
                                    key=Key("controls_holder_margin"),
                                    height=13,
                                ),
                                Container(
                                    key=Key("controls_holder"),
                                    height=112,
                                    width="100%",
                                    # padding=EdgeInsets.all(9),
                                    decoration=BoxDecoration(
                                        color=Colors.hex("#484848"),
                                        borderRadius=BorderRadius.circular(18.0),
                                    ),
                                    # child=Controls(),
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
        self.my_app = PlayerApp(key=Key("player_app_root_with_state"))
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
