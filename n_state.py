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
    TextField, Icons  # <-- ADD THESE IMPORTS
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
                    icon=Icon(
                        Icons.settings_rounded,
                        # size=48,
                        color=Colors.secondary,
                        fill=True,
                        weight=700),
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
                    Icon(icon=Icons.star),
                    IconButton(
                    icon=Icon(
                        Icons.settings_rounded,
                        # size=48,
                        color=Colors.secondary,
                        fill=True,
                        weight=700),
                    
                ),
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



if __name__ == "__main__":
    app_runner = Application()
    app_runner.run()
