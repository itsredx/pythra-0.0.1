# In your main application file (e.g., main.py)

from pythra.core import Framework
from pythra.widgets import *
from pythra.styles import *
from pythra.state import StatefulWidget, State
from pythra.base import Key
from pythra.controllers import *

from pythra import (
    Framework, State, StatefulWidget, Key, Container,
    Column, Row, Text, ElevatedButton, SizedBox,
    Colors, EdgeInsets, MainAxisAlignment, CrossAxisAlignment,
    ButtonStyle, BoxDecoration, BorderRadius, Alignment, # <-- ADD THESE IMPORTS
    TextEditingController, InputDecoration,
)

class MyDropDown(StatefulWidget):
    def __init__(self, key: Key):
        super().__init__(key=key)

    def createState(self):
        return DropDownState()

class DropDownState(State):
    def initState(self):
        # 1. Create and hold the controller in your state.
        #    Initialize with a value if you have a default selection.
        self.dropdown_controller = DropdownController(selectedValue='usa')

        self.countries = [
            ("United States", "usa"),
            ("Canada", "can"),
            ("Mexico", "mex")
        ]

    def _on_country_changed(self, new_value):
        # 3. This callback updates the controller and triggers a rebuild.
        print(f"Dropdown value changed to: {new_value}")
        self.dropdown_controller.selectedValue = new_value
        self.setState()

    def build(self) -> Widget:
        # Get the current label to display it elsewhere in the UI if needed
        current_label = ""
        for label, val in self.countries:
            if val == self.dropdown_controller.selectedValue:
                current_label = label
                break

        return Column(
            crossAxisAlignment = CrossAxisAlignment.START,
            children=[
                Text(f"Selected Country Code: {self.dropdown_controller.selectedValue}"),
                Text(f"Selected Country Name: {current_label}"),
                SizedBox(height=20),
                
                # 2. In your build method, create the Dropdown widget.
                Dropdown(
                    key=Key("country_selector"),
                    controller=self.dropdown_controller,
                    items=self.countries,
                    onChanged=self._on_country_changed
                )
            ]
        )

class RadioExample(StatefulWidget):
    def __init__(self, key: Key):
        super().__init__(key=key)

    def createState(self):
        return RadioExampleState()

class RadioExampleState(State):
    def initState(self):
        # This one variable controls the entire radio group.
        self._selected_option = "apple"

    def _on_option_changed(self, new_value):
        print(f"Radio option changed to: {new_value}")
        self._selected_option = new_value
        self.setState()

    def build(self) -> Widget:
        # Helper function to create a row for a radio button and its label
        def create_radio_row(text: str, value: str):
            return Row(
                key=Key(f"row_{value}"),
                crossAxisAlignment=CrossAxisAlignment.CENTER,
                children=[
                    Radio(
                        key=Key(value),
                        value=value,
                        groupValue=self._selected_option,
                        onChanged=self._on_option_changed
                    ),
                    SizedBox(width=8),
                    Text(text)
                ]
            )

        return Column(
            key=Key("radio_group_column"),
            crossAxisAlignment=CrossAxisAlignment.START,
            children=[
                create_radio_row("Apple", "apple"),
                SizedBox(key=Key("sizer_apple"), height=8),
                create_radio_row("Orange", "orange"),
                SizedBox(key=Key("sizer_orange"),height=8),
                create_radio_row("Banana", "banana"),
                SizedBox(key=Key("sizer_banana"),height=16),
                Text(f"Selected fruit: {self._selected_option.capitalize()}", key=Key("selection_text"))
            ]
        )


class SwitchExample(StatefulWidget):
    def __init__(self, key: Key):
        super().__init__(key=key)

    def createState(self):
        return SwitchExampleState()

class SwitchExampleState(State):
    def initState(self):
        self._is_on = True

    def _on_switch_changed(self, new_value: bool):
        print(f"Switch toggled to: {new_value}")
        self._is_on = new_value
        self.setState()

    def build(self) -> Widget:
        return Container(
            padding=EdgeInsets.all(16),
            child=Row(
                mainAxisAlignment=MainAxisAlignment.SPACE_BETWEEN,
                children=[
                    Text("Notifications"),
                    Switch(
                        key=Key("notification_switch"),
                        value=self._is_on,
                        onChanged=self._on_switch_changed,
                        # Optional: override the active color
                        activeColor=Colors.green,
                    )
                ]
            )
        )

class SwitchExample2(StatefulWidget):
    def __init__(self, key: Key):
        super().__init__(key=key)

    def createState(self):
        return SwitchExample2State()

