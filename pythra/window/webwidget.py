"""
=============================================================================
                    PYTHRA WEBWIDGET MODULE
=============================================================================

This module is the core web interface component of the PyThra Framework.
It handles the creation and management of desktop windows that display web content
using Qt's WebEngine (which is based on Chromium browser engine).

🎯 MAIN PURPOSES:
    1. Create desktop application windows
    2. Display web content (HTML/CSS/JavaScript) inside Qt widgets
    3. Enable communication between Python backend and JavaScript frontend
    4. Handle window management (minimize, maximize, close, etc.)
    5. Suppress browser deprecation warnings for clean console output

📚 KEY CONCEPTS FOR STUDENTS:
    - Qt: Cross-platform application framework (think of it as the "engine")
    - WebEngine: Embeds a web browser inside a desktop application
    - WebChannel: Allows Python and JavaScript to talk to each other
    - QApplication: The main application container (every Qt app needs one)

🔧 TECHNICAL STACK:
    - PySide6: Python bindings for Qt framework
    - QtWebEngine: Web browser component based on Chromium
    - WebChannel: Bidirectional communication bridge

Author: PyThra Framework Team
Last Modified: 2025
=============================================================================
"""

import os

# =============================================================================
# BROWSER ENGINE CONFIGURATION
# =============================================================================

# 🌐 CHROMIUM ENGINE SETUP
# These environment variables configure the underlying Chromium browser engine
# that powers Qt's WebEngine component. Think of this as "browser settings"
# that we set before the browser starts up.

# Set Chromium flags to suppress CSS deprecation warnings and console messages
# This is like passing command-line arguments to Chrome/Chromium when it starts
os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = (
    "--disable-logging "                    # Turn off Chromium's internal logging
    "--silent "                            # Run in silent mode (less console noise)
    "--log-level=3 "                       # Only show critical errors (0=INFO, 3=FATAL)
    "--disable-web-security "              # Allow cross-origin requests (for local development)
    "--disable-features=VizDisplayCompositor " # Disable certain GPU features that can cause warnings
    "--suppress-message-center-popups "    # No popup notifications
    "--disable-dev-shm-usage"             # Prevents /dev/shm usage issues on some systems
)

# 📝 ALTERNATIVE CONFIGURATIONS (Currently commented out)
# These are other Chromium flags you might use for different purposes:
# - GPU acceleration control
# - Software rendering fallbacks  
# - Sandbox security settings
# - OpenGL driver selection
# Uncomment and modify these if you encounter graphics or performance issues

# os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--disable-gpu --disable-software-rasterizer"
# os.environ["QT_QUICK_BACKEND"] = "software"         # Force software rendering
# os.environ["QTWEBENGINE_DISABLE_GPU"] = "1"          # Completely disable GPU
# os.environ["QTWEBENGINE_DISABLE_SANDBOX"] = "1"      # Disable security sandbox
# os.environ["QT_OPENGL"] = "software"                # Use software OpenGL

# =============================================================================
# LIBRARY IMPORTS
# =============================================================================

# 📦 PySide6 (Qt for Python) - Main GUI Framework
# These imports give us the building blocks for creating desktop applications
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout    # Basic UI components
from PySide6.QtCore import Qt, QObject, Slot, QUrl, QSize, qInstallMessageHandler, QtMsgType  # Core functionality
from PySide6.QtWebEngineWidgets import QWebEngineView               # Web browser widget
from PySide6.QtWebEngineCore import QWebEngineSettings              # Browser configuration
from PySide6.QtWebChannel import QWebChannel                        # Python ↔ JavaScript communication
from PySide6.QtGui import QShortcut, QKeySequence                   # Keyboard shortcuts and UI helpers

# 🐍 Standard Python Libraries
import sys                                      # System-specific parameters and functions
import re                                       # Regular expressions for pattern matching
import io                                       # Input/Output operations
from contextlib import redirect_stdout, redirect_stderr  # Context managers for stream redirection

# =============================================================================
# PYTHRA FRAMEWORK IMPORTS
# =============================================================================

# 🎯 Import PyThra's Event System
# These classes define the data structures for touch and gesture events
# that get passed between the JavaScript frontend and Python backend
from ..events import TapDetails, PanUpdateDetails

