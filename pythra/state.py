# pythra/state.py
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

# --- StatefulWidget Class ---
class StatefulWidget(Widget):
    """
    A widget that has mutable state managed by a State object.
    (Docstring remains the same)
    """
    _framework_ref: Optional[weakref.ref['Framework']] = None

    @classmethod
    def set_framework(cls, framework: 'Framework'):
        cls._framework_ref = weakref.ref(framework)

    def __init__(self, key: Optional[Key] = None):
        super().__init__(key=key) # Pass key to base Widget
        # Framework reference for the *instance*
        self.framework: Optional['Framework'] = self._framework_ref() if self._framework_ref else None
        self._state = self.createState() # Create the associated State object
        self._state._set_widget(self) # Link State back to this widget instance
        self._state.initState() # <-- CALL THE NEW LIFECYCLE HOOK

    def createState(self) -> 'State': # Hint uses forward reference 'State'
        """Create the mutable state for this widget."""
        raise NotImplementedError(f"{self.__class__.__name__} must implement createState()")

    def get_state(self) -> 'State': # Hint uses forward reference 'State'
        """Returns the associated State object."""
        return self._state


class StatelessWidget(Widget):
    """
    A widget that describes part of the user interface by building a constellation
    of other widgets that describe the user interface more concretely.

    The building process is stateless, meaning it depends only on the configuration
    information in the object itself (its constructor parameters) and the build context.
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

# --- State Class ---
class State:
    """
    Manages the mutable state for a StatefulWidget.
    (Docstring remains the same)
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
            print(f"Warning: Cannot setState for {self.__class__.__name__}, widget reference lost.")
            return

        if self.framework:
            # Use getattr for safety, though framework should exist if widget exists
            key_info = getattr(widget, 'key', None)
            print(f">>> setState triggered for State: {self.__class__.__name__} (Widget Key: {key_info}) <<<")
            # Pass 'self' (the State instance) to the framework
            self.framework.request_reconciliation(self)
        else:
            print(f"setState failed for {self.__class__.__name__}: Framework not available.")


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