import sys
from typing import Optional, Set, Callable

# --- Framework Imports ---
# Import everything needed to build the UI
from pythra import (
    Framework,
    State,
    StatefulWidget,
    StatelessWidget,
    Key,
    Widget,
    Container,
    ElevatedButton,
    VirtualListController,
    Column,
    Row,
    Text,
    ListTile,
    Checkbox,
    VirtualListView,
    ScrollbarTheme,
    Colors,
    EdgeInsets,
    Alignment,
    TextStyle,
    BorderSide,
    BorderRadius,
    BoxDecoration,
    MainAxisAlignment,
    CrossAxisAlignment,
    SizedBox,
    Expanded,
)
import json
from matplotlib import font_manager

def get_system_fonts_as_json():
    """
    Finds all unique system font families and formats them into a JSON string
    suitable for a dropdown, with common fonts placed at the top.
    
    Returns:
        str: A JSON string representing a list of font dictionaries.
    """
    
    # 1. Define a list of common, high-priority fonts.
    # The "System Default" uses a robust CSS font stack.
    default_fonts = [
        { "label": "System Default", "val": '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif' },
        { "label": "Arial", "val": "Arial, sans-serif" },
        { "label": "Verdana", "val": "Verdana, sans-serif" },
        { "label": "Times New Roman", "val": "'Times New Roman', serif" },
        { "label": "Georgia", "val": "Georgia, serif" },
        { "label": "Courier New", "val": "'Courier New', monospace" },
    ]
    
    # 2. Get all unique font family names from the system.
    # We use a set to automatically handle duplicates.
    try:
        font_paths = font_manager.findSystemFonts(fontpaths=None, fontext='ttf')
        font_names = sorted({font_manager.FontProperties(fname=fname).get_name() for fname in font_paths})
    except Exception as e:
        print(f"Warning: Could not get system fonts. Falling back to defaults. Error: {e}")
        font_names = []

    # 3. Combine the lists.
    # Start with our defaults, then add unique system fonts that aren't already in the default list.
    final_font_list = list(default_fonts)
    default_labels = {font['label'] for font in default_fonts}
    
    for name in font_names:
        if name not in default_labels:
            final_font_list.append({"label": name, "val": name})
            
    # 4. Convert the final list to a JSON string.
    return json.dumps(final_font_list, indent=2)
# --- Application-specific Data ---

# A simple data store to hold the checked state for our 10,000 items.
# In a real app, this might come from a database or API.
checked_items: Set[int] = set()

# --- Reusable List Item Widget ---

# Creating a stateless widget for the list item is good practice.
# It keeps the main build method clean.

formatted_fonts_json = get_system_fonts_as_json()
# print(json.loads(formatted_fonts_json))
labels = []
for font in json.loads(formatted_fonts_json):
    labels.append(font['label'])

# In v_list.py


class MyListItemState(State):
    def __init__(self):
        # The __init__ method should be simple and call its parent.
        super().__init__()
        # Declare instance variables here, but don't set them from the widget yet.
        self.index = -1
        self.on_checked = None
        self.is_checked = False

    def initState(self):
        """
        This is the correct lifecycle method to access the widget's properties.
        It's called after the state has been linked to its widget.
        """
        widget = self.get_widget()
        if not widget:
            return

        # Pull the configuration FROM the widget into the state.
        self.index = widget.index
        self.on_checked = widget.on_checked
        self.is_checked = self.index in checked_items
        self.parent_key = widget.key.value

        

    def build(self) -> Widget:
        item = labels[self.index]
        # A standard ListTile containing a Checkbox and Text.
        return Container(
                                # height=self.theme.dropdownHeight,
                                padding=EdgeInsets.symmetric(horizontal=16)
                                or EdgeInsets.symmetric(horizontal=12, vertical=8),
                                color=(
                                    Colors.rgba(103, 80, 164, 0.1)
                                    if item == self.is_checked
                                    else Colors.transparent
                                ),
                                width="100%",
                                decoration=BoxDecoration(
                                    borderRadius=BorderRadius.circular(4),
                                ),
                                key=Key(f"dropdown_item_{item}_padding_{self.parent_key}"),
                                child=ListTile(
                                    key=Key(f"dropdown_item_{item}_{self.parent_key}"),
                                    title=Text(
                                        item,
                                        key=Key(
                                            f"dropdown_item_title_{item}_{self.parent_key}"
                                        ),
                                        style=TextStyle(
                                            color=Colors.black
                                        ),
                                    ),
                                    onTap=self.on_checked,
                                    onTapName=f"item_tap_callback_{id(self.is_checked)}",
                                    onTapArg=[item],
                                    selected=item == self.is_checked,
                                    selectedTileColor=Colors.rgba(103, 80, 164, 0.1),
                                    contentPadding=EdgeInsets.symmetric(
                                        horizontal=12, vertical=8
                                    ),
                                ),
                            )
        # Container(
        #     key=Key(f"item_{self.index}"),
        #     margin=EdgeInsets.symmetric(horizontal=16, vertical=10),
        #     padding=EdgeInsets.symmetric(horizontal=16),
        #     height=50, 
        #     alignment=Alignment.center(),
        #     color=(
        #         Colors.rgba(103, 80, 164, 0.1)
        #         if self.is_checked
        #         else Colors.transparent
        #     ),  # A light purple
        #     child=Row(
        #         crossAxisAlignment=CrossAxisAlignment.CENTER,
        #         children=[
        #             Checkbox(
        #                 key=Key(f"cb_{self.index}_checkbox"),
        #                 value=self.is_checked,
        #                 onChanged=self.on_checked,
        #             ),
        #             SizedBox(key=Key(f"cb_{self.index}_sizedbox"), width=16),
        #             Text(f"List Item Number {self.index + 1}"),
        #         ],
        #     ),
        # )