# =============================================================================
# CONSOLE OUTPUT FILTERING SYSTEM
# =============================================================================

# 📝 PROBLEM: Web browsers (including Qt's WebEngine) often output deprecation warnings
# and other messages that clutter the console. This affects user experience.

# 🛡️ SOLUTION: Create a custom output stream wrapper that intercepts all console
# output and filters out unwanted messages before they reach the terminal.

class FilteredOutput:
    """
    🎯 PURPOSE: A "smart filter" for console output that suppresses unwanted messages
    
    📚 HOW IT WORKS:
        1. Wraps around the normal output streams (stdout/stderr)
        2. Intercepts every message before it gets printed
        3. Checks if the message contains unwanted keywords
        4. Either suppresses the message or lets it through
    
    🎮 ANALOGY: Like a spam filter for your email, but for console messages
    
    🔧 TECHNICAL DETAILS:
        - Implements the same interface as sys.stdout/sys.stderr
        - Uses duck typing to replace the original streams seamlessly
        - Preserves all original functionality while adding filtering
    """
    
    def __init__(self, original_stream):
        """
        Initialize the filter with the original output stream to wrap.
        
        Args:
            original_stream: The original sys.stdout or sys.stderr object
        """
        self.original_stream = original_stream
        
    def write(self, message):
        """
        📝 The main filtering logic - decides whether to show or hide a message.
        
        This method gets called every time something tries to print to the console.
        We check the message content and either suppress it or pass it through.
        
        Args:
            message (str): The text that something is trying to print
        """
        # 🔍 Check if the message contains any unwanted keywords
        # We convert to lowercase to catch variations in capitalization
        unwanted_keywords = [
            'inset-area',                    # CSS deprecation warnings
            'position-area',                 # CSS deprecation warnings  
            'has been deprecated',           # General deprecation messages
            'autofill.enable failed',       # Browser autofill errors
            'autofill.setaddresses failed',  # Browser autofill errors
            'setLifecycleState:',
            'DevTools open',
            'failed to transition from Active to Discarded state:'
        ]
        
        # If the message contains any unwanted keywords, suppress it
        if any(keyword in message.lower() for keyword in unwanted_keywords):
            return  # 🚫 SUPPRESS: Don't print this message
        
        # ✅ ALLOW: Message is clean, pass it to the original stream
        self.original_stream.write(message)
    
    def flush(self):
        """
        Force any buffered output to be written immediately.
        This is required for proper stream compatibility.
        """
        self.original_stream.flush()
    
    def __getattr__(self, name):
        """
        🧿 Magic method that forwards any other method calls to the original stream.
        
        This ensures our FilteredOutput behaves exactly like the original stream
        for any methods we haven't explicitly overridden.
        
        Args:
            name (str): The name of the attribute/method being accessed
            
        Returns:
            The corresponding attribute/method from the original stream
        """
        return getattr(self.original_stream, name)

# =============================================================================
# QT MESSAGE FILTERING SYSTEM
# =============================================================================

def custom_message_handler(msg_type, context, message):
    """
    🎯 PURPOSE: Custom Qt message handler to filter system-level messages
    
    📚 BACKGROUND: Qt (the GUI framework) has its own internal logging system
    that can output various types of messages (debug, warnings, errors, etc.).
    By default, these messages go directly to the console.
    
    🔧 HOW IT WORKS:
        1. Qt calls this function whenever it wants to log a message
        2. We examine the message content and type
        3. We either suppress the message or let it through with formatting
        4. This works at a lower level than the stdout/stderr filtering
    
    🎮 ANALOGY: Like having a security guard at the Qt framework level
    who decides which messages are allowed to reach the console
    
    Args:
        msg_type (QtMsgType): The type of message (Debug, Warning, Critical, Fatal)
        context (QMessageLogContext): Information about where the message came from
        message (str): The actual message text
    """
    # 🔍 Check if this message contains unwanted content
    # This catches Qt-level messages that might not go through stdout/stderr
    unwanted_keywords = [
        'inset-area',                    # CSS deprecation warnings
        'position-area',                 # CSS deprecation warnings
        'has been deprecated',           # General deprecation messages
        'autofill.enable failed',       # Browser autofill errors
        'autofill.setaddresses failed',  # Browser autofill errors
        'setLifecycleState:',
        'DevTools open',
        'failed to transition from Active to Discarded state:'
    ]
    
    if any(keyword in message.lower() for keyword in unwanted_keywords):
        return  # 🚫 SUPPRESS: Don't print this Qt message
    
    # ✅ ALLOW: Format and display the message based on its severity level
    if msg_type == QtMsgType.QtDebugMsg:
        print(f"🐛 Debug: {message}")        # Debug info (usually for developers)
    elif msg_type == QtMsgType.QtWarningMsg:
        print(f"⚠️  Warning: {message}")       # Warning messages
    elif msg_type == QtMsgType.QtCriticalMsg:
        print(f"🔴 Critical: {message}")     # Critical errors
    elif msg_type == QtMsgType.QtFatalMsg:
        print(f"☠️  Fatal: {message}")         # Fatal errors (app will likely crash)

