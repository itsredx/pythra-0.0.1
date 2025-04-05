import time
from threading import Thread
from framework.core import Framework
from framework.state import State, StateManager
from framework.widgets import *
from framework.styles import *

       


class MyApp:
    def __init__(self):
        self.framework = Framework()
        self.new_text = 'Initial Text'

    def change_text_periodically(self):
        text_variants = ["Hello, World!", "Welcome to Teesical!", "State Management in Action!", "Python is awesome!"]
        i = 0
        while True:
            self.new_text = text_variants[i % len(text_variants)]
            self.ui()
            i += 1
            time.sleep(2)

    def ui(self):
        text_widget = Text(self.new_text)

        scaffold = Scaffold(
            body=Container(
                child=text_widget,
                padding=EdgeInsets.all(20),
                constraints=BoxConstraints(max_width=300, max_height=300)
            )
        )

        self.framework.set_root(scaffold)

    def run(self):
        self.ui()
        
        Thread(target=self.change_text_periodically, daemon=True).start()
        
        self.framework.run(title='State Management Test')

if __name__ == "__main__":
    app = MyApp()
    app.run()
