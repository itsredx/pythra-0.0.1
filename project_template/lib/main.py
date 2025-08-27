import os

# Welcome to your new Pythra App!
from pythra import (
    Framework,
    StatefulWidget,
    State,
    Key,
    Widget,
    Container,
    Text,
    Alignment,
    Colors
)

class HomePageState(State):
    def build(self) -> Widget:
        return Container(
            color=Colors.background,
            alignment=Alignment.center(),
            child=Text("Welcome to Pythra!")
        )

class HomePage(StatefulWidget):
    def createState(self) -> HomePageState:
        return HomePageState()

def main() -> Widget:
    """The main entry point for the application."""
    return HomePage(key=Key("home_page"))

if __name__ == '__main__':
    # This allows running the app directly with `python lib/main.py`
    # as well as with the CLI's `pythra run` command.
    app = Framework.instance()
    app.set_root(main())
    app.run(title="My New Pythra App")