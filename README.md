# Pythra

<!--![Pythra Logo]()  <!-- Add a link to your logo image -->

Pythra is a powerful and flexible GUI framework designed to bring the familiar and intuitive experience of Flutter to Python. With Pythra, developers can create beautiful, responsive desktop applications using a similar approach to Flutter, but with the full power and simplicity of Python.

## Features

- **Flutter-like Structure**: Pythra brings the same widget-based structure as Flutter, making it easy for Flutter developers to transition to Python or for Python developers to enjoy a modern UI framework.
- **State Management**: Manage application state efficiently with a built-in state management system inspired by Flutter's approach.
- **Widget Flexibility**: Create custom widgets with ease, leveraging the power of Python while keeping your UI code clean and maintainable.
- **Responsive Design**: Design your application once and have it look great on various desktop environments.
- **HTML & CSS Integration**: Render your GUI using HTML and CSS, providing flexibility and familiarity for web developers.

## Getting Started

### Prerequisites

- Python 3.7+
- PyWebView (for rendering the GUI)

### Installation

To get started with Pythra, you can clone the repository and install the necessary dependencies:

```bash
git clone https://github.com/yourusername/pythra.git
cd pythra
pip install -r requirements.txt
```

## Basic Usage

Here’s a quick example to get you started with Pythra:

```
# main.py

from framework.core import Framework
from framework.widgets import *
from framework.styles import *
from framework.state import StatefulWidget, State

class CounterApp(StatefulWidget):
    def createState(self):
        return CounterAppState()

class CounterAppState(State):
    def __init__(self):
        super().__init__()
        self.count = 0

    def create_widget(self):
        return Scaffold(
            body=Text(f'Counter: {self.count}'),
            floatingActionButton=ElevatedButton(
                text="Increment",
                onPressed=self.increment_count
            )
        )

    def increment_count(self):
        self.count += 1
        self.setState()

if __name__ == '__main__':
    app = PythraApp(root_widget=CounterApp())
    app.run()
```

