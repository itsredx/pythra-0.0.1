# componetns/music_list.py
from pathlib import Path

import sys
import time
import random
import string

from media_scanner import scan_media_library
from song_utils import group_songs
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

def play_music():
    print('play')

class MusicListBodyState(State):
    def __init__(self):
        super().__init__()
        self.control_widget = Controls(key=Key("my_control_widget_with_slider"))
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
                    "path": entry["path"],
                    "id": entry["id"],
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
        # print("songs: ", self.songs)

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
                        onPressed=play_music,
                        callbackArgs=[
                            song["title"],
                            song["path"],
                            song["id"],
                            song["sort_id"],
                        ],
                        child=Container(
                            key=Key(f"{grp['heading']}_item_{i}"),
                            height=46,
                            color=(
                                Colors.hex("#363636")
                                if song["sort_id"] % 2 != 0
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

    def build(self):
        return Container(
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
                                        key=Key("music_header_title_content_row"),
                                        children=[
                                            Container(
                                                key=Key(
                                                    "music_header_title_content_container"
                                                ),
                                                height=50,
                                                width="100%",
                                                padding=EdgeInsets.symmetric(16),
                                                color=Colors.transparent,
                                                child=Row(
                                                    key=Key("music_header_title_row"),
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
                                                key=Key("minimize_root_container_btn"),
                                                height=14,
                                                width=14,
                                                margin=EdgeInsets.only(
                                                    top=-130,
                                                ),
                                                decoration=BoxDecoration(
                                                    color=Colors.lightgreen,
                                                    borderRadius=BorderRadius.circular(
                                                        4.0
                                                    ),
                                                ),
                                                child=ElevatedButton(
                                                    key=Key("minimize_elevated_btn"),
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
                                                        padding=EdgeInsets.all(0),
                                                        margin=EdgeInsets.all(0),
                                                        shape=BorderRadius.circular(
                                                            4.0
                                                        ),
                                                        backgroundColor=Colors.lightgreen,
                                                    ),
                                                    onPressed=self.framework.minimize,
                                                ),
                                            ),
                                            SizedBox(
                                                key=Key("close_container_padding"),
                                                width=6,
                                            ),
                                            Container(
                                                key=Key("close_root_container_btn"),
                                                height=14,
                                                width=14,
                                                margin=EdgeInsets.only(
                                                    top=-130,
                                                ),
                                                decoration=BoxDecoration(
                                                    color=Colors.error,
                                                    borderRadius=BorderRadius.circular(
                                                        4.0
                                                    ),
                                                ),
                                                child=ElevatedButton(
                                                    key=Key("close_elevated_btn"),
                                                    child=Container(
                                                        key=Key("close_container_btn"),
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
                                                        padding=EdgeInsets.all(0),
                                                        margin=EdgeInsets.all(0),
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
                            height="100%",
                            width="100%",
                            margin=EdgeInsets.only(
                                top=-77,
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
                                                    key=Key("sort_identifier_padding"),
                                                    height=30,
                                                ),
                                                Container(
                                                    key=Key("list_container_path"),
                                                    height=496,
                                                    width="100%",
                                                    child=Scrollbar(
                                                        key=Key("scrollbar_body_list"),
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
                                                            key=Key("item_list_column"),
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
                    ],
                ),
            )


class MusicListBody(StatefulWidget):
    def createState(self) -> MusicListBodyState:
        return MusicListBodyState()