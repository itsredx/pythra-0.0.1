# main.py
from pathlib import Path

import sys
import time
import random
import string
from PySide6.QtCore import QTimer, QCoreApplication
from components.drawer import DrawerState, Drawer
from components.control import ControlsState, Controls
from components.search_field import SearchComponent, _SearchComponentState

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
    Axis,  # <-- ADD THESE IMPORTS
)
import math  # For the StarClipper


# --- Application State ---
class PlayerAppState(State):
    def __init__(self):
        super().__init__()
        

        # self.search_controller = TextEditingController()
        # self.search_controller.add_listener(self.on_search_updates)
        self.value_entered = False

        self.search_widget = SearchComponent(key=Key("my_search_field_widget"))

        self.control_widget = Container(
            width="100%",
            height=112,
            padding=EdgeInsets.all(14),
            # color=Colors.green,
            # padding=EdgeInsets.all(9),
            decoration=BoxDecoration(
                color=Colors.hex("#484848"),
                borderRadius=BorderRadius.circular(18.0),
            ),
            child=Column(
                mainAxisAlignment=MainAxisAlignment.SPACE_BETWEEN,
                crossAxisAlignment=CrossAxisAlignment.START,
                children=[
                    Row(
                        children=[
                            Text(
                                "01:35",
                                style=TextStyle(
                                    color=Colors.hex("#D9D9D9"),
                                    fontSize=12.0,
                                    fontFamily="verdana",
                                ),
                            ),
                            SizedBox(width=8),
                            Container(
                                width="100%",
                                height=9,
                                color=Colors.hex("#D9D9D9"),
                                decoration=BoxDecoration(
                                    borderRadius=BorderRadius.all(3)
                                ),
                                child=Container(
                                    width="66%",
                                    height=9,
                                    color=Colors.hex("#363636"),
                                    decoration=BoxDecoration(
                                        borderRadius=BorderRadius.all(3)
                                    ),
                                ),
                            ),
                            SizedBox(width=8),
                            Text(
                                "02:23",
                                style=TextStyle(
                                    color=Colors.hex("#D9D9D9"),
                                    fontSize=12.0,
                                    fontFamily="verdana",
                                ),
                            ),
                        ]
                    ),
                    Row(
                        children=[
                            Row(
                                children=[
                                    ElevatedButton(
                                        child=Container(
                                            width=24,
                                            height=24,
                                            color=Colors.hex("#363636"),
                                            padding=EdgeInsets.all(4),
                                            child=Icon(
                                                Icons.shuffle_rounded,
                                                color=Colors.hex("#D9D9D9"),
                                                size=16,
                                                fill=True,
                                                weight=700,
                                            ),
                                            decoration=BoxDecoration(
                                                borderRadius=BorderRadius.all(4)
                                            ),
                                        ),
                                        style=ButtonStyle(
                                            padding=EdgeInsets.all(0),
                                            margin=EdgeInsets.all(0),
                                            shape=BorderRadius.circular(4.0),
                                            backgroundColor=Colors.transparent,
                                        ),
                                    ),
                                    SizedBox(width=16),
                                    ElevatedButton(
                                        child=Container(
                                            width=24,
                                            height=24,
                                            color=Colors.hex("#363636"),
                                            padding=EdgeInsets.all(4),
                                            child=Icon(
                                                Icons.skip_previous_rounded,
                                                color=Colors.hex("#D9D9D9"),
                                                size=16,
                                                fill=True,
                                                weight=700,
                                            ),
                                            decoration=BoxDecoration(
                                                borderRadius=BorderRadius.all(4)
                                            ),
                                        ),
                                        style=ButtonStyle(
                                            padding=EdgeInsets.all(0),
                                            margin=EdgeInsets.all(0),
                                            shape=BorderRadius.circular(4.0),
                                            backgroundColor=Colors.transparent,
                                        ),
                                    ),
                                    SizedBox(width=16),
                                    ElevatedButton(
                                        child=Container(
                                            width=48,
                                            height=48,
                                            color=Colors.gradient(
                                                "to bottom right",
                                                Colors.red,
                                                Colors.blue,
                                            ),
                                            padding=EdgeInsets.all(2),
                                            child=Container(
                                                width=44,
                                                height=44,
                                                color=Colors.hex(
                                                    "#767676"
                                                ),  # Colors.hex("#D9D9D9"),
                                                padding=EdgeInsets.all(10),
                                                child=Container(
                                                    width=24,
                                                    height=24,
                                                    color=Colors.hex(
                                                        "#363636"
                                                    ),  # Colors.gradient("to bottom right", Colors.red, Colors.blue), #,
                                                    padding=EdgeInsets.all(4),
                                                    child=Icon(
                                                        Icons.play_arrow_rounded,
                                                        color=Colors.hex("#D9D9D9"),
                                                        size=16,
                                                        fill=True,
                                                        weight=700,
                                                    ),
                                                    decoration=BoxDecoration(
                                                        borderRadius=BorderRadius.all(4)
                                                    ),
                                                ),
                                                decoration=BoxDecoration(
                                                    borderRadius=BorderRadius.all(14)
                                                ),
                                            ),
                                            decoration=BoxDecoration(
                                                borderRadius=BorderRadius.all(16)
                                            ),
                                        ),
                                        style=ButtonStyle(
                                            padding=EdgeInsets.all(0),
                                            margin=EdgeInsets.all(0),
                                            shape=BorderRadius.circular(16.0),
                                            backgroundColor=Colors.transparent,
                                        ),
                                    ),
                                    SizedBox(width=16),
                                    ElevatedButton(
                                        child=Container(
                                            width=24,
                                            height=24,
                                            color=Colors.hex("#363636"),
                                            padding=EdgeInsets.all(4),
                                            child=Icon(
                                                Icons.skip_next_rounded,
                                                color=Colors.hex("#D9D9D9"),
                                                size=16,
                                                fill=True,
                                                weight=700,
                                            ),
                                            decoration=BoxDecoration(
                                                borderRadius=BorderRadius.all(4)
                                            ),
                                        ),
                                        style=ButtonStyle(
                                            padding=EdgeInsets.all(0),
                                            margin=EdgeInsets.all(0),
                                            shape=BorderRadius.circular(4.0),
                                            backgroundColor=Colors.transparent,
                                        ),
                                    ),
                                    SizedBox(width=16),
                                    ElevatedButton(
                                        child=Container(
                                            width=24,
                                            height=24,
                                            color=Colors.hex("#363636"),
                                            padding=EdgeInsets.all(4),
                                            child=Icon(
                                                Icons.repeat_rounded,
                                                color=Colors.hex("#D9D9D9"),
                                                size=16,
                                                fill=True,
                                                weight=700,
                                            ),
                                            decoration=BoxDecoration(
                                                borderRadius=BorderRadius.all(4)
                                            ),
                                        ),
                                        style=ButtonStyle(
                                            padding=EdgeInsets.all(0),
                                            margin=EdgeInsets.all(0),
                                            shape=BorderRadius.circular(4.0),
                                            backgroundColor=Colors.transparent,
                                        ),
                                    ),
                                    SizedBox(width=16),
                                ]
                            ),
                            Row(
                                mainAxisAlignment=MainAxisAlignment.END,
                                children=[
                                    ElevatedButton(
                                        child=Container(
                                            width=24,
                                            height=24,
                                            color=Colors.hex("#363636"),
                                            padding=EdgeInsets.all(4),
                                            child=Icon(
                                                Icons.volume_up_rounded,
                                                color=Colors.hex("#D9D9D9"),
                                                size=16,
                                                fill=True,
                                                weight=700,
                                            ),
                                            decoration=BoxDecoration(
                                                borderRadius=BorderRadius.all(4)
                                            ),
                                        ),
                                        style=ButtonStyle(
                                            padding=EdgeInsets.all(0),
                                            margin=EdgeInsets.all(0),
                                            shape=BorderRadius.circular(4.0),
                                            backgroundColor=Colors.transparent,
                                        ),
                                    ),
                                    SizedBox(width=16),
                                    ElevatedButton(
                                        child=Container(
                                            width=24,
                                            height=24,
                                            color=Colors.hex("#363636"),
                                            padding=EdgeInsets.all(4),
                                            child=Icon(
                                                Icons.open_in_full_rounded,
                                                color=Colors.hex("#D9D9D9"),
                                                size=16,
                                                fill=True,
                                                weight=700,
                                            ),
                                            decoration=BoxDecoration(
                                                borderRadius=BorderRadius.all(4)
                                            ),
                                        ),
                                        style=ButtonStyle(
                                            padding=EdgeInsets.all(0),
                                            margin=EdgeInsets.all(0),
                                            shape=BorderRadius.circular(4.0),
                                            backgroundColor=Colors.transparent,
                                        ),
                                    ),
                                    SizedBox(width=16),
                                    ElevatedButton(
                                        child=Container(
                                            width=24,
                                            height=24,
                                            color=Colors.hex("#363636"),
                                            padding=EdgeInsets.all(4),
                                            child=Icon(
                                                Icons.open_in_new_rounded,
                                                color=Colors.hex("#D9D9D9"),
                                                size=16,
                                                fill=True,
                                                weight=700,
                                            ),
                                            decoration=BoxDecoration(
                                                borderRadius=BorderRadius.all(4)
                                            ),
                                        ),
                                        style=ButtonStyle(
                                            padding=EdgeInsets.all(0),
                                            margin=EdgeInsets.all(0),
                                            shape=BorderRadius.circular(4.0),
                                            backgroundColor=Colors.transparent,
                                        ),
                                    ),
                                    SizedBox(width=16),
                                    ElevatedButton(
                                        child=Container(
                                            width=24,
                                            height=24,
                                            color=Colors.hex("#363636"),
                                            padding=EdgeInsets.all(4),
                                            child=Icon(
                                                Icons.expand_less_rounded,
                                                color=Colors.hex("#D9D9D9"),
                                                size=16,
                                                fill=True,
                                                weight=700,
                                            ),
                                            decoration=BoxDecoration(
                                                borderRadius=BorderRadius.all(4)
                                            ),
                                        ),
                                        style=ButtonStyle(
                                            padding=EdgeInsets.all(0),
                                            margin=EdgeInsets.all(0),
                                            shape=BorderRadius.circular(4.0),
                                            backgroundColor=Colors.transparent,
                                        ),
                                    ),
                                ],
                            ),
                        ]
                    ),
                ],
            ),
        )

        # 1) at startup, build your library
        library_path = Path.home() / "Music"
        artwork_cache_dir = Path.home() / ".artwork_cache"
        library_cache_file = Path.home() / ".library_cache.json"

        raw_library = scan_media_library(
            library_path=library_path,
            artwork_cache_dir=artwork_cache_dir,
            library_cache_file=library_cache_file,
            fallback_artwork_path=None,
            force_rescan=False,
        )
        # 2) convert ffprobe output into the dict shape your UI needs
        #    (keys: title, artist, album, genre, duration, now_playing)
        self.songs = []
        for entry in raw_library:
            self.songs.append(
                {
                    "title": (
                        f"{entry["title"][:30]}..."
                        if len(entry["title"]) >= 31
                        else entry["title"]
                    ),
                    "artist": (
                        f"{entry["artist"][:17]}..."
                        if len(entry["artist"]) >= 18
                        else entry["artist"]
                    ),
                    "album": (
                        f"{entry.get("album", "")[:17]}..."
                        if len(entry.get("album", "")) >= 18
                        else entry.get("album", "")
                    ),
                    "genre": (
                        f"{entry.get("genre", "")[:17]}..."
                        if len(entry.get("genre", "")) >= 18
                        else entry.get("genre", "")
                    ),
                    "duration": f"{int(entry['duration_s']//60)}:{int(entry['duration_s']%60):02d}",
                    "now_playing": False,
                }
            )

        self.search_field_decoration = InputDecoration(
            hintText="Search",
            fillColor="#363636",  # Use a different color on focus
            border=BorderSide(width=1, color=Colors.grey),  # Thinner, grey border
            filled=True,
            focusColor=Colors.hex("#FF94DA"),
        )

        # 3) group by first-letter and sort
        grouped = group_songs(self.songs, key="title")

        # 4) build a flat widget list: one heading + its items
        self.widgets = []
        for grp in grouped:
            self.widgets.append(
                Container(
                    key=Key(f"heading_textbutton_container_{grp['heading']}"),
                    margin=EdgeInsets.only(top=4, bottom=4),
                    child=TextButton(
                        key=Key(f"heading_textbutton_{grp['heading']}"),
                        child=Row(
                            key=Key(f"heading_textbutton_innerrow_{grp['heading']}"),
                            mainAxisAlignment=MainAxisAlignment.START,
                            children=[
                                Text(
                                    grp["heading"],
                                    key=Key(f"heading_{grp['heading']}"),
                                    style=TextStyle(
                                        color=Colors.hex("#FF94DA"),
                                        fontSize=16.0,
                                        fontFamily="verdana",
                                    ),
                                ),
                            ],
                        ),
                        style=ButtonStyle(
                            backgroundColor=Colors.transparent,
                        ),
                    ),
                )
            )
            for i, song in enumerate(grp["items"]):
                self.widgets.append(
                    ElevatedButton(
                        key=Key(f"{grp['heading']}_elevated_btn_item_{i}"),
                        child=Container(
                            key=Key(f"{grp['heading']}_item_{i}"),
                            height=46,
                            color=(
                                Colors.hex("#363636")
                                if i % 2 != 0
                                else Colors.transparent
                            ),
                            padding=EdgeInsets.all(9),
                            margin=EdgeInsets.all(0),
                            decoration=BoxDecoration(borderRadius=BorderRadius.all(8)),
                            child=Row(
                                key=Key(f"{grp['heading']}_elevated_btn_row_item_{i}"),
                                mainAxisAlignment=MainAxisAlignment.SPACE_BETWEEN,
                                children=[
                                    SizedBox(
                                        key=Key(
                                            f"{grp['heading']}playing_icon_left_padding_item_{i}"
                                        ),
                                        width=20,
                                    ),
                                    Icon(
                                        key=Key(
                                            f"{grp['heading']}playing_icon_item_{i}"
                                        ),
                                        icon=Icons.bar_chart_rounded,
                                        size=12,
                                        color=Colors.hex("#D9D9D9"),
                                    ),
                                    # if item["id"] == 5
                                    # else SizedBox(width=16)
                                    SizedBox(
                                        key=Key(
                                            f"{grp['heading']}playing_icon_top_right_padding_item_{i}"
                                        ),
                                        width=20,
                                    ),
                                    Container(
                                        key=Key(
                                            f"{grp['heading']}_title_container_item_{i}"
                                        ),
                                        width=300,
                                        child=Row(
                                            key=Key(
                                                f"{grp['heading']}_title_container_row_item_{i}"
                                            ),
                                            mainAxisAlignment=MainAxisAlignment.START,
                                            children=[
                                                Text(
                                                    song["title"][:45],
                                                    key=Key(
                                                        f"{grp['heading']}_title_text_item_{i}"
                                                    ),
                                                    style=TextStyle(
                                                        color=Colors.hex("#D9D9D9"),
                                                        fontSize=12.0,
                                                        fontFamily="verdana",
                                                    ),
                                                ),
                                            ],
                                        ),
                                    ),
                                    Container(
                                        key=Key(
                                            f"{grp['heading']}_artist_container_item_{i}"
                                        ),
                                        # color=Colors.green,
                                        child=Row(
                                            key=Key(
                                                f"{grp['heading']}_artist_container_row_item_{i}"
                                            ),
                                            mainAxisAlignment=MainAxisAlignment.END,
                                            children=[
                                                Container(
                                                    key=Key(
                                                        f"{grp['heading']}_artist_container_row_container_item_{i}"
                                                    ),
                                                    width=150,
                                                    height=28,
                                                    child=Row(
                                                        key=Key(
                                                            f"{grp['heading']}_artist_container_row_container_row_item_{i}"
                                                        ),
                                                        mainAxisAlignment=MainAxisAlignment.START,
                                                        children=[
                                                            Text(
                                                                (
                                                                    "Unknown Artist"
                                                                    if song["artist"]
                                                                    == "<unknown>"
                                                                    else song["artist"]
                                                                ),
                                                                key=Key(
                                                                    f"{grp['heading']}_artist_text_item_{i}"
                                                                ),
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
                                                    alignment=Alignment.center(),
                                                    color=Colors.transparent,
                                                    decoration=BoxDecoration(
                                                        borderRadius=BorderRadius.all(4)
                                                    ),
                                                ),
                                                SizedBox(
                                                    key=Key(
                                                        f"{grp['heading']}_artist_padding_right_item_{i}"
                                                    ),
                                                    width=80,
                                                ),
                                                Container(
                                                    key=Key(
                                                        f"{grp['heading']}_album_container_item_{i}"
                                                    ),
                                                    width=160,
                                                    color=Colors.transparent,
                                                    height=28,
                                                    child=Row(
                                                        key=Key(
                                                            f"{grp['heading']}_album_container_row_item_{i}"
                                                        ),
                                                        mainAxisAlignment=MainAxisAlignment.START,
                                                        children=[
                                                            Text(
                                                                (
                                                                    "Unknown Album"
                                                                    if song["album"]
                                                                    == "audio"
                                                                    else song["album"]
                                                                ),
                                                                key=Key(
                                                                    f"{grp['heading']}_album_text_item_{i}"
                                                                ),
                                                                style=TextStyle(
                                                                    color=Colors.hex(
                                                                        "#D9D9D9"
                                                                    ),
                                                                    fontSize=12.0,
                                                                    fontFamily="verdana",
                                                                    # textAlign=TextAlign.left()
                                                                ),
                                                            ),
                                                        ],
                                                    ),
                                                    alignment=Alignment.center_left(),
                                                    decoration=BoxDecoration(
                                                        borderRadius=BorderRadius.all(4)
                                                    ),
                                                ),
                                                SizedBox(
                                                    key=Key(
                                                        f"{grp['heading']}_album_right_padding_item_{i}"
                                                    ),
                                                    width=80,
                                                ),
                                                Container(
                                                    key=Key(
                                                        f"{grp['heading']}_genre_container_item_{i}"
                                                    ),
                                                    width=150,
                                                    child=Row(
                                                        key=Key(
                                                            f"{grp['heading']}_genre_container_row_item_{i}"
                                                        ),
                                                        mainAxisAlignment=MainAxisAlignment.START,
                                                        children=[
                                                            Text(
                                                                (
                                                                    "Unknown Genre"
                                                                    if song["genre"]
                                                                    == "<unknown>"
                                                                    else song["genre"]
                                                                ),
                                                                key=Key(
                                                                    f"{grp['heading']}_genre_text_item_{i}"
                                                                ),
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
                                                    alignment=Alignment.center(),
                                                ),
                                                SizedBox(
                                                    key=Key(
                                                        f"{grp['heading']}_genre_right_margin_item_{i}"
                                                    ),
                                                    width=30,
                                                ),
                                                Container(
                                                    key=Key(
                                                        f"{grp['heading']}_duration_container_item_{i}"
                                                    ),
                                                    # color=Colors.blue,
                                                    width=100,
                                                    child=Text(
                                                        song["duration"],
                                                        key=Key(
                                                            f"{grp['heading']}_duration_text_item_{i}"
                                                        ),
                                                        style=TextStyle(
                                                            color=Colors.hex("#D9D9D9"),
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
                    # for item in self.items
                )

        self.clip_path = ClipPath(
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
                key=Key("Image_path_border_container"),
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
                    key=Key("Image_path_content_path"),
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
                        key=Key("Image_path_content_container"),
                        width="100%",
                        height=330,
                        padding=EdgeInsets.all(9),
                        decoration=BoxDecoration(
                            color=Colors.hex("#363636"),
                        ),
                        child=Column(
                            key=Key("Image_content_root_column"),
                            mainAxisAlignment=MainAxisAlignment.SPACE_BETWEEN,
                            crossAxisAlignment=CrossAxisAlignment.START,
                            children=[
                                Container(
                                    key=Key("Song_artwork_mage_container"),
                                    width=262,
                                    height=262,
                                    # padding=EdgeInsets.all(5),
                                    child=Image(
                                        AssetImage("artwork.jpeg"),
                                        key=Key("Song_artwork_mage"),
                                        width=261,
                                        height=261,
                                        borderRadius=BorderRadius.all(6),
                                    ),
                                ),
                                # SizedBox(height=9),
                                Image(
                                    AssetImage("avatar.jpg"),
                                    key=Key("Song_artist_mage"),
                                    width=42,
                                    height=42,
                                    borderRadius=BorderRadius.all(5),
                                ),
                            ],
                        ),
                    ),
                ),
            ),
        )

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
                                                            key=Key(
                                                                "Title_row_back_icon"
                                                            ),
                                                            size=16,
                                                            color=Colors.hex(
                                                                "#d9d9d955"
                                                            ),
                                                        ),
                                                        SizedBox(
                                                            key=Key(
                                                                "Title_row_back_icon_right_padding"
                                                            ),
                                                            width=12,
                                                        ),
                                                        Icon(
                                                            icon=Icons.play_music_rounded,
                                                            key=Key(
                                                                "Title_row_music_player_icon"
                                                            ),
                                                            size=22,
                                                            color=Colors.hex("#D9D9D9"),
                                                        ),
                                                        SizedBox(
                                                            key=Key(
                                                                "Title_row_music_player_icon_right_padding"
                                                            ),
                                                            width=12,
                                                        ),
                                                        Text(
                                                            "Music Player",
                                                            key=Key(
                                                                "Title_row_music_player_name_text"
                                                            ),
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
                                                self.search_widget,
                                                # TextField(
                                                #     key=Key(
                                                #         "search_field"
                                                #     ),  # Another unique key
                                                #     controller=self.search_controller,
                                                #     decoration=self.search_field_decoration,
                                                #     # enabled= False,
                                                #     # obscureText= True,
                                                #     # You would add a property to make this a password type input
                                                # ),
                                                # Container(
                                                #     key=Key("search_icon_container"),
                                                #     margin=EdgeInsets.only(
                                                #         top=-26, left=262, right=12
                                                #     ),
                                                #     child=Icon(
                                                #         key=Key("search_icon"),
                                                #         icon=Icons.search_rounded,
                                                #         size=16,
                                                #         color=Colors.hex("#D9D9D9"),
                                                #     ),
                                                # ),
                                                # (
                                                #     Container(
                                                #         key=Key("clear_icon_container"),
                                                #         margin=EdgeInsets.only(
                                                #             top=-20, left=238
                                                #         ),
                                                #         child=ElevatedButton(
                                                #             key=Key("clear_btn"),
                                                #             child=Icon(
                                                #                 key=Key("clear_icon"),
                                                #                 icon=Icons.close_rounded,
                                                #                 size=16,
                                                #                 color=Colors.hex(
                                                #                     "#D9D9D9"
                                                #                 ),
                                                #             ),
                                                #             onPressed=self.clear_search,
                                                #             style=ButtonStyle(
                                                #                 padding=EdgeInsets.all(
                                                #                     0
                                                #                 ),
                                                #                 margin=EdgeInsets.all(
                                                #                     0
                                                #                 ),
                                                #                 shape=BorderRadius.circular(
                                                #                     4.0
                                                #                 ),
                                                #                 backgroundColor=Colors.transparent,
                                                #                 elevation=0,
                                                #             ),
                                                #         ),
                                                #     )
                                                #     if self.value_entered
                                                #     else SizedBox(
                                                #         key=Key(
                                                #             "clear_icon_placeholder"
                                                #         ),
                                                #         width=0,
                                                #     )
                                                # ),
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
                                                                SizedBox(
                                                                    key=Key(
                                                                        "Music_library_icon_padding"
                                                                    ),
                                                                    width=16,
                                                                ),
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
                                                SizedBox(
                                                    key=Key("drawer_divider_padding"),
                                                    height=12,
                                                ),
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
                                                                SizedBox(
                                                                    key=Key(
                                                                        "Play_queue_icon_padding"
                                                                    ),
                                                                    width=16,
                                                                ),
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
                                                                            key=Key(
                                                                                "playlist_icon_btn_padding"
                                                                            ),
                                                                            width=16,
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
                                                                SizedBox(
                                                                    key=Key(
                                                                        "settings_icon_btn_padding"
                                                                    ),
                                                                    width=16,
                                                                ),
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
                                                    child=self.clip_path,
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
                                                                                key=Key(
                                                                                    "Songs_text_in_header_margin_bottom"
                                                                                ),
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
                                                                                    "A - Z",
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
                                                                                key=Key(
                                                                                    "sort_by_dropdown_text_margin_right"
                                                                                ),
                                                                                width=5,
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
                                                        Container(
                                                            key=Key(
                                                                "list_container_path"
                                                            ),
                                                            height=496,
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
                                                                    children=self.widgets,
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
                                    child=self.control_widget,  # Controls(),
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
