# =============================================================================
# PYTHRA STATE MANAGEMENT SYSTEM - The "Memory" of Your App
# =============================================================================

"""
PyThra State Management System

This is the "memory system" of your PyThra app - it handles widgets that need to 
remember things and change over time (like counters, form inputs, shopping carts, etc.)

**Key Concepts:**
1. **StatefulWidget**: A widget that can change and "remember" things
2. **StatelessWidget**: A widget that never changes (like static text or images)
3. **State**: The "brain" that manages what a StatefulWidget remembers

**Real-world analogy:**
- StatelessWidget = A printed poster (never changes)
- StatefulWidget = A digital display screen (can show different content)
- State = The computer controlling what the digital screen shows

**When to use which:**
- Use StatelessWidget for things that never change (logos, static text)
- Use StatefulWidget for interactive elements (buttons with counters, forms, etc.)
"""

import weakref
import time
from PySide6.QtCore import QTimer
from typing import Optional, TYPE_CHECKING

# Import base classes needed at runtime
from .base import Widget, Key

# Use TYPE_CHECKING to prevent circular imports for type hints
if TYPE_CHECKING:
    from .core import Framework # Framework uses State, State uses Framework
    # No need to import StatefulWidget itself if defined in this file

# =============================================================================
# STATEFUL WIDGET - Widgets That Can "Remember" and Change
# =============================================================================

class StatefulWidget(Widget):
    """
    A widget that can change and "remember" things - like a counter button or a form input.
    
    **What makes it "Stateful"?**
    Unlike a StatelessWidget (which is like a printed poster that never changes),
    a StatefulWidget is like a digital screen that can show different content over time.
    
    **How it works:**
    1. **Widget**: The "screen" that displays something to the user
    2. **State**: The "computer" that controls what the screen shows
    3. **Connection**: They're linked together so they can communicate
    
    **Real-world examples:**
    - Counter button (remembers the current count)
    - Text input field (remembers what you've typed)
    - Shopping cart (remembers what items are in it)
    - Toggle switch (remembers if it's on or off)
    
    **Key difference from StatelessWidget:**
    ```python
    # StatelessWidget - always shows the same thing
    class Welcome(StatelessWidget):
        def build(self):
            return Text("Welcome to my app!")  # Never changes
    
    # StatefulWidget - can show different things
    class Counter(StatefulWidget):
        def createState(self):
            return CounterState()  # Has a "brain" that manages changing data
    ```
    
    **Usage:**
    You inherit from this class and implement createState() to define what
    your widget needs to "remember".
    """
    _framework_ref: Optional[weakref.ref['Framework']] = None

    @classmethod
    def set_framework(cls, framework: 'Framework'):
        cls._framework_ref = weakref.ref(framework)

    def __init__(self, key: Optional[Key] = None):
        super().__init__(key=key) # Pass key to base Widget
        # Framework reference for the *instance*
        # self.framework: Optional['Framework'] = self._framework_ref() if self._framework_ref else None
        self._state = self.createState() # Create the associated State object
        self._state._set_widget(self) # Link State back to this widget instance
        self._state.initState() # <-- CALL THE NEW LIFECYCLE HOOK

    def createState(self) -> 'State': # Hint uses forward reference 'State'
        """Create the mutable state for this widget."""
        raise NotImplementedError(f"{self.__class__.__name__} must implement createState()")

    def get_state(self) -> 'State': # Hint uses forward reference 'State'
        """Returns the associated State object."""
        return self._state


# =============================================================================
# STATELESS WIDGET - Widgets That Never Change (Like Static Posters)
# =============================================================================

