from pythra.core import Framework
from pythra.widgets import *
from pythra.styles import *
from pythra.state import StatefulWidget, State
import time
from threading import Thread

Colors = Colors()
class MyAppState(State):
    def __init__(self):
        super().__init__()
        self.new_text = ''

    def change_text_periodically(self):
        text_variants = ["Settings Page", "Hello, World!", "Welcome to Teesical!", "State Management in Action!", "Python is awesome!"]
        i = 0
        while True:
            self.new_text = text_variants[i % len(text_variants)]
            self.setState()
            i += 1
            time.sleep(10)

    def build(self):
        Thread(target=self.change_text_periodically, daemon=True).start()
        return Container(
                key='container',
                child=Text(
                    self.new_text, 
                    key='container-text',
                    ),
                padding=EdgeInsets.all(20),
                margin=EdgeInsets.all(20),
                constraints=BoxConstraints(max_width=300, max_height=300),
                decoration=BoxDecoration(
                    color=Colors.lightblue,
                    borderRadius=25,
                )
            )


class MyApp(StatefulWidget):
    def createState(self):
        return MyAppState()


# The main application class to run the framework
class Application:
    def __init__(self):
        self.framework = Framework()
        self.my_app = MyApp()

    def run(self):
        self.framework.set_root(self.my_app)
        
        self.framework.run(title='MyApp')


if __name__ == "__main__":
    app = Application()
    app.run()