from typing import Callable, List, Optional

# ==============================================================================
# 1. CONTROLLER AND THEME (The Data and Style Models)
# ==============================================================================

class DerivedDropdownController:
    """Manages the state of a DerivedDropdown, allowing it to be controlled externally."""

    def __init__(self, value=None, items: Optional[List[str]] = None):
        self.value = value
        self.items = items or []
        # print("Items: ", self.items)
        self._listeners = []

    def set_value(self, new_value: str):
        """Programmatically sets the dropdown's value and notifies listeners."""
        if self.value != new_value:
            self.value = new_value
            # Notify all registered listeners of the change
            for callback in self._listeners:
                callback(new_value)

    def add_listener(self, callback: Callable[[str], None]):
        """Register a callback to be invoked when the value changes."""
        self._listeners.append(callback)

    def remove_listener(self, callback: Callable[[str], None]):
        """Remove a previously registered callback."""
        if callback in self._listeners:
            self._listeners.remove(callback)