# =============================================================================
# APPLICATION INITIALIZATION AND FILTERING SETUP
# =============================================================================

# 🚀 CREATE THE MAIN APPLICATION INSTANCE
# QApplication is the heart of any Qt application - it manages the event loop,
# system resources, and provides the foundation for all GUI operations
app = QApplication(sys.argv)  # sys.argv allows the app to process command-line arguments
if app is None:
    # 🛡️ Fallback: Create a new application if one doesn't exist
    # This shouldn't normally happen, but it's good defensive programming
    app = QApplication(sys.argv)

# =============================================================================
# INSTALL THE MULTI-LAYER FILTERING SYSTEM
# =============================================================================

# 🎯 LAYER 1: Qt Framework Level Filtering
# Install our custom message handler to intercept Qt's internal logging system
# This catches messages at the framework level before they reach any output streams
qInstallMessageHandler(custom_message_handler)

# 🎯 LAYER 2: Python Output Stream Filtering  
# Replace the standard output streams with our filtered versions
# This catches any messages that bypass Qt's logging system

# 📝 WHY WE NEED BOTH LAYERS:
# - Qt messages might use Qt's logging system OR Python's print/stdout
# - JavaScript console messages from WebEngine go through different channels
# - By filtering both layers, we ensure comprehensive message suppression

# Install the output stream filters
sys.stdout = FilteredOutput(sys.stdout)  # Filter normal print() statements
sys.stderr = FilteredOutput(sys.stderr)  # Filter error messages and warnings


class WindowManager:
    def __init__(self):
        self.windows = {}

    def register_window(self, window_id, window):
        self.windows[window_id] = window

    def set_window_state(self, window_id, state):
        if window_id in self.windows:
            window = self.windows[window_id]
            if state == "minimized":
                window.setWindowState(Qt.WindowMinimized)
            elif state == "maximized":
                window.setWindowState(Qt.WindowMaximized)
            elif state == "normal":
                window.setWindowState(Qt.WindowNoState)
            else:
                print(f"Invalid state: {state}")
        else:
            print(f"Window ID {window_id} not found.")


