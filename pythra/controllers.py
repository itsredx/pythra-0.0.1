# =============================================================================
# PYTHRA CONTROLLERS - The "Remote Controls" for Interactive Widgets
# =============================================================================
#
# Controllers are the "remote controls" that let you programmatically interact
# with widgets from your application code. Think of them like TV remote controls:
# - You can change the channel (set values)
# - You can check what's currently showing (get values) 
# - You can get notified when something changes (add listeners)
#
# This file contains all the controller classes that manage state for
# interactive widgets like text fields, sliders, dropdowns, etc.
#
# =============================================================================

from typing import Any, List, Optional, Callable
import json
import weakref


# =============================================================================
# TEXT EDITING CONTROLLER - The "Keyboard Manager" for Text Input
# =============================================================================

class TextEditingController:
    """
    The "remote control" for text input fields - manages text content and notifies you of changes.
    
    **What is TextEditingController?**
    Think of this as a "smart notepad" that not only holds text, but also tells you
    when someone writes or erases something. It's the bridge between your TextField
    widget and your application logic.
    
    **Real-world analogy:**
    Like a shared Google Doc:
    - You can write text in it (set text)
    - You can read what's currently written (get text)
    - You can get notified when someone else changes it (add listeners)
    - Multiple people can "watch" for changes (multiple listeners)
    
    **When to use TextEditingController:**
    - User input forms (name, email, password fields)
    - Search boxes that need to react to typing
    - Chat applications where you need to process messages
    - Any time you need to programmatically control text input
    
    **Key features:**
    1. **Text storage**: Holds the current text value
    2. **Change detection**: Automatically detects when text changes
    3. **Observer pattern**: Notifies listeners when changes happen
    4. **Programmatic control**: You can set text from code
    
    **Basic usage pattern:**
    ```python
    # 1. Create a controller
    name_controller = TextEditingController(text="John Doe")
    
    # 2. Use it in a TextField
    name_field = TextField(
        key=Key("name"),
        controller=name_controller,
        decoration=InputDecoration(label="Full Name")
    )
    
    # 3. Read the current value anytime
    current_name = name_controller.text
    
    # 4. Set a new value programmatically
    name_controller.text = "Jane Smith"  # This will update the UI!
    
    # 5. Listen for changes
    def on_name_changed():
        print(f"Name changed to: {name_controller.text}")
        # Maybe validate the input, save to database, etc.
    
    name_controller.add_listener(on_name_changed)
    ```
    
    **Advanced example - Form validation:**
    ```python
    email_controller = TextEditingController()
    error_message = ""
    
    def validate_email():
        global error_message
        email = email_controller.text
        if "@" not in email:
            error_message = "Please enter a valid email"
        else:
            error_message = ""
        # Trigger UI rebuild to show/hide error
        framework.rebuild()
    
    email_controller.add_listener(validate_email)
    ```
    
    Args:
        text: The initial text content (default: empty string)
    
    Attributes:
        text: Current text value (can be read and written)
        
    Methods:
        add_listener(): Register a function to call when text changes
        remove_listener(): Unregister a change listener
        clear(): Quickly erase all text
    """
    def __init__(self, text: str = ""):
        self._text = text
        self._listeners: List[Callable[[], None]] = []

    @property
    def text(self) -> str:
        """The current text value of the controller."""
        return self._text

    @text.setter
    def text(self, new_value: str):
        """Sets the text value and notifies all listeners of the change."""
        if self._text != new_value:
            self._text = new_value
            self._notify_listeners()

    def add_listener(self, listener: Callable[[], None]):
        """Register a closure to be called when the text in the controller changes."""
        if listener not in self._listeners:
            self._listeners.append(listener)

    def remove_listener(self, listener: Callable[[], None]):
        """Remove a previously registered closure."""
        if listener in self._listeners:
            self._listeners.remove(listener)

    def _notify_listeners(self):
        """Calls all registered listeners."""
        for listener in self._listeners:
            listener()

    def clear(self):
        """Clears the text in the controller."""
        self.text = ""

    def __repr__(self):
        return f"TextEditingController(text='{self.text}')"


# class SliderController:
#     """Manages the value for a Slider widget."""
#     def __init__(self, value: float = 0.0):
#         self._value = value
#         self._listeners: List[Callable] = []

#     @property
#     def value(self) -> float:
#         return self._value

#     @value.setter
#     def value(self, new_value: float):
#         # Use a tolerance for float comparison
#         if abs(self._value - new_value) > 1e-9:
#             self._value = new_value
#             self._notify_listeners()

#     def addListener(self, listener: Callable):
#         """Register a closure to be called when the value changes."""
#         self._listeners.append(listener)

#     def removeListener(self, listener: Callable):
#         """Remove a previously registered closure."""
#         if listener in self._listeners:
#             self._listeners.remove(listener)

#     def _notify_listeners(self):
#         """Call all registered listeners."""
#         for listener in self._listeners:
#             listener()

#     def __repr__(self):
#         return f"SliderController(value={self._value})"

# =============================================================================
# SLIDER CONTROLLER - The "Volume Knob" for Range Inputs
# =============================================================================

