# framework/core.py
import os
import time
import weakref
from typing import Optional, Set, List, Dict, TYPE_CHECKING

# PySide imports for main thread execution
from PySide6.QtCore import QTimer

# Framework imports
from .config import Config
from .server import AssetServer
from .api import Api # Assuming Api class remains similar for callbacks
from .window import webwidget # Assuming webwidget provides create_window, start

# New/Refactored Imports
from .base import Widget, Key # Import refactored base Widget and Key
from .state import State, StatefulWidget # Import refactored State/StatefulWidget
from .reconciler import Reconciler, Patch # Import the Reconciler engine
from .widgets import * # Import specific widgets for CSS generation lookup

# Type Hinting for circular dependencies
if TYPE_CHECKING:
    from .state import State # Already imported above, but good practice

class Framework:
    """
    Manages the application window, widget tree, state updates,
    and reconciliation process for rendering HTML/CSS. (Updated Docstring)
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

        # Core Components
        self.api = webwidget.Api() # For JS callbacks
        self.reconciler = Reconciler() # Manages diffing and element mapping
        self.root_widget: Optional[Widget] = None
        self.window = None
        self.id = 'main_window_id' # Define a consistent ID for the window context

        # State Management / Reconciliation Control
        self._reconciliation_requested: bool = False
        self._pending_state_updates: Set[State] = set()

        # File Paths & Asset Server
        self.html_file_path = os.path.abspath('web/index.html')
        self.css_file_path = os.path.abspath('web/styles.css') # Path for *base* CSS if any
        self.asset_server = AssetServer(directory='assets', port=self.config.get('assets_server_port'))
        self.asset_server.start()
        os.makedirs('web', exist_ok=True) # Ensure web directory exists

        # --- Link Framework to Widget Classes ---
        Widget.set_framework(self)
        StatefulWidget.set_framework(self)

        # --- Deprecated / Removed ---
        # self.id_manager = IDManager() # IDs handled by Reconciler
        # self.widget_registry = {} # Reconciler map is primary source of truth for rendered state
        # self.registry = WidgetRegistry() # ^ Same as above

        print("Framework Initialized with Reconciler.")

    # --- Widget Registry Methods (Keep or Remove?) ---
    # Decide if you still need a separate registry from the Reconciler's map.
    # If kept, ensure it's updated appropriately during reconciliation (add/remove).
    # For now, commenting out as Reconciler map is central to rendering.
    # def register_widget(...)
    # def get_widget(...)
    # def delete_widget(...)
    # ... etc ...

    def set_root(self, widget: Widget):
        """Sets the root widget and performs the initial render."""
        self.root_widget = widget
        # Scaffold component access (keep if useful shortcuts)
        if isinstance(widget, Scaffold): # Assuming Scaffold is still used
            self.drawer = widget.drawer
            self.end_drawer = widget.endDrawer
            self.bottom_sheet = widget.bottomSheet
            self.snack_bar = widget.snackBar
            # self.body = widget.body # Body is usually built by state
        else:
            pass

        print("\n>>> Framework: Performing Initial Render via Reconciliation <<<")
        # Initial render now happens within the run() method after window setup
        # self._perform_initial_reconciliation() # Moved to run()

    def run(self, title: str, width: int = 800, height: int = 600, frameless: bool = False):
        """
        Builds initial UI, writes necessary files, creates the window, and starts the app.
        """
        if not self.root_widget:
            raise ValueError("Root widget not set. Use set_root() before run().")

        # 1. Build the initial widget tree fully
        initial_tree = self._build_widget_tree(self.root_widget)
        #print("Root Widget: ", self.root_widget)
        #print("initial_tree: ", initial_tree)

        # 2. Perform initial reconciliation (populates map, assigns HTML IDs)
        # The patches aren't used for initial load, but map population is key.
        self.reconciler.reconcile(initial_tree, parent_html_id='root-container')

        # 3. Generate initial HTML structure string using the populated map
        initial_html_content = self._generate_initial_html(initial_tree)

        # 4. Generate initial CSS rules based on the tree
        active_classes = self._collect_active_css_classes(initial_tree)
        initial_css_rules = self._generate_css_for_active_classes(active_classes)

        # 5. Write initial HTML and *Base* CSS files
        self._write_initial_files(title, initial_html_content, initial_css_rules)

        # 6. Create the PySide Window
        self.window = webwidget.create_window(
            title,
            self.id, # Use the consistent window ID
            html_file=self.html_file_path,
            js_api=self.api,
            width=width,
            height=height,
            frameless=frameless
        )

        # 7. Start the application event loop
        print("Framework: Starting application...")
        webwidget.start(window=self.window, debug=bool(config.get("Debug", False)))


    # --- State Update / Reconciliation ---

    def request_reconciliation(self, state_instance: State):
        """Called by State.setState to schedule a UI update."""
        self._pending_state_updates.add(state_instance)
        self._reconciliation_requested = False
        
        print("Pending updates: ", self._pending_state_updates)
        if not self._reconciliation_requested:
            self._reconciliation_requested = True
            
            print("Framework: Reconciliation scheduled.")
            #self._process_reconciliation()
            QTimer.singleShot(0, lambda: self._process_reconciliation())

    def _build_widget_tree(self, widget: Optional[Widget]) -> Optional[Widget]:
        """Recursively builds the widget tree, handling StatefulWidgets."""
        print("Widget is:", widget)
        if widget is None:
            
            return None

        if isinstance(widget, StatefulWidget):
            state = widget.get_state()
            print(widget, ' state is: ', state)
            try:
                built_child = state.build()
                # Recursively build the subtree returned by the state
                return self._build_widget_tree(built_child) if built_child else None
            except Exception as e:
                print(f"Error building state for {widget.key or widget.__class__.__name__}: {e}")
                # Render an error placeholder or return None?
                return None # Or return an ErrorWidget
        else:
            # For regular widgets, rebuild their children recursively
            # This assumes children are defined declaratively and passed via __init__
            # in the state's build method.
            new_children = []
            if hasattr(widget, 'get_children'):
                for child in widget.get_children():
                    built_child = self._build_widget_tree(child)
                    if built_child: # Only add if build didn't fail/return None
                        new_children.append(built_child)
                # This might be too simplistic. Widgets might need to update their
                # internal state based on new children, not just replace the list.
                # However, for reconciliation, we primarily need the new tree structure.
                widget._children = new_children
            return widget

    def _process_reconciliation(self):
        """Performs the actual reconciliation and applies updates to the DOM."""
        self._reconciliation_requested = False
        if not self.root_widget:
            print("Error: Root widget not set for reconciliation.")
            return
        if not self.window:
             print("Error: Window not available for reconciliation.")
             return

        print("\n--- Framework: Processing Reconciliation ---")
        start_time = time.time()

        # 1. Build the new widget tree
        build_start = time.time()
        new_tree = self._build_widget_tree(self.root_widget)
        print(f"  Build time: {time.time() - build_start:.4f}s")

        # 2. Perform reconciliation
        reconcile_start = time.time()
        patches = self.reconciler.reconcile(new_tree, parent_html_id='root-container')
        print(f"  Reconcile time: {time.time() - reconcile_start:.4f}s")

        # 3. Generate CSS updates
        css_start = time.time()
        active_classes = self._collect_active_css_classes(new_tree)
        css_rules = self._generate_css_for_active_classes(active_classes)
        css_update_script = self._generate_css_update_script(css_rules)
        print(f"  CSS Gen time: {time.time() - css_start:.4f}s")

        # 4. Generate DOM patch script
        patch_script_start = time.time()
        dom_patch_script = self._generate_dom_patch_script(patches)
        print(f"  Patch Script Gen time: {time.time() - patch_script_start:.4f}s")

        # 5. Execute JS
        combined_script = css_update_script + "\n" + dom_patch_script
        if combined_script.strip():
            js_start = time.time()
            print(f"Framework: Executing {len(patches)} DOM patches and CSS update.")
            # print("--- JS START ---") # Debug
            # print(combined_script) # Debug
            # print("--- JS END ---")   # Debug
            self.window.evaluate_js(self.id, combined_script)
            print(f"  JS Execution time: {time.time() - js_start:.4f}s")
        else:
            print("Framework: No DOM or CSS changes detected.")

        self._pending_state_updates.clear()
        print("Pending updates: ", self._pending_state_updates)
        print(f"--- Framework: Reconciliation Complete (Total: {time.time() - start_time:.4f}s) ---")


    # --- CSS Generation / Collection Helpers ---

    def _collect_active_css_classes(self, widget_tree: Optional[Widget]) -> Set[str]:
        """Recursively scans the tree for required CSS classes."""
        active_classes = set()
        if not widget_tree:
            return active_classes

        queue = [widget_tree]
        visited_widgets = set() # Avoid infinite loops with recursive structures if any

        while queue:
            current_widget = queue.pop(0)
            # Use object ID for visited check as widgets might be recreated but equal
            if id(current_widget) in visited_widgets:
                continue
            visited_widgets.add(id(current_widget))

            # Check if the widget instance has the method
            if hasattr(current_widget, 'get_required_css_classes'):
                try:
                     classes = current_widget.get_required_css_classes()
                     if classes: # Ensure it returned something iterable
                          active_classes.update(classes)
                except Exception as e:
                     print(f"Error collecting CSS classes from {current_widget}: {e}")


            # Add children to the queue
            if hasattr(current_widget, 'get_children'):
                children = current_widget.get_children()
                if children: # Check if children is not None or empty
                     queue.extend(children)

        # print(f"Collected active classes: {active_classes}") # Debug
        return active_classes

    def _generate_css_for_active_classes(self, active_classes: Set[str]) -> str:
        """Generates CSS rule strings for the given active class names."""
        all_rules = []
        # TODO: This mapping needs to be robust. How to efficiently find the
        # generator and style_key for any given class name?
        # Option 1: Iterate through known widget types' shared_styles (less efficient).
        # Option 2: Reconciler could store this mapping when it processes nodes.
        # Option 3: A global registry mapping class_name -> (generator_func, style_key).

        # --- Using Option 1 for now (less efficient but simpler) ---
        widget_classes_with_shared_styles = [Container, Text, Column, IconButton, Icon] # Add all relevant widgets

        class_to_details = {}
        for widget_cls in widget_classes_with_shared_styles:
             if hasattr(widget_cls, 'shared_styles') and isinstance(widget_cls.shared_styles, dict):
                  for style_key, css_class_name in widget_cls.shared_styles.items():
                       if css_class_name in active_classes:
                            # Store generator func and key
                            if hasattr(widget_cls, 'generate_css_rule'):
                                 class_to_details[css_class_name] = (widget_cls.generate_css_rule, style_key)
                            #else: # Debugging
                            #    print(f"Warning: {widget_cls.__name__} has shared_styles but no static generate_css_rule method.")

        generated_count = 0
        for css_class_name in active_classes:
            if css_class_name in class_to_details:
                generator_func, style_key = class_to_details[css_class_name]
                try:
                     rule = generator_func(style_key, css_class_name)
                     if rule and "Error generating" not in rule: # Basic check
                          all_rules.append(rule)
                          generated_count += 1
                except Exception as e:
                     print(f"Error calling generate_css_rule for {css_class_name}: {e}")
            # else: # Debugging
            #     print(f"Warning: No generator found for active class: {css_class_name}")

        print(f"Generated CSS for {generated_count} active shared classes.")
        # TODO: Add generation for non-shared/instance-specific classes if needed
        return "\n".join(all_rules)


    def _generate_css_update_script(self, css_rules: str) -> str:
        """Generates JS to update the <style id="dynamic-styles"> tag."""
        # Escape backticks, backslashes, newlines for JS template literal/string
        # Use JSON dumps for robust escaping, then slice quotes
        import json
        escaped_css = json.dumps(css_rules)[1:-1]

        return f'''
            var styleSheet = document.getElementById('dynamic-styles');
            if (!styleSheet) {{
                styleSheet = document.createElement('style');
                styleSheet.id = 'dynamic-styles';
                document.head.appendChild(styleSheet);
                console.log('Created dynamic stylesheet.');
            }}
            if (styleSheet.textContent !== `{escaped_css}`) {{
                 styleSheet.textContent = `{escaped_css}`;
                 // console.log('Updated dynamic stylesheet content.');
            }} else {{
                 // console.log('Dynamic stylesheet content unchanged.');
            }}
        '''

    # --- DOM Patch Script Generation ---
    def _generate_dom_patch_script(self, patches: List[Patch]) -> str:
        """Converts the list of patches from the reconciler into executable JavaScript."""
        js_commands = []
        for action, target_id, data in patches:
            if action == 'INSERT':
                parent_id = data.get('parent_html_id', 'root-container')
                html_stub = data.get('html', '<!-- Error: Missing HTML -->')
                # Use JSON dumps for robust escaping
                import json
                escaped_html = json.dumps(html_stub)[1:-1]

                # TODO: Implement 'before_id' for ordered insertion if needed
                # insert_pos = "'beforeend'"
                # before_id = data.get('before_id')
                # if before_id: ... find sibling and use 'before' ...

                js_commands.append(f'''
                    try {{
                        var parentEl = document.getElementById('{parent_id}');
                        if (parentEl) {{
                            parentEl.insertAdjacentHTML('beforeend', `{escaped_html}`);
                            // console.log('INSERTED {target_id} into {parent_id}');
                        }} else {{
                            console.warn('Parent element {parent_id} not found for INSERT of {target_id}');
                        }}
                    }} catch (e) {{ console.error("Error during INSERT {target_id}:", e); }}
                ''')
            elif action == 'REMOVE':
                js_commands.append(f'''
                    try {{
                        var elToRemove = document.getElementById('{target_id}');
                        if (elToRemove) {{
                            elToRemove.remove();
                            // console.log('REMOVED {target_id}');
                        }} else {{
                            // console.warn('Element {target_id} not found for REMOVE');
                        }}
                    }} catch (e) {{ console.error("Error during REMOVE {target_id}:", e); }}
                ''')
            elif action == 'UPDATE':
                props = data.get('props', {})
                prop_update_js = self._generate_prop_update_js(target_id, props)
                if prop_update_js:
                    js_commands.append(f'''
                        try {{
                            var elToUpdate = document.getElementById('{target_id}');
                            if (elToUpdate) {{
                                // console.log('UPDATING {target_id} with props: {list(props.keys())}');
                                {prop_update_js}
                            }} else {{
                                // console.warn('Element {target_id} not found for UPDATE');
                            }}
                        }} catch (e) {{ console.error("Error during UPDATE {target_id}:", e); }}
                    ''')
            # Add 'REORDER' / 'MOVE' action later if needed
        return "\n".join(js_commands)

    def _generate_prop_update_js(self, target_id: str, props: Dict) -> str:
        """Generates specific JS commands for updating element properties."""
        import json
        js_prop_updates = []
        style_updates = {}

        for key, value in props.items():
            # Handle common properties efficiently
            if key == 'data' and isinstance(value, (str, int, float)): # Text content
                escaped_value = json.dumps(str(value))[1:-1]
                js_prop_updates.append(f"elToUpdate.textContent = '{escaped_value}';")
            elif key == 'css_class' and isinstance(value, str):
                escaped_value = json.dumps(value)[1:-1]
                # Using className might be safer than classList if replacing all
                js_prop_updates.append(f"elToUpdate.className = '{escaped_value}';")
            # --- Style Handling ---
            # Group style changes to apply them efficiently
            elif key == 'color': style_updates['backgroundColor'] = value
            elif key == 'padding': # Assume EdgeInsets with to_css()
                 if hasattr(value, 'to_css'): style_updates['padding'] = value.to_css()
            elif key == 'margin': # Assume EdgeInsets with to_css()
                 if hasattr(value, 'to_css'): style_updates['margin'] = value.to_css()
            elif key == 'width' and value is not None: style_updates['width'] = f"{value}px"
            elif key == 'height' and value is not None: style_updates['height'] = f"{value}px"
            # Add more style mappings based on your widget props
            # ...

            # --- Attribute Handling ---
            elif key == 'href' and isinstance(value, str): # Example attribute
                 escaped_value = json.dumps(value)[1:-1]
                 js_prop_updates.append(f"elToUpdate.setAttribute('href', '{escaped_value}');")
            elif key == 'disabled' and isinstance(value, bool): # Example boolean attribute
                 js_prop_updates.append(f"elToUpdate.disabled = {str(value).lower()};")
            # Add more attribute mappings

            else:
                 print(f"Note: No specific JS handler for updating prop '{key}' - Skipping update.")

        # Apply grouped style updates
        if style_updates:
             for style_prop, style_value in style_updates.items():
                  if style_value is not None:
                       escaped_style_value = json.dumps(str(style_value))[1:-1]
                       # Convert camelCase JS prop to kebab-case CSS prop if needed
                       # Example: backgroundColor -> background-color (basic conversion)
                       css_prop = ''.join(['-' + c.lower() if c.isupper() else c for c in style_prop]).lstrip('-')
                       js_prop_updates.append(f"elToUpdate.style.setProperty('{css_prop}', '{escaped_style_value}');")
                  else: # Handle removing a style
                       css_prop = ''.join(['-' + c.lower() if c.isupper() else c for c in style_prop]).lstrip('-')
                       js_prop_updates.append(f"elToUpdate.style.removeProperty('{css_prop}');")


        return "\n".join(js_prop_updates)

    # --- Initial File Generation ---
    def _write_initial_files(self, title, html_content: str, css_rules: str):
         """Writes the initial HTML file and potentially a base CSS file."""
         base_css = """
         /* Base styles - fonts, resets, body */
         body { margin: 0; font-family: sans-serif; background-color: #f0f0f0; }
         * { box-sizing: border-box; }
         /* Add other base rules */
         """
         try:
              # Write base CSS (optional, could be empty if dynamic handles all)
              with open(self.css_file_path, 'w') as c:
                   c.write(base_css)
              print(f"Base styles written to {self.css_file_path}")

              # Write HTML file including dynamic style tag and root container
              with open(self.html_file_path, 'w') as f:
                    f.write(f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <link id="base-stylesheet" type="text/css" rel="stylesheet" href="styles.css?v={int(time.time())}">
    <style id="dynamic-styles">{css_rules}</style> 
    {self._get_js_includes()}
</head>
<body>
    <div id="root-container">
        {html_content} 
    </div>
</body>
</html>""")
              print(f"Initial HTML written to {self.html_file_path}")
              print(f"Initial HTML content:  {html_content}")
         except IOError as e:
              print(f"Error writing initial files: {e}")

    def _generate_initial_html(self, widget_node: Optional[Widget]) -> str:
        """Recursively generates the full HTML string for the initial load."""
        print("Widget node: ", widget_node)
        if not widget_node: return "<p>Widget Node is None</p>"

        # Get assigned HTML ID from reconciler map
        unique_id = widget_node.get_unique_id()
        node_data = self.reconciler.rendered_elements_map.get(unique_id)
        if not node_data:
             print(f"Warning: No data found in reconciler map for initial HTML generation of {widget_node}")
             return "<!-- Error: Widget data not found -->"
        html_id = node_data['html_id']
        props = node_data['props']
        css_class = props.get('css_class', '') # Get class from props

        # Determine tag (Simplified - needs improvement)
        tag = "div"
        content = ""
        if isinstance(widget_node, Text):
            tag = "p"
            content = props.get('data', '')
        # Add more elif for other widget types...

        # Generate children HTML recursively
        children_html = "".join(self._generate_initial_html(child) for child in widget_node.get_children())

        # Add onclick for callbacks if widget has onPressed prop
        onclick_attr = ""
        if 'onPressed' in props and props['onPressed']:
             callback_name = props['onPressed'] # Assuming prop stores the callback name string
             # Escape callback name for JS string literal
             import json
             escaped_cb_name = json.dumps(callback_name)[1:-1]
             onclick_attr = f' onclick="handleClick(\'{escaped_cb_name}\')"'


        # Basic HTML structure
        # TODO: Add inline styles or other attributes based on props if necessary
        import html
        escaped_content = html.escape(str(content)) if content else ''

        return f'<{tag} id="{html_id}" class="{css_class}"{onclick_attr}>{escaped_content}{children_html}</{tag}>'

    def _get_js_includes(self):
         """Generates standard script includes for QWebChannel etc."""
         # Make sure files exist or paths are correct
         return f"""
              <script src="qwebchannel.js"></script>
              <script>
                   document.addEventListener('DOMContentLoaded', function() {{
                       if (typeof qt !== 'undefined' && qt.webChannelTransport) {{
                           new QWebChannel(qt.webChannelTransport, function (channel) {{
                               window.pywebview = channel.objects.pywebview;
                               console.log("PyWebChannel connected: window.pywebview is ready.");
                               // Optionally dispatch a custom event when ready
                               // document.dispatchEvent(new Event('pywebviewready'));
                           }});
                       }} else {{
                           console.error("qt.webChannelTransport not found. QWebChannel cannot connect.");
                           // Fallback or error handling
                       }}
                   }});

                   // Basic handleClick for callbacks
                   function handleClick(callbackName) {{
                       console.log("handleClick called for:", callbackName);
                       if (window.pywebview) {{
                           // Use on_pressed_str for no-argument callbacks
                           window.pywebview.on_pressed_str(callbackName, function(result) {{
                               console.log(`Callback ${{callbackName}} result: `, result);
                           }});
                           // Add on_pressed if you need arguments later
                       }} else {{
                           console.error("window.pywebview not ready for callback:", callbackName);
                       }}
                   }}
              </script>
              {self._get_main_js()} 
         """

    def _get_main_js(self):
        """Reads content from web/main.js if it exists."""
        main_js_path = os.path.abspath('web/main.js')
        try:
             if os.path.exists(main_js_path):
                  with open(main_js_path, 'r') as f:
                       return f"<script>{f.read()}</script>"
        except IOError as e:
             print(f"Error reading web/main.js: {e}")
        return "<!-- web/main.js not found or error reading -->"


    # --- Utility / Direct Manipulation Methods ---
    # Keep methods like hide_snack_bar that perform direct JS execution
    def hide_snack_bar(self, widget_id=''):
        """Hides the snack bar using direct JS execution."""
        if not widget_id:
            print("hide_snack_bar called with empty widget_id")
            return
        if self.window and hasattr(self.window, 'evaluate_js'):
            script = f"""
                var snackbarElement = document.getElementById('{widget_id}');
                if (snackbarElement) {{
                    snackbarElement.style.display = 'none';
                    // console.log('Snackbar {widget_id} hidden via JS.');
                }} else {{
                    // console.warn('Snackbar element {widget_id} not found in DOM to hide.');
                }}
            """
            self.window.evaluate_js(self.id, script)
        else:
            print(f"Window or evaluate_js not available for hiding snackbar {widget_id}")

    # --- Collect Callbacks (If Using handleClick) ---
    def _collect_and_register_callbacks(self, widget: Optional[Widget]):
         """ Recursively find 'onPressed' props and register them with the API."""
         if widget is None:
              return

         if hasattr(widget, 'render_props'):
             props = widget.render_props()
             if 'onPressed' in props and props['onPressed']:
                  callback_name = props['onPressed']
                  # Assume the State object has the actual method matching the name
                  state_obj = self._find_owning_state(widget) # Need helper to find state
                  if state_obj and hasattr(state_obj, callback_name):
                       callback_method = getattr(state_obj, callback_name)
                       self.api.register_callback(callback_name, callback_method)
                       # print(f"Registered callback: {callback_name}")
                  # else: # Debug
                  #     print(f"Warning: Could not find state or method for callback '{callback_name}'")

         if hasattr(widget, 'get_children'):
              for child in widget.get_children():
                   self._collect_and_register_callbacks(child)

    def _find_owning_state(self, widget: Widget) -> Optional[State]:
         """ Helper to trace up the widget hierarchy to find the managing State.
             NOTE: This relies on parent pointers or framework tracking, which
             were removed/changed. Re-implement if needed, or pass state down.
             Placeholder implementation - THIS WON'T WORK without parent links.
         """
         # This logic needs revision based on how state/widget relationships are tracked.
         # If State always belongs to the immediate StatefulWidget parent, it's easier.
         # For now, return None as this needs more context.
         print("Warning: _find_owning_state needs implementation based on hierarchy tracking.")
         return None