# main.py

import sys
import random
import string
from PySide6.QtCore import QTimer, QCoreApplication # Use QCoreApplication for timer loop if needed

# Framework Imports
from pythra import (
    Framework, State, StatefulWidget, Key, Widget, Icon,
    Container, Column, Row, Text, ElevatedButton, Spacer, IconButton,
    Colors, EdgeInsets, MainAxisAlignment, CrossAxisAlignment,
    ButtonStyle, # Assuming ButtonStyle is compatible
    ListTile, Divider, __all__ # Example usage
)

# --- Application State ---
class TestAppState(State):
    def __init__(self):
        super().__init__()
        self.counter = 0
        # Initial items with keys derived from their names
        self.items = [
            {'id': 'apple', 'name': 'Apple 🍎'},
            {'id': 'banana', 'name': 'Banana 🍌'},
            {'id': 'cherry', 'name': 'Cherry 🍒'},
        ]
        self.show_extra = False
        self._timer = None
        print("TestAppState Initialized")

    # --- Actions ---
    def increment(self):
        print("ACTION: Increment Counter")
        self.counter += 1
        self.setState()
    
    def decrement(self):
        print("ACTION: Decrement Counter")
        self.counter -= 1
        self.setState()

    def add_item(self):
        print("ACTION: Add Item")
        # Generate a pseudo-random ID/name
        new_id = ''.join(random.choices(string.ascii_lowercase, k=4))
        new_name = f"New {new_id.capitalize()} ✨"
        self.items.append({'id': new_id, 'name': new_name})
        self.setState()

    def remove_last_item(self):
        print("ACTION: Remove Last Item")
        if self.items:
            removed = self.items.pop()
            print(f"  Removed: {removed['name']}")
            self.setState()
        else:
             print("  No items to remove.")

    def remove_first_item(self):
        print("ACTION: Remove First Item")
        if self.items:
            removed = self.items.pop(0)
            print(f"  Removed: {removed['name']}")
            self.setState()
        else:
             print("  No items to remove.")


    def swap_items(self):
        print("ACTION: Swap First Two Items")
        if len(self.items) >= 2:
            self.items[0], self.items[1] = self.items[1], self.items[0]
            print(f"  Swapped. New order: {[item['name'] for item in self.items]}")
            self.setState()
        else:
             print("  Not enough items to swap.")

    def toggle_extra(self):
        print("ACTION: Toggle Extra Text")
        self.show_extra = not self.show_extra
        self.setState()

    # --- Build Method ---
    def build(self) -> Widget:
        print(f"\n--- Building TestApp UI (Counter: {self.counter}, Items: {len(self.items)}, ShowExtra: {self.show_extra}) ---")

        # Create list item widgets using keys
        list_item_widgets = []
        for item in self.items:
            list_item_widgets.append(
                # Use ListTile for better structure
                ListTile(
                    key=Key(item['id']), # Use stable ID for key
                    # leading=Icon(icon_name='check', size=18), # Requires Icon widget
                    title=Text(item['name']),
                    # Add a button within the list item for removal
                    trailing=IconButton( # Requires IconButton widget
                         icon=Icon(icon_name='times-circle'), # Requires Icon widget
                         onPressed=lambda item_id=item['id']: self.remove_item_by_id(item_id), # Pass ID
                         onPressedName=f"remove_{item['id']}" # Unique name
                    ),
                    selected=(self.counter % len(self.items) == self.items.index(item)) if self.items else False # Example selection
                )
            )
            list_item_widgets.append(Divider(key=Key(f"div_{item['id']}"))) # Divider with key

        return Container(
            key=Key("root_container"),
            padding=EdgeInsets.all(10),
            child=Column(
                key=Key("main_column"),
                crossAxisAlignment=CrossAxisAlignment.START, # Align items left
                children=[
                    # Counter Row
                    Row(
                        key=Key("counter_row"),
                        mainAxisAlignment=MainAxisAlignment.SPACE_BETWEEN,
                        children=[
                            Text(f"Counter: {self.counter}", key=Key("counter_text")),
                            ElevatedButton(
                                key=Key("inc_button"),
                                child=Text("Increment"),
                                onPressed=self.increment
                            ),
                            ElevatedButton(
                                key=Key("dec_button"),
                                child=Text("Decrement"),
                                onPressed=self.decrement
                            )
                        ]
                    ),
                    Container(height=10), # SizedBox equivalent

                    # Item List Control Row
                    Row(
                         key=Key("control_row"),
                         mainAxisAlignment=MainAxisAlignment.SPACE_AROUND,
                         children=[
                              ElevatedButton(
                                   key=Key("add_button"),
                                   child=Text("Add Item"),
                                   onPressed=self.add_item,
                              ),
                              ElevatedButton(
                                   key=Key("swap_button"),
                                   child=Text("Swap First Two"),
                                   onPressed=self.swap_items,
                              ),
                              ElevatedButton(
                                   key=Key("remove_last_button"),
                                   child=Text("Remove Last"),
                                   onPressed=self.remove_last_item,
                              ),
                              ElevatedButton(
                                   key=Key("remove_first_button"),
                                   child=Text("Remove First"),
                                   onPressed=self.remove_first_item,
                              ),
                         ]
                    ),
                    Container(height=10),

                     # Conditional Widget Button
                     ElevatedButton(
                          key=Key("toggle_button"),
                          child=Text("Toggle Extra Text"),
                          onPressed=self.toggle_extra,
                     ),
                     Container(height=10),

                     # Conditional Widget
                     Container(
                          key = Key("conditional_container"),
                          # Render conditionally - reconciler should handle insert/remove
                          child=Text("This text appears/disappears!", key=Key("extra_text")) if self.show_extra else None
                     ),

                    Container(height=20),
                    Divider(key=Key("list_divider")),
                    Text("Item List:", key=Key("list_header")),
                    Container(height=10),

                    # Column for the List Items
                    Column(
                         key=Key("item_list_column"),
                         children=list_item_widgets if list_item_widgets else [Text("No items.", key=Key("empty_list"))]
                    )
                ]
            )
        )

    # Helper to remove item by ID (used by ListTile trailing button)
    def remove_item_by_id(self, item_id_to_remove):
        print(f"ACTION: Removing item by ID '{item_id_to_remove}'")
        original_length = len(self.items)
        self.items = [item for item in self.items if item['id'] != item_id_to_remove]
        if len(self.items) < original_length:
            self.setState()
        else:
            print(f"  Item with ID '{item_id_to_remove}' not found.")