class StatelessWidget(Widget):
    """
    A widget that never changes - like a printed poster or a road sign.
    
    **What makes it "Stateless"?**
    "Stateless" means it has no memory and doesn't change. Once you create it,
    it shows the same thing forever (unless you rebuild the entire widget tree).
    
    **Think of it like:**
    - A printed poster on a wall (the content never changes)
    - A road sign (always shows the same message)
    - A company logo (looks the same every time)
    
    **When to use StatelessWidget:**
    - Static text that never changes ("Welcome to my app!")
    - Images that are always the same
    - Layout containers that don't need to remember anything
    - Navigation bars with fixed content
    
    **How it works:**
    1. You create a StatelessWidget by inheriting from this class
    2. You implement the build() method to return other widgets
    3. The build() method is called once when the widget is created
    4. The result is always the same (given the same input parameters)
    
    **Example:**
    ```python
    class WelcomeMessage(StatelessWidget):
        def __init__(self, name):
            super().__init__()
            self.name = name  # This won't change after creation
            
        def build(self):
            return Text(f"Welcome, {self.name}!")  # Always shows the same welcome
    ```
    
    **Key principle:**
    The build() method should always return the same widget structure
    when given the same constructor parameters. No surprises, no changes!
    """
    def __init__(self, key: Optional[Key] = None):
        super().__init__(key=key)

    def build(self) -> Widget:
        """
        Describes the part of the user interface represented by this widget.

        The framework calls this method when this widget is inserted into the tree.
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement the build() method."
        )

# =============================================================================
# STATE CLASS - The "Brain" That Controls StatefulWidgets
# =============================================================================

class State:
    """
    The "brain" that controls what a StatefulWidget shows and remembers.
    
    **What is State?**
    State is like the "computer" that controls a digital display screen (StatefulWidget).
    It holds all the data that can change, and tells the screen what to show.
    
    **Real-world analogy:**
    Think of a vending machine:
    - StatefulWidget = The display screen showing "Insert $2.50"
    - State = The computer inside that tracks money inserted, items selected, etc.
    - When you insert money, the State updates and tells the screen to show "$1.00 inserted"
    
    **What does State manage?**
    - Variables that change over time (like counters, user input, etc.)
    - Business logic (what happens when buttons are clicked)
    - UI updates (when to refresh the display)
    
    **Key State responsibilities:**
    1. **Memory**: Stores data that changes (like `self.counter = 0`)
    2. **Logic**: Handles events (like `def increment(): self.counter += 1`)
    3. **Updates**: Tells PyThra when the UI needs to refresh (`self.setState()`)
    4. **Lifecycle**: Handles setup and cleanup (initState, dispose)
    
    **Example State class:**
    ```python
    class CounterState(State):
        def initState(self):
            self.count = 0  # This is what we "remember"
            
        def increment(self):
            self.count += 1  # Change the data
            self.setState()  # Tell PyThra "please update the UI!"
            
        def build(self):
            return Button(
                text=f"Count: {self.count}",
                onClick=self.increment  # Wire up the logic
            )
    ```
    
    **Lifecycle methods you can override:**
    - initState(): Called once when created (like __init__ but for UI)
    - build(): Called whenever UI needs to update (returns the widgets to show)
    - dispose(): Called when removed (cleanup timers, save data, etc.)
    """
    def __init__(self):
        self._widget_ref: Optional[weakref.ref['StatefulWidget']] = None
        self.framework: Optional['Framework'] = None # Initialized in _set_widget

    def _set_widget(self, widget: 'StatefulWidget'): # Hint uses forward reference
        """Internal method to link State to its StatefulWidget and get framework."""
        self._widget_ref = weakref.ref(widget)
        # Get framework reference *from the widget instance*
        self.framework = getattr(widget, 'framework', None)
        if not self.framework:
             # This check is now more robust
             print(f"Warning: Framework not found on widget {widget} during State linking.")

    def initState(self):
        """
        Called once when this state object is inserted into the tree.
        
        This is the right place for one-time initialization, such as
        subscribing to controllers or streams.
        """
        pass # Default implementation does nothing

    def dispose(self):
        """
        Called when this state object is removed from the tree permanently.
        
        Subclasses should override this method to release any resources,
        such as unsubscribing from controllers or streams, to prevent
        memory leaks.
        """
        pass # Default implementation does nothing

    def didUpdateWidget(self, oldWidget: 'StatefulWidget', new_widget: 'StatefulWidget'):
        """
        Called whenever the widget configuration changes.

        If the parent widget rebuilds and creates a new instance of this
        widget (with the same key and type), this method is called to notify
        the state object of the new configuration.

        This is the right place to re-subscribe to controllers or update
        internal state based on the new widget properties.
        """
        pass # Default implementation does nothing


    def get_widget(self) -> Optional['StatefulWidget']: # Hint uses forward reference
        """Safely retrieves the associated StatefulWidget instance."""
        return self._widget_ref() if self._widget_ref else None

    def build(self) -> Optional['Widget']: # Return Optional[Widget]
        """Describes the part of the user interface represented by this state."""
        raise NotImplementedError(f"{self.__class__.__name__} must implement build()")

    def setState(self):
        """Notify the framework that the internal state of this object has changed."""
        widget = self.get_widget()
        if not widget:
            print(f"⚠️ PyThra State | Cannot setState for {self.__class__.__name__} - widget reference lost")
            return

        if self.framework:
            # Use getattr for safety, though framework should exist if widget exists
            key_info = getattr(widget, 'key', None)
            print(f"🔄 PyThra State | setState triggered: {self.__class__.__name__} (Widget Key: {key_info})")
            # Pass 'self' (the State instance) to the framework
            self.framework.request_reconciliation(self)
        else:
            print(f"❌ PyThra State | setState failed for {self.__class__.__name__}: Framework not available")


    # --- Drawer/Snackbar/etc. Methods ---
    # These remain largely the same, relying on self.framework being set
    # Ensure snackbar uses _id from base.Widget if needed

    def openDrawer(self):
         # ... (implementation as before, check self.framework) ...
         if self.framework and self.framework.root_widget and hasattr(self.framework.root_widget, 'drawer') and self.framework.root_widget.drawer:
            #print("Requesting JS toggle for left drawer")
            # Ask framework to execute the JS function
            self.framework.trigger_drawer_toggle('left')
         else:
            print("Cannot open drawer: Framework or root drawer not found.")

    def closeDrawer(self):
         # ... (implementation as before, check self.framework) ...
         if self.framework and self.framework.root_widget and hasattr(self.framework.root_widget, 'drawer') and self.framework.root_widget.drawer:
            #print("Requesting JS toggle for left drawer")
            # Ask framework to execute the JS function
            self.framework.trigger_drawer_toggle('right')
         else:
            print("Cannot close drawer: Framework or root drawer not found.")

    # ... other direct manipulation methods ...
    # In MyAppState (or similar)

    def open_my_bottom_sheet(self):
        if self.framework:
            # Get the BottomSheet instance (assuming it's on the Scaffold)
            bottom_sheet_widget = getattr(self.framework.root_widget, 'bottomSheet', None)
            if bottom_sheet_widget:
                html_id = self.framework.reconciler.rendered_elements_map.get(bottom_sheet_widget.get_unique_id(), {}).get('html_id')
                props = bottom_sheet_widget.render_props() # Get props defined in BottomSheet widget
                is_modal = props.get('isModal', True)
                on_dismiss_name = props.get('onDismissedName', '')

                if html_id:
                    print(f"Framework requesting JS toggleBottomSheet for ID: {html_id}")
                    self.framework.trigger_bottom_sheet_toggle(
                        html_id,
                        show=True,
                        is_modal=is_modal,
                        on_dismiss_name=on_dismiss_name
                    )
                else:
                    print("Error: Could not find HTML ID for bottom sheet in reconciler map.")
            else:
                print("No bottom sheet widget found on root widget.")

    def close_my_bottom_sheet(self):
        # Similar logic to open, but with show=False
        if self.framework:
            bottom_sheet_widget = getattr(self.framework.root_widget, 'bottomSheet', None)
            if bottom_sheet_widget:
                html_id = self.framework.reconciler.rendered_elements_map.get(bottom_sheet_widget.get_unique_id(), {}).get('html_id')
                props = bottom_sheet_widget.render_props()
                is_modal = props.get('isModal', True)
                # Dismiss name not needed when explicitly closing
                if html_id:
                    self.framework.trigger_bottom_sheet_toggle(
                        html_id,
                        show=False,
                        is_modal=is_modal
                    )
                # ... error handling ...
            # ... error handling ...

    def handle_dismiss(self): # Example dismiss callback
        print("Bottom Sheet was dismissed (e.g., by scrim click)")
        # Optionally update state here if needed
        # self.setState() # Only if dismiss changes app state that build() uses

    def openSnackBar(self):
         # ... (implementation using QTimer as before) ...
         # Make sure to get snack_bar_id from snack_bar_widget._id
         if not self.framework or not self.framework.root_widget or not hasattr(self.framework.root_widget, 'snackBar'):
             print("Snackbar widget or framework not available.")
             return
         # ... rest of QTimer logic ...
         snack_bar_widget = self.framework.root_widget.snackBar
         if not snack_bar_widget: return
         snack_bar_id = getattr(snack_bar_widget, '_id', None) # Access _id from base Widget
         if not snack_bar_id:
              print("Error: Snackbar widget ID (_id) is missing.")
              return
         # ... schedule QTimer using snack_bar_id ...
         snack_bar_widget.toggle(True) # Assuming this triggers JS show
         duration_sec = getattr(snack_bar_widget, 'duration', 3)
         duration_ms = int(duration_sec * 1000)
         QTimer.singleShot(duration_ms, lambda: self._schedule_snackbar_hide(snack_bar_id))


    def _schedule_snackbar_hide(self, snack_bar_id_to_hide):
        # ... (implementation as before, using snack_bar_id_to_hide) ...
        print(f"Timer fired: Attempting to hide snackbar {snack_bar_id_to_hide}")
        if self.framework:
            current_snackbar = getattr(self.framework.root_widget, 'snackBar', None)
            current_id = getattr(current_snackbar, '_id', None) if current_snackbar else None
            if current_id == snack_bar_id_to_hide:
                self.framework.hide_snack_bar(snack_bar_id_to_hide)
                if current_snackbar and hasattr(current_snackbar, 'toggle'):
                    current_snackbar.toggle(False)
            # ... else print warning ...
        # ... else print warning ...

    def closeSnackBar(self):
        # ... (implementation as before, using _id) ...
        if self.framework and self.framework.root_widget and hasattr(self.framework.root_widget, 'snackBar'):
            snack_bar_widget = self.framework.root_widget.snackBar
            if snack_bar_widget:
                 snack_bar_id = getattr(snack_bar_widget, '_id', None)
                 if snack_bar_id:
                      self.framework.hide_snack_bar(snack_bar_id)
                      if hasattr(snack_bar_widget, 'toggle'):
                           snack_bar_widget.toggle(False)
                 print("Snackbar closed directly.")