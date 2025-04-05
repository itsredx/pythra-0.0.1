# This Python file uses the following encoding: utf-8
from webwidget import create_window, start, Api

api = Api()

def change_color():
    window.run_js("main_window", "document.body.style.backgroundColor = 'lightblue';")


window = create_window(
                "Test Window",
                window_id="main_window",
                html_file="/home/red-x/Documents/pythra/web/index.html",
                js_api=api,
                frameless=True)
# Create API instance and register callbacks

api.register_callback("close", window.close_window)
api.register_callback("bg", change_color)
api.register_callback("testCallback", lambda: print("Button clicked!"))

if __name__ == "__main__":
    start(window=window, debug=True)