class SliderController:
    """
    The "volume knob" for sliders - keeps track of the slider's position and status.
    
    **What is SliderController?**
    A SliderController manages the numeric value of a Slider widget (like a volume slider
    or brightness control). It knows both the current value and whether the user has
    finished dragging (useful for knowing when to save the final value).
    
    **Real-world analogy:**
    Like a dimmer switch for lights:
    - You can see the current brightness level (value)
    - You can set the brightness from elsewhere (change value)
    - You can tell when someone stops adjusting it (isDragEnded)
    
    **When to use SliderController:**
    - Volume controls in media players
    - Brightness/contrast adjustments
    - Progress indicators (e.g., video playback position)
    - Any numeric input with a visual range representation
    - Settings that have a continuous range (font size, zoom level)
    
    **Key features:**
    1. **Value storage**: Holds the current slider value (0.0 to 1.0 by default)
    2. **Drag state**: Indicates if user is actively dragging or has finished
    3. **Direct control**: You can set values programmatically
    
    **Example usage:**
    ```python
    # Create a controller with an initial value of 0.5 (halfway)
    volume_controller = SliderController(value=0.5)
    
    # Use it in a Slider widget
    volume_slider = Slider(
        key=Key("volume"),
        controller=volume_controller,
        min=0.0,
        max=100.0,
        divisions=10,  # Optional tick marks
        label="Volume",
    )
    
    # Read the current value anywhere in your code
    current_volume = volume_controller.value
    
    # Set a new value programmatically
    def mute_audio():
        volume_controller.value = 0.0
        # Remember to call setState() to update the UI
    ```
    
    Args:
        value: The initial numeric value (default: 0.0)
        isDragEnded: Whether drag operation is complete (used internally)
    
    Attributes:
        value: The current slider value (read/write)
        isDragEnded: Flag indicating if user has released the slider
    """
    def __init__(self, value: float = 0.0, isDragEnded: bool = False):
        self.value = value
        self.isDragEnded = isDragEnded




# =============================================================================
# DROPDOWN CONTROLLER - The "Menu Selector" for DropdownButton
# =============================================================================

class DropdownController:
    """
    The "menu manager" for dropdown fields - tracks selected item and open/closed state.
    
    **What is DropdownController?**
    A DropdownController keeps track of what's currently selected in a dropdown menu
    and whether the dropdown is currently expanded or collapsed. It bridges your
    DropdownButton widget with your application's logic.
    
    **Real-world analogy:**
    Like a TV's input selector:
    - Shows what input is currently selected (HDMI, AV, etc.)
    - Can be in open or closed state (menu displayed or hidden)
    - Can be controlled programmatically (remote) or manually (buttons)
    
    **When to use DropdownController:**
    - Selection menus (categories, sort orders, filters)
    - Settings that have discrete options (language, theme, font)
    - Form fields with predefined choices (state/province, country)
    - Navigation between related views
    
    **Key features:**
    1. **Selection tracking**: Remembers what item is currently chosen
    2. **Open/close state**: Keeps track of whether the menu is expanded
    3. **Programmatic control**: You can set the selected value from code
    
    **Example usage:**
    ```python
    # Create a controller with "Medium" initially selected
    size_controller = DropdownController(selectedValue="Medium")
    
    # Available options
    size_options = ["Small", "Medium", "Large", "X-Large"]
    
    # Use it in a dropdown widget
    size_dropdown = DropdownButton(
        key=Key("size_selector"),
        controller=size_controller,
        items=[DropdownMenuItem(value=size, child=Text(size)) for size in size_options],
        hint=Text("Select Size"),
    )
    
    # Read the current selection anywhere
    current_size = size_controller.selectedValue
    
    # Set a new selection programmatically
    def reset_to_default():
        size_controller.selectedValue = "Medium"
        # Remember to call setState() to update the UI
    ```
    
    Args:
        selectedValue: The initially selected item (default: None = nothing selected)
    
    Attributes:
        selectedValue: The currently selected item (read/write)
        isOpen: Whether the dropdown menu is currently expanded (internal use)
    """
    def __init__(self, selectedValue: Any = None):
        self.selectedValue = selectedValue
        self.isOpen = False # Internal state for toggling, managed by JS engine




class VirtualListController:
    """
    A controller for a VirtualListView.

    This allows a parent widget to programmatically command the list to
    refresh its content when the underlying data source changes.
    """
    def __init__(self):
        self._state: Optional['_VirtualListViewState'] = None # type: ignore

    def _attach(self, state: '_VirtualListViewState'): # type: ignore
        """Internal method for the state to link itself to the controller."""
        self._state = state

    def _detach(self):
        """Internal method to unlink."""
        self._state = None

    def refresh(self):
        """Commands the virtual list to clear its cache and re-render visible items."""
        
        if self._state:
            print("Refreshing")
            self._state.refresh_js(indices=None)
            print("Refreshed")

    def refreshItem(self, index: int):
        """Commands the virtual list to refresh a single item at a specific index."""
        if self._state:
            self._state.refresh_js(indices=[index]) # Pass a specific index




class MarkdownEditingController:
    def __init__(self, initialText: str = ""):
        self.markdown = initialText
        self._listeners = []
        self._js_instance_name: Optional[str] = None
        self._framework_ref: Optional[weakref.ref['Framework']] = None # type: ignore

    def _attach_js(self, instance_name: str, framework: 'Framework'): # type: ignore
        self._js_instance_name = instance_name
        self._framework_ref = weakref.ref(framework)

    def add_listener(self, listener: Callable):
        self._listeners.append(listener)

    def remove_listener(self, listener: Callable):
        self._listeners.remove(listener)

    def _notify_listeners(self):
        for listener in self._listeners:
            listener()

    def execCommand(self, command: str, payload: Optional[Any] = None):
        """Commands the JS editor to execute a command like 'bold' or 'addLink'."""
        framework = self._framework_ref() if self._framework_ref else None
        if self._js_instance_name and framework:
            # Escape for JS string
            command_str = json.dumps(command)
            payload_str = json.dumps(payload) if payload is not None else 'null'
            
            script = f"window._pythra_instances['{self._js_instance_name}']?.execCommand({command_str}, {payload_str});"
            framework.window.evaluate_js(framework.id, script)

    def setMarkdown(self, markdown: str):
        """Sets the entire content of the editor."""
        self.markdown = markdown
        # ... similar logic to send command to JS ...