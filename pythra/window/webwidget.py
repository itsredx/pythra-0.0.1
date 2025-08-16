import os

# os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--disable-gpu --disable-software-rasterizer"
# os.environ["QT_QUICK_BACKEND"] = "software"
# os.environ["QTWEBENGINE_DISABLE_GPU"] = "1"
# os.environ["QTWEBENGINE_DISABLE_SANDBOX"] = "1"
# os.environ["QT_OPENGL"] = "software"

from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout
from PySide6.QtCore import Qt, QObject, Slot, QUrl, QSize 
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEngineSettings
from PySide6.QtWebChannel import QWebChannel
from PySide6.QtGui import QShortcut, QKeySequence # <-- ADD THIS IMPORT
import sys

# --- THIS IS THE FIX ---
# Import the gesture event data classes so the Api class can use them.
# Adjust the path if your events file is located elsewhere (e.g., from .styles import ...)
from ..events import TapDetails, PanUpdateDetails
# --- END OF FIX ---

app = QApplication(sys.argv)
if app is None:
    app = QApplication(sys.argv)


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
        hot_restart_handler=None,
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

        # --- THIS IS THE NEW LOGIC FOR HOT RESTART ---
        # If a handler is provided, create a keyboard shortcut and connect it.
        if hot_restart_handler:
            print("⚡ Hot Restart enabled with Ctrl+R shortcut.")
            shortcut = QShortcut(QKeySequence("Ctrl+R"), self)
            shortcut.activated.connect(hot_restart_handler)
        # --- END OF NEW LOGIC ---

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
        hot_restart_handler=None,
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
        hot_restart_handler=hot_restart_handler,
        
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

# --- You will need to modify your create_window function to accept this ---
# Example of the required change in pythra/window/webwidget.py:

# def create_window(title, window_id, url, api, ..., hot_restart_handler=None):
#     # ... existing window creation code ...
# 
#     # Add a keyboard shortcut to the window
#     if hot_restart_handler:
#         from PySide6.QtGui import QShortcut, QKeySequence
#         shortcut = QShortcut(QKeySequence("Ctrl+R"), window)
#         shortcut.activated.connect(hot_restart_handler)
#
#     return window