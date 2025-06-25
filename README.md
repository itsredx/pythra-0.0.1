---

# PyThra Framework

<p align="center">
  <img src="https://via.placeholder.com/150/6750A4/FFFFFF?text=PyThra" alt="PyThra Logo">
</p>

<p align="center">
  <strong>A declarative Python framework for building beautiful, modern desktop applications using web technologies.</strong>
  <br>
  Inspired by the development patterns of Flutter, PyThra brings the power of a stateful, component-based UI model to Python developers.
</p>

<p align="center">
  <a href="#-key-features">Key Features</a> •
  <a href="#-getting-started">Getting Started</a> •
  <a href="#-example-usage">Example</a> •
  <a href="#-philosophy">Philosophy</a> •
  <a href="#-core-concepts">Core Concepts</a> •
  <a href="#-contributing">Contributing</a>
</p>

---

## 🚀 Key Features

*   **Declarative UI:** Describe your UI as a function of your application's state. When the state changes, PyThra intelligently updates only the necessary parts of the UI.
*   **Component-Based:** Build your application by composing small, reusable `Widget`s, just like in modern web frameworks.
*   **Python-First:** Write your entire application logic, state management, and UI structure in pure Python. No need to write HTML, CSS, or JavaScript by hand.
*   **Efficient Reconciliation:** Features a sophisticated reconciliation algorithm that minimizes DOM manipulations, ensuring a smooth and responsive user experience.
*   **Rich Widget Library:** Includes a set of pre-built, Material Design-inspired widgets like `Scaffold`, `AppBar`, `TextField`, `ListView`, `Dialog`, and more.
*   **Themed and Customizable:** Widgets are styled using a shared, dynamic CSS system. Easily create and apply themes, including custom scrollbars powered by SimpleBar.js.
*   **Hot Reloading (Concept):** The architecture is designed to support hot reloading for a rapid development cycle. (Full implementation pending).

## 📦 Getting Started

### Prerequisites

*   Python 3.8+
*   PySide6 (`pip install pyside6`)

### Installation

Currently, PyThra is under active development. To use it, clone the repository and install the dependencies.

```bash
# 1. Clone the repository
git clone https://github.com/your-username/pythra.git
cd pythra

# 2. (Optional but recommended) Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`

# 3. Install required packages
pip install -r requirements.txt 
```
*(Note: You will need to create a `requirements.txt` file containing `PySide6` and any other dependencies).*

## 💡 Example Usage

Building an application with PyThra is simple and intuitive. Here’s a classic "Counter App" example:

```python
# main.py
from pythra.core import Framework
from pythra.widgets import *
from pythra.state import StatefulWidget, State
from pythra.base import Key
from pythra.styles import *

class CounterApp(StatefulWidget):
    """The root of our application."""
    def __init__(self, key: Key):
        super().__init__(key=key)

    def createState(self):
        return _CounterAppState()

class _CounterAppState(State):
    """Manages the state for the CounterApp."""
    def __init__(self):
        super().__init__()
        self.counter = 0

    def increment_counter(self):
        """A method to update the state and trigger a UI rebuild."""
        self.counter += 1
        self.setState()

    def build(self) -> Widget:
        """
        Describes the UI for the current state.
        This method is called every time setState() is invoked.
        """
        return Scaffold(
            appBar=AppBar(
                title=Text("PyThra Counter App")
            ),
            body=Center(
                child=Column(
                    mainAxisAlignment=MainAxisAlignment.CENTER,
                    children=[
                        Text("You have pushed the button this many times:"),
                        Text(
                            data=str(self.counter),
                            style=TextStyle(fontSize=36, fontWeight="bold", color=Colors.primary)
                        )
                    ]
                )
            ),
            floatingActionButton=FloatingActionButton(
                onPressed=self.increment_counter,
                onPressedName="increment_counter_fab", # A unique name for the callback
                tooltip="Increment",
                child=Icon(icon_name="plus") # Requires Font Awesome
            )
        )

if __name__ == '__main__':
    # Initialize and run the framework
    app = Framework.instance()
    app.set_root(CounterApp(key=Key("app_root")))
    app.run(title="My PyThra App")
```

## 📜 Philosophy

PyThra is built on the idea that building desktop UIs should be as fluid and logical as building for the modern web.

*   **The UI is a reflection of the state.** You don't manually show, hide, or update UI elements. You change the state, and the framework figures out the most efficient way to reflect those changes in the UI.
*   **Composition over inheritance.** Complex UIs are built by nesting simple widgets. A `Button` isn't a complex class; it's a `Container` with padding, a `Text` child, and an event listener.
*   **Developer Experience is paramount.** Features like hot reloading, a declarative API, and a single language (Python) for everything are designed to make development faster and more enjoyable.

## 🔬 Core Concepts

*   **Widget:** The base class for everything you see on the screen. Widgets are lightweight, immutable "blueprints" for UI elements.
*   **StatefulWidget & State:** For UI that needs to change dynamically, you use a `StatefulWidget`. Its mutable data is held in a separate `State` object. Calling `setState()` on this object is what triggers a UI rebuild.
*   **`build()` method:** The core of every `State` object. It must return a `Widget` tree that describes the UI for the current state.
*   **Reconciler:** The engine of the framework. It compares the widget tree returned by `build()` with the previous tree, generates a list of minimal changes (patches), and sends them to the web front-end to be applied to the DOM.
*   **Key:** A special object that gives a widget a stable identity across rebuilds. This is crucial for preserving state in lists and for maintaining focus on elements like `TextField`.

## 🤝 Contributing

Contributions are welcome! Whether it's reporting a bug, proposing a new feature, or submitting a pull request, your help is appreciated.

Please feel free to open an issue to discuss any changes or ideas.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details.

---
