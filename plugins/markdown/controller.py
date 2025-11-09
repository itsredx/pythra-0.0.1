# plugins/markdown/controller.py
from typing import Optional

class MarkdownEditorController:
    """
    Controller exposed to plugin consumers to interact with the editor.
    Provides a clean, Pythonic API for executing rich text commands.

    IMPORTANT USAGE NOTE ON `setState()`:
    This controller manages two types of operations:
    
    1. Direct UI Commands (e.g., `bold()`, `set_font_color()`): These commands
       are sent to the browser, which updates the UI immediately. The browser
       then notifies Python of the change via its `onChange` event. You
       **MUST NOT** call `setState()` in your application after calling these
       methods, as it will cause a race condition and unexpected behavior.

    2. State-Modifying Commands (e.g., `load_from_markdown()`): These methods
       change the editor's content from the Python side. They handle their
       own internal state updates and will trigger a rebuild when `setState()`
        is called. You **SHOULD** call `setState()` after these methods.
    """
    def __init__(self):
        self._state_ref = None

    def _attach(self, state):
        self._state_ref = state

    def _detach(self):
        self._state_ref = None

    def exec_command(self, command: str, value: Optional[str] = None):
        """
        The low-level method to send any command to the browser's editor.
        This directly mutates the DOM in the browser.

        **WARNING:** `setState()` should **ABSOLUTELY NOT** be called after this
        method. The browser's `onChange` event will handle state synchronization.
        Prefer using the higher-level convenience methods like `bold()`.
        """
        if self._state_ref:
            self._state_ref.exec_command(command, value)

    def set_content(self, html: str):
        if self._state_ref:
            self._state_ref.set_content(html)

    def get_content(self) -> Optional[str]:
        """
        Gets the current HTML content from the editor's Python state.
        This is a read-only operation and does not affect the UI.
        `setState()` is not relevant here.
        """
        if self._state_ref:
            return self._state_ref.get_content()
        return None

    def focus(self):
        """
        Sets the focus back to the editor's text area. This is a direct UI
        command that does not change any state.

        **NOTE:** `setState()` should **NOT** be called after this method.
        """
        if self._state_ref:
            self._state_ref.focus()

    # --- NEW: CONVENIENCE WRAPPER METHODS ---

    # --- Text Style Toggles ---
    def bold(self):
        """
        Toggles bold on the selected text. This is a direct UI command.

        **WARNING:** `setState()` should **ABSOLUTELY NOT** be called after this
        method. The editor's `onChange` event handles state synchronization.
        """
        self.exec_command('bold')
        self.focus()

    def italic(self):
        """
        Toggles italic on the selected text. This is a direct UI command.

        **WARNING:** `setState()` should **ABSOLUTELY NOT** be called after this
        method. The editor's `onChange` event handles state synchronization.
        """
        self.exec_command('italic')
        self.focus()

    def underline(self):
        """
        Toggles underline on the selected text. This is a direct UI command.

        **WARNING:** `setState()` should **ABSOLUTELY NOT** be called after this
        method. The editor's `onChange` event handles state synchronization.
        """
        self.exec_command('underline')
        self.focus()

    def strike_through(self):
        """
        Toggles strikethrough on the selected text. This is a direct UI command.

        **WARNING:** `setState()` should **ABSOLUTELY NOT** be called after this
        method. The editor's `onChange` event handles state synchronization.
        """
        self.exec_command('strikeThrough')
        self.focus()

    # --- Block Formatting ---
    def set_heading(self, level: int):
        """
        Changes the current block to a heading. This is a direct UI command.

        **WARNING:** `setState()` should **ABSOLUTELY NOT** be called after this
        method. The editor's `onChange` event handles state synchronization.
        :param level: An integer from 1 to 6.
        """
        if 1 <= level <= 6:
            self.exec_command('formatBlock', f'H{level}')
            self.focus()
        else:
            print(f"Warning: Heading level must be between 1 and 6, but got {level}.")

    def set_paragraph(self):
        """
        Changes the current block to a normal paragraph. This is a direct UI command.
        
        **WARNING:** `setState()` should **ABSOLUTELY NOT** be called after this
        method. The editor's `onChange` event handles state synchronization.
        """
        self.exec_command('formatBlock', 'P')
        self.focus()
        
    def insert_unordered_list(self):
        """
        Toggles a bulleted list. This is a direct UI command.

        **WARNING:** `setState()` should **ABSOLUTELY NOT** be called after this
        method. The editor's `onChange` event handles state synchronization.
        """
        self.exec_command('insertUnorderedList')
        self.focus()

    def insert_ordered_list(self):
        """
        Toggles a numbered list. This is a direct UI command.

        **WARNING:** `setState()` should **ABSOLUTELY NOT** be called after this
        method. The editor's `onChange` event handles state synchronization.
        """
        self.exec_command('insertOrderedList')
        self.focus()

    # --- Value-Based Commands ---
    def set_font_color(self, color: str):
        """
        Changes the font color of the selected text. This is a direct UI command.

        **WARNING:** `setState()` should **ABSOLUTELY NOT** be called after this
        method. The editor's `onChange` event handles state synchronization.
        :param color: A CSS color string (e.g., '#FF0000', 'red').
        """
        self.exec_command('foreColor', color)
        self.focus()
        
    def set_font_name(self, font_family: str):
        """
        Changes the font of the selected text. This is a direct UI command.

        **WARNING:** `setState()` should **ABSOLUTELY NOT** be called after this
        method. The editor's `onChange` event handles state synchronization.
        :param font_family: A font family string (e.g., 'Arial', 'Verdana').
        """
        self.exec_command('fontName', font_family)
        self.focus()
        
    def insert_image(self, url: str):
        """
        Inserts an image at the current cursor position. This is a direct UI command.

        **WARNING:** `setState()` should **ABSOLUTELY NOT** be called after this
        method. The editor's `onChange` event handles state synchronization.
        :param url: The URL of the image to insert.
        """
        self.exec_command('insertImage', url)
        self.focus()

     # --- NEW: Markdown Import/Export Methods ---

    def load_from_markdown(self, markdown_text: str):
        """
        Imports and renders Markdown content into the editor, converting it to rich HTML.
        This is a state-modifying operation that transforms the editor's content.

        This method:
        1. Parses the provided Markdown text
        2. Converts it to semantic HTML with proper formatting
        3. Updates the internal editor state
        4. Triggers a UI rebuild to reflect the changes

        Example usage:
            editor.load_from_markdown("# Hello\n\nThis is **bold** text")
            editor.setState()  # Required to apply changes

        **IMPORTANT:** You MUST call `setState()` after this method to apply the changes.
        This ensures proper synchronization between Python state and UI rendering.

        :param markdown_text: Raw Markdown content to parse and render (e.g., "# Heading\n\nParagraph")
        :raises ValueError: If markdown_text is None or not a valid string
        """
        if self._state_ref:
            self._state_ref.load_from_markdown(markdown_text)

    def export_to_markdown(self) -> Optional[str]:
        """
        Gets the current editor content and converts it to Markdown.
        This is a read-only operation. `setState()` is not relevant here.
        """
        if self._state_ref:
            return self._state_ref.export_to_markdown()
        return None

     # --- ADD THIS NEW METHOD AT THE END OF THE CLASS ---

    def replace_selection_from_markdown(self, markdown_text: str):
        """
        Converts a Markdown string to HTML and replaces the currently selected
        text in the editor with the result. If no text is selected, it inserts
        the content at the cursor position. This is a direct UI command.

        **WARNING:** `setState()` should **ABSOLUTELY NOT** be called after this
        method. The editor's `onChange` event will automatically handle state
        synchronization after the browser's DOM is updated.
        :param markdown_text: The Markdown content to insert/replace.
        """
        if self._state_ref:
            self._state_ref.replace_selection_from_markdown(markdown_text)
