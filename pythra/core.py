# pythra/core.py

import os
import time
import json
import html
import weakref
from typing import Optional, Set, List, Dict, TYPE_CHECKING, Callable, Any

# PySide imports for main thread execution
from PySide6.QtCore import QTimer

# Framework imports
from .config import Config
from .server import AssetServer
from .api import Api
from .window import webwidget

# New/Refactored Imports
from .base import Widget, Key
from .state import State, StatefulWidget
# The Reconciler now exports its Result class, which is a key part of the API
from .reconciler import Reconciler, Patch, ReconciliationResult
from .widgets import * # Import all widgets for class lookups if needed


# Type Hinting for circular dependencies
if TYPE_CHECKING:
    from .state import State

class Framework:
    """
    Manages the application window, widget tree, state updates,
    and the reconciliation data flow for rendering the UI.
    """
    _instance = None
    config = Config()

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        """Initializes the framework, reconciler, and core components."""
        if Framework._instance is not None:
            raise Exception("This class is a singleton!")
        Framework._instance = self

        self.api = webwidget.Api()
        self.reconciler = Reconciler()
        self.root_widget: Optional[Widget] = None
        self.window = None
        self.id = 'main_window_id'

        # State Management / Reconciliation Control
        self._reconciliation_requested: bool = False
        self._pending_state_updates: Set[State] = set()

        # Asset Management
        self.html_file_path = os.path.abspath('web/index.html')
        self.css_file_path = os.path.abspath('web/styles.css')
        self.asset_server = AssetServer(directory='assets', port=self.config.get('assets_server_port'))
        self.asset_server.start()
        os.makedirs('web', exist_ok=True)

        Widget.set_framework(self)
        StatefulWidget.set_framework(self)
        print("Framework Initialized with new Reconciler architecture.")

    def set_root(self, widget: Widget):
        """Sets the root widget for the application."""
        self.root_widget = widget

    def run(self, title: str, width: int = 800, height: int = 600, frameless: bool = False):
        """
        Builds the initial UI, writes necessary files, creates the window, and starts the app.
        """
        if not self.root_widget:
            raise ValueError("Root widget not set. Use set_root() before run().")

        print("\n>>> Framework: Performing Initial Render <<<")

        # 1. Build the initial widget tree from the root widget.
        initial_tree = self._build_widget_tree(self.root_widget)

        # 2. Perform initial reconciliation. The previous map is empty.
        result = self.reconciler.reconcile(
            previous_map={}, new_widget_root=initial_tree, parent_html_id='root-container'
        )

        # 3. Update framework state from the initial result.
        self.reconciler.context_maps['main'] = result.new_rendered_map
        for cb_id, cb_func in result.registered_callbacks.items():
            self.api.register_callback(cb_id, cb_func)

        # 4. Generate initial HTML from the map created by the reconciler.
        root_key = initial_tree.get_unique_id() if initial_tree else None
        initial_html_content = self._generate_html_from_map(root_key, result.new_rendered_map)
        
        # 5. Generate initial CSS from the details collected by the reconciler.
        initial_css_rules = self._generate_css_from_details(result.active_css_details)

        # 6. Write files and create the application window.
        self._write_initial_files(title, initial_html_content, initial_css_rules)
        
        self.window = webwidget.create_window(
            title, self.id, self.html_file_path, self.api, width, height, frameless
        )
        
        # 7. Start the application event loop.
        print("Framework: Starting application event loop...")
        webwidget.start(window=self.window, debug=bool(self.config.get("Debug", False)))

    # --- State Update and Reconciliation Cycle ---

    def request_reconciliation(self, state_instance: State):
        """Called by State.setState to schedule a UI update."""
        self._pending_state_updates.add(state_instance)
        
        if not self._reconciliation_requested:
            self._reconciliation_requested = True
            QTimer.singleShot(0, self._process_reconciliation)

    def _process_reconciliation(self):
        """Performs a full reconciliation cycle for all active UI contexts."""
        self._reconciliation_requested = False
        if not self.window:
            print("Error: Window not available for reconciliation.")
            return

        print("\n--- Framework: Processing Reconciliation Cycle ---")
        start_time = time.time()

        # 1. Build the main widget tree based on the current application state.
        main_tree = self._build_widget_tree(self.root_widget)
        
        # 2. Reconcile the main tree against the 'root-container'.
        old_main_map = self.reconciler.get_map_for_context('main')
        main_result = self.reconciler.reconcile(old_main_map, main_tree, 'root-container')
        
        # 3. Handle Declarative Overlays (Dialogs, SnackBars, etc.)
        # This assumes your build() method places overlay widgets on the Scaffold.
        scaffold_instance = main_tree # Assuming root is Scaffold, or find it
        
        # Reconcile Dialog
        dialog_widget = getattr(scaffold_instance, 'dialog', None) if scaffold_instance else None
        old_dialog_map = self.reconciler.get_map_for_context('dialog')
        dialog_result = self.reconciler.reconcile(old_dialog_map, dialog_widget, 'body') 
    
        # Reconcile SnackBar
        snackbar_widget = getattr(scaffold_instance, 'snackBar', None) if scaffold_instance else None
        old_snackbar_map = self.reconciler.get_map_for_context('snackbar')
        snackbar_result = self.reconciler.reconcile(old_snackbar_map, snackbar_widget, 'body')

        # (Add more for BottomSheet, etc. as needed)

        # 4. Combine results from all reconciliation contexts.
        all_patches = main_result.patches + dialog_result.patches + snackbar_result.patches
        all_css_details = {**main_result.active_css_details, **dialog_result.active_css_details, **snackbar_result.active_css_details}
        all_callbacks = {**main_result.registered_callbacks, **dialog_result.registered_callbacks, **snackbar_result.registered_callbacks}

        # 5. Update the framework's state maps and register callbacks.
        self.reconciler.context_maps['main'] = main_result.new_rendered_map
        self.reconciler.context_maps['dialog'] = dialog_result.new_rendered_map
        self.reconciler.context_maps['snackbar'] = snackbar_result.new_rendered_map
        
        for cb_id, cb_func in all_callbacks.items():
            self.api.register_callback(cb_id, cb_func)

        # 6. Generate payloads from the combined results.
        css_rules = self._generate_css_from_details(all_css_details)
        css_update_script = self._generate_css_update_script(css_rules)
        dom_patch_script = self._generate_dom_patch_script(all_patches)

        # 7. Execute JS to apply updates to the UI.
        combined_script = (css_update_script + "\n" + dom_patch_script).strip()
        if combined_script:
            print(f"Framework: Executing {len(all_patches)} DOM patches and CSS update.")
            self.window.evaluate_js(self.id, combined_script)
        else:
            print("Framework: No DOM or CSS changes detected.")

        self._pending_state_updates.clear()
        print(f"--- Framework: Reconciliation Complete (Total: {time.time() - start_time:.4f}s) ---")

    # --- Widget Tree Building ---
    def _build_widget_tree(self, widget: Optional[Widget]) -> Optional[Widget]:
        """
        Recursively builds the widget tree, calling build() on StatefulWidget instances.
        (This function's logic remains the same and is correct for a declarative model).
        """
        if widget is None: return None

        if isinstance(widget, StatefulWidget):
            state = widget.get_state()
            if not state: return None
            try:
                built_child = state.build()
                return self._build_widget_tree(built_child)
            except Exception as e:
                import traceback
                print(f"ERROR building state for {widget.key or widget.__class__.__name__}: {e}")
                traceback.print_exc()
                return None
        else:
            if hasattr(widget, 'get_children'):
                new_children = []
                for child in widget.get_children():
                    built_child = self._build_widget_tree(child)
                    if built_child:
                        new_children.append(built_child)
                widget._children = new_children
            return widget

    # --- HTML and CSS Generation ---

    def _generate_html_from_map(self, root_key: Optional[Union[Key, str]], rendered_map: Dict) -> str:
        """Generates the full HTML string by recursively traversing the flat rendered_map."""
        if not root_key or root_key not in rendered_map: return ""

        node_data = rendered_map[root_key]
        html_id = node_data['html_id']
        props = node_data['props']
        widget_instance = node_data['widget_instance']

        stub = self.reconciler._generate_html_stub(widget_instance, html_id, props)

        children_html = "".join(
            self._generate_html_from_map(child_key, rendered_map)
            for child_key in node_data.get('children_keys', [])
        )

        if ">" in stub and "</" in stub:
            tag = self.reconciler._get_widget_render_tag(widget_instance)
            closing_tag = f"</{tag}>"
            if stub.endswith(closing_tag):
                content_part = stub[:-len(closing_tag)]
                return f"{content_part}{children_html}{closing_tag}"
        
        return stub

    def _generate_css_from_details(self, css_details: Dict[str, Tuple[Callable, Any]]) -> str:
        """Generates CSS rules directly from the details collected by the Reconciler."""
        all_rules = []
        for css_class, (generator_func, style_key) in css_details.items():
            try:
                rule = generator_func(style_key, css_class)
                if rule: all_rules.append(rule)
            except Exception as e:
                import traceback
                print(f"ERROR generating CSS for class '{css_class}': {e}")
                traceback.print_exc()
        
        print(f"Generated CSS for {len(all_rules)} active shared classes.")
        return "\n".join(all_rules)

    # --- Script Generation and File Writing ---

    def _generate_css_update_script(self, css_rules: str) -> str:
        """Generates JS to update the <style id="dynamic-styles"> tag."""
        escaped_css = json.dumps(css_rules)[1:-1]
        return f'''
            var styleSheet = document.getElementById('dynamic-styles');
            if (styleSheet.textContent !== `{escaped_css}`) {{
                 styleSheet.textContent = `{escaped_css}`;
            }}
        '''

    def _generate_dom_patch_script(self, patches: List[Patch]) -> str:
        """Converts the list of Patch objects from the reconciler into executable JavaScript."""
        js_commands = []
        for patch in patches:
            action, target_id, data = patch.action, patch.html_id, patch.data
            command_js = ""
            if action == 'INSERT':
                parent_id, html_stub, props, before_id = data['parent_html_id'], data['html'], data['props'], data['before_id']
                final_escaped_html = json.dumps(html_stub)[1:-1].replace('`', '\\`').replace('${', '\\${')
                before_id_js = f"document.getElementById('{before_id}')" if before_id else 'null'
                command_js = f'''
                    var parentEl = document.getElementById('{parent_id}');
                    if (parentEl) {{
                        var tempContainer = document.createElement('div');
                        tempContainer.innerHTML = `{final_escaped_html}`;
                        var insertedEl = tempContainer.firstChild;
                        if (insertedEl) {{
                            parentEl.insertBefore(insertedEl, {before_id_js});
                            {self._generate_prop_update_js(target_id, props, is_insert=True)}
                        }}
                    }}
                '''
            elif action == 'REMOVE':
                command_js = f'var el = document.getElementById("{target_id}"); if(el) el.remove();'
            elif action == 'UPDATE':
                prop_update_js = self._generate_prop_update_js(target_id, data['props'])
                if prop_update_js:
                    command_js = f'var elToUpdate = document.getElementById("{target_id}"); if (elToUpdate) {{ {prop_update_js} }}'
            elif action == 'MOVE':
                parent_id, before_id = data['parent_html_id'], data['before_id']
                before_id_js = f"document.getElementById('{before_id}')" if before_id else 'null'
                command_js = f'''
                    var el = document.getElementById('{target_id}');
                    var p = document.getElementById('{parent_id}');
                    if (el && p) p.insertBefore(el, {before_id_js});
                '''

            if command_js:
                js_commands.append(f"try {{ {command_js} }} catch (e) {{ console.error('Error applying patch {action} {target_id}:', e); }}")

        return "\n".join(js_commands)

    def _generate_prop_update_js(self, target_id: str, props: Dict, is_insert: bool = False) -> str:
        """Generates specific JS commands for updating element properties."""
        # This function was already well-designed to handle props, but now it's simpler
        # because it no longer receives a separate `layout_override`. That logic is now
        # handled by the widgets themselves rendering styled `div`s.
        js_prop_updates = []
        style_updates = {}
        element_var = 'insertedEl' if is_insert else 'elToUpdate'

        for key, value in props.items():
            if key == 'data': js_prop_updates.append(f"{element_var}.textContent = {json.dumps(str(value))};")
            elif key == 'css_class': js_prop_updates.append(f"{element_var}.className = {json.dumps(value)};")
            elif key == 'src': js_prop_updates.append(f"{element_var}.src = {json.dumps(value)};")
            elif key == 'tooltip': js_prop_updates.append(f"{element_var}.title = {json.dumps(value)};")
            
            # Direct style props (use sparingly, prefer shared CSS classes)
            elif key == 'color': style_updates['color'] = value
            elif key == 'backgroundColor': style_updates['backgroundColor'] = value
            elif key == 'width' and value is not None: style_updates['width'] = f"{value}px" if isinstance(value, (int, float)) else value
            elif key == 'height' and value is not None: style_updates['height'] = f"{value}px" if isinstance(value, (int, float)) else value
        
        if style_updates:
             for prop, val in style_updates.items():
                  css_prop = ''.join(['-' + c.lower() if c.isupper() else c for c in prop]).lstrip('-')
                  js_prop_updates.append(f"{element_var}.style.{prop} = {json.dumps(val)};")

        return "\n".join(js_prop_updates)

    def _write_initial_files(self, title: str, html_content: str, initial_css_rules: str):
         base_css = """
         body { margin: 0; font-family: sans-serif; background-color: #f0f0f0; overflow: hidden;}
         * { box-sizing: border-box; }
         #root-container { height: 100vh; width: 100vw; overflow: hidden; position: relative;}
         """
         try:
              with open(self.css_file_path, 'w', encoding='utf-8') as c: c.write(base_css)
              with open(self.html_file_path, 'w', encoding='utf-8') as f:
                    f.write(f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{html.escape(title)}</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css">
    <link id="base-stylesheet" type="text/css" rel="stylesheet" href="styles.css?v={int(time.time())}">
    <style id="dynamic-styles">{initial_css_rules}</style>
    {self._get_js_includes()}
</head>
<body>
    <svg id="global-svg-defs" width="0" height="0" style="position:absolute;pointer-events:none;visibility:hidden;"><defs></defs></svg>
    <div id="root-container">{html_content}</div>
    <div id="overlay-container"></div>
</body>
</html>""")
         except IOError as e:
              print(f"Error writing initial files: {e}")

    def _get_js_includes(self):
        """Generates standard script includes for QWebChannel and event handling."""
        return f"""
        <script src="qwebchannel.js"></script>
        <script>
            document.addEventListener('DOMContentLoaded', () => {{
                new QWebChannel(qt.webChannelTransport, (channel) => {{
                    window.pywebview = channel.objects.pywebview;
                    console.log("PyWebChannel connected.");
                }});
            }});
            function handleClick(name) {{ if(window.pywebview) window.pywebview.on_pressed_str(name, ()=>{{}}); }}
            function handleItemTap(name, index) {{ if(window.pywebview) window.pywebview.on_item_tap(name, index, ()=>{{}}); }}
        </script>
        """