class Api(QObject):
    def __init__(self):
        super().__init__()
        self.callbacks = {}

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Api, cls).__new__(cls)
        return cls._instance

    def register_callback(self, name, callback):
        self.callbacks[name] = callback
        # print("Callbacks: ", self.callbacks)

    def clear_callbacks(self):
        """Removes all registered callbacks."""
        print("API: Clearing all callbacks.")
        self.callbacks.clear()

    @Slot(str, int, result=str)
    @Slot(str, str, result=str)
    @Slot(str, list, result=str)
    def on_pressed(self, callback_name, *args):
        if callback_name in self.callbacks:
            for x in args[0]: f"webwiget arg: {x}"
            self.callbacks[callback_name](*args)

            return f"Callback '{callback_name}' executed successfully."
        else:
            return f"Callback '{callback_name}' not found."

    @Slot(str, result=str)
    def on_pressed_str(self, callback_name):
        if callback_name in self.callbacks:
            # print("callbacks: ", self.callbacks)
            self.callbacks[callback_name]()

            return f"Callback '{callback_name}' executed successfully."
        else:
            return f"Callback '{callback_name}' not found."

    @Slot(str, str, result=None)
    def on_input_changed(self, callback_name, value):
        """
        Slot to handle 'oninput' events from text fields.
        Finds the registered callback by its name and executes it with the new value.
        """
        callback = self.callbacks.get(callback_name)
        if callback:
            try:
                # The callback will be the state method (e.g., self.on_username_changed)
                callback(value)
            except Exception as e:
                print(f"Error executing input callback '{callback_name}': {e}")
        else:
            print(f"Warning: Input callback '{callback_name}' not found.")

     # --- ADD THIS NEW SLOT FOR THE SLIDER ---
    @Slot(str, float, bool, result=None)
    def on_drag_update(self, callback_name, value, drag_ended):
        """
        Slot to handle 'oninput' events from range sliders.
        Executes the registered callback with the new float value.
        """
        callback = self.callbacks.get(callback_name)
        print("callback drag_ended: ", drag_ended)
        if callback:
            try:
                callback(value, drag_ended)
            except Exception as e:
                print(f"Error executing slider callback '{callback_name}': {e}")
        else:
            print(f"Warning: Slider callback '{callback_name}' not found.")
    # --- END OF NEW SLOT ---

    @Slot(str, int)
    def send_message(self, message, *args):
        print(f"Frontend message: {message}, ", *args)
        return "Message received!"

    @Slot(str)
    def on_button_clicked(self, message):
        print(f"Message from JavaScript: {message}")

    # --- THIS IS THE NEW SLOT ---
    # It's specifically for building virtual list items.
    # It returns a QVariantMap, which maps to a JavaScript object.
    @Slot(str, int, result='QVariantMap')
    def build_list_item(self, builder_name, index):
        """
        Called by the virtual list JS engine to build the HTML and CSS
        for a single item.
        """
        callback = self.callbacks.get(builder_name)
        if callback and callable(callback):
            try:
                # This call now returns a dict: {"html": "...", "css": "..."}
                return callback(index)
            except Exception as e:
                print(f"Error executing item builder '{builder_name}' for index {index}: {e}")
                return {"html": "<div>Error</div>", "css": ""}
        else:
            print(f"Warning: Item builder '{builder_name}' not found.")
            return {"html": "<div>Builder not found</div>", "css": ""}

    # --- ADD THIS NEW GENERIC SLOT ---
    @Slot(str, 'QVariantMap', result=None)
    def on_gesture_event(self, callback_name, details):
        """
        Generic slot to handle all events from the GestureDetector JS engine.
        """
        callback = self.callbacks.get(callback_name)
        print("Callback tap debug info: ",callback, " " ,details)
        if callback:
            try:
                # Based on the callback name, we can construct the correct data class.
                if "pupdate" in callback_name:
                    # For PanUpdate, details is a dict {'dx': float, 'dy': float}
                    callback(PanUpdateDetails(dx=details.get('dx', 0), dy=details.get('dy', 0)))
                elif "tap" in callback_name and "dbtap" not in callback_name:
                    callback(TapDetails())
                else:
                    # For DoubleTap, LongPress, PanStart, PanEnd, no details are needed.
                    callback()
            except Exception as e:
                print(f"Error executing gesture callback '{callback_name}': {e}")
        else:
            print(f"Warning: Gesture callback '{callback_name}' not found.")


# Create a global instance of the WindowManager
window_manager = WindowManager()


