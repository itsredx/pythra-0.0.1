# dropdown.py
from ...styles import *
from ...widgets import *
from ...state import *
from .controller import DerivedDropdownController
from .style import DerivedDropdownTheme
from typing import Callable, List, Optional


# ==============================================================================
# 2. THE DROPDOWN WIDGET AND ITS STATE (The Core Component)
# ==============================================================================


class DerivedDropdown(StatefulWidget):
    """
    A composable dropdown widget that displays a menu of selectable items.
    Its value is controlled by a DerivedDropdownController.
    """

    def __init__(
        self,
        key: Key,
        controller: DerivedDropdownController,
        onChanged: Optional[Callable[[str], None]] = None,
        theme: Optional[DerivedDropdownTheme] = None,
    ):

        # Store configuration on the widget instance.
        self.controller = controller
        self.onChanged = onChanged
        self.theme = theme or DerivedDropdownTheme()

        # print("key init: ", key)

        # super().__init__() must be called to kick off the state creation lifecycle.
        super().__init__(key=key)

    def createState(self):
        return _DerivedDropdownState()


class _DerivedDropdownState(State):
    """Manages the internal UI state of the DerivedDropdown (e.g., if it's open)."""

    def __init__(self):
        self.is_open: bool = False
        self.controller: DerivedDropdownController = None
        self.theme: DerivedDropdownTheme = DerivedDropdownTheme()
        self.selected_value: Optional[Any] = None

    def initState(self):
        """Called once when the state is created."""

        # Listen for external changes to the controller's value
        self.get_widget().controller.add_listener(self._on_external_update)

    def dispose(self):
        """Called when the widget is removed, to prevent memory leaks."""
        self.get_widget().controller.remove_listener(self._on_external_update)

    def _on_external_update(self, new_value: str):
        """When the controller changes externally, just rebuild the widget."""
        self.setState()

    def toggle_dropdown(self, key):
        """Opens or closes the dropdown menu."""
        self.is_open = not self.is_open
        # if key[1] == self.selected_value:
        # print(self.selected_value)
        # print("Pressed dropdown key: ", key[0], key[1], key[2])
        self.setState()

    def select_item(self, value):
        """Handles item selection, updates the controller, and closes the menu."""
        widget = self.get_widget()
        if not widget:
            return

        # 1. Update the controller. This will trigger the listener.
        widget.controller.set_value(value[0])

        # 2. Close the dropdown menu.
        self.is_open = False

        # 3. Call the developer's onChanged callback.
        if widget.onChanged:
            widget.onChanged(value[0])

        # 4. We don't need a setState() here because the listener (_on_external_update)
        #    will be called by set_value, which in turn calls setState().
        #    However, to ensure the dropdown closes instantly, we'll call it.
        self.setState()

    def build(self) -> Widget:
        """Builds the dropdown UI, including the overlay menu if it's open."""
        widget = self.get_widget()
        if not widget:
            return SizedBox()  # Return empty if widget is gone

        # Get the authoritative configuration from the widget instance
        self.controller = widget.controller
        self.theme = widget.theme
        self.selected_value = self.controller.value

        # --- SOLUTION: Use the parent widget's key to create stable child keys ---
        parent_key = widget.key.value

        # --- Build the DerivedDropdown Menu (only if open) ---
        menu_items = []
        if self.is_open:
            menu_items.append(
                Container(
                    key=Key(f"dropdown_menu_container{parent_key}"),
                    margin=self.theme.dropdownMargin.edit(operation='+', top=40),
                    padding=self.theme.padding,
                    color=self.theme.dropdownColor,
                    width=self.theme.width,
                    zAxisIndex= 1900,
                    # padding=EdgeInsets.all(4),
                    decoration=BoxDecoration(
                        color=self.theme.dropdownColor,
                        borderRadius=BorderRadius.circular(self.theme.borderRadius),
                        boxShadow=[
                            BoxShadow(
                                color=Colors.rgba(0, 0, 0, 0.15),
                                blurRadius=12,
                                offset=Offset(0, 6),
                            )
                        ],
                    ),
                    child=Column(
                        mainAxisAlignment=MainAxisAlignment.START,
                        crossAxisAlignment=CrossAxisAlignment.START,
                        key=Key(f"dropdown_item_Column_{parent_key}"),
                        children=[
                            Container(
                                padding=self.theme.itemPadding
                                or EdgeInsets.symmetric(horizontal=12, vertical=8),
                                color=(
                                    self.theme.selectedItemColor
                                    if item == self.selected_value
                                    else Colors.transparent
                                ),
                                width="100%",
                                decoration=BoxDecoration(
                                    borderRadius=self.theme.selectedItemShape
                                    or BorderRadius.circular(4),
                                ),
                                key=Key(f"dropdown_item_{item}_padding_{parent_key}"),
                                child=ListTile(
                                    key=Key(f"dropdown_item_{item}_{parent_key}"),
                                    title=Text(
                                        item,
                                        key=Key(
                                            f"dropdown_item_title_{item}_{parent_key}"
                                        ),
                                        style=TextStyle(
                                            color=self.theme.dropdownTextColor
                                        ),
                                    ),
                                    onTap=self.select_item,
                                    onTapName=f"item_tap_callback_{id(self.select_item)}",
                                    onTapArg=[item],
                                    selected=item == self.selected_value,
                                    selectedTileColor=self.theme.selectedItemColor,
                                    contentPadding=EdgeInsets.symmetric(
                                        horizontal=12, vertical=8
                                    ),
                                ),
                            )
                            for item in self.controller.items
                        ],
                    ),
                )
            )
        # print("widget key: ", widget.key, parent_key)
        # --- Build the Main Display Box ---
        main_box = TextButton(
            key=Key(f"dropdown_button_{parent_key}_{self.controller.items, self.selected_value}"),
            onPressed=self.toggle_dropdown,
            onPressedArgs=[
                "dropdown_button_",
                self.selected_value,
                self.controller.items,
            ],
            onPressedName=f"my_dropdown_toggle_callback_{id(self.toggle_dropdown)}",
            style=ButtonStyle(
                padding=EdgeInsets.all(0),
                shape=BorderRadius.circular(self.theme.borderRadius),
            ),  # Remove default button padding
            child=Container(
                key=Key(f"dropdown_button_{parent_key}_container"),
                padding=self.theme.padding,
                width=self.theme.width,
                decoration=BoxDecoration(
                    color=self.theme.backgroundColor,
                    border=BorderSide(
                        width=self.theme.borderWidth, color=self.theme.borderColor
                    ),
                    borderRadius=BorderRadius.circular(self.theme.borderRadius),
                ),
                child=Row(
                    key=Key(f"dropdown_button_{parent_key}_row"),
                    mainAxisAlignment=MainAxisAlignment.SPACE_BETWEEN,
                    crossAxisAlignment=CrossAxisAlignment.CENTER,
                    children=[
                        Text(
                            self.selected_value or "Select...",
                            key=Key(f"dropdown_button_{parent_key}_text"),
                            style=TextStyle(
                                color=self.theme.textColor, fontSize=self.theme.fontSize
                            ),
                        ),
                        SizedBox(
                            width=8,
                            key=Key(f"dropdown_button_{parent_key}_icon_padding"),
                        ),
                        Icon(
                            Icons.arrow_drop_down_rounded,
                            key=Key(f"dropdown_button_{parent_key}_icon"),
                            color=self.theme.textColor,
                            size=20,
                        ),
                    ],
                ),
            ),
        )
        # print("dropdown margin: ", self.theme.dropdownMargin)

        # print("key: ", f"dropdown_op_container_{parent_key}_icon")

        # --- Use a Stack to layer the menu over other content ---
        # `clipBehavior=ClipBehavior.NONE` is crucial to allow the menu
        # to draw outside the bounds of the Stack's original layout space.
        return Container(
            key=Key(f"dropdown_op_Stack_{parent_key}_root_container"),
            child=Stack(
                key=Key(f"dropdown_op_Stack_{parent_key}_icon"),
                clipBehavior=ClipBehavior.NONE,
                children=[
                    # The main box is the base layer of the stack.
                    main_box,
                    # The menu is positioned relative to the Stack.
                    Positioned(
                        key=Key(f"dropdown_op_Positioned_{parent_key}_icon"),
                        top=450,  # Position it just below the main box (adjust as needed)
                        left=0,
                        right=0,
                        width=self.theme.width,
                        child=(
                            Container(
                                key=Key(f"dropdown_op_container_{parent_key}_icon"),
                                child=Column(
                                    key=Key(
                                        f"dropdown_op_container_column_{parent_key}_icon"
                                    ),
                                    mainAxisAlignment=MainAxisAlignment.START,
                                    crossAxisAlignment=CrossAxisAlignment.START,
                                    children=menu_items,
                                ),
                                decoration=BoxDecoration(
                                    borderRadius=BorderRadius.circular(
                                        self.theme.borderRadius
                                    ),
                                ),
                            )
                            if self.is_open
                            else Container(
                                child=SizedBox(width=0),
                            )
                        ),  # The menu will only appear if `is_open` is true
                    ),
                ],
            )
        )




