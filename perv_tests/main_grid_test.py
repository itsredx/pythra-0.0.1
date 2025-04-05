# main.py

from framework.core import Framework
from framework.widgets import *
from framework.styles import *

class ButtonApp:
    def __init__(self):
        self.framework = Framework()
        self.count = 0

    def increment_count(self):
        self.count += 1
        self.update_ui()

    def decrement_count(self):
        self.count -= 1
        self.update_ui()

    def update_ui(self):
        counter_text = Text(
            data=f'Button pressed {self.count} times',
            style=TextStyle(fontSize=20, color=Colors.color('black')),
            textAlign='center'
        )

        button_style_increment = ButtonStyle(
            backgroundColor=Colors.color('blue'),
            foregroundColor=Colors.color('white'),
            padding=EdgeInsets.all(10),
            textStyle=TextStyle(fontSize=18)
        )

        button_style_decrement = ButtonStyle(
            backgroundColor=Colors.color('red'),
            foregroundColor=Colors.color('white'),
            padding=EdgeInsets.all(10),
            textStyle=TextStyle(fontSize=18)
        )

        increment_button = IconButton(
            child=Icon(icon_name='plus'),
            onPressed='increment_count',
            style=button_style_increment
        )

        decrement_button = IconButton(
            child=Icon(icon_name='minus'),
            onPressed='decrement_count',
            style=button_style_decrement
        )

        items = [
            Text(data=f'Item {i}', style=TextStyle(fontSize=16, color=Colors.color('black'))) for i in range(20)
        ]

        grid_view = GridView(
            children=items,
            padding=EdgeInsets.all(10),
            scrollDirection=Axis.VERTICAL,
            primary=True,
            crossAxisCount=3,
            mainAxisSpacing=10,
            crossAxisSpacing=10,
            childAspectRatio=1.0,
            physics=ScrollPhysics.BOUNCING
        )

        column = Column(
            children=[
                counter_text,
                increment_button,
                decrement_button,
                grid_view
            ],
            mainAxisAlignment=MainAxisAlignment.CENTER,
            crossAxisAlignment=CrossAxisAlignment.CENTER,
        )

        container = Container(
            child=column,
            padding=EdgeInsets.all(20),
            color=Colors.color('lightgrey'),
            width=400,
            height=1500,
            constraints=BoxConstraints(min_width=300, min_height=1500),
            alignment=Alignment.center(),
            margin=EdgeInsets.all(10)
        )

        self.framework.set_root(container)

    def run(self):
        self.framework.api.register_callback('increment_count', self.increment_count)
        self.framework.api.register_callback('decrement_count', self.decrement_count)
        self.update_ui()
        self.framework.run(title='Button App')

if __name__ == "__main__":
    app = ButtonApp()
    app.run()
