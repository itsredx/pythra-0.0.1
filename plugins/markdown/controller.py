from typing import Optional

class MarkdownEditorController:
    """Controller exposed to plugin consumers to interact with the editor.

    Methods:
      - exec_command(command, value=None)
      - set_content(html)
      - get_content() -> str
      - focus()
    """
    def __init__(self):
        self._state_ref = None

    def _attach(self, state):
        self._state_ref = state

    def _detach(self):
        self._state_ref = None

    def exec_command(self, command: str, value: Optional[str] = None):
        if self._state_ref:
            self._state_ref.exec_command(command, value)

    def set_content(self, html: str):
        if self._state_ref:
            self._state_ref.set_content(html)

    def get_content(self) -> Optional[str]:
        if self._state_ref:
            return self._state_ref.get_content()
        return None

    def focus(self):
        if self._state_ref:
            self._state_ref.focus()
