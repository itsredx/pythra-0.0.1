# pythra/core.py
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
        """
        Recursively builds the widget tree for the current state,
        calling build() on StatefulWidget instances.

        NOTE: This version mutates the children list of existing widget instances.
              A more robust implementation might construct a new tree to ensure
              immutability, but this adds complexity.
        """
        # print(f"  Building node: {widget}") # Debugging can be verbose
        if widget is None:
            return None

        # If it's a StatefulWidget, replace it with the result of its build() method
        if isinstance(widget, StatefulWidget):
            state = widget.get_state()
            # print(f"    Building StatefulWidget: {widget.key} -> State: {state}")
            if not state:
                print(f"Error: State not found for StatefulWidget {widget.key}")
                return None # Or return an ErrorWidget
            try:
                built_child = state.build()
                # Recursively build whatever the state returned
                return self._build_widget_tree(built_child)
            except Exception as e:
                import traceback
                print(f"Error building state for {widget.key or widget.__class__.__name__}: {e}")
                traceback.print_exc() # Print full traceback
                return None # Or return an ErrorWidget
        else:
            # For regular widgets, recursively build their children
            if hasattr(widget, 'get_children'):
                new_children = []
                try:
                    current_children = widget.get_children()
                    if current_children: # Check if children list exists and is iterable
                         # print(f"    Building children for {widget.key or widget.__class__.__name__}: {current_children}")
                         for child in current_children:
                              built_child = self._build_widget_tree(child)
                              # Only add non-None children to the new list
                              if built_child is not None:
                                   new_children.append(built_child)
                    # Replace the widget's children list with the newly built list
                    # This MUTATES the widget instance.
                    widget._children = new_children
                except Exception as e:
                     import traceback
                     print(f"Error processing children for {widget.key or widget.__class__.__name__}: {e}")
                     traceback.print_exc()
                     widget._children = [] # Reset children on error?

            # Return the (potentially mutated) original widget instance
            return widget

    # --- Update Reconciliation Process ---
    def _process_reconciliation(self):
        """Performs reconciliation for main tree AND active dialog."""
        self._reconciliation_requested = False
        if not self.window:
             print("Error: Window not available for reconciliation.")
             return

        print("\n--- Framework: Processing Reconciliation Cycle ---")
        start_time = time.time()

        # 1. Build the main widget tree (from root_widget)
        build_start = time.time()
        main_tree = self._build_widget_tree(self.root_widget)
        print(f"  Main Tree Build time: {time.time() - build_start:.4f}s")

        # 2. Combine Trees? Or Reconcile Separately?
        # Option A: Reconcile main tree, then overlay dialog patches (simpler DOM structure)
        # Option B: Create a combined conceptual tree (harder)

        # --- Using Option A ---

        # 2a. Reconcile the main tree
        reconcile_main_start = time.time()
        main_patches = self.reconciler.reconcile_subtree( # New method needed in Reconciler
             current_subtree_root=main_tree,
             parent_html_id='root-container', # Target main content area
             previous_map_subset_key='main' # Identify subset of map
        )
        print(f"  Main Tree Reconcile time: {time.time() - reconcile_main_start:.4f}s")

        # 2b. Reconcile the active dialog (if any)
        dialog_patches = []
        if self._active_dialog_instance:
             reconcile_dialog_start = time.time()
             # Reconcile dialog, targeting document.body or a specific overlay div
             dialog_patches = self.reconciler.reconcile_subtree(
                  current_subtree_root=self._active_dialog_instance,
                  parent_html_id='body', # Append directly to body or overlay div
                  previous_map_subset_key='dialog' # Use separate map key
             )
             print(f"  Dialog Reconcile time: {time.time() - reconcile_dialog_start:.4f}s")
        # else: # Handle case where dialog was just hidden - need REMOVE patch
        #    dialog_patches = self.reconciler.reconcile_subtree(None, 'body', 'dialog')


        # Combine patches
        all_patches = main_patches + dialog_patches

        # 3. Generate CSS updates (scan both trees or combine?)
        css_start = time.time()
        active_classes = set()
        active_classes.update(self._collect_active_css_classes(main_tree))
        if self._active_dialog_instance:
             active_classes.update(self._collect_active_css_classes(self._active_dialog_instance))
        css_rules = self._generate_css_for_active_classes(active_classes)
        css_update_script = self._generate_css_update_script(css_rules)
        print(f"  CSS Gen time: {time.time() - css_start:.4f}s")

        # 4. Generate DOM patch script
        patch_script_start = time.time()
        dom_patch_script = self._generate_dom_patch_script(all_patches)
        print(f"  Patch Script Gen time: {time.time() - patch_script_start:.4f}s")

        # 5. Execute JS
        combined_script = css_update_script + "\n" + dom_patch_script
        if combined_script.strip():
            js_start = time.time()
            print(f"Framework: Executing {len(all_patches)} DOM patches and CSS update.")
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

    # framework/core.py (Update within Framework class)

    def _generate_css_for_active_classes(self, active_classes: Set[str]) -> str:
        """Generates CSS rule strings using details collected by the Reconciler."""
        all_rules = []
        generated_count = 0

        # --- NEW: Use details collected by reconciler ---
        # active_classes argument might not even be needed if reconciler holds all info
        # css_details_map = self.reconciler.active_css_details

        # Iterate through the details collected during the latest reconcile cycle
        # Use active_classes set to ensure we only process classes relevant to current trees
        for css_class_name in active_classes:
            if css_class_name in self.reconciler.active_css_details:
                generator_func, style_key = self.reconciler.active_css_details[css_class_name]
                try:
                     rule = generator_func(style_key, css_class_name)
                     if rule and "Error generating" not in rule: # Basic check
                          all_rules.append(rule)
                          generated_count += 1
                except Exception as e:
                     print(f"Error calling generate_css_rule for {css_class_name}: {e}")
            # else: # Debugging
            #     print(f"Warning: CSS class '{css_class_name}' was collected but no details found in reconciler map.")


        # --- Remove manual list and loop ---
        # widget_classes_with_shared_styles = [...] # REMOVED
        # class_to_details = {} # REMOVED
        # for widget_cls in widget_classes_with_shared_styles: # REMOVED
             # ... loop logic removed ...


        print(f"Generated CSS for {generated_count} active shared classes (using reconciler map).")
        # TODO: Still need to consider instance-specific CSS if any (e.g., foreground decorations)
        return "\n".join(all_rules)    

    """def _generate_css_for_active_classes(self, active_classes: Set[str]) -> str:
        '''Generates CSS rule strings for the given active class names.'''
        all_rules = []
        # TODO: This mapping needs to be robust. How to efficiently find the
        # generator and style_key for any given class name?
        # Option 1: Iterate through known widget types' shared_styles (less efficient).
        # Option 2: Reconciler could store this mapping when it processes nodes.
        # Option 3: A global registry mapping class_name -> (generator_func, style_key).

        # --- Using Option 1 for now (less efficient but simpler) ---
        widget_classes_with_shared_styles = [
            Container, 
            Text, 
            Column, 
            Row,
            TextButton,
            ElevatedButton,
            FloatingActionButton,
            IconButton, 
            Icon] # Add all relevant widgets

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
        return "\n".join(all_rules)"""


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
            # Wrap each action in a try-catch for robustness
            command_js = ""
            if action == 'INSERT':
                parent_id = data.get('parent_html_id', 'root-container') # Default parent?
                html_stub = data.get('html', '<!-- Error: Missing HTML -->')
                props = data.get('props', {}) # Get props for initial styling
                layout_override = props.get('layout_override') # Check for layout overrides

                # Use JSON dumps for robust escaping of HTML stub
                escaped_html = json.dumps(html_stub)[1:-1]

                # Generate JS for insertion
                command_js = f'''
                    var parentEl = document.getElementById('{parent_id}');
                    if (parentEl) {{
                        parentEl.insertAdjacentHTML('beforeend', `{escaped_html}`);
                        var insertedEl = document.getElementById('{target_id}'); // Get reference to inserted element
                        if (insertedEl) {{
                            // Apply initial props (including layout overrides) after insertion
                            {self._generate_prop_update_js(target_id, props, is_insert=True)}
                            // console.log('INSERTED {target_id} into {parent_id}');
                        }} else {{
                             console.warn('Could not find element {target_id} immediately after insert.');
                        }}
                    }} else {{
                        console.warn('Parent element {parent_id} not found for INSERT of {target_id}');
                    }}
                '''
            elif action == 'REMOVE':
                command_js = f'''
                    var elToRemove = document.getElementById('{target_id}');
                    if (elToRemove) {{
                        elToRemove.remove();
                        // console.log('REMOVED {target_id}');
                    }} else {{
                        // console.warn('Element {target_id} not found for REMOVE');
                    }}
                '''
            elif action == 'UPDATE':
                props = data.get('props', {}) # Changed props
                layout_override = data.get('layout_override') # Layout context (might be None)

                # Get JS for standard prop changes AND layout overrides
                prop_update_js = self._generate_prop_update_js(target_id, props, layout_override=layout_override)

                if prop_update_js: # Only add block if there are updates
                    command_js = f'''
                        var elToUpdate = document.getElementById('{target_id}');
                        if (elToUpdate) {{
                            // console.log('UPDATING {target_id} with props: {list(props.keys())}');
                            {prop_update_js}
                        }} else {{
                            // console.warn('Element {target_id} not found for UPDATE');
                        }}
                    '''
            elif action == 'MOVE':
                parent_id = data.get('parent_html_id')
                before_id = data.get('before_id') # ID of node to insert before (or null for end)
                command_js = f'''
                    var elToMove = document.getElementById('{target_id}');
                    var parentEl = document.getElementById('{parent_id}');
                    if (elToMove && parentEl) {{
                        var beforeNode = {f"document.getElementById('{before_id}')" if before_id else 'null'};
                        parentEl.insertBefore(elToMove, beforeNode);
                        // console.log('MOVED {target_id} into {parent_id}' + ({f"' before {before_id}'" if before_id else "' to end'"}));
                    }} else {{
                        console.warn('Element or parent not found for MOVE: el={target_id}, parent={parent_id}');
                    }}
                '''

            if command_js:
                # Add individual try-catch for each operation
                js_commands.append(f"try {{\n{command_js}\n}} catch (e) {{ console.error('Error applying patch {action} {target_id}:', e); }}")

        return "\n".join(js_commands)

    def _generate_prop_update_js(self,
                                 target_id: str,
                                 props: Dict,
                                 is_insert: bool = False, # Flag if called during insertion
                                 layout_override: Optional[Dict] = None
                                 ) -> str:
        """
        Generates specific JS commands for updating element properties AND
        applying layout override styles.

        Args:
            target_id: The HTML ID of the element to update ('elToUpdate' or 'insertedEl' in JS).
            props: The dictionary of changed properties OR initial properties on insert.
            is_insert: True if generating for initial insertion, False for update.
            layout_override: Dictionary of layout instructions from a parent widget (Padding, Align, etc.).
        """
        js_prop_updates = []
        style_updates = {} # Group style changes
        element_var = 'insertedEl' if is_insert else 'elToUpdate' # JS variable name

        # --- 1. Apply Layout Overrides FIRST (Padding, Align, Flex, Position etc.) ---
        if layout_override:
            override_type = layout_override.get('render_type')
            # print(f"    Applying layout override: {override_type} to {target_id}") # Debug
            if override_type == 'padding':
                padding_data = layout_override.get('padding')
                if padding_data and 'top' in padding_data: # Check if it looks like EdgeInsets dict
                    css_val = f"{padding_data['top']}px {padding_data['right']}px {padding_data['bottom']}px {padding_data['left']}px"
                    style_updates['padding'] = css_val
            elif override_type == 'align' or override_type == 'center':
                alignment_data = layout_override.get('alignment')
                style_updates['display'] = 'flex' # Align needs flex parent
                style_updates['justifyContent'] = alignment_data.get('justify_content', 'center') # Default center
                style_updates['alignItems'] = alignment_data.get('align_items', 'center') # Default center
                style_updates['width'] = '100%' # Align usually fills parent
                style_updates['height'] = '100%'
            elif override_type == 'flex' or override_type == 'spacer': # Spacer uses flex
                style_updates['flexGrow'] = layout_override.get('flex_grow', 0)
                style_updates['flexShrink'] = layout_override.get('flex_shrink', 1 if override_type == 'flex' else 0) # Spacer shouldn't shrink
                style_updates['flexBasis'] = layout_override.get('flex_basis', 'auto')
                style_updates['minWidth'] = 0 # Prevent blowout
                style_updates['minHeight'] = 0
            elif override_type == 'positioned':
                style_updates['position'] = 'absolute'
                for edge in ['top', 'right', 'bottom', 'left', 'width', 'height']:
                    val = layout_override.get(edge)
                    if val is not None:
                         # Append 'px' if number, otherwise use string value
                         css_val = f"{val}px" if isinstance(val, (int, float)) else val
                         style_updates[edge] = css_val
                    # else: # Remove style if prop is gone? Maybe needed for updates.
                    #     js_prop_updates.append(f"{element_var}.style.removeProperty('{edge}');")
            elif override_type == 'aspect_ratio':
                ratio = layout_override.get('aspectRatio')
                if ratio and ratio > 0:
                    # Apply to wrapper, child needs absolute positioning
                    padding_bottom = (1 / ratio) * 100
                    style_updates['position'] = 'relative'
                    style_updates['width'] = '100%' # Base width
                    style_updates['height'] = '0'
                    style_updates['paddingBottom'] = f'{padding_bottom}%'
                    style_updates['overflow'] = 'hidden'
                    # Child styles applied separately? Or signal patch generator?
                    # Signal that child needs absolute positioning styles
                    js_prop_updates.append(f"{element_var}.dataset.aspectRatioChild = 'true';") # Use data attribute as signal
            elif override_type == 'fitted_box':
                # Apply container styles for alignment/clipping
                style_updates['display'] = 'flex'
                style_updates['width'] = '100%'
                style_updates['height'] = '100%'
                alignment_data = layout_override.get('alignment')
                style_updates['justifyContent'] = alignment_data.get('justify_content', 'center')
                style_updates['alignItems'] = alignment_data.get('align_items', 'center')
                clip = layout_override.get('clipBehavior')
                if clip and clip != ClipBehavior.NONE: style_updates['overflow'] = 'hidden'
                # Signal child needs fit styles
                js_prop_updates.append(f"{element_var}.dataset.fittedBoxChild = 'true';")
                js_prop_updates.append(f"{element_var}.dataset.fitMode = '{layout_override.get('fit', 'contain')}';")
            elif override_type == 'fractionally_sized':
                # Apply container styles for alignment
                style_updates['display'] = 'flex'
                style_updates['width'] = '100%'
                style_updates['height'] = '100%'
                alignment_data = layout_override.get('alignment')
                style_updates['justifyContent'] = alignment_data.get('justify_content', 'center')
                style_updates['alignItems'] = alignment_data.get('align_items', 'center')
                 # Signal child needs fractional sizing
                js_prop_updates.append(f"{element_var}.dataset.fractionalChild = 'true';")
                if layout_override.get('widthFactor') is not None:
                     js_prop_updates.append(f"{element_var}.dataset.widthFactor = '{layout_override['widthFactor']}';")
                if layout_override.get('heightFactor') is not None:
                     js_prop_updates.append(f"{element_var}.dataset.heightFactor = '{layout_override['heightFactor']}';")

        # --- 2. Apply Standard Widget Prop Changes (or initial props) ---
        for key, value in props.items():
            # Skip layout override structure itself
            if key == 'layout_override': continue
            # Skip render type helper prop
            if key == 'render_type': continue

            if key == 'data' and isinstance(value, (str, int, float)): # Text content
                escaped_value = json.dumps(str(value))[1:-1]
                js_prop_updates.append(f"{element_var}.textContent = '{escaped_value}';")
            elif key == 'css_class' and isinstance(value, str):
                escaped_value = json.dumps(value)[1:-1]
                js_prop_updates.append(f"{element_var}.className = '{escaped_value}';")
            elif key == 'src' and isinstance(value, str): # Image src
                 escaped_value = json.dumps(value)[1:-1]
                 js_prop_updates.append(f"{element_var}.setAttribute('src', '{escaped_value}');")
            elif key == 'icon_name' and isinstance(value, str) and props.get('render_type') != 'img': # Icon font class
                 # Assumes FontAwesome structure, adjust if needed
                 base_fa_class = "fa"
                 icon_name_class = f"fa-{value}"
                 # Get existing classes, remove old fa-, add new ones
                 current_classes = props.get('css_class','') # Need original full class list?
                 # This needs refinement - should set className based on *all* classes
                 js_prop_updates.append(f"// TODO: Update Icon class for {target_id} to {icon_name_class}")
                 # Example (better done via className update):
                 # js_prop_updates.append(f"{element_var}.classList.remove(...old fa classes...);")
                 # js_prop_updates.append(f"{element_var}.classList.add('{base_fa_class}', '{icon_name_class}');")
            elif key == 'tooltip' and isinstance(value, str):
                 escaped_value = json.dumps(value)[1:-1]
                 js_prop_updates.append(f"{element_var}.setAttribute('title', '{escaped_value}');")
            elif key == 'semanticChildCount' and isinstance(value, int):
                 js_prop_updates.append(f"{element_var}.setAttribute('aria-setsize', '{value}');")
                 if not is_insert: # Only set role on insert if needed
                      js_prop_updates.append(f"{element_var}.setAttribute('role', 'grid');") # Assuming for GridView

            # Direct Style updates (use sparingly, prefer classes)
            elif key == 'color': style_updates['color'] = value # Text color
            elif key == 'backgroundColor': style_updates['backgroundColor'] = value
            elif key == 'width' and value is not None: # Placeholder/SizedBox width
                 style_updates['width'] = f"{value}px" if isinstance(value, (int, float)) else value
            elif key == 'height' and value is not None: # Placeholder/SizedBox height
                 style_updates['height'] = f"{value}px" if isinstance(value, (int, float)) else value
            # Add other direct prop-to-style/attribute mappings...

        # --- 3. Apply collected style updates ---
        if style_updates:
             for style_prop, style_value in style_updates.items():
                  # Convert camelCase JS prop to kebab-case CSS prop
                  css_prop = ''.join(['-' + c.lower() if c.isupper() else c for c in style_prop]).lstrip('-')
                  if style_value is not None:
                       escaped_style_value = json.dumps(str(style_value))[1:-1]
                       js_prop_updates.append(f"{element_var}.style.setProperty('{css_prop}', '{escaped_style_value}');")
                  else:
                       js_prop_updates.append(f"{element_var}.style.removeProperty('{css_prop}');")

        # --- 4. Apply styles based on data attributes (for layout children) ---
        # These apply styles to the *child* element based on data attributes set by the *parent* layout override
        js_prop_updates.append(f'''
           if ({element_var}.dataset.aspectRatioChild === 'true') {{
               {element_var}.style.position = 'absolute';
               {element_var}.style.top = '0'; {element_var}.style.left = '0';
               {element_var}.style.width = '100%'; {element_var}.style.height = '100%';
           }}
           if ({element_var}.dataset.fittedBoxChild === 'true') {{
               let fitMode = {element_var}.dataset.fitMode || 'contain';
               {element_var}.style.maxWidth = '100%'; {element_var}.style.maxHeight = '100%';
               if ({element_var}.tagName === 'IMG' || {element_var}.tagName === 'VIDEO') {{
                   {element_var}.style.objectFit = fitMode;
               }} else if (fitMode === 'fill') {{
                    {element_var}.style.width = '100%'; {element_var}.style.height = '100%';
               }}
               // Add more complex transform/scaling for other fits if needed
           }}
           if ({element_var}.dataset.fractionalChild === 'true') {{
               {element_var}.style.width = {element_var}.dataset.widthFactor ? ({element_var}.dataset.widthFactor * 100) + '%' : 'auto';
               {element_var}.style.height = {element_var}.dataset.heightFactor ? ({element_var}.dataset.heightFactor * 100) + '%' : 'auto';
           }}
        ''')


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

    def trigger_drawer_toggle(self, side: str):
        """Executes the JavaScript function to toggle a drawer."""
        if self.window and hasattr(self.window, 'evaluate_js'):
            js_command = f"toggleDrawer('{side}');"
            print(f"Framework executing JS: {js_command}")
            self.window.evaluate_js(self.id, js_command)
        else:
            print(f"Cannot toggle drawer '{side}': Window not available.")

    def trigger_bottom_sheet_toggle(self, html_id: str, show: bool, is_modal: bool = True, on_dismiss_name: str = ''):
        """Executes the JavaScript function to toggle a bottom sheet."""
        if self.window and hasattr(self.window, 'evaluate_js'):
            # Pass necessary arguments to the JS function
            # Ensure strings are properly quoted for JS if needed, but evaluate_js often handles types
            js_command = f"toggleBottomSheet('{html_id}', {str(show).lower()}, {str(is_modal).lower()}, 'scaffold-scrim', '{on_dismiss_name}');"
            print(f"Framework executing JS: {js_command}")
            self.window.evaluate_js(self.id, js_command)
        else:
            print(f"Cannot toggle bottom sheet '{html_id}': Window not available.")

