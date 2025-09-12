"""
Sample text editor plugin for PyThra Framework

This is a demonstration of the new package system with enhanced metadata
and discovery capabilities.
"""

class TextEditorPlugin:
    """Simple text editor plugin"""
    
    def __init__(self):
        self.name = "sample-text-editor"
        self.version = "1.0.0"
    
    def get_widget_definition(self):
        """Return the widget definition for the text editor"""
        return {
            "name": "TextEditor",
            "component": "TextEditorWidget",
            "props": {
                "placeholder": "Enter text here...",
                "multiline": True,
                "readonly": False
            }
        }
    
    def initialize(self, framework):
        """Initialize the plugin with the PyThra framework"""
        print(f"Initializing {self.name} v{self.version}")
        return True

# Plugin entry point
def create_plugin():
    """Factory function to create plugin instance"""
    return TextEditorPlugin()