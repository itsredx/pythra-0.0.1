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
    TextEditingController, InputDecoration,
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

        # --- State now holds controllers, not raw strings ---
        self.username_controller = TextEditingController(text="initial text")
        self.password_controller = TextEditingController()

        # Add a listener to a controller to react to changes
        self.username_controller.add_listener(self.on_username_updates)
        
        # State to track login errors
        self.login_error = None

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


    def on_username_updates(self):
        print(f"Listener notified! Username is now: {self.username_controller.text}")
        # We still need to call setState if a listener changes other parts of the UI
        # For simple text updates, this isn't necessary, but for validation it is.
        if self.login_error and len(self.username_controller.text) > 3:
            self.login_error = None
            self.setState() # Re-render to remove the error message

    def attempt_login(self):
        username = self.username_controller.text
        password = self.password_controller.text
        
        print(f"Login attempt: {username} / {password}")
        if len(username) <= 3:
            self.login_error = "Username must be longer than 3 characters."
            self.setState()
            print(self.login_error)
        else:
            self.login_error = None
            # Do actual login logic
            self.setState()

        print(self.login_error)


    def build(self):
        username_decoration = InputDecoration(
            label="Username",
            errorText=self.login_error
        )
        
        password_decoration = InputDecoration(
            label="Password",
            focusColor=Colors.tertiary, # Use a different color on focus
            border=BorderSide(width=1, color=Colors.grey), # Thinner, grey border
            filled=False
            # You could add a suffix icon to toggle visibility here
        )
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
                        controller=self.username_controller,
                        decoration= username_decoration,
                    ),
                    
                    SizedBox(height=16),

                    TextField(
                        key=Key("password_field"), # Another unique key
                        controller=self.password_controller,
                        decoration= password_decoration,
                        # enabled= False,
                        # You would add a property to make this a password type input
                    ),
                    
                    SizedBox(height=24),
                    
                    ElevatedButton(
                        onPressed=self.attempt_login,
                        child=Text("Login"),
                    ),
                    SizedBox(height=24),
                    Text(self.username_controller.text, key=Key("logged")),
                ]
            )
        )

if __name__ == '__main__':
    app = Framework.instance()
    app.set_root(MyForm(key=Key("my_app_root")))
    app.run(title="TextField Focus Test")