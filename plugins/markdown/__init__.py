"""
PyThra Markdown Editor Plugin
A WYSIWYG Markdown editor plugin for Pythra
"""

from .widget import MarkdownEditor

__version__ = "1.0.0"
__all__ = ['MarkdownEditor']

# Plugin definition for Pythra framework
plugin_definition = {
    'name': 'pythra-markdown-editor',
    'version': __version__,
    'js_modules': {
        'PythraMarkdownEditor': {
            'file': 'markdown_editor_engine.js',
            'global': 'pythraMarkdownEditor',
            'initializer': 'initialize'
        }
    }
}