# --- SnackBar State ---
    # Store the *current* active SnackBar instance and its timer
    _active_snackbar_instance: Optional[SnackBar] = None
    _active_snackbar_timer: Optional[QTimer] = None
    _active_snackbar_html_id: Optional[str] = None

    def show_snackbar(self,
                      content: Union[str, Widget],
                      action_label: Optional[str] = None,
                      action_onPressed: Optional[Callable] = None,
                      action_onPressedName: Optional[str] = None,
                      duration: int = 4000, # Default duration ms
                      key: Optional[Key] = None, # Optional key for the SnackBar itself
                      **snackbar_props: Any # Pass other SnackBar props like backgroundColor etc.
                     ):
        """
        Displays a SnackBar. Replaces the current one if already showing.
        Triggers reconciliation to render/update the SnackBar widget slot.
        """
        print(f"Framework: show_snackbar requested. Content: {content}")

        # --- Cancel Existing Timer ---
        if self._active_snackbar_timer and self._active_snackbar_timer.isActive():
            print("  Cancelling previous snackbar timer.")
            self._active_snackbar_timer.stop()
            self._active_snackbar_timer = None # Clear timer reference

        # --- Prepare Widgets ---
        content_widget: Widget
        if isinstance(content, Widget):
            content_widget = content
        elif isinstance(content, str):
            # Default wrap string content in a Text widget
            content_widget = Text(content, key=Key("snackbar_content_text")) # Add a key
        else:
            print("Error: SnackBar content must be a Widget instance or a string.")
            return

        action_widget: Optional[SnackBarAction] = None
        if action_label and action_onPressed:
            onPressedName = action_onPressedName if action_onPressedName else (action_onPressed.__name__ if action_onPressed else None)
            action_widget = SnackBarAction(
                 label=Text(action_label, key=Key("snackbar_action_label")), # Wrap label
                 onPressed=action_onPressed,
                 onPressedName=onPressedName,
                 key=Key("snackbar_action") # Add key
                 # Pass textColor etc. via snackbar_props if needed
            )

            print(f"  Registering SnackBar action callback: '{actual_action_name}'")
            self.api.register_callback(action_onPressedName, onPressedName)

        # --- Create/Update SnackBar Instance ---
        # If you want snackbars to be entirely managed by state's build,
        # this logic changes. This assumes Scaffold has a dedicated snackbar slot.
        snackbar_key = key or Key("default_snackbar") # Ensure a key for reconciliation
        self._active_snackbar_instance = SnackBar(
            content=content_widget,
            action=action_widget,
            duration=duration,
            key=snackbar_key,
            **snackbar_props # Pass through other styling props
        )

        # Assign it to the root widget's slot (assuming Scaffold)
        if self.root_widget and hasattr(self.root_widget, 'snackBar'):
            # This assignment tells the next build cycle to include this snackbar
            print("  Assigning new SnackBar instance to root widget slot.")
            self.root_widget.snackBar = self._active_snackbar_instance
        else:
             print("Warning: Cannot assign SnackBar, root widget or snackBar slot not found.")
             # If no slot, reconciler won't automatically render it unless handled differently
             # For now, we proceed assuming the slot exists and build/reconciliation handles it.

        # --- Trigger Reconciliation ---
        # This will cause the Framework to rebuild the tree, including the new SnackBar.
        # The reconciler will then generate INSERT or UPDATE patches.
        print("  Requesting reconciliation to render/update SnackBar.")
        self.request_reconciliation(None) # Pass None or a dummy state if needed

        # --- Schedule Show & Hide ---
        # We need the HTML ID, which is only known *after* reconciliation.
        # Schedule these actions slightly delayed, assuming reconciliation completes quickly.
        # A better approach might involve getting the ID *back* from the reconciler/patching phase.
        QTimer.singleShot(50, lambda: self._schedule_snackbar_show_after_reconcile(snackbar_key, duration)) # 50ms delay

    def _schedule_snackbar_show_after_reconcile(self, snackbar_key: Key, duration: int):
        """Called after a short delay to allow reconciliation to assign an HTML ID."""
        if not self.reconciler or not self._active_snackbar_instance or self._active_snackbar_instance.key != snackbar_key:
            print("  SnackBar changed or reconciler missing before showing.")
            return # SnackBar instance changed before we could show it

        # Find the HTML ID assigned by the reconciler
        node_data = self.reconciler.rendered_elements_map.get(snackbar_key)
        if node_data and 'html_id' in node_data:
            self._active_snackbar_html_id = node_data['html_id']
            print(f"  Found SnackBar HTML ID: {self._active_snackbar_html_id}. Triggering JS show.")
            self._trigger_snackbar_toggle_js(self._active_snackbar_html_id, True)

            # Schedule hide timer *after* finding ID and showing
            self._active_snackbar_timer = QTimer()
            self._active_snackbar_timer.setSingleShot(True)
            # Use lambda to capture the specific html_id at this moment
            current_html_id = self._active_snackbar_html_id
            self._active_snackbar_timer.timeout.connect(lambda: self.hide_snackbar(current_html_id))
            self._active_snackbar_timer.start(duration)
            print(f"  Scheduled hide for SnackBar {current_html_id} in {duration}ms.")
        else:
            print(f"Error: Could not find rendered HTML ID for SnackBar key {snackbar_key} after reconciliation.")
            # SnackBar might not have rendered correctly. Clear state?
            self._active_snackbar_instance = None


    def hide_snackbar(self, snackbar_html_id: Optional[str] = None):
        """
        Hides the specified SnackBar (or the currently active one if ID is None)
        and cleans up internal state.
        """
        target_html_id = snackbar_html_id or self._active_snackbar_html_id

        if not target_html_id:
            print("hide_snackbar: No target HTML ID provided or active.")
            return

        print(f"Framework: hide_snackbar requested for ID: {target_html_id}")

        # --- Stop Timer ---
        if self._active_snackbar_timer and self._active_snackbar_timer.isActive():
            self._active_snackbar_timer.stop()
            print("  Stopped active snackbar timer.")
        self._active_snackbar_timer = None

        # --- Trigger JS Hide ---
        self._trigger_snackbar_toggle_js(target_html_id, False)

        # --- Clean Up State ---
        # If hiding the *currently tracked* active snackbar, clear references
        if target_html_id == self._active_snackbar_html_id:
            print("  Clearing active snackbar instance.")
            self._active_snackbar_instance = None
            self._active_snackbar_html_id = None
            # Optionally, remove from scaffold slot immediately or wait for next reconcile?
            # Let's remove immediately to prevent flicker if reconcile is slow.
            if self.root_widget and hasattr(self.root_widget, 'snackBar'):
                 self.root_widget.snackBar = None
                 # Optionally trigger reconcile *again* to remove from DOM map?
                 # self.request_reconciliation(None) # Might be excessive

    def _trigger_snackbar_toggle_js(self, html_id: str, show: bool):
        """Internal helper to execute the toggleSnackBar JS function."""
        if self.window and hasattr(self.window, 'evaluate_js'):
            js_command = f"toggleSnackBar('{html_id}', {str(show).lower()});"
            # print(f"  Framework executing JS: {js_command}") # Debug
            self.window.evaluate_js(self.id, js_command)
        else:
            print(f"Cannot toggle snackbar '{html_id}': Window not available.")



    # --- Dialog State ---
    _active_dialog_instance: Optional[Dialog] = None
    _active_dialog_html_id: Optional[str] = None
    _is_dialog_showing: bool = False # Track visibility state

    def show_dialog(self,
                    dialog_widget: Dialog, # Pass the configured Dialog instance
                    onDismissed: Optional[Callable] = None, # Optional dismiss callback
                    onDismissedName: Optional[str] = None # Name for the dismiss callback
                   ):
        """
        Displays the provided Dialog widget instance as an in-page overlay.
        Triggers reconciliation to render the dialog if not already present.
        """
        if not isinstance(dialog_widget, Dialog):
            print("Error: show_dialog requires a Dialog widget instance.")
            return
        if self._is_dialog_showing and self._active_dialog_instance and dialog_widget.key == self._active_dialog_instance.key:
             print(f"Dialog with key {dialog_widget.key} is already showing.")
             return # Avoid showing the same dialog instance twice

        print(f"Framework: show_dialog requested. Key: {dialog_widget.key}")

        # --- Register Dismiss Callback (if any) ---
        # Note: Dismissal often triggered by action buttons inside the dialog content
        # This specific callback is mainly for *external* dismissal (e.g., scrim click)
        actual_dismiss_name = onDismissedName if onDismissedName else getattr(onDismissed, '__name__', None)
        if onDismissed and actual_dismiss_name:
             print(f"  Registering Dialog dismiss callback: '{actual_dismiss_name}'")
             self.api.register_callback(actual_dismiss_name, onDismissed)
        elif onDismissed:
             print("Warning: Dialog onDismissed provided without a usable name for JS.")
             actual_dismiss_name = '' # Ensure it's a string

        # --- Store Instance and Trigger Render ---
        # Store the instance. Reconciliation will handle adding it to the DOM.
        self._active_dialog_instance = dialog_widget
        self._is_dialog_showing = False # Mark as not yet visible via JS

        # Trigger reconciliation. The _process_reconciliation method needs to
        # know how to find and render the _active_dialog_instance separately
        # from the main root_widget tree, likely appending it to document.body.
        print("  Requesting reconciliation to render/update Dialog.")
        self.request_reconciliation(None) # Trigger update cycle

        # --- Schedule Show Animation ---
        # Wait briefly for reconciliation to render the element and assign ID
        QTimer.singleShot(50, lambda: self._schedule_dialog_show_after_reconcile(dialog_widget.key, actual_dismiss_name or ''))

    def _schedule_dialog_show_after_reconcile(self, dialog_key: Optional[Key], dismiss_callback_name: str):
        """Called after reconciliation to trigger the JS show animation."""
        if not self.reconciler or not self._active_dialog_instance or self._active_dialog_instance.key != dialog_key:
            print("  Dialog changed or reconciler missing before showing.")
            self._is_dialog_showing = False # Ensure state is correct
            return # Dialog instance changed

        # Find the HTML ID assigned by the reconciler
        node_data = self.reconciler.rendered_elements_map.get(dialog_key)
        if node_data and 'html_id' in node_data:
            self._active_dialog_html_id = node_data['html_id']
            print(f"  Found Dialog HTML ID: {self._active_dialog_html_id}. Triggering JS show.")
            # Get modal property from the widget instance
            is_modal = getattr(self._active_dialog_instance, 'isModal', True)
            self._trigger_dialog_toggle_js(
                self._active_dialog_html_id,
                show=True,
                is_modal=is_modal,
                on_dismiss_name=dismiss_callback_name
            )
            self._is_dialog_showing = True # Mark as visible
        else:
            print(f"Error: Could not find rendered HTML ID for Dialog key {dialog_key} after reconciliation.")
            self._active_dialog_instance = None # Clear if render failed
            self._is_dialog_showing = False


    def hide_dialog(self, dialog_key: Optional[Key] = None):
        """
        Hides the currently active dialog (or one specified by key).
        Triggers JS hide animation and requests reconciliation to remove the element.
        """
        target_key = dialog_key or getattr(self._active_dialog_instance, 'key', None)
        target_html_id = self._active_dialog_html_id

        if not self._is_dialog_showing or not target_key or not target_html_id:
            print(f"hide_dialog: No active dialog or target key/ID mismatch (Target key: {target_key}).")
            return

        print(f"Framework: hide_dialog requested for Key: {target_key}, ID: {target_html_id}")

        # --- Trigger JS Hide ---
        is_modal = getattr(self._active_dialog_instance, 'isModal', True)
        self._trigger_dialog_toggle_js(target_html_id, False, is_modal)
        self._is_dialog_showing = False # Mark as hidden

        # --- Clean Up Instance and Request Removal ---
        # Clear the active instance *after* triggering hide animation
        print("  Clearing active dialog instance reference.")
        self._active_dialog_instance = None
        self._active_dialog_html_id = None

        # Trigger reconciliation to *remove* the dialog element from the DOM map and tree
        # The reconciler logic needs to see _active_dialog_instance is None now.
        print("  Requesting reconciliation to remove Dialog element.")
        self.request_reconciliation(None)


    def _trigger_dialog_toggle_js(self, html_id: str, show: bool, is_modal: bool = True, on_dismiss_name: str = ''):
        """Internal helper to execute the toggleDialog JS function."""
        if self.window and hasattr(self.window, 'evaluate_js'):
            # Arguments: dialogId, show, isModal, scrimClass, onDismissedName
            js_command = f"toggleDialog('{html_id}', {str(show).lower()}, {str(is_modal).lower()}, 'dialog-scrim', '{on_dismiss_name}');"
            print(f"  Framework executing JS: {js_command}")
            self.window.evaluate_js(self.id, js_command)
        else:
            print(f"Cannot toggle dialog '{html_id}': Window not available.")



    # Ensure request_reconciliation and _process_reconciliation exist
    # ... (implementation from previous answers) ...

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