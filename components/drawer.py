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
    BorderSide,
    GradientTheme,  # <-- ADD THESE IMPORTS
)
import math  # For the StarClipper
from .search_field import SearchComponent, _SearchComponentState
from .tab_controller import *





class DrawerState(State):
    def __init__(self, onTabSelected: Callable[[int], None]):
        super().__init__()
        print("Initializing home page with visibility: ", True)
        self.search_widget = SearchComponent(key=Key("my_search_field_widget"))
        self.onTabSelected_callback = onTabSelected
        self.search_controller = TextEditingController()
        self.is_field_populated = False
        self.search_controller.add_listener(self.on_search_updated)
        print("my_tab_controller.index: ",my_tab_controller.index)
        # my_tab_controller.isDragEnded = False
        # The decoration is now part of this component's state
        self.search_field_decoration = InputDecoration(
            hintText="Search",
            fillColor="#363636",
            border=BorderSide(width=1, color=Colors.grey),
            filled=True,
            focusColor=Colors.hex("#FF94DA"),
        )
        self.value_entered = False
        self.currentIndex = 1

        self.rotating_gradient_theme = GradientTheme(
            gradientColors=["red", "yellow", "green", "blue", "red"],
            rotationSpeed="4s",  # <-- Set a rotation speed to enable rotation
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
                gradient=self.rotating_gradient_theme,
                # decoration=BoxDecoration(
                #     color=Colors.gradient(
                #         "to bottom",
                #         Colors.red,
                #         Colors.blue,
                #     ),
                # ),
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

    def on_search_updated(self):
        """Listener that updates the internal state of THIS component."""
        new_value = self.search_controller.text != ""
        print("New Value: ", self.search_controller.text, " ", new_value)
        if self.is_field_populated != new_value:
            self.is_field_populated = new_value
            print("is_field_populated: ", self.is_field_populated)
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

    # --- THIS IS THE CRITICAL CHANGE ---
    def on_tab_button_pressed(self, index: int):
        """
        This method is called by the button's onPressed lambda.
        Instead of changing its own state, it calls the callback passed from the parent.
        """
        print(f"Drawer: Button for tab {index} pressed. Calling parent callback.")
        if self.onTabSelected_callback:
            self.onTabSelected_callback(index)
        # We REMOVE the setState() call from here. This component no longer
        # manages the `currentIndex`.

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
                                            key=Key("Title_row_back_icon"),
                                            size=16,
                                            color=Colors.hex("#d9d9d955"),
                                        ),
                                        SizedBox(
                                            key=Key(
                                                "Title_row_back_icon_right_padding"
                                            ),
                                            width=12,
                                        ),
                                        Icon(
                                            icon=Icons.play_music_rounded,
                                            key=Key("Title_row_music_player_icon"),
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
                                            key=Key("Title_row_music_player_name_text"),
                                            style=TextStyle(
                                                color=Colors.hex("#D9D9D9"),
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
                                # Column(
                                #     key=Key("search_component_root_col"),
                                #     crossAxisAlignment=CrossAxisAlignment.STRETCH,
                                #     children=[
                                #         TextField(
                                #             key=Key("search_field_input"),
                                #             controller=self.search_controller,
                                #             decoration=self.search_field_decoration,
                                #         ),
                                #         Container(
                                #             key=Key("search_icons_container"),
                                #             margin=EdgeInsets.only(
                                #                 top=-26, left=260, right=12
                                #             ),
                                #             child=Row(
                                #                 key=Key("search_icons_row"),
                                #                 mainAxisAlignment=MainAxisAlignment.END,
                                #                 children=[
                                #                     Container(
                                #                         height=16,
                                #                         width=16,
                                #                         key=Key(
                                #                             "clear_icons_container"
                                #                         ),
                                #                         margin=EdgeInsets.only(
                                #                             left=-20, right=5
                                #                         ),
                                #                         visible=self.is_field_populated,
                                #                         child=ElevatedButton(
                                #                             key=Key(
                                #                                 "clear_search_button"
                                #                             ),  # Stable key
                                #                             child=Icon(
                                #                                 key=Key("clear_icon"),
                                #                                 icon=Icons.close_rounded,
                                #                                 color=Colors.hex(
                                #                                     "#D9D9D9"
                                #                                 ),
                                #                                 size=16,
                                #                             ),
                                #                             onPressed=self.clear_search,
                                #                             style=ButtonStyle(
                                #                                 padding=EdgeInsets.all(
                                #                                     0
                                #                                 ),
                                #                                 margin=EdgeInsets.all(
                                #                                     0
                                #                                 ),
                                #                                 backgroundColor=Colors.transparent,
                                #                                 elevation=0,
                                #                             ),
                                #                         ),
                                #                     ) if self.is_field_populated
                                #                     else SizedBox(key=Key("clear_button_placeholder")), # Stable key for the "else" case,
                                #                     ElevatedButton(
                                #                         key=Key(
                                #                             "search_icon_button"
                                #                         ),  # Stable key
                                #                         child=Icon(
                                #                             key=Key("search_icon"),
                                #                             icon=Icons.search_rounded,
                                #                             color=Colors.hex("#D9D9D9"),
                                #                             size=16,
                                #                         ),
                                #                         onPressed=self.search,
                                #                         style=ButtonStyle(
                                #                             padding=EdgeInsets.all(0),
                                #                             margin=EdgeInsets.only(
                                #                                 left=2,
                                #                             ),
                                #                             backgroundColor=Colors.transparent,
                                #                             elevation=0,
                                #                         ),
                                #                     ),
                                #                 ],
                                #             ),
                                #         ),
                                #     ],
                                # ),
                                SizedBox(
                                    key=Key("how_text_icon_container_margin"),
                                    height=12,
                                ),
                                ElevatedButton(
                                    key=Key("how_text_icon_elevated_btn"),
                                    onPressed=lambda: self.on_tab_button_pressed(1),
                                    onPressedName=f"tab_select_callback_home_{id(self.on_tab_button_pressed)}",
                                    child=Container(
                                        key=Key("how_text_icon_container"),
                                        width="100%",
                                        height=36,
                                        padding=EdgeInsets.only(
                                            top=6,
                                            left=12,
                                            right=12,
                                            bottom=6,
                                        ),
                                        child=Row(
                                            key=Key("home_text_icon_row"),
                                            mainAxisAlignment=MainAxisAlignment.START,
                                            children=[
                                                Icon(
                                                    icon=Icons.home_rounded,
                                                    key=Key("home_icon"),
                                                    size=22,
                                                    color=Colors.hex("#D9D9D9"),
                                                ),
                                                SizedBox(width=16),
                                                Text(
                                                    "Home",
                                                    key=Key("Home_text"),
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
                                SizedBox(
                                    key=Key("Music_library_text_icon_selector_margin"),
                                    height=4,
                                ),
                                ElevatedButton(
                                    key=Key(
                                        "Music_library_text_icon_selector_elevated_btn"
                                    ),
                                    onPressed=lambda: self.on_tab_button_pressed(0),
                                    onPressedName=f"tab_select_callback_music_{id(self.on_tab_button_pressed)}",
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
                                            borderRadius=BorderRadius.all(4),
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
                                                        AssetImage("selector-.svg"),
                                                        key=Key(
                                                            "Music_library_selctor_identifier"
                                                        ),
                                                        width=3,
                                                        height=20,
                                                    ),
                                                ),
                                                Icon(
                                                    icon=Icons.library_music_rounded,
                                                    key=Key("Music_library_icon"),
                                                    size=22,
                                                    color=Colors.hex("#D9D9D9"),
                                                ),
                                                SizedBox(
                                                    key=Key(
                                                        "Music_library_icon_padding"
                                                    ),
                                                    width=16,
                                                ),
                                                Text(
                                                    "Music library",
                                                    key=Key("Music_library_text"),
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
                                    key=Key("Play_queue_text_icon_elevated_btn"),
                                    child=Container(
                                        key=Key("Play_queue_text_icon_container"),
                                        width="100%",
                                        height=36,
                                        padding=EdgeInsets.only(
                                            top=6,
                                            left=12,
                                            right=12,
                                            bottom=6,
                                        ),
                                        child=Row(
                                            key=Key("Play_queue_text_icon_row"),
                                            mainAxisAlignment=MainAxisAlignment.START,
                                            children=[
                                                Icon(
                                                    icon=Icons.queue_music_rounded,
                                                    key=Key("Play_queue_icon"),
                                                    size=22,
                                                    color=Colors.hex("#D9D9D9"),
                                                ),
                                                SizedBox(
                                                    key=Key("Play_queue_icon_padding"),
                                                    width=16,
                                                ),
                                                Text(
                                                    "Play queue",
                                                    key=Key("Play_queue_text"),
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
                                SizedBox(
                                    key=Key("playlist_and_icons_margin_4"),
                                    height=4,
                                ),
                                ElevatedButton(
                                    key=Key("playlist_and_icons_elevated_button"),
                                    child=Container(
                                        key=Key("playlist_and_icons_container"),
                                        width="100%",
                                        height=36,
                                        padding=EdgeInsets.only(
                                            top=6,
                                            left=12,
                                            right=12,
                                            bottom=6,
                                        ),
                                        child=Row(
                                            key=Key("playlist_and_icons_root_row"),
                                            mainAxisAlignment=MainAxisAlignment.SPACE_BETWEEN,
                                            children=[
                                                Row(
                                                    key=Key("playlist_and_icons_row"),
                                                    mainAxisAlignment=MainAxisAlignment.START,
                                                    children=[
                                                        Icon(
                                                            icon=Icons.playlist_play_rounded,
                                                            key=Key(
                                                                "playlist_icon_btn"
                                                            ),
                                                            size=22,
                                                            color=Colors.hex("#D9D9D9"),
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
                                                    key=Key("playlist_dropdown_icon"),
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
                        key=Key("settings_btn_and_playing_status_container"),
                        child=Column(
                            key=Key("settings_btn_and_playing_status_column"),
                            crossAxisAlignment=CrossAxisAlignment.START,
                            children=[
                                ElevatedButton(
                                    key=Key("settings_btn"),
                                    child=Container(
                                        key=Key("settings_btn_iner_container"),
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
                                                    key=Key("settings_icon_btn"),
                                                    icon=Icons.settings_rounded,
                                                    size=22,
                                                    color=Colors.hex("#D9D9D9"),
                                                ),
                                                SizedBox(
                                                    key=Key(
                                                        "settings_icon_btn_padding"
                                                    ),
                                                    width=16,
                                                ),
                                                Text(
                                                    "Settings",
                                                    key=Key("settings_text_btn"),
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
                                SizedBox(
                                    key=Key("playing_status_margin_under_settins"),
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
                                        borderRadius=BorderRadius.all(4),
                                    ),
                                    child=self.clip_path,
                                ),
                                Container(
                                    key=Key("playing_status_root_container_in_path"),
                                    width="100%",
                                    margin=EdgeInsets.only(top=-46),
                                    child=Row(
                                        key=Key("playing_status_row_in_path"),
                                        mainAxisAlignment=MainAxisAlignment.END,
                                        children=[
                                            Container(
                                                key=Key(
                                                    "playing_status_container_in_path"
                                                ),
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
        )


class Drawer(StatefulWidget):
    def __init__(self, key: Key, onTabSelected: Callable[[int], None]):
        self.onTabSelected = onTabSelected # Store the callback
        super().__init__(key=key)

    def createState(self) -> DrawerState:
        return DrawerState(onTabSelected=self.onTabSelected)


class Application:
    def __init__(self):
        self.framework = Framework.instance()
        self.my_app = Drawer(key=Key("drawer_app_root"))
        self.state_instance: Optional[DrawerState] = None

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
