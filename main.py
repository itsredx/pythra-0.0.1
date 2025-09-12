# import colors
# from constants.colors import *

# Welcome to your new Pythra App!
from pythra import (
    Framework,
    StatefulWidget,
    State,
    Column,
    Row,
    Key,
    Widget,
    Container,
    Text,
    Alignment,
    Colors,
    Center,
    ElevatedButton,
    SizedBox,
    MainAxisAlignment,
    CrossAxisAlignment,
    ClipPath,
    EdgeInsets,
    Icon,
    IconButton,
    Icons,
    ButtonStyle,
    TextStyle,
    Stack,
    Positioned,
    ClipBehavior,
    GradientTheme,
)


class HomePageState(State):
    def __init__(self):
        self.count = 0

    def incrementCounter(self):
        self.count += 1
        print("self.count: ", self.count)
        self.setState()

    def decrementCounter(self):
        self.count -= 1
        print("self.count: ", self.count)
        self.setState()

    def build(self) -> Widget:
        rotating_gradient_theme = GradientTheme(
            gradientColors=["red", "yellow", "green", "blue", "red"],
            rotationSpeed="4s",  # <-- Set a rotation speed to enable rotation
        )
        return Container(
            key=Key("home_page_Pythra_wrapper_container"),
            height="100vh",
            width="100vw",
            color=Colors.black,
            child=Center(
                key=Key("home_page_Pythra_center"),
                child=Stack(
                    key=Key("home_page_Pythra_center_Stack"),
                    clipBehavior=ClipBehavior.NONE,
                    children=[
                        ClipPath(
                            height="30vh",
                            width="30vh",
                            viewBox=[100, 100],
                            points=[
                                (0, 100),
                                (20, 100),
                                (20, 75),
                                (80, 75),
                                (80, 100),
                                (100, 100),
                                (100, 0),
                                (0, 0),
                            ],
                            radius=8,
                            key=Key("home_page_Pythra_home_page_clip_path"),
                            child=Container(
                                key=Key("home_page_Pythra_home_page_container"),
                                height="30vh",
                                width="30vh",
                                gradient=rotating_gradient_theme,
                                padding=EdgeInsets.all(2),
                                child=ClipPath(
                                    height="29.4vh",
                                    width="29.4vh",
                                    viewBox=[100, 100],
                                    points=[
                                        # _ |
                                        (0, 100),
                                        (18.5, 100),
                                        (18.5, 74.8),
                                        (81.5, 74.8),
                                        (81.5, 100),
                                        (100, 100),
                                        (100, 0),
                                        (0, 0),
                                    ],
                                    radius=8,
                                    key=Key(
                                        "home_page_Pythra_home_page_clip_path_child"
                                    ),
                                    child=Container(
                                        key=Key(
                                            "home_page_Pythra_home_page_column_cont"
                                        ),
                                        color=Colors.white,
                                        padding=EdgeInsets.all(12),
                                        height="100%",
                                        child=Column(
                                            key=Key(
                                                "home_page_Pythra_home_page_column"
                                            ),
                                            children=[
                                                Row(
                                                    crossAxisAlignment=CrossAxisAlignment.END,
                                                    key=Key(
                                                        "home_page_Pythra_counter_headerRow"
                                                    ),
                                                    children=[
                                                        Text(
                                                            "Pythra",
                                                            key=Key("home_page_Pythra"),
                                                            style=TextStyle(
                                                                color=Colors.black,
                                                                fontSize=20,
                                                            ),
                                                        ),
                                                        SizedBox(
                                                            width=4,
                                                            key=Key("sixe_2_box"),
                                                        ),
                                                        Text(
                                                            "GUI TOOLKIT v0.1.0",
                                                            key=Key(
                                                                "home_page_Pythra_ver"
                                                            ),
                                                            style=TextStyle(
                                                                color=Colors.grey,
                                                                fontSize=10,
                                                            ),
                                                        ),
                                                    ],
                                                ),
                                                SizedBox(
                                                    height=24,
                                                    key=Key("sixe_box_head"),
                                                ),
                                                Row(
                                                    crossAxisAlignment=CrossAxisAlignment.END,
                                                    key=Key(
                                                        "home_page_Pythra_counter_txtRow"
                                                    ),
                                                    children=[
                                                        Text(
                                                            f"Count:",
                                                            key=Key(
                                                                "home_page_Pythra_counter_txt"
                                                            ),
                                                            style=TextStyle(
                                                                color=Colors.black,
                                                                fontSize=14,
                                                            ),
                                                        ),
                                                        SizedBox(
                                                            width=12,
                                                            key=Key("sixe_box"),
                                                        ),
                                                        Text(
                                                            f"{self.count}",
                                                            key=Key(
                                                                "home_page_Pythra_counter_txt_count"
                                                            ),
                                                            style=TextStyle(
                                                                color=Colors.black,
                                                                fontSize=20,
                                                                fontWeight="bold",
                                                            ),
                                                        ),
                                                    ],
                                                ),
                                            ],
                                        ),
                                    ),
                                ),
                            ),
                        ),
                        Positioned(
                            height="30vh",
                            width="30vh",
                            top="24.4vh",
                            key=Key("home_page_Pythra_decrement_btn_Positioned"),
                            child=Container(
                                key=Key(
                                    "home_page_Pythra_decrement_btn_Positioned_Container"
                                ),
                                child=Row(
                                    mainAxisAlignment=MainAxisAlignment.CENTER,
                                    key=Key(
                                        "home_page_Pythra_decrement_btn_Positioned_Container_Row"
                                    ),
                                    children=[
                                        IconButton(
                                            key=Key("home_page_Pythra_decrement_btn"),
                                            icon=Icon(
                                                Icons.stat_minus_1_rounded,
                                                key=Key("home_page_Pythra_dec_btn_txt"),
                                            ),
                                            onPressed=self.decrementCounter,
                                        ),
                                        SizedBox(
                                            width=24,
                                            key=Key("sixe_box_dec"),
                                        ),
                                        IconButton(
                                            key=Key("home_page_Pythra_increment_btn"),
                                            icon=Icon(
                                                Icons.stat_1_rounded,
                                                key=Key("home_page_Pythra_btn_txt"),
                                            ),
                                            onPressed=self.incrementCounter,
                                        ),
                                    ],
                                ),
                            ),
                        ),
                    ],
                ),
            ),
        )


class HomePage(StatefulWidget):
    def createState(self) -> HomePageState:
        return HomePageState()


class MainState(State):
    def __init__(self):
        self.home_page = HomePage(key=Key("home_page"))

    def build(self):
        return self.home_page


class Main(StatefulWidget):
    def createState(self) -> MainState:
        return MainState()


if __name__ == "__main__":
    # This allows running the app directly with `python lib/main.py`
    # as well as with the CLI's `pythra run` command.
    app = Framework.instance()
    app.set_root(Main(key=Key("home_page_wrapper")))
    app.run(title="My New Pythra App")
