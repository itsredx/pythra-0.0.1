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
    TextField,  # <-- ADD THESE IMPORTS
)
import math  # For the StarClipper


# --- Application State ---
class TestAppState(State):
    def __init__(self):
        super().__init__()
        self.counter = 0
        self.username = ""
        self.items = [
            {"id": "apple", "name": "Apple 🍎"},
            {"id": "banana", "name": "Banana 🍌"},
            {"id": "cherry", "name": "Cherry 🍒"},
        ]
        self.show_extra = False
        print("TestAppState Initialized")

    # --- Actions (increment, add_item, etc. remain the same) ---
    def increment(self):
        print("ACTION: Increment Counter")
        self.counter += 1
        self.setState()

    def on_username_changed(self, new_value):
        print(f"Username changed to: {new_value}")
        self.username = new_value
        self.setState()

    def decrement(self):
        print("ACTION: Decrement Counter")
        self.counter -= 1
        self.setState()

    def add_item(self):
        print("ACTION: Add Item")
        new_id = "".join(random.choices(string.ascii_lowercase, k=4))
        new_name = f"New {new_id.capitalize()} ✨"
        self.items.append({"id": new_id, "name": new_name})
        self.setState()

    def remove_last_item(self):
        print("ACTION: Remove Last Item")
        if self.items:
            self.items.pop()
            self.setState()

    def remove_first_item(self):
        print("ACTION: Remove First Item")
        if self.items:
            self.items.pop(0)
            self.setState()

    def swap_items(self):
        print("ACTION: Swap First Two Items")
        if len(self.items) >= 2:
            self.items[0], self.items[1] = self.items[1], self.items[0]
            self.setState()

    def toggle_extra(self):
        print("ACTION: Toggle Extra Text")
        self.show_extra = not self.show_extra
        self.setState()

    def remove_item_by_id(self, item_id_to_remove):
        print(f"ACTION: Removing item by ID '{item_id_to_remove}'")
        self.items = [item for item in self.items if item["id"] != item_id_to_remove]
        self.setState()

    # --- Build Method ---TODO SINGLECHILDSCROL
    def build(self) -> Widget:
        print(
            f"\n--- Building TestApp UI (Counter: {self.counter}, Items: {len(self.items)}, ShowExtra: {self.show_extra}) ---"
        )

        list_item_widgets = [
            ListTile(
                key=Key(item["id"]),
                title=Text(item["name"]),
                trailing=IconButton(
                    icon=Icon(icon_name="times-circle", color=Colors.error),
                    onPressed=lambda item_id=item["id"]: self.remove_item_by_id(
                        item_id
                    ),
                    onPressedName=f"remove_{item['id']}",
                ),
                selected=(
                    (self.counter % len(self.items) == self.items.index(item))
                    if self.items
                    else False
                ),
            )
            for item in self.items
        ]

        return Container(
            key=Key("root_container"),
            padding=EdgeInsets.all(20),
            child=Column(
                key=Key("main_column"),
                children=[
                    # ... (Counter Row and Item List Control Row remain the same) ...
                    Row(
                        key=Key("counter_row"),
                        mainAxisAlignment=MainAxisAlignment.SPACE_BETWEEN,
                        children=[
                            Text(f"Counter: {self.counter}", key=Key("counter_text")),
                            ElevatedButton(
                                key=Key("inc_button"),
                                child=Text("Increment"),
                                onPressed=self.increment,
                            ),
                            ElevatedButton(
                                key=Key("dec_button"),
                                child=Text("Decrement"),
                                onPressed=self.decrement,
                            ),
                        ],
                    ),
                    SizedBox(height=20),
                    TextField(
                        # The Key is CRITICAL for preserving focus!
                        key=Key("username_field"), 
                        label="Username",
                        value=self.username,
                        onChanged=self.on_username_changed
                    ),
                    SizedBox(height=20),
                    Text(f"Username Test:{self.username}", key=Key("Username")),
                    SizedBox(height=10),
                    Row(
                        key=Key("control_row"),
                        mainAxisAlignment=MainAxisAlignment.SPACE_AROUND,
                        children=[
                            ElevatedButton(child=Text("Add"), onPressed=self.add_item),
                            ElevatedButton(
                                child=Text("Swap"), onPressed=self.swap_items
                            ),
                            ElevatedButton(
                                child=Text("Rem Last"), onPressed=self.remove_last_item
                            ),
                            ElevatedButton(
                                child=Text("Rem First"),
                                onPressed=self.remove_first_item,
                            ),
                        ],
                    ),
                    SizedBox(height=20),
                    # --- ClipPath Test Section ---
                    Text("ClipPath Test:", key=Key("clippath_header")),
                    SizedBox(height=10),
                    Container(
                        key=Key("clippath_container_wrapper"),
                        decoration=BoxDecoration(
                            color=Colors.lightblue,
                            borderRadius=BorderRadius.circular(8),
                        ),
                        alignment=Alignment.center(),
                        padding=EdgeInsets.all(16.0),
                        width="70%",
                        height="50vh",
                        child=ClipPath(
                            key=Key("responsive_star_clip"),
                            width="50%",
                            aspectRatio=1.0,
                            viewBox=(
                                100,
                                100,
                            ),  # Define the coordinate system of the path
                            child=Container(
                                width="100%",
                                height="100%",
                                decoration=BoxDecoration(color=Colors.red),
                            ),
                            points=[
                                (50, 0),
                                (61, 35),
                                (98, 35),
                                (68, 57),
                                (79, 91),
                                (50, 70),
                                (21, 91),
                                (32, 57),
                                (2, 35),
                                (39, 35),
                            ],
                            radius=8.0,
                        ),
                    ),
                    SizedBox(height=20),
                    # --- End ClipPath Test Section ---
                    ElevatedButton(
                        child=Text("Toggle Extra Text"), onPressed=self.toggle_extra
                    ),
                    SizedBox(height=10),
                    Container(
                        key=Key("conditional_container"),
                        child=(
                            Text("This text appears/disappears!", key=Key("extra_text"))
                            if self.show_extra
                            else None
                        ),
                    ),
                    SizedBox(height=20),
                    Divider(key=Key("list_divider")),
                    Text("Item List:", key=Key("list_header")),
                    SizedBox(height=10),
                    Column(key=Key("item_list_column"), children=list_item_widgets),
                ],
            ),
        )


# --- App Definition & Runner (remain the same) ---
class TestApp(StatefulWidget):
    def createState(self) -> TestAppState:
        return TestAppState()


class Application:
    def __init__(self):
        self.framework = Framework.instance()
        self.my_app = TestApp(key=Key("test_app_root"))
        self.state_instance: Optional[TestAppState] = None

    def schedule_tests(self):
        # ... (same test scheduling logic) ...
        pass  # Let's run manually for this test

    def run(self):
        self.framework.set_root(self.my_app)
        if isinstance(self.my_app, StatefulWidget):
            self.state_instance = self.my_app.get_state()
        self.framework.run()


"""[
                                MoveTo(x=75, y=0),
                                LineTo(x=92, y=52),
                                LineTo(x=150, y=52),
                                LineTo(x=101, y=85),
                                LineTo(x=121, y=140),
                                LineTo(x=75, y=105),
                                LineTo(x=29, y=140),
                                LineTo(x=49, y=85),
                                LineTo(x=0, y=52),
                                LineTo(x=58, y=52),
                                ClosePath(),
                            ],"""

if __name__ == "__main__":
    app_runner = Application()
    app_runner.run()
