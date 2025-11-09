# plugins/markdown/editor_state.py`
import os
import json
from typing import Optional, Dict, Any

import markdown
from markdownify import markdownify as md

from pythra import State, Container, Key, Framework

from .controller import MarkdownEditorController
from .style import EditorStyle

framework = Framework.instance()  # Placeholder for the framework reference
class MarkdownEditorState(State):
    def __init__(self):
        super().__init__()
        # --- MODIFICATION: Start with None to indicate it's not yet initialized ---
        self._content: Optional[str] = None
        self._callback_name = None
        self._container_html_id = 'fw_id_8'  # Will store the actual framework-assigned ID

        # --- NEW: State variable for toolbar visibility ---
        self._controls_visible = True # Default to visible
        self._toggle_controls_callback_name = None
       
    
    def _get_html_id_for_key(self, key: Key) -> str:
        """
        Get the framework-assigned HTML ID for a widget with given key.
        Returns None if not found in the render map.
        """
        if not framework or not framework.reconciler:
            return None
            
        # Get the main context map which contains all rendered widgets
        context_map = framework.reconciler.get_map_for_context("main")
        
        # Find the entry with matching key
        for node_data in context_map.values():
            if node_data.get("key") == key:
                return node_data.get("html_id")
        return None

    def initState(self):
        widget = self.get_widget()
        if not widget:
            return

        # --- MODIFICATION: Set initial content from the widget, but only once ---
        if self._content is None:
            self._content = widget.initial_content if hasattr(widget, 'initial_content') else ""

        # Attach controller
        if widget.controller:
            widget.controller._attach(self)

        # Register a callback for content-change events coming from JS
        self._callback_name = f"markdown_content_change_{widget.key.value}"

        # --- NEW: Register the toggle controls callback ---
        self._toggle_controls_callback_name = f"markdown_toggle_controls_{widget.key.value}"
        
        # Register our callbacks with the framework's API
        if framework and hasattr(framework, 'api') and framework.api:
            framework.api.register_callback(self._callback_name, self._handle_content_change)
            framework.api.register_callback('markdown_content_change_markdown_default', self._handle_content_change)
            framework.api.register_callback(self._toggle_controls_callback_name, self._handle_toggle_controls) # Register the new handler
        else:
            print('Warning: framework.api not available; callback registration delayed')


    def dispose(self):
        widget = self.get_widget()
        if widget and widget.controller:
            widget.controller._detach()
        super().dispose()

    # Controller-facing methods called by MarkdownEditorController
    def exec_command(self, command: str, value: Optional[str] = None):
        """Ask the frontend to execute a command (e.g., bold, italic)."""
        if not self._container_html_id or not framework or not framework.window:
            return

        # Execute command using the known framework-assigned ID
        val_js = json.dumps(value) if value is not None else 'null'
        container_id = self._container_html_id
        
        js = f"""
            (function(){{
                    try {{
                        document.execCommand('{command}', false, `{val_js}`);
                        if ('{command}' === 'fontName') {{
                            var ret = document.execCommand('{command}', false, {val_js});
                            console.log('Executing command: ', '{command}', false, {val_js}, `with return: ${{ret}}`);
                        }}
                        
                    }} catch(e) {{
                        console.warn('Editor command failed:', e);
                    }}
            }})()
        """
        window_id = getattr(self, '_window_id', framework.id)
        framework.window.evaluate_js(window_id, js)

    def set_content(self, html: str):
        if not self._container_html_id or not framework or not framework.window:
            return
            
        html_js = json.dumps(html)
        container_id = self._container_html_id
        
        js = f"""
            (function(){{
                console.log('Setting editor content');
                    var editable = document.querySelector('.editor-inner-container');
                    if(editable) editable.innerHTML = {html_js};
            }})()
        """
        window_id = getattr(self, '_window_id', framework.id)
        framework.window.evaluate_js(window_id, js)
        self._content = html

    def get_content(self) -> str:
        return self._content

    def focus(self):
        js = "(function(){var ed=document.getElementById('editor'); if(ed) ed.focus(); })()"
        if hasattr(self, '_window_id'):
            framework.window.evaluate_js(self._window_id, js)
        else:
            framework.window.evaluate_js(framework.id, js)

    # API callback invoked from JS when content changes
    def _handle_content_change(self, new_content):
        try:
            self._content = new_content
            print("New Content: ", new_content)
        except Exception:
            pass

    # --- NEW: Handler for the toggle event from JavaScript ---
    def _handle_toggle_controls(self, is_visible: bool):
        """Called by JS when the user clicks the Hide/Show Controls button."""
        print(f"Controls visibility changed to: {is_visible}")
        self._controls_visible = is_visible
        # We don't call setState() here because no other part of the UI needs to know.
        # The change is purely internal to this component's state.

     # --- NEW: Implement the core logic for Markdown conversion ---

    def load_from_markdown(self, markdown_text: str):
        """
        Converts Markdown to HTML using the 'markdown' library and updates the editor.
        """
        # 1. Convert the Markdown to HTML.
        html_content = markdown.markdown(markdown_text, extensions=['fenced_code', 'tables'])
        
        # 2. Update the state's source of truth.
        self._content = html_content
        
        # 3. Tell the framework that this state has changed and a rebuild is needed.
        # self.setState()

    def export_to_markdown(self) -> Optional[str]:
        """
        Converts the editor's current HTML content to Markdown using 'markdownify'.
        """
        # Get the current, up-to-the-second content from our state.
        html_content = self.get_content()
        if html_content:
            # The 'heading_style="ATX"' option creates clean '#' style headings.
            markdown_text = md(html_content, heading_style="ATX")
            return markdown_text
        return None

    def replace_selection_from_markdown(self, markdown_text: str):
        """
        Converts Markdown to HTML and sends a command to the browser to
        replace the current selection with the new HTML.
        """
        if not framework or not framework.window:
            return

        # 1. Convert the incoming Markdown to HTML, just like in load_from_markdown.
        html_content = markdown.markdown(markdown_text, extensions=['fenced_code', 'tables'])
        
        # --- THIS IS THE FIX ---
        # 2. Append an "escape hatch" paragraph.
        #    The <br> tag is crucial for some browsers to recognize the empty
        #    paragraph as a valid cursor position.
        html_with_escape_hatch = f"{html_content}<p><br></p>"
        
        # 3. Safely escape the combined HTML for injection.
        html_js = json.dumps(html_with_escape_hatch)
        
        # 4. Construct the JavaScript command. 'insertHTML' is the key.
        #    It's a standard browser command for rich text editing.
        js_command = f"""
            (function(){{
                try {{
                    document.execCommand('insertHTML', false, {html_js});
                }} catch(e) {{
                    console.warn('Failed to replace selection with HTML:', e);
                }}
            }})()
        """
        
        # 4. Send the command to the browser.
        window_id = getattr(self, '_window_id', framework.id)
        framework.window.evaluate_js(window_id, js_command)

    def build(self):
        widget = self.get_widget()
        if not widget:
            return Container(width=0, height=0)

        style = widget.style if widget.style else EditorStyle() # Use default style if none provided
            
        # Container that will be initialized by our JS engine
        return Container(
            key=widget.key,
            width=widget.width,
            height=widget.height,
            js_init={
                "engine": "PythraMarkdownEditor",
                "instance_name": f"{widget.key.value}_PythraMarkdownEditor",
                "options": {
                    'callback': self._callback_name,
                    'instanceId': f"{widget.key.value}_PythraMarkdownEditor",
                    "showControls": widget.show_controls,
                    "initialContent": self._content,
                    "width": widget.width,
                    "height": widget.height,
                    "showGrid": widget.show_grid, # Was "shoe_grid"
                    "style": style.to_dict(),  # Pass the complete style configuration
                },
            },
        )