class MyListItem(StatefulWidget):
    def __init__(self, key: Key, index: int, on_checked: Callable[[bool], None]):
        # This widget correctly stores the configuration data. No changes needed here.
        self.index = index
        self.on_checked = on_checked
        super().__init__(key=key)

    def createState(self) -> MyListItemState:
        # This is correct. It creates a "blank" state object.
        return MyListItemState()


# --- The rest of your v_list.py file is correct. ---
# VirtualListTestState, itemBuilder, VirtualListTestApp, etc. are all perfect.


# --- Main Application State ---


class VirtualListTestState(State):
    def __init__(self):
        """Initialize the application state."""
        self.item_count = len(labels)
        checked_items.add(0)
        # This will be initialized in initState
        self.itemBuilder = None
        

    def initState(self):
        """Initialize the application state and create stable callbacks."""
        checked_items.add(0)
        # --- THIS IS THE FIX ---
        # Define the itemBuilder here, once. It will now be a stable
        # instance variable on the state object.
        self.itemBuilder = self._build_one_item
        self.data_version = 0 # <-- NEW: Initialize data version counter
        # --- END OF FIX ---

        # --- THIS IS THE FIX ---
        # 1. Create and own the controller for the virtual list.
        self.list_controller = VirtualListController()
        # --- END OF FIX ---

    def _build_one_item(self, index: int) -> Widget:
        """
        This is the actual builder function. It's now a stable method
        on the state class.
        """
        # print("Building list item: ", index) # Keep for debugging if you like
        return MyListItem(
            key=Key(f"list_item_{index}"),
            index=index,
            on_checked=lambda new_value: self.handle_item_checked(index, new_value),
        )


    def handle_item_checked(self, index: int, new_value: bool):
        """
        Callback passed to the itemBuilder. This is where the application's
        main state is modified.
        """
        print(f"Item {index} checked state changed to: {new_value}")
        if new_value:
            checked_items.add(index)
        elif index in checked_items:
            checked_items.remove(index)


        # --- THIS IS THE FIX ---
        # 1. Command the list to refresh ONLY the specific item that changed.
        self.list_controller.refreshItem(index=index)

        # 2. After changing the data, explicitly command the list to refresh.
        # self.list_controller.refresh()

        # We must call setState to trigger a rebuild, which will pass the
        # new `checked_items` data down to the VirtualListView.
        self.setState()

    def build(self) -> Widget:
        """Builds the main application UI."""
        return Container(
            color=Colors.background,
            width="100vw",
            height="100vh",
            padding=EdgeInsets.all(20),
            child=Column(
                crossAxisAlignment=CrossAxisAlignment.STRETCH,
                children=[
                    Text(
                        f"Virtual List Test ({self.item_count} Items)",
                        style=TextStyle(fontSize=24, fontWeight="bold"),
                    ),
                    Text(
                        f"{len(checked_items)} item(s) selected. Scroll to see virtualization in action."
                    ),
                    SizedBox(height=16),
                    # Use Expanded to make the list fill the remaining space
                    Container(
                        height="80vh",
                        # Add a border to clearly see the list's boundaries
                        decoration=BoxDecoration(
                            border=BorderSide(color=Colors.outlineVariant, width=1)
                        ),
                        child=VirtualListView(
                            key=Key("my_virtual_list"),
                            controller=self.list_controller, # <-- 4. Pass the controlle
                            itemCount=self.item_count,
                            itemBuilder=self.itemBuilder, 
                            initialItemCount=12,                           
                            itemExtent=60.0,  # Each ListTile will be 50px high
                            # Optionally, provide a custom theme for the scrollbar
                            theme=ScrollbarTheme(
                                width=14,
                                thumbColor=Colors.lightpink,
                                trackColor=Colors.hex("#3535353e"),
                                thumbHoverColor=Colors.hex("#9c9b9b"),
                                radius=6,
                            ),
                        ),
                    ),
                ],
            ),
        )


# --- Application Entry Point ---


class VirtualListTestApp(StatefulWidget):
    def createState(self) -> VirtualListTestState:
        return VirtualListTestState()


# --- THIS IS THE NEW CONVENTION ---
def main() -> Widget:
    """
    This function is the main entry point that the Pythra CLI will call.
    It should return the root widget of the application.
    """
    return VirtualListTestApp(key=Key("app_root"))

if __name__ == "__main__":
    # Standard application runner
    app = Framework.instance()
    app.set_root(main())
    app.run(title="Pythra Virtual List Test")
