# In a new file: pythra/plugins.py

from ..widgets import Widget, IconButton, Icons
from ..controllers import MarkdownEditingController
from abc import ABC, abstractmethod

class MarkdownToolbarItem(ABC):
    """Abstract base class for a custom button in the MarkdownEditor toolbar."""
    
    @abstractmethod
    def build_widget(self, controller: MarkdownEditingController) -> Widget:
        """
        Returns the Pythra Widget to be displayed in the toolbar.
        The widget's onPressed should use the provided controller to execute commands.
        """
        pass

# --- Default Implementations ---

class BoldToolbarItem(MarkdownToolbarItem):
    def build_widget(self, controller: MarkdownEditingController) -> Widget:
        return IconButton(
            icon=Icons.format_bold_rounded,
            tooltip="Bold",
            onPressed=lambda: controller.execCommand('bold')
        )

class ItalicToolbarItem(MarkdownToolbarItem):
    def build_widget(self, controller: MarkdownEditingController) -> Widget:
        return IconButton(
            icon=Icons.format_italic_rounded,
            tooltip="Italic",
            onPressed=lambda: controller.execCommand('italic')
        )

# ... create more for Heading, Strike, Quote, etc. ...```

#### Step 2: Create the Controller (`pythra/controllers.py`)

