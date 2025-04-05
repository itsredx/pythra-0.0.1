# main.py state v--01 test

from framework.core import Framework
from framework.widgets import *
from framework.styles import *
from framework.state import StatefulWidget, State

Colors = Colors()

class CounterState(State):
    def __init__(self):
        super().__init__()
        self.count = 0

    def increment(self):
        self.count += 1
        self.setState()

    def decrement(self):
        self.count -= 1
        self.setState()

    def build(self):
        return Column(
            children=[
                Text(f'Count: {self.count}'),
                ElevatedButton(
                    child=Text('Increment'),
                    onPressed=self.increment,
                ),
                SizedBox(
                    height=16
                ),
                ElevatedButton(
                    child=Text('Decrement'),
                    onPressed=self.decrement,
                )
            ]
        )


class CounterWidget(StatefulWidget):
    def createState(self):
        return CounterState()


class MyApp:
    def __init__(self):
        self.framework = Framework()
        self.counter_widget = CounterWidget()

    def update_ui(self):
        scaffold = Scaffold(
            appBar=AppBar(
                title=Text('Counter App'),
            ),
            body=Body(
                child=Column(
                    children=[
                        self.counter_widget, # Using the CounterWidget
                        Dialog(
                            title=Text(
                                'Dialog Title',
                                style=TextStyle(
                                    fontSize=14,
                                    fontWeight='bold',

                                )
                            ),
                            content=Text(
                                "Dialog Content can be seen here Dialog Content can be seen here",
                                style=TextStyle(
                                    fontSize=10,
                                    #fontWeight=10,

                                )
                            ),
                            actions=[
                                Padding(
                                    EdgeInsets.LRTB(top=10, bottom=10),
                                    child=Row(
                                    mainAxisAlignment=MainAxisAlignment.SPACE_AROUND,
                                    children=[
                                        TextButton(
                                    child=Text('Click Me'),
                                    style=ButtonStyle(
                                        backgroundColor= Colors.grey ,
                                        foregroundColor= Colors.white, 
                                    )
                                ),
                                SizedBox(
                                    width=10
                                ),
                                TextButton(
                                    child=Text('Dont Click')
                                )
                                    ]
                                )
                                ),
                                
                            ]
                        )
                    ]
                ) 
            ),
        )
        self.framework.set_root(scaffold)
        #print('Debug print from MyApp(){','First ID:', self.counter_widget.widget_id(),'First HTML:', self.counter_widget.to_html(),'}')

    def run(self):
        self.update_ui()
        self.framework.run(title='MyApp')

if __name__ == "__main__":
    app = MyApp()
    app.run()
