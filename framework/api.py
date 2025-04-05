# framework/api.py
# Import the Api class from webwidget
from .window.webwidget import Api as WebWidgetApi

# Extend the WebWidgetApi class
class Api(WebWidgetApi):
    """
    Extended API class for the framework, inheriting from WebWidgetApi.

    Methods:
        custom_method: Demonstrates how to add custom behavior to the extended API.
    """
    def __init__(self):
        """
        Initialize the extended API class.

        Calls the initializer of the parent WebWidgetApi class.
        """
        super().__init__()

    # Add any additional methods or overrides as needed
    def custom_method(self):
        """
        A custom method added to the extended API.

        Prints a message to the console.
        """
        print("This is a custom method in the extended API.")
