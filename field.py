# In your main application file (e.g., main.py)

from pythra.core import Framework
from pythra.widgets import *
from pythra.styles import *
from pythra.state import StatefulWidget, State
from pythra.base import Key
from pythra.controllers import SliderController

from pythra import (
    Framework, State, StatefulWidget, Key, Container,
    Column, Row, Text, ElevatedButton, SizedBox,
    Colors, EdgeInsets, MainAxisAlignment, CrossAxisAlignment,
    ButtonStyle, BoxDecoration, BorderRadius, Alignment, # <-- ADD THESE IMPORTS
    TextEditingController, InputDecoration,
)

# In your main.py or any component's build method

class MyComponent(StatefulWidget):
    def __init__(self, key: Key):
        super().__init__(key=key)

    def createState(self):
        return MyComponentState()

class MyComponentState(State):
    def __init__(self):
        super().__init__()
        self.slider_controller = SliderController(value=0.5)

    def handle_slider_change(self, new_value):
        print(f"Slider value changed to: {new_value}")
        # The Slider's internal state handles the visual update automatically.
        # We just store the final value.
        self.slider_controller.value = new_value
        self.setState()
        # No need to call setState here unless this value affects other widgets.

    def handle_slider_change_async(self, new_value):
        print(f"Slider value changed to: {new_value}")
        # The Slider's internal state handles the visual update automatically.
        # We just store the final value.
        self.slider_controller.value = new_value
        self.setState()
        # No need to call setState here unless this value affects other widgets.

    def move_slider(self):
        self.slider_controller.value += 0.1
        self.setState()
        pass

    def build(self) -> Widget:
        red_slider_theme = SliderTheme(
            activeTrackColor=Colors.red,
            inactiveTrackColor=Colors.rgba(255, 0, 0, 0.3),
            thumbColor=Colors.red,
            overlayColor=Colors.rgba(255, 0, 0, 0.2),
            trackHeight=8.0,
            thumbSize=12.0
        )
        return Column(
            key=Key("my_volume_slider_column"),
            crossAxisAlignment = CrossAxisAlignment.STRETCH,
            children=[
                Text(f"Current Value: {self.slider_controller.value:.2f}", key=Key("my_volume_slider_value"),),
                Slider(
                    key=Key("my_volume_slider"),
                    controller=self.slider_controller,
                    # onChanged=self.handle_slider_change_async,
                    onChangeEnd=self.handle_slider_change,
                    theme=red_slider_theme,
                    min=0.0,
                    max=1.0,
                    divisions=10, # Creates 10 discrete steps
                    # activeColor=Colors.green,
                    # thumbColor=Colors.white
                ),
                SizedBox(key=Key("sizedbox-for-mv-slider-btn"),height=24),
                ElevatedButton(
                    key=Key("mv-slider-btn"),
                        onPressed=self.move_slider,
                        child=Text("Move"),
                    ),
            ]
        )


class MyTextField(StatefulWidget):
    def __init__(self, key: Key):
        super().__init__(key=key)

    def createState(self):
        return MyTextFieldState()

class MyTextFieldState(State):
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

    def attempt_login(self, args):
        username = self.username_controller.text
        password = self.password_controller.text
        print(args[0], "From attempt_login")
        print(args[1], "From attempt_login")
        
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

    def build(self) -> Widget:
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
        return Column(
            key=Key("my_textfields_column"),
            crossAxisAlignment = CrossAxisAlignment.STRETCH,
            children=[
                TextField(
                        # The Key is CRITICAL for preserving focus!
                        key=Key("username_field"),
                        controller=self.username_controller,
                        decoration= username_decoration,
                    ),
                    
                    SizedBox(key=Key("sizedbox-for-txt-fields"),height=16),

                    TextField(
                        key=Key("password_field"), # Another unique key
                        controller=self.password_controller,
                        decoration= password_decoration,
                        # enabled= False,
                        obscureText= True,
                        # You would add a property to make this a password type input
                    ),
                    
                    SizedBox(key=Key("sizedbox-for-btn"),height=24),
                    
                    ElevatedButton(
                        key=Key("login-btn"),
                        onPressed=self.attempt_login,
                        callbackArgs=['clalback', 23],
                        child=Text("Login"),
                    ),
                    SizedBox(key=Key("sizedbox-for-logged-txt"),height=24),
                    Text(self.username_controller.text, key=Key("logged")),
            ]
        )


class MyForm(StatefulWidget):
    def __init__(self, key: Key):
        super().__init__(key=key)

    def createState(self):
        return MyFormState()

class MyFormState(State):
    def __init__(self):
        super().__init__()
        self.my_textfield = MyTextField(key=Key("my_textfields"))
        self.my_slider = MyComponent(key=Key("my_slider"))


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
                    self.my_textfield,
                    SizedBox(height=24),
                    self.my_slider
                ]
            )
        )

if __name__ == '__main__':
    app = Framework.instance()
    app.set_root(MyForm(key=Key("my_app_root")))
    app.run(title="TextField Focus Test")