# =============================================================================
# PYTHRA API SYSTEM - The "Communication Bridge" Between Python and JavaScript
# =============================================================================

"""
PyThra API System

This is the "communication bridge" that allows your Python code to talk to the 
web browser (JavaScript) and vice versa. Think of it like a translator that helps
two different languages understand each other.

**What does the API handle?**
- Button clicks from the web page → Python functions
- Python data updates → Web page changes  
- Form inputs from browser → Python variables
- Python commands → Browser actions (like showing alerts)

**Real-world analogy:**
Like a walkie-talkie system between a control room (Python) and field workers (JavaScript).
The API makes sure messages get delivered correctly in both directions.
"""

from .window.webwidget import Api as WebWidgetApi

# =============================================================================
# EXTENDED API CLASS - PyThra's Enhanced Communication System
# =============================================================================

class Api(WebWidgetApi):
    """
    PyThra's Enhanced Communication Bridge - extends the basic web communication with PyThra-specific features.
    
    **What this class does:**
    - Inherits all the basic web communication abilities from WebWidgetApi
    - Adds PyThra-specific methods for advanced functionality
    - Provides a place to customize how Python and JavaScript communicate
    
    **Think of it like:**
    Upgrading a basic walkie-talkie to a smartphone - you get all the basic 
    communication features, plus advanced capabilities specific to your needs.
    
    **Key Responsibilities:**
    1. **Event Handling**: Processes clicks, form inputs, and other user interactions
    2. **Callback Management**: Manages Python functions that respond to web events
    3. **Data Synchronization**: Keeps Python data in sync with what the user sees
    4. **Custom Extensions**: Provides a place to add PyThra-specific communication features
    
    **Usage:**
    You typically don't create this directly - the Framework creates it automatically.
    But if you need custom communication features, this is where you'd add them.
    """
    def __init__(self):
        """
        Sets up PyThra's communication bridge when your app starts.
        
        **What happens during initialization:**
        1. Calls the parent WebWidgetApi setup (gets basic web communication working)
        2. Sets up PyThra-specific communication features
        3. Prepares the bridge for two-way Python ↔ JavaScript communication
        
        **Think of it like:**
        Setting up a phone line between two offices - making sure both ends
        can call each other and understand the conversation.
        """
        # Initialize the base web communication system first
        super().__init__()
        
        # TODO: Add PyThra-specific initialization here if needed
        # For example: custom event handlers, special callback registration, etc.

    # =============================================================================
    # CUSTOM PYTHRA METHODS - Add Your Own Communication Features Here
    # =============================================================================
    
    def custom_method(self):
        """
        Example of how to add custom communication features to PyThra.
        
        **This is a template method** - replace this with actual functionality you need!
        
        **Ideas for custom methods:**
        - custom_alert(): Show custom notifications to users
        - send_analytics(): Send usage data to analytics services  
        - handle_file_uploads(): Process files uploaded by users
        - sync_with_database(): Synchronize data with external databases
        
        **Example of a real custom method:**
        ```python
        def show_success_message(self, message: str):
            \"\"\"Shows a success message to the user in the browser\"\"\"
            self.evaluate_js(f"alert('Success: {message}')")
        ```
        """
        print("🔧 PyThra API | Custom method called - replace this with real functionality!")