class DebugWindow(QWebEngineView):
    """A separate window for inspecting HTML elements."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Debug Window")
        self.resize(800, 600)


class WebWindow(QWidget):
    def __init__(
        self,
        title,
        window_id="main_window",
        html_file=None,
        js_api=None,
        width=800,
        height=600,
        window_state="normal",
        frameless=False,
        on_top=False,
        maximized=False,
        fixed_size=False,
    ):
        super().__init__()
        self.setWindowTitle(title)
        self.fixed_size = fixed_size
        if not maximized and not fixed_size:
            self.setGeometry(100, 100, width, height)

        if fixed_size and not maximized:
            self.setFixedSize(QSize(width, height))

        if on_top:
            # Make the window stay on top
            self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)

        if frameless:
            self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
            self.setAttribute(Qt.WA_TranslucentBackground)

        self.layout = QVBoxLayout(self)

        # Register the window with the WindowManager
        window_manager.register_window(window_id, self)

        # WebView
        self.webview = QWebEngineView(self)
        self.webview.settings().setAttribute(
            QWebEngineSettings.LocalContentCanAccessRemoteUrls, True
        )
        self.webview.settings().setAttribute(
            QWebEngineSettings.LocalContentCanAccessFileUrls, True
        )
        self.webview.settings().setAttribute(
            QWebEngineSettings.AllowRunningInsecureContent, True
        )
        self.webview.settings().setAttribute(
            QWebEngineSettings.JavascriptCanOpenWindows, True
        )
        
        # Suppress various console warnings and messages
        self.webview.settings().setAttribute(
            QWebEngineSettings.ShowScrollBars, False
        )

        # Enable transparency
        if frameless:
            self.webview.setAttribute(Qt.WA_TranslucentBackground, True)
            self.webview.setStyleSheet("background: transparent;")
            self.webview.page().setBackgroundColor(Qt.transparent)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.addWidget(self.webview)

        if html_file:
            self.webview.setUrl(QUrl.fromLocalFile(html_file))
            # print(js_api.callbacks)
            print("⚡ HTML loaded:")
        else:
            print("HTML not loaded: ", html_file)

        self.layout.addWidget(self.webview)  # Webview occupies the entire space
        print("⚡ WEBVIEW loaded:")

        # Setup QWebChannel
        self.channel = QWebChannel()
        if js_api:
            self.channel.registerObject("pywebview", js_api)
        self.webview.page().setWebChannel(self.channel)

        # Change window state
        window_manager.set_window_state(window_id, window_state)

        # Developer Tools
        self.debug_window = DebugWindow()
        self.webview.page().setDevToolsPage(self.debug_window.page())

        # Add a toggle to show/hide the debug window
        self.debug_window.hide()

       

    def toggle_debug_window(self):
        if self.debug_window.isVisible():
            self.debug_window.hide()
        else:
            self.debug_window.show()

    def show_window(self):
        self.show()
    
    def show_max_window(self):
        self.showMaximized()
        size = self.size()
        screen = QApplication.primaryScreen()
        size = screen.availableGeometry().size()
        max_size = screen.availableGeometry().size()
        # self.setFixedSize(max_size)

        if self.fixed_size:
            self.setFixedSize(max_size)

    def minimize(self):
        self.showMinimized()

    def restore_normal(slef):
        self.showNormal()

    def close_window(self):
        self.close()
        self.debug_window.close() if self.debug_window else print("closed")

    def evaluate_js(self, window_id, *scripts):
        # Define a dummy callback function to make the call non-blocking.
        def dummy_callback(result):
            # We can log the result here for debugging if needed.
            # print(f"JS execution finished with result: {result}")
            pass
        if window_id in window_manager.windows:
            window = window_manager.windows[window_id]
            if hasattr(window, "webview") and window.webview:
                for script in scripts:
                    window.webview.page().runJavaScript(script, dummy_callback)
            else:
                print(f"Window {window_id} does not have a webview.")
        else:
            print(f"Window ID {window_id} not found.")

    def toggle_overlay(self):
        self.overlay_box.setVisible(not self.overlay_box.isVisible())


# Create Window Function
def create_window(
    title: str,
    window_id: str,
    html_file: str = None,
    js_api: Api = None,
    width: int = 800,
    height: int = 600,
    window_state: str = "normal",
    frameless: bool = True,
    maximized: bool =False,
        fixed_size: bool =False,
):
    window = WebWindow(
        title,
        window_id=window_id,
        html_file=html_file,
        js_api=js_api,
        width=width,
        height=height,
        window_state=window_state,
        frameless=frameless,
        maximized=maximized,
        fixed_size=fixed_size,
        
    )
    if maximized:
        window.show_max_window()
    else:
        window.show_window()
        
    return window


def change_color():
    window.run_js("main_window", "document.body.style.backgroundColor = 'lightblue';")


def start(window, debug):

    # Example to toggle debug window (could connect to a button or shortcut)
    if debug:
        window.toggle_debug_window()

    sys.exit(app.exec())


"""
if __name__ == '__main__':

    # Create API instance and register callbacks
    api = Api()
    api.register_callback("bg", change_color)
    api.register_callback("testCallback", lambda: print("Button clicked!"))
    window = create_window("Test Window", window_id="main_window", html_file="/home/red-x/Engine/ind.html", js_api=api, frameless=False)
    start(debug=True)

"""

