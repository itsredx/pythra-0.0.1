from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout
from PySide6.QtCore import Qt, QObject, Slot, QUrl
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEngineSettings
from PySide6.QtWebChannel import QWebChannel
import sys

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

    @Slot(str, int, result=str)
    def on_pressed(self, callback_name, *args):
        if callback_name in self.callbacks:
            self.callbacks[callback_name](*args)

            return f"Callback '{callback_name}' executed successfully."
        else:
            return f"Callback '{callback_name}' not found."

    @Slot(str, result=str)
    def on_pressed_str(self, callback_name):
        if callback_name in self.callbacks:
            self.callbacks[callback_name]()

            return f"Callback '{callback_name}' executed successfully."
        else:
            return f"Callback '{callback_name}' not found."

    @Slot(str, int)
    def send_message(self, message, *args):
        print(f"Frontend message: {message}, " ,*args)
        return "Message received!"

    @Slot(str)
    def on_button_clicked(self, message):
        print(f"Message from JavaScript: {message}")


# Create a global instance of the WindowManager
window_manager = WindowManager()

class DebugWindow(QWebEngineView):
    """A separate window for inspecting HTML elements."""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Debug Window")
        self.resize(800, 600)

class WebWindow(QWidget):
    def __init__(self, title, window_id="main_window", html_file=None, js_api=None, width=800, height=600, window_state="normal", frameless=False, on_top=True):
        super().__init__()
        self.setWindowTitle(title)
        self.setGeometry(100, 100, width, height)
        

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
        self.webview.settings().setAttribute(QWebEngineSettings.LocalContentCanAccessRemoteUrls, True)
        self.webview.settings().setAttribute(QWebEngineSettings.LocalContentCanAccessFileUrls, True)
        self.webview.settings().setAttribute(QWebEngineSettings.AllowRunningInsecureContent, True)
        self.webview.settings().setAttribute(QWebEngineSettings.JavascriptCanOpenWindows, True)

        # Enable transparency
        if frameless:
            self.webview.setAttribute(Qt.WA_TranslucentBackground, True)
            self.webview.setStyleSheet("background: transparent;")
            self.webview.page().setBackgroundColor(Qt.transparent)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.addWidget(self.webview)

        if html_file:
            self.webview.setUrl(QUrl.fromLocalFile(html_file))
            #print(js_api.callbacks)
        else:
            print('HTML not loaded: ',html_file)

        self.layout.addWidget(self.webview)  # Webview occupies the entire space

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

    def close_window(self):
        self.close()

    def evaluate_js(self, window_id, *scripts):
        if window_id in window_manager.windows:
            window = window_manager.windows[window_id]
            if hasattr(window, 'webview') and window.webview:
                for script in scripts:
                    window.webview.page().runJavaScript(script)
            else:
                print(f"Window {window_id} does not have a webview.")
        else:
            print(f"Window ID {window_id} not found.")



    def toggle_overlay(self):
        self.overlay_box.setVisible(not self.overlay_box.isVisible())



# Create Window Function
def create_window(title: str, window_id: str, html_file: str = None, js_api: Api = None, width: int = 800, height: int = 600, window_state: str = "normal", frameless: bool = False):
    window = WebWindow(title, window_id=window_id, html_file=html_file, js_api=js_api, width=width, height=height, window_state=window_state, frameless=frameless)
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
