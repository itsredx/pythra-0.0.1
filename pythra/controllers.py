# pythra/controllers.py
from typing import Callable, List, Optional

class TextEditingController:
    """
    A controller for an editable text field.

    This class is used to read and modify the text of a TextField, and to listen
    for changes.

    :param text: The initial text this controller should have.
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