"""
# ==============================================================================
# 3. EXAMPLE USAGE
# ==============================================================================
class myLangDropDownState(State):

    def build(self):
        another_controller = DerivedDropdownController(
            value="Python", items=["Python", "Rust", "JavaScript", "C++"]
        )
        return DerivedDropdown(
            key=Key("lang_dropdown"),
            controller=another_controller,
            onChanged=lambda: print(f"Language changed to: "),
        )


class myLangDropDown(StatefulWidget):
    def __init__(self, key: Key):
        super().__init__(key=key)

    def createState(self):
        return myLangDropDownState()


fruit = ""


class myFruitDropDownState(State):
    def __init__(self):
        self.current_fruit = "Banana"

        self.dropdown_controller = DerivedDropdownController(
            value="Apple", items=["Apple", "Orange", "Banana", "Grape", "Mango"]
        )

    def set_fruit_to_banana(self):
        # Programmatically update the controller from outside the widget
        self.dropdown_controller.set_value("Banana")

    def set_fruit(self, v):
        print(f"Fruit changed to: {v}")
        self.current_fruit = v
        self.setState()

    def get_fruit(self):
        return self.current_fruit

    def build(self):
        return DerivedDropdown(
            key=Key("fruit_dropdown"),
            controller=self.dropdown_controller,
            onChanged=lambda v: self.set_fruit(v),
            theme=DerivedDropdownTheme(
                borderColor=Colors.hex("#CCCCCC"),
                dropdownColor=Colors.hex("#F9F9F9"),
                selectedItemColor=Colors.hex("#E0E0E0"),
            ),
        )


class myFruitDropDown(StatefulWidget):
    def __init__(self, key: Key):
        super().__init__(key=key)

    def createState(self):
        return myFruitDropDownState()


class MyFormState(State):
    def __init__(self):
        self.langdrop = myLangDropDown(key=Key("lang_dr"))
        self.fruitdrop = myFruitDropDown(key=Key("fruit_dr"))

    # def initState(self):

    #     # The controller is the source of truth for the dropdown's state.

    def build(self):
        # print("Cur fur: ", self.fruitdrop.get_fruit())
        return Container(
            key=Key("dropdown_root_container"),
            padding=EdgeInsets.all(32),
            alignment=Alignment.top_center(),
            child=Column(
                key=Key("dropdown_column"),
                crossAxisAlignment=CrossAxisAlignment.START,
                children=[
                    Text(
                        "Select a Lang:",
                        style=TextStyle(fontSize=16),
                    ),
                    SizedBox(height=8),
                    self.langdrop,
                    SizedBox(height=64),
                    Text("Select a Fruit:", style=TextStyle(fontSize=16)),
                    SizedBox(height=8),
                    self.fruitdrop,
                    SizedBox(height=24),
                    Text("Select a Car:", style=TextStyle(fontSize=16)),
                    # TextButton(
                    #     onPressed=self.set_fruit_to_banana,
                    #     child=Text("Set Fruit to Banana Externally"),
                    # ),
                ],
            ),
        )


class MyForm(StatefulWidget):
    def __init__(self, key: Key):
        super().__init__(key=key)

    def createState(self):
        return MyFormState()


if __name__ == "__main__":
    # It's crucial to instantiate the Framework *before* any widgets are created.
    app = Framework.instance()

    # Now that the framework is linked to the base Widget class, we can create our app.
    my_app = MyForm(key=Key("my_app_root"))

    app.set_root(my_app)
    app.run(title="DerivedDropdown Test")
"""