class SwitchExample2State(State):
    def initState(self):
        self._is_on = False

    def _on_switch_changed(self, new_value: bool):
        print(f"Switch toggled to: {new_value}")
        self._is_on = new_value
        self.setState()

    def build(self) -> Widget:
        return Container(
            key=Key("switch_ex_container"),
            padding=EdgeInsets.all(16),
            child=Row(
                key=Key("switch_ex_row"),
                mainAxisAlignment=MainAxisAlignment.SPACE_BETWEEN,
                children=[
                    Text("Pop up Notifications",key=Key("Pop_up_notification_switch_txt")),
                    Switch(
                        key=Key("Pop_up_notification_switch"),
                        value=self._is_on,
                        onChanged=self._on_switch_changed,
                        # Optional: override the active color
                        activeColor=Colors.green,
                    )
                ]
            )
        )

class CheckBox(StatefulWidget):
    def __init__(self, key: Key):
        super().__init__(key=key)

    def createState(self):
        return CheckBoxState()


class CheckBoxState(State):
    def initState(self):
        # 1. Hold the boolean state for your checkbox.
        self._is_checked = False
        self._is_custom_checked = True

    def _on_checkbox_changed(self, new_value: bool):
        # 3. This callback updates the state and triggers a rebuild.
        print(f"Checkbox value changed to: {new_value}")
        self._is_checked = new_value
        self.setState()
        
    def _on_custom_checkbox_changed(self, new_value: bool):
        self._is_custom_checked = new_value
        self.setState()

    def build(self) -> Widget:
        # Define an optional custom theme
        custom_theme = CheckboxTheme(
            activeColor=Colors.green,
            inactiveColor=Colors.grey,
            checkColor=Colors.white,
            size=24.0
        )
        
        return Container(
            alignment=Alignment.center(),
            child=Column(
                mainAxisAlignment=MainAxisAlignment.CENTER,
                crossAxisAlignment=CrossAxisAlignment.START,
                children=[
                    # --- Example 1: Default Checkbox ---
                    Row(
                        children=[
                            Checkbox(
                                key=Key("default_checkbox"),
                                value=self._is_checked,
                                onChanged=self._on_checkbox_changed
                            ),
                            SizedBox(key=Key("sizer_def_cb"), width=8),
                            Text("Default Checkbox")
                        ]
                    ),
                    SizedBox(key=Key("sizer_cb_main"), height=8),
                    # --- Example 2: Themed Checkbox ---
                    Row(
                        children=[
                            Checkbox(
                                key=Key("custom_checkbox"),
                                value=self._is_custom_checked,
                                onChanged=self._on_custom_checkbox_changed,
                                theme=custom_theme
                            ),
                            SizedBox(key=Key("sizer_cus_cb"), width=8),
                            Text("Custom Themed Checkbox")
                        ]
                    )
                ]
            )
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
        self.my_checkBox = CheckBox(key=Key("my_checkBox_wig"))
        self.my_switch = SwitchExample(key=Key("my_switch_example")) # <-- Instantiate it
        self.my_switch2 = SwitchExample2(key=Key("my_switch2_example")) # <-- Instantiate it
        self.my_radio_group = RadioExample(key=Key("my_radio_group")) # <-- Instantiate it
        self.my_dropdown_example = MyDropDown(key=Key("my_dropdown"))


    def build(self):
        
        return Container(
            key=Key("Build_container"),
            alignment=Alignment.top_center(),
            padding=EdgeInsets.all(32),
            child=Column(
                key=Key("main__column"),
                crossAxisAlignment=CrossAxisAlignment.STRETCH,
                children=[
                    Row(
                        mainAxisAlignment = MainAxisAlignment.SPACE_BETWEEN,
                        children=[
                            Text("Dropdown Test",key=Key('Login_header'), style=TextStyle(fontSize=24, fontWeight='bold')),
                            ElevatedButton(
                                onPressed= self.framework.close,
                                child=Container(
                                    height=15,
                                    width=15,
                                    color=Colors.red,
                                    decoration = BoxDecoration(
                                        borderRadius = BorderRadius.circular(4),
                                    )
                                ),
                                style=ButtonStyle(
                                    padding=EdgeInsets.all(0),
                                    margin=EdgeInsets.all(0),
                                    backgroundColor=Colors.transparent,
                                    shape = BorderRadius.all(0),
                                    elevation= 0,
                                )
                            )
                        ]
                    ),
                    # SizedBox(height=24),
                    # self.my_textfield,
                    # SizedBox(height=24),
                    # self.my_slider,
                    SizedBox(height=24),
                    # self.my_checkBox,
                    # SizedBox(height=16), # <-- Add some space
                    # self.my_switch,     # <-- Add the switch example here
                    # SizedBox(height=24),
                    # self.my_switch2,     # <-- Add the switch example here
                    # SizedBox(height=24),
                    # self.my_radio_group, # <-- Add the radio group here
                    SizedBox(height=24),
                    self.my_dropdown_example,
                ]
            )
        )

if __name__ == '__main__':
    app = Framework.instance()
    app.set_root(MyForm(key=Key("my_app_root")))
    app.run(title="TextField Focus Test")