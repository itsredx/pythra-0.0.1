# In your main application file (e.g., main.py)

from pythra.core import Framework
from pythra.widgets import *
from pythra.state import StatefulWidget, State
from pythra.base import Key

from pythra import (
    Framework, State, StatefulWidget, Key, Container,
    Column, Row, Text, ElevatedButton, SizedBox,
    Colors, EdgeInsets, MainAxisAlignment, CrossAxisAlignment,
    ButtonStyle, BoxDecoration, BorderRadius, Alignment, # <-- ADD THESE IMPORTS
)

class MyForm(StatefulWidget):
    def __init__(self, key: Key):
        super().__init__(key=key)

    def createState(self):
        return MyFormState()

class MyFormState(State):
    def __init__(self):
        super().__init__()
        # --- State variables to hold the text field values ---
        self.username = ""
        self.password = ""
        self.logged = ""

    # --- Callback method for the username field ---
    def on_username_changed(self, new_value):
        print(f"Username changed to: {new_value}")
        self.username = new_value
        self.setState() # Trigger a UI rebuild

    def on_login(self):
        self.logged = f'Logged in as {self.username}'
        print(f"Login attempt: {self.username} / {self.password}")
        self.setState()

    # --- Callback method for the password field ---
    def on_password_changed(self, new_value):
        self.password = new_value
        self.setState()

    def build(self):
        return Container(
            key=Key("Build_container"),
            alignment=Alignment.top_center(),
            padding=EdgeInsets.all(32),
            child=Column(
                key=Key("main__column"),
                crossAxisAlignment=CrossAxisAlignment.STRETCH,
                children=[
                    Text("Login Form",key=Key('Login_header'), style=TextStyle(fontSize=24, fontWeight='bold')),
                    SizedBox(height=24),
                    
                    TextField(
                        # The Key is CRITICAL for preserving focus!
                        key=Key("username_field"), 
                        label="Username",
                        value=self.username,
                        onChanged=self.on_username_changed
                    ),
                    
                    SizedBox(height=16),

                    TextField(
                        key=Key("password_field"), # Another unique key
                        label="Password",
                        value=self.password,
                        onChanged=self.on_password_changed
                        # You would add a property to make this a password type input
                    ),
                    
                    SizedBox(height=24),
                    
                    ElevatedButton(
                        onPressed=self.on_login,
                        child=Text("Login"),
                    ),
                    SizedBox(height=24),
                    Text(self.logged, key=Key("logged")),
                ]
            )
        )

if __name__ == '__main__':
    app = Framework.instance()
    app.set_root(MyForm(key=Key("my_app_root")))
    app.run(title="TextField Focus Test")