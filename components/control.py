# componetns/control.py

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
    Slider,
    SliderController,
    BorderSide,  # <-- ADD THESE IMPORTS
)

# import math  # For the StarClipper


# In your main.py or any component's build method


class MyComponent(StatefulWidget):
    def __init__(self, key: Key):
        super().__init__(key=key)

    def createState(self):
        return MyComponentState()


class MyComponentState(State):
    def __init__(self):
        super().__init__()
        self.slider_controller = SliderController(value=0.5)

    def handle_slider_change(self, new_value):
        print(f"Slider value changed to: {new_value}")
        # The Slider's internal state handles the visual update automatically.
        # We just store the final value.
        self.slider_controller.value = new_value
        self.setState()
        # No need to call setState here unless this value affects other widgets.

    def move_slider(self):
        self.slider_controller.value += 0.1
        self.setState()
        pass

    def build(self) -> Widget:
        return Slider(
            key=Key("my_volume_slider"),
            controller=self.slider_controller,
            onChangeEnd=self.handle_slider_change,
            min=0.0,
            max=1.0,
            divisions=100,
            activeColor=Colors.hex("#363636"),
            thumbColor=Colors.hex("#FFF"),#FF94DA
        )


class ControlsState(State):
    def __init__(self):
        super().__init__()
        self.my_slider = MyComponent(key=Key("my_slider"))

    def build(self) -> Widget:
        # print(f"\n--- Building Controls UI ---")

        return Container(
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
                            SizedBox(width=12),
                            Container(width="100%", child=self.my_slider),
                            SizedBox(width=12),
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


class Controls(StatefulWidget):
    def createState(self) -> ControlsState:
        return ControlsState()
