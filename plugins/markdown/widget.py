from pythra import StatefulWidget, Key

from .editor_state import MarkdownEditorState


class MarkdownEditor(StatefulWidget):
    """High-level widget for the Markdown editor plugin.

    This class follows the same pattern as toolkit widgets: it's a small
    StatefulWidget that holds configuration and returns its State.
    """
    def __init__(self, key: Key, controller=None, width='100%', height='70vh', onChange: callable= None,# --- ADD THIS PARAMETER ---
                 initial_content: str = "<h1>Welcome!</h1><p>Start writing your document here...</p>", show_grid: bool = False):
        self.controller = controller
        self.width = width
        self.height = height
        self.onChange = onChange
        # --- STORE IT ---
        self.initial_content = initial_content
        self.show_grid = show_grid
        super().__init__(key=key)

    def createState(self):
        state = MarkdownEditorState()
        return state
