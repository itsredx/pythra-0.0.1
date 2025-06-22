# import sys
# import time
# import random
# import string
# from PySide6.QtCore import (
#     QTimer,
#     QCoreApplication,
# )  # Use QCoreApplication for timer loop if needed

# # Framework Imports
# from pythra import (
#     Framework,
#     State,
#     StatefulWidget,
#     Key,
#     Widget,
#     Icon,
#     Container,
#     Column,
#     Row,
#     Text,
#     ElevatedButton,
#     Spacer,
#     IconButton,
#     SizedBox,
#     Colors,
#     EdgeInsets,
#     MainAxisAlignment,
#     CrossAxisAlignment,
#     AssetImage,
#     FloatingActionButton,
#     ButtonStyle,
#     BoxDecoration,
#     BorderRadius,  # Assuming ButtonStyle is compatible
#     ListTile,
#     Divider,
#     SingleChildScrollView,
#     Scaffold,
#     AppBar,
#     ScrollBar,
#     ListView,
#     Padding,
#     __all__,  # Example usage
# )


# class MyTestApp(StatefulWidget):
#     def createState(self):
#         return MyTestAppState()

# class MyTestAppState(State):
#     def build(self):
#         return ScrollBar(
#             content=Container(
#                 child=ListView(
#                 children=[
#                         ListTile(
#                             key=Key(f"item_{i}"),
#                             title=Text(f"List Item Number {i+1}"),
#                             subtitle=Text("This is a subtitle for the item."),
#                             leading=Icon(icon_name="check")
#                         ) for i in range(50) # Create enough items to make it scroll
#                     ]
#                 )))

# if __name__ == '__main__':
#     app = Framework.instance()
#     app.set_root(MyTestApp(key=Key("app_root")))
#     app.run(title="ScrollBar Test")


# In your main application file (e.g., main.py)
# In your main.py

from pythra.core import Framework
from pythra.widgets import *
from pythra.state import StatefulWidget, State
from pythra.base import Key
from pythra.styles import *


class MyApp(StatefulWidget):
    def createState(self) -> State:
        return MyAppState()


class MyAppState(State):
    def build(self):
        # A nice blue theme for our scrollbar
        blue_theme = ScrollbarTheme(
            width=12,
            thumbColor="#2196F3",
            trackColor="rgba(0, 0, 128, 0.1)",
            thumbHoverColor="#1976D2",
            radius=6,
        )

        long_list = [ListTile(key=Key(i), title=Text(f"Item #{i}")) for i in range(100)]

        return Scaffold(
            appBar=AppBar(title=Text("SimpleBar Integration Demo")),
            body=Container(
                color=Colors.lightgreen,
                height=300,
                padding=EdgeInsets.all(16),
                child=Container(
                    color=Colors.lightpink,
                    height="100%",
                    child=Scrollbar(
                        # The Scrollbar now defines the scrollable area's height
                        height=100,
                        theme=blue_theme,
                        autoHide=False,  # Make scrollbar always visible for demo
                        child=Column(
                            crossAxisAlignment=CrossAxisAlignment.STRETCH,
                            children=[
                                Container(
                                    height=200,
                                    padding=EdgeInsets.all(16),
                                    child=Scrollbar(
                                        # The Scrollbar now defines the scrollable area's height
                                        height=100,
                                        theme=blue_theme,
                                        autoHide=False,  # Make scrollbar always visible for demo
                                        child=ListView(
                                            padding=EdgeInsets.all(12),
                                            children=long_list,
                                        ),
                                    ),
                                ),
                                SizedBox(
                                    height=20,
                                ),
                                Container(
                                    height=200,
                                    padding=EdgeInsets.all(16),
                                    child=Scrollbar(
                                        # The Scrollbar now defines the scrollable area's height
                                        height=100,
                                        theme=blue_theme,
                                        autoHide=False,  # Make scrollbar always visible for demo
                                        child=ListView(
                                            padding=EdgeInsets.all(12),
                                            children=long_list,
                                        ),
                                    ),
                                ),
                                SizedBox(
                                    height=20,
                                ),
                                Container(
                                    height=200,
                                    padding=EdgeInsets.all(16),
                                    child=Scrollbar(
                                        # The Scrollbar now defines the scrollable area's height
                                        height=100,
                                        theme=blue_theme,
                                        autoHide=False,  # Make scrollbar always visible for demo
                                        child=ListView(
                                            padding=EdgeInsets.all(12),
                                            children=long_list,
                                        ),
                                    ),
                                ),
                                SizedBox(
                                    height=50,
                                ),
                            ],
                        ),
                    ),
                ),
            ),
        )


if __name__ == "__main__":
    app = Framework.instance()
    app.set_root(MyApp(key=Key("app")))
    app.run(title="Pythra with SimpleBar")
