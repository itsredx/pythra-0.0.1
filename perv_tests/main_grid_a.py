# main.py

from framework.core import Framework
from framework.widgets import *
from framework.styles import *


class GridApp:
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
            padding=EdgeInsets.symmetric(horizontal=12, vertical=10),
            textStyle=TextStyle(fontSize=18),
            side=BorderSide(style=BorderStyle.HIDDEN, color=Colors.color('red'), borderRadius=10)
        )

        button_style_decrement = ButtonStyle(
            backgroundColor=Colors.color('red'),
            foregroundColor=Colors.color('white'),
            padding=EdgeInsets.symmetric(horizontal=12, vertical=10),
            textStyle=TextStyle(fontSize=18),
            side=BorderSide(style=BorderStyle.HIDDEN, color=Colors.color('red'), borderRadius=10)
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
            Text(data=f'Item {i + 1}', style=TextStyle(fontSize=16, color=Colors.color('black'))) for i in range(self.count if self.count != 0 else 20)
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

        row = Row(
            children=[
                increment_button,
                decrement_button
            ],
            mainAxisSize= mainAxisSize.MAX,
            mainAxisAlignment=MainAxisAlignment.SPACE_EVENLY,
            crossAxisAlignment=CrossAxisAlignment.CENTER,
        )

        column = Column(
            children=[
                counter_text,
                row,
                grid_view
            ],
            mainAxisAlignment=MainAxisAlignment.START,
            crossAxisAlignment=CrossAxisAlignment.CENTER,
        )

        container = Container(
            child=column,
            padding=EdgeInsets.all(20),
            color=Colors.color('lightgrey'),
            width=400,
            height=1000,
            constraints=BoxConstraints(min_width=300, min_height=1000),
            alignment=Alignment.top_center(),
            margin=EdgeInsets.all(10)
        )

        floating_button = FloatingActionButton(
            child=Icon(icon_name="plus"),
            onPressed="increment_count"
        )

        body = Body(
            child= container,
        )

        title = Text(
            data=f'Grid App',
            style=TextStyle(fontSize=20, color=Colors.color('white')),
            textAlign=TextAlign.left()
        )

        appBar = AppBar(
            title=title,
            pinned=True,
            backgroundColor=Colors.color('blue'),
            elevation=20,
            titleSpacing=15,
            shadowColor=Colors.rgba(100, 100, 111, 0.2),#0px 7px 29px 0px;
            leading= Image(
                AssetImage('soldiers.jpg'),
                height=20,
                width=20,
                fit= ImageFit.COVER,  
            )
        )

        scaffold = Scaffold(
            appBar= appBar,
            body= body,
            floatingActionButton= floating_button,
            extendBodyBehindAppBar= True
        )

        self.framework.set_root(scaffold)

    def run(self):
        self.framework.api.register_callback('increment_count', self.increment_count)
        self.framework.api.register_callback('decrement_count', self.decrement_count)
        self.update_ui()
        self.framework.run(title='Grid App')

if __name__ == "__main__":
    app = GridApp()
    app.run()
