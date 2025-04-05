import webview

# HTML with dialog for dragging
dialog_html = '''
<html>
<head>
    <style>
        body {
            margin: 0;
            padding: 0;
            background-color: rgba(0, 0, 0, 0);  /* Transparent background */
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            overflow: hidden;
        }
        .dialog-container {
            background-color: white;
            padding: 20px;
            border-radius: 10px;
            width: 100%;
            max-width: 400px;
            text-align: center;
            box-shadow: 0px 4px 12px rgba(0, 0, 0, 0.15);
            cursor: move; /* Indicate that it's draggable */
        }
    </style>
</head>
<body>
    <div class="dialog-container" id="dialog">
        <h2>Draggable Dialog Window</h2>
        <p>Click and drag this dialog to move the window around.</p>
        <button onclick="window.close()">Close</button>
    </div>

    
</body>
</html>
'''

# Python API to handle window movement
class Api:
    def move_window_by(self, dx, dy):
        window = webview.windows[0]

        # Calculate the new window position by adding dx and dy to the current window position
        current_x, current_y = window.x, window.y
        new_x = current_x + dx
        new_y = current_y + dy

        # Move the window to the new position
        window.move(new_x, new_y)

def show_dialog():
    pass  # Not needed for this logic

if __name__ == '__main__':
    api = Api()

    # Create the borderless, transparent window
    window = webview.create_window(
        'Draggable Dialog Window',
        html=dialog_html,
        width=400,
        height=193,
        resizable=False,
        frameless=True,  # No borders
        easy_drag=True,
        draggable=True,
        frameless_padding=40,
        transparent=True,  # Make window background transparent
        #on_top=True,
        #backend='qt',
        #js_api=api  # Register the API to allow window movement
    )

    # Start the webview window
    webview.start(debug=True, gui='qt')
