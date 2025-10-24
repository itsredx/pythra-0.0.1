import os
import json
from typing import Optional, Dict, Any

from pythra import State, Container, Key, Framework

from .controller import MarkdownEditorController

framework = Framework.instance()  # Placeholder for the framework reference
class MarkdownEditorState(State):
    def __init__(self):
        super().__init__()
        self._content = ""
        self._callback_name = None
        self._container_html_id = 'fw_id_8'  # Will store the actual framework-assigned ID
       
    
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

        # Attach controller
        if widget.controller:
            widget.controller._attach(self)

        # Register a callback for content-change events coming from JS
        self._callback_name = f"markdown_content_change_{widget.key.value}"
        
        # Register our callbacks with the framework's API
        if framework and hasattr(framework, 'api') and framework.api:
            framework.api.register_callback(self._callback_name, self._handle_content_change)
            framework.api.register_callback('markdown_content_change_markdown_default', self._handle_content_change)
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
                var editable = document.querySelector('.editor-inner-container');
                if(editable) {{
                    try {{
                        document.execCommand('{command}', false, {val_js});
                    }} catch(e) {{
                        console.warn('Editor command failed:', e);
                    }}
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

    def build(self):
        widget = self.get_widget()
        if not widget:
            return Container(width=0, height=0)
            
        # Container that will be initialized by our JS engine
        return Container(
            key=widget.key,
            width=widget.width,
            height=widget.height,
            js_init={
            "engine": "PythraMarkdownEditor",
            "instance_name" : f"{widget.key.value}_PythraMarkdownEditor",
            "options": {
                'callback': self._callback_name,
                'instanceId': f"{widget.key.value}_PythraMarkdownEditor",
                "showControls": True,
                "initialContent": "<h1>Welcome!</h1><p>Start writing your document here...</p>",
            },
            },
            # Add minimal editor container that our JS will enhance
            child=Container(
                key=Key(f"{widget.key.value}_inner"),
                cssClass="editor-inner-container",
                width="100%",
                height="100%"
            )
        )
