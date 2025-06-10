# main.py

import sys
import time # For delays in test scheduling
from PySide6.QtCore import QTimer # For countdown and scheduling test actions

# Framework Imports (assuming they are in the 'pythra' package)
from pythra.core import Framework
from pythra.state import StatefulWidget, State
from pythra.base import Key # Import Key
from pythra.widgets import Container, Text, Column # Only import compatible widgets
from pythra.styles import * # Use Colors if needed


Colors = Colors()

# --- Test State ---
class TestAppState(State):
    def __init__(self):
        super().__init__()
        self.countdown = 10
        self.items = ["Apple", "Banana", "Cherry"]
        self.timer = QTimer()
        self.timer.timeout.connect(self._tick)
        print("TestAppState Initialized")

    def start_countdown(self):
        if not self.timer.isActive():
             print(f"Starting countdown from {self.countdown}...")
             self.timer.start(1000) # 1 second interval

    def _tick(self):
        """Called by the QTimer every second."""
        if self.countdown > 0:
            self.countdown -= 1
            print(f"Countdown Tick: {self.countdown}")
            self.setState() # Trigger rebuild to update the text
        else:
            print("Countdown Finished.")
            self.timer.stop()
            self.setState() # Update one last time to show 0

    def add_item(self, name):
        print(f"ACTION: Adding item '{name}'")
        if name not in self.items:
            self.items.append(name)
            self.setState()

    def remove_item(self, name):
        print(f"ACTION: Removing item '{name}'")
        if name in self.items:
            self.items.remove(name)
            self.setState()

    def swap_items(self):
        print("ACTION: Swapping first two items")
        if len(self.items) >= 2:
            self.items[0], self.items[1] = self.items[1], self.items[0]
            self.setState()

    def build(self):
        """Build the UI using only Container and Text."""
        print(f"\n--- Building TestApp UI (Countdown: {self.countdown}, Items: {self.items}) ---")

        # Create Text widgets for list items, using the item value as the Key
        list_item_widgets = []
        for item_value in self.items:
            list_item_widgets.append(
                Text(f"- {item_value}", key=Key(item_value)) # Keyed by value
            )

        # Basic Structure
        return Container(
            key=Key("root_cont"),
            color=Colors.lightgrey, # Use basic color name
            padding=EdgeInsets.all(12), # Simple integer padding for now if EdgeInsets needs hash fix
            child=Container( # Simulate a Column with nested Containers
                 key=Key("inner_col"),
                 color=Colors.white,
                 padding=EdgeInsets.all(10),
                 child=Column( # Container for text elements
                      key=Key("text_group"),
                      children=[
                           Text(
                                f"Countdown: {self.countdown}",
                                key=Key("timer_text"), # Key for the countdown text
                                style={'fontSize': 20, 'fontWeight': 'bold'} # Basic style dict
                           ),
                           Container(height=10), # Simulate spacing
                           Text("Items:", key=Key("items_header")),
                           # Include the list item widgets directly as children
                           *list_item_widgets, # Unpack the list
                           Container(height=10), # Simulate spacing
                           # Example of a widget without a key
                           Text("Footer Text (No Key)")
                      ]
                 )
            )
        )

# --- Test StatefulWidget ---
class TestApp(StatefulWidget):
    def createState(self):
        return TestAppState()

# --- Application Runner ---
class Application:
    def __init__(self):
        self.framework = Framework()
        self.my_app = TestApp(key=Key("my_test_app")) # Give the root a key
        self.state_instance: Optional[TestAppState] = None # To hold the state instance

    def run(self):
        # Set root must happen before run
        self.framework.set_root(self.my_app)

        # Get the state instance AFTER framework is linked in StatefulWidget init
        # This assumes get_state() is implemented on StatefulWidget
        self.state_instance = self.my_app.get_state()

        # --- Schedule Test Actions using QTimer.singleShot ---
        # These will run *after* the Qt event loop starts
        QTimer.singleShot(2000, lambda: print("\n>>> Starting Test Sequence <<<"))
        QTimer.singleShot(3000, lambda: self.state_instance.start_countdown())
        # Let countdown run for a few seconds...
        QTimer.singleShot(7000, lambda: self.state_instance.add_item("Date"))
        QTimer.singleShot(9000, lambda: self.state_instance.swap_items())
        QTimer.singleShot(11000, lambda: self.state_instance.remove_item("Apple"))
        # Allow countdown to finish around 13s...
        QTimer.singleShot(15000, lambda: print("\n>>> Test Sequence Complete <<<"))
        # Optional: Close after tests
        # QTimer.singleShot(17000, lambda: self.framework.window.close() if self.framework.window else None)


        # Start the framework and Qt event loop
        self.framework.run(title='Reconciliation Test')

# --- Main Execution ---
if __name__ == "__main__":
    # Ensure PySide6 Application exists (usually done by webwidget.start or similar)
    # If webwidget.start doesn't create QApplication, uncomment the next line
    # from PySide6.QtWidgets import QApplication; app_instance = QApplication.instance() or QApplication(sys.argv)

    app = Application()
    app.run()
