from typing import Callable, List, Optional

class TabController:

    def __init__(self, index: int = 0):
        self.index = index
        self._listeners = []
        # self.isDragEnded = isDragEnded

    def set_index(self, new_index: str):
        """Programmatically sets the dropdown's value and notifies listeners."""
        if self.index != new_index:
            self.index = new_index
            # Notify all registered listeners of the change
            for callback in self._listeners:
                callback(new_index)

    def add_listener(self, callback: Callable[[str], None]):
        """Register a callback to be invoked when the value changes."""
        self._listeners.append(callback)

    def remove_listener(self, callback: Callable[[str], None]):
        """Remove a previously registered callback."""
        if callback in self._listeners:
            self._listeners.remove(callback)


my_tab_controller = TabController(0)