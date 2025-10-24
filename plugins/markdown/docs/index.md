# PyThra Markdown Editor API Documentation

## Overview

The PyThra Markdown Editor is a powerful WYSIWYG editor that combines rich text editing with Markdown support. This document provides detailed API documentation for developers integrating and extending the editor.

## Installation Requirements

```bash
pythra package install pythra-markdown-editor
```

The editor requires these peer dependencies:

markdown >= 3.0.0
markdownify >= 0.11.0

## Core Classes

MarkdownEditor
The main widget class that provides the WYSIWYG editor interface.

```python
from pythra.plugins.markdown import MarkdownEditor

editor = MarkdownEditor()
```

## MarkdownEditorController

Handles editor operations and state management. This is the main API for interacting with the editor.

```python
from pythra.plugins.markdown.controller import MarkdownEditorController
```

## API Reference

### Content Management

#### `set_content(html: str)`

Sets the editor content using HTML.

```python
editor.set_content("<h1>Hello</h1><p>This is <strong>bold</strong> text</p>")
```

#### `get_content() -> Optional\[str]`

Gets the current HTML content.

```python
html_content = editor.get_content()
```

#### `load_from_markdown(markdown_text: str)`

Converts and loads Markdown content.

```python
editor.load_from_markdown("# Hello//n//nThis is ////bold//// text")
editor.setState()  # Required after this method
```

#### `export_to_markdown() -> Optional\[str]`

Exports content as Markdown.

```python
markdown = editor.export_to_markdown()
```

### Text Formatting

#### `bold()`

Toggles bold on selected text.

```python
editor.bold()  # No setState() needed
```

#### `italic()`

Toggles italic on selected text.

```python
editor.italic()  # No setState() needed
```

#### `underline()`

Toggles underline on selected text.

```python
editor.underline()  # No setState() needed
```

#### `strike_through()`

Toggles strikethrough on selected text.

```python
editor.strike_through()  # No setState() needed
```

### Block Formatting

#### `set_heading(level: int)`

Sets heading level (1-6).

```python
editor.set_heading(1)  # H1
editor.set_heading(2)  # H2
```

#### `set_paragraph()`

Converts block to paragraph.

```python
editor.set_paragraph()
```

#### `insert_unordered_list()`

Creates/toggles bullet list.

```python
editor.insert_unordered_list()
```

#### `insert_ordered_list()`

Creates/toggles numbered list.

```python
editor.insert_ordered_list()
```

### Styling

#### `set_font_color(color: str)`

Changes text color.

```python
editor.set_font_color("#FF0000")  # Red
editor.set_font_color("blue")     # Named color
```

#### `set_font_name(font_family: str)`

Changes text font.

```python
editor.set_font_name("Arial")
```

### Media

#### `insert_image(url: str)`

Inserts image at cursor.

```python
editor.insert_image("https://example.com/image.png")
```

## Important Concepts

### State Management

The editor uses two types of state updates:

1. **Direct UI Commands** (most formatting methods)

   * Update UI immediately
   * Do NOT call `setState()`
   * Examples: `bold()`, `italic()`, `set_font_color()`

2. **State-Modifying Commands**

   * Change content programmatically
   * MUST call `setState()`
   * Example:

```python
editor.load_from_markdown("# Title")
editor.setState()  # Required!
```

### Event System

The editor provides several events:

```python
def on_change(html_content):
    print("Content changed:", html_content)

def on_selection(selection):
    print("Selection changed:", selection)

editor.on_change = on_change
editor.on_selection_change = on_selection
```

Available events:

* `on_change`: Content changes
* `on_selection_change`: Selection changes
* `on_focus`: Editor focused
* `on_blur`: Editor lost focus

### CSS Customization

The editor provides CSS classes for styling:

```css
.pythra-markdown-editor {
    /* Main container */
    border: 1px solid #ccc;
    border-radius: 4px;
}

.pythra-markdown-toolbar {
    /* Toolbar styling */
    background: #f5f5f5;
    padding: 8px;
}

.pythra-markdown-content {
    /* Editor content area */
    min-height: 200px;
    padding: 16px;
}

.pythra-markdown-placeholder {
    /* Placeholder text */
    color: #999;
}
```

## Error Handling

The editor throws these exceptions:

* `ValueError`: Invalid input parameters
* `StateError`: State synchronization issues
* `EditorError`: General editor operations

Example error handling:

```python
try:
    editor.load_from_markdown(markdown_text)
    editor.setState()
except ValueError as e:
    print("Invalid markdown:", e)
except Exception as e:
    print("Editor error:", e)
```

## Performance Tips

1. Batch multiple content changes:

```python
editor.load_from_markdown(content)
editor.set_font_name("Arial")
editor.setState()  # Single update at the end
```

2. Use direct commands for user interactions
3. Avoid frequent programmatic content changes
4. Consider using `debounce` for rapid updates

## Contributing

For development setup and contribution guidelines, see CONTRIBUTING.md

## Support

* Issues: [GitHub Issues](https://github.com/itsredx/pythra-markdown-editor/issues)
* Discussions: [GitHub Discussions](https://github.com/itsredx/pythra-markdown-editor/discussions)
