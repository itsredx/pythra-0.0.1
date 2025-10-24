# PyThra Markdown Editor Plugin

A powerful WYSIWYG Markdown editor plugin for the PyThra Framework. Write Markdown with real-time preview and rich text editing capabilities.

## Features

- WYSIWYG Markdown editing
- Real-time preview
- Rich text formatting tools
- Support for tables, lists, and code blocks
- Image insertion support
- Custom font and color styling
- Link management
- Keyboard shortcuts

## Installation

Install the plugin using the PyThra package manager:

```bash
pythra package install pythra-markdown-editor
```

### Dependencies

The plugin requires the following Python packages:
- markdown >= 3.0.0
- markdownify >= 0.11.0

These will be automatically installed as peer dependencies.

## Usage

### Basic Integration

```python
from pythra import Framework
from pythra.plugins.markdown import MarkdownEditor

def main():
    app = Framework.instance()
    
    editor = MarkdownEditor()
    app.set_root(editor)
    
    app.run()

if __name__ == "__main__":
    main()
```

## API Reference

See [API Documentation](docs/index.md) for detailed information about all available methods and classes.

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m "Add some amazing feature"`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

- Documentation: [https://github.com/itsredx/pythra-markdown-editor/docs](https://github.com/itsredx/pythra-markdown-editor/docs)
- Issue Tracker: [https://github.com/itsredx/pythra-markdown-editor/issues](https://github.com/itsredx/pythra-markdown-editor/issues)
- Homepage: [https://github.com/itsredx/pythra-markdown-editor#readme](https://github.com/itsredx/pythra-markdown-editor#readme)
