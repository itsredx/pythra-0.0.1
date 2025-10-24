from pythra import (
    Widget,
    StatefulWidget,
    State,
    Container,
    Key,
    EdgeInsets,
    Column,
    Row,
    Text,
    Colors,
    TextStyle,
    Stack,
    IconButton,
    Icons,
    Icon,
    SizedBox
)
import os

class MarkdownEditorController:
    def __init__(self, state):
        self.state = state
        self._content = ""
    
    def execCommand(self, command, value=None):
        """Execute a command in the editor"""
        # For now, just update the content
        if command == 'bold':
            self._content = f"**{self._content}**"
        elif command == 'italic':
            self._content = f"*{self._content}*"
        self.state.setState()
    
    def get_content(self):
        """Get the editor content"""
        return self._content
    
    def set_content(self, content):
        """Set the editor content"""
        self._content = content
        self.state.setState()
        
    def handle_content_change(self, new_content):
        """Handle content changes from the editor"""
        self._content = new_content
        self.state.setState()

class MarkdownEditorState(State):
    def __init__(self):
        super().__init__()
        self.controller = MarkdownEditorController(self)
    
    def build(self) -> Widget:
        return Container(
            key=Key("markdown_editor_container"),
            padding=EdgeInsets.all(16),
            color=Colors.white,
            child=Column(
                children=[
                    # Toolbar
                    Container(
                        key=Key("markdown_editor_toolbar"),
                        padding=EdgeInsets.all(8),
                        color=Colors.grey,
                        child=Row(
                            children=[
                                IconButton(
                                    key=Key("bold_button"),
                                    icon=Icon(Icons.format_bold_rounded),
                                    onPressed=lambda: self.controller.execCommand('bold')
                                ),
                                SizedBox(width=8),
                                IconButton(
                                    key=Key("italic_button"),
                                    icon=Icon(Icons.format_italic_rounded),
                                    onPressed=lambda: self.controller.execCommand('italic')
                                ),
                            ]
                        )
                    ),
                    # Editor area
                    Container(
                        key=Key("markdown_editor_content"),
                        padding=EdgeInsets.all(16),
                        color=Colors.white,
                        child=Text(
                            self.controller.get_content() or "Start typing your content here...",
                            style=TextStyle(
                                color=Colors.black,
                                fontSize=16
                            )
                        )
                    )
                ]
            )
        )

class MarkdownEditor(StatefulWidget):
    def __init__(self, key=None):
        super().__init__(key=key)
    
    def createState(self) -> MarkdownEditorState:
        return MarkdownEditorState()
    
# Export the widget for use in other modules
__all__ = ['MarkdownEditor']