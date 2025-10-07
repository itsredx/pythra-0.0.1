# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Development Commands

### Project Setup and Installation
```bash
# Create a virtual environment (recommended)
python -m venv venv
# Activate on Windows
venv\Scripts\activate
# Activate on Linux/macOS
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install PyThra framework in development mode
pip install -e .
```

### Common Development Commands

#### Running Applications
```bash
# Run the main example application
python main.py

# Run the template project example
python lib/main.py

# Using the CLI to run projects
pythra run                    # Runs lib/main.py by default
pythra run --script main.py   # Run specific script
```

#### Project Management
```bash
# Create a new PyThra project
pythra create-project <project_name>

# Build a standalone application
pythra build                  # Builds to build/ directory
pythra build --onefile       # Create single executable
pythra build --icon app.ico  # Include custom icon
```

#### Development and Testing
```bash
# Run tests (using the test files in perv_tests/)
python perv_tests/main.py
python perv_tests/state_test.py

# Test specific UI components
python components/control.py
python components/home.py
```

## Architecture Overview

### Core Framework Architecture

PyThra is a **declarative GUI framework** for Python that renders desktop applications using web technologies (HTML/CSS/JS) within a native PySide6 webview container. It implements Flutter-inspired patterns with a component-based architecture.

#### Key Architectural Components

1. **Framework Core** (`pythra/core.py`)
   - Singleton Framework class manages application lifecycle
   - Handles widget tree building, reconciliation, and rendering
   - Manages asset server and web bridge communication

2. **Widget System** (`pythra/base.py`, `pythra/widgets/`)
   - Base Widget class for all UI components
   - StatefulWidget and StatelessWidget for different component types
   - Key-based widget identification for efficient reconciliation
   - Hierarchical widget tree structure

3. **State Management** (`pythra/state.py`)
   - State class manages mutable application state
   - `setState()` triggers UI reconciliation and updates
   - Weak references prevent memory leaks
   - Framework integration for state change notifications

4. **Reconciliation Engine** (`pythra/reconciler.py`)
   - Diffs widget trees to determine minimal DOM changes
   - Generates patches (INSERT, UPDATE, REMOVE, MOVE operations)
   - CSS class management and optimization
   - JavaScript initializer coordination

### Widget Tree and Reconciliation Flow

1. **Build Phase**: StatefulWidget.build() returns widget tree
2. **Reconciliation**: Reconciler compares old vs new widget trees
3. **Patch Generation**: Creates minimal set of DOM operations
4. **Rendering**: Applies patches to HTML/CSS/JS in webview
5. **Event Handling**: JavaScript events callback to Python handlers

### Project Structure Patterns

#### Standard PyThra Project Layout
```
project/
├── lib/main.py          # Main application entry point
├── config.yaml          # App configuration (window size, assets, etc.)
├── components/          # Reusable UI components
├── constants/colors.py  # Shared styling constants
├── assets/              # Images, fonts, static resources
├── render/                 # Generated HTML/CSS/JS (auto-created)
└── plugins/             # Optional plugin system
```

#### Component Organization
- **Stateful Components**: Use for components with changing data
- **Stateless Components**: Use for static/computed UI elements
- **Controllers**: Manage complex state (TextEditingController, etc.)
- **Keys**: Always provide Keys for list items and dynamic content

### Styling and Theming System

PyThra uses a **CSS-in-Python** approach where widgets generate CSS classes:
- Widget properties map to CSS rules
- Shared CSS classes optimize performance
- Style objects (EdgeInsets, BorderRadius, etc.) provide type safety
- GradientTheme and other theme objects enable complex styling

### JavaScript Bridge and Plugins

The framework includes a **plugin system** for extending functionality:
- Plugins live in `plugins/` directory with `pythra_plugin.py` manifest
- JavaScript engines can be loaded for complex interactions
- Asset serving supports plugin resources
- Examples: sliders, dropdowns, virtual lists, gesture detectors

## Framework-Specific Concepts

### Widget Lifecycle
1. **Creation**: Widget instantiated with props and key
2. **Building**: State.build() called to create widget tree
3. **Reconciliation**: Changes detected and patches generated
4. **Rendering**: DOM updated with minimal changes
5. **Disposal**: State cleanup when widget removed

### Key Usage Patterns
- **Always use Keys** for list items that can be reordered
- **Stable Keys** prevent unnecessary reconciliation
- **Unique Keys** within same parent level

### State Management Best Practices
- Keep state local to components when possible
- Use `setState()` to trigger UI updates
- Pass data down through widget properties
- Use callbacks to communicate state changes up the tree

### Performance Considerations
- **CSS Memoization**: Framework caches CSS generation
- **Partial Reconciliation**: Only rebuilds changed widget subtrees
- **JavaScript Optimization**: Engines loaded once and reused
- **Asset Serving**: Local HTTP server for optimal resource loading

## Common Patterns and Utilities

### Creating New Widgets
```python
class CustomWidget(StatelessWidget):
    def __init__(self, title: str, key: Optional[Key] = None):
        super().__init__(key=key)
        self.title = title
    
    def build(self) -> Widget:
        return Container(
            child=Text(self.title),
            padding=EdgeInsets.all(16)
        )
```

### State Management Pattern
```python
class MyWidgetState(State):
    def __init__(self):
        super().__init__()
        self.counter = 0
    
    def increment(self):
        self.counter += 1
        self.setState()  # Triggers UI update
    
    def build(self) -> Widget:
        return Column(children=[
            Text(f"Count: {self.counter}"),
            ElevatedButton(
                child=Text("Increment"),
                onPressed=self.increment
            )
        ])
```

### Asset and Resource Management
- Place assets in `assets/` directory
- Reference using `AssetImage("path/to/image.png")`
- Configure asset server port in `config.yaml`
- Use `AssetIcon` for local icon resources

## Testing and Debugging

### Running Test Suites
The `perv_tests/` directory contains various UI component tests:
- `main.py` - Core framework functionality
- `state_test.py` - State management patterns
- Component-specific tests for different widgets

### Debugging Tips
- Enable Debug mode in `config.yaml`
- Check console output for reconciliation details
- Use browser developer tools to inspect generated HTML/CSS
- Framework prints detailed reconciliation timing and patch information
- If you see JavaScript `ReferenceError`, ensure JS utilities are properly loaded
- DOMException errors typically indicate elements not found or invalid DOM operations

## Configuration

### config.yaml Structure
```yaml
version: "0.1.0"
app_name: "My PyThra App"
assets_dir: "assets"
assets_server_port: 8006
Debug: true
frameless: false
maximized: false
win_height: 600
win_width: 800
```

Key configuration options affect framework behavior and should be adjusted for different deployment scenarios.

## Troubleshooting Common Issues

### JavaScript Errors
- **`ReferenceError: generateRoundedPath is not defined`**: Fixed by ensuring JS utilities are loaded during initial render
- **`Identifier 'PythraSlider' has already been declared`**: Fixed by preventing duplicate JS injection between initial render and reconciliation
- **DOMException during patch application**: Improved with better error handling and element existence checks

### Asset Loading Issues
- **Font 404 errors**: Check that Material Symbols fonts exist in `assets/fonts/` directory
- **Port conflicts**: Change `assets_server_port` in config.yaml if 8006 is in use
- **Plugin assets not found**: Ensure plugin directories have correct structure and manifests

### Performance Issues
- **Slow reconciliation**: Use more specific Keys for widgets, especially in lists
- **CSS regeneration**: Framework caches CSS classes to avoid unnecessary recalculation
- **Memory leaks**: StatefulWidget state is properly disposed when widgets are removed