# --- App Definition ---
class TestApp(StatefulWidget):
    def createState(self) -> TestAppState:
        return TestAppState()

# --- Application Runner ---
class Application:
    def __init__(self):
        print("Initializing Application...")
        self.framework = Framework()
        self.my_app = TestApp(key=Key("test_app_root")) # Give root a key
        self.state_instance: Optional[TestAppState] = None

    def schedule_tests(self):
        """Schedules a sequence of state changes."""
        if not self.state_instance:
            print("Error: State instance not available for scheduling tests.")
            return

        print("\n>>> Scheduling Test Sequence <<<")
        delays = [2000, 4000, 5000, 6000, 7000, 8000, 9000, 10000, 11000, 12000, 13000, 15000]
        actions = [
            lambda: print("\n--- Starting Tests ---"),
            self.state_instance.increment,           # Test Update
            self.state_instance.add_item,            # Test Insert
            self.state_instance.increment,           # Test Update
            self.state_instance.swap_items,          # Test Move (keyed)
            self.state_instance.toggle_extra,        # Test Conditional Insert
            self.state_instance.increment,           # Test Update
            self.state_instance.remove_last_item,    # Test Remove
            self.state_instance.toggle_extra,        # Test Conditional Remove
            self.state_instance.remove_first_item,   # Test Remove (keyed)
            self.state_instance.increment,           # Test Update
            lambda: print("\n>>> Test Sequence Complete <<<")
        ]

        for delay, action in zip(delays, actions):
            QTimer.singleShot(delay, action)


    def run(self):
        self.framework.set_root(self.my_app)

        # Get state instance *after* set_root ensures framework is linked
        if isinstance(self.my_app, StatefulWidget):
             self.state_instance = self.my_app.get_state()
        else:
             print("Error: Root widget is not a StatefulWidget.")
             return # Cannot schedule tests without state

        # Schedule tests *after* the event loop starts (run will block)
        # Use QTimer with 0 delay to run after initial events are processed
        QTimer.singleShot(0, self.schedule_tests)

        # Run the framework (starts Qt event loop via webwidget)
        self.framework.run(title='Framework Reconciliation Test') # Blocks here

# --- Main Execution ---
if __name__ == "__main__":
    # PySide6/Qt Application instance is usually created by webwidget.py or framework.run
    # If not, create it here:
    # app_instance = QCoreApplication.instance()
    # if app_instance is None:
    #     print("Creating QApplication instance...")
    #     from PySide6.QtWidgets import QApplication
    #     app_instance = QApplication(sys.argv)

    print("Starting Application...")
    app_runner = Application()
    app_runner.run()

    # No sys.exit(app_instance.exec()) needed here, framework.run handles it.
    print("Application Finished.")
