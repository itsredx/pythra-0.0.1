# pythra/core.py

# --- ADD THESE IMPORTS AT THE TOP OF THE FILE ---
import cProfile
import pstats
import io
# --- END OF IMPORTS ---

import os
from pathlib import Path
import sys
import shutil
import time
import json
import math
import html
import weakref
from typing import Optional, Set, List, Dict, TYPE_CHECKING, Callable, Any, Union

# PySide imports for main thread execution
from PySide6.QtCore import QTimer

# Framework imports
from .config import Config
from .server import AssetServer
from .api import Api
from .window import webwidget

# New/Refactored Imports
from .base import Widget, Key
from .state import State, StatefulWidget, StatelessWidget
from .reconciler import Reconciler, Patch, ReconciliationResult
from .widgets import *  # Import all widgets for class lookups if needed


# Type Hinting for circular dependencies
if TYPE_CHECKING:
    from .state import State


class Framework:
    """
    Manages the application window, widget tree, state updates,
    and the reconciliation data flow for rendering the UI.
    """

    _instance = None
    # config = Config()

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

        # --- THIS IS THE DEFINITIVE FIX ---
        # 1. Determine the project root. We define this as the directory
        #    where the user's main application script is running.
        #    `sys.argv[0]` reliably gives us the path to the executed script (e.g., 'lib/main.py').
        main_script_path = os.path.abspath(sys.argv[0])
        # We assume the project root is the parent of the 'lib' directory, or the
        # directory of the script itself if not in 'lib'.
        if "lib" in Path(main_script_path).parts:
            self.project_root = Path(main_script_path).parent.parent
        else:
            self.project_root = Path(main_script_path).parent

        print(f"✅ Framework initialized. Project Root detected at: {self.project_root}")

        self.config = Config(config_path=self.project_root / 'config.yaml')

        # All paths are now relative to the project root
        self.web_dir = self.project_root / self.config.get('web_dir', 'web')
        self.assets_dir = self.project_root / self.config.get('assets_dir', 'assets')

        # Ensure these directories exist within the user's project
        self.web_dir.mkdir(exist_ok=True)
        self.assets_dir.mkdir(exist_ok=True)
        
        # Copy default assets if they don't exist
        self._ensure_default_assets()

        self.html_file_path = self.web_dir / "index.html"
        self.css_file_path = self.web_dir / "styles.css"
        
        # The asset server now serves from the project's asset directory
        self.asset_server = AssetServer(
            directory=str(self.assets_dir),
            port=self.config.get("assets_server_port"),
        )
        # --- END OF KEY CHANGE ---

        self.api = webwidget.Api()
        self.reconciler = Reconciler()
        self.root_widget: Optional[Widget] = None
        self.window = None
        self.id = "main_window_id"

        self.called = False

        # State Management / Reconciliation Control
        self._reconciliation_requested: bool = False
        self._pending_state_updates: Set[State] = set()

        self._result = None

        # # Asset Management
        # self.html_file_path = os.path.abspath("web/index.html")
        # self.css_file_path = os.path.abspath("web/styles.css")
        # self.asset_server = AssetServer(
        #     directory=self.config.get("assets_dir"),
        #     port=self.config.get("assets_server_port"),
        # )
        self.asset_server.start()
        # os.makedirs("web", exist_ok=True)

        Widget.set_framework(self)
        StatefulWidget.set_framework(self)
        print("Framework Initialized with new Reconciler architecture.")

    def _ensure_default_assets(self):
        """
        Copies essential default assets (like JS files and fonts) from the
        framework's package to the user's project directory if they are missing.
        """
        # Find the source path inside the installed pythra package
        package_root = Path(__file__).parent
        source_web_dir = package_root / 'web_template'
        source_assets_dir = package_root / 'assets_template'
        
        # Copy web files (js, etc.)
        if source_web_dir.exists():
            for item in source_web_dir.iterdir():
                dest_item = self.web_dir / item.name
                if not dest_item.exists():
                    if item.is_dir():
                        shutil.copytree(item, dest_item)
                    else:
                        shutil.copy(item, dest_item)
        
        # Copy asset files (fonts, etc.)
        if source_assets_dir.exists():
            for item in source_assets_dir.iterdir():
                dest_item = self.assets_dir / item.name
                if not dest_item.exists():
                    if item.is_dir():
                        shutil.copytree(item, dest_item)
                    else:
                        shutil.copy(item, dest_item)

    def set_root(self, widget: Widget):
        """Sets the root widget for the application."""
        self.root_widget = widget

    # We will refactor the rendering logic out of `run` into its own method
    def _perform_initial_render(self, root_widget: Widget, title: str):
        """Builds, reconciles, and generates the initial HTML, CSS, and JS."""
        print("\n>>> Framework: Performing Initial Render <<<")

        # 1. Build the full widget tree
        built_tree_root = self._build_widget_tree(root_widget)
        initial_tree_to_reconcile = built_tree_root
        if isinstance(built_tree_root, StatefulWidget):
            children = built_tree_root.get_children()
            initial_tree_to_reconcile = children[0] if children else None

        # 2. Perform initial reconciliation
        result = self.reconciler.reconcile(
            previous_map={},
            new_widget_root=initial_tree_to_reconcile,
            parent_html_id="root-container",
        )
        self._result = result # Store the result

        # 3. Update framework state from the result
        self.reconciler.context_maps["main"] = result.new_rendered_map
        for cb_id, cb_func in result.registered_callbacks.items():
            self.api.register_callback(cb_id, cb_func)

        # 4. Generate initial HTML, CSS, and JS
        root_key = initial_tree_to_reconcile.get_unique_id() if initial_tree_to_reconcile else None
        html_content = self._generate_html_from_map(root_key, result.new_rendered_map)
        css_rules = self._generate_css_from_details(result.active_css_details)
        js_script = self._generate_initial_js_script(result)

        # 5. Write files
        self._write_initial_files(title, html_content, css_rules, js_script)

    def run(
        self,
        title: str = config.get("app_name"),
        width: int = config.get("win_width"),
        height: int = config.get("win_height"),
        frameless: bool = config.get("frameless"),
        maximized: bool = config.get("maximixed"),
        fixed_size: bool = config.get("fixed_size"),
        # --- THIS IS THE CRUCIAL ADDITION ---
        block: bool = True
    ):
        """
        Builds the initial UI, writes necessary files, creates the window, and starts the app.
        """
        if not self.root_widget:
            raise ValueError("Root widget not set. Use set_root() before run().")

        # print("\n>>> Framework: Performing Initial Render <<<")

        # # 1. Build the full widget tree, which will include the StatefulWidget at the root.
        # built_tree_root = self._build_widget_tree(self.root_widget)

        # # 2. <<< THE FIX >>>
        # # If the root is a StatefulWidget, we reconcile what it *builds*, not the widget itself.
        # initial_tree_to_reconcile = built_tree_root
        # if isinstance(built_tree_root, StatefulWidget):
        #     children = built_tree_root.get_children()
        #     initial_tree_to_reconcile = children[0] if children else None

        # # 3. Perform initial reconciliation on the *renderable* tree.
        # result = self.reconciler.reconcile(
        #     previous_map={},
        #     new_widget_root=initial_tree_to_reconcile,
        #     parent_html_id="root-container",
        # )

        # self._result = result
        

        # # 4. Update framework state from the initial result.
        # self.reconciler.context_maps["main"] = result.new_rendered_map
        # for cb_id, cb_func in result.registered_callbacks.items():
        #     self.api.register_callback(cb_id, cb_func)

        # # 5. Generate initial HTML from the map created by the reconciler.
        # root_key = (
        #     initial_tree_to_reconcile.get_unique_id()
        #     if initial_tree_to_reconcile
        #     else None
        # )
        # initial_html_content = self._generate_html_from_map(
        #     root_key, result.new_rendered_map
        # )

        # # 6. Generate initial CSS from the details collected by the reconciler.
        # initial_css_rules = self._generate_css_from_details(result.active_css_details)

        # # 7. Generate the initial JS script for things like responsive clip paths.
        # initial_js_script = self._generate_initial_js_script(result.js_initializers)

        # # 8. Write files and create the application window.
        # self._write_initial_files(
        #     title, initial_html_content, initial_css_rules, initial_js_script
        # )

        # Now `run` just calls the new helper method
        self._perform_initial_render(self.root_widget, title)

        self.window = webwidget.create_window(
            title,
            self.id,
            self.html_file_path,
            self.api,
            width,
            height,
            frameless=frameless,
            maximized = maximized,
            fixed_size = fixed_size,
            hot_restart_handler = self.hot_restart
        )

        # 9. Start the application event loop.
        print("Framework: Starting application event loop...")
        webwidget.start(window=self.window, debug=bool(self.config.get("Debug", False)))

    def close(self):
        # self.asset_server.stop()
        self.window.close_window() if self.window else print("unable to close window: window is None")
        self.asset_server.stop()

    def minimize(self):
        self.window.minimize() if self.window else print("unable to close window: window is None")

    def _dispose_widget_tree(self, widget: Optional[Widget]):
        """Recursively disposes of the state of a widget and its children."""
        if widget is None:
            return
        
        # Dispose of the current widget's state if it's stateful
        if isinstance(widget, StatefulWidget):
            state = widget.get_state()
            if state:
                state.dispose()
        
        # Recurse on all children
        if hasattr(widget, 'get_children'):
            for child in widget.get_children():
                self._dispose_widget_tree(child)

    # --- State Update and Reconciliation Cycle ---

    # --- NEW HOT RESTART METHOD ---
    def hot_restart(self):
        """
        Performs a full teardown and rebuild of the application state and UI
        on the existing window. This is achieved by regenerating the entire HTML
        body and applying it in one atomic operation, avoiding patch race conditions.
        """
        # --- PROFILER SETUP ---
        # profiler = cProfile.Profile()
        # profiler.enable()
        # --- END PROFILER SETUP ---

        if not self.window or not self.root_widget:
            print("Hot Restart Error: Application not running.")
            return

        print("\n🔥 --- Framework: Initiating Hot Restart --- 🔥")
        start_time = time.time()

        # 1. --- FULL TEARDOWN ---
        print("Tearing down old state...")
        self._dispose_widget_tree(self.root_widget) # Dispose old states and listeners
        self.reconciler.clear_all_contexts()         # Clear reconciler's memory
        self.api.clear_callbacks()                   # Clear old API callbacks

        # 2. --- CLEAN REBUILD ---
        # Create a fresh instance of the root widget to get the new code.
        root_widget_class = self.root_widget.__class__
        new_root_widget = root_widget_class(key=self.root_widget.key) # Recreate with the same root key
        self.set_root(new_root_widget)

        print("Rebuilding new widget tree...")
        built_tree_root = self._build_widget_tree(self.root_widget)
        tree_to_reconcile = built_tree_root
        if isinstance(built_tree_root, StatefulWidget):
            children = built_tree_root.get_children()
            tree_to_reconcile = children[0] if children else None

        # 3. --- GENERATE NEW UI CONTENT (NO PATCHES) ---
        # Reconcile against an EMPTY map to populate the new rendered_map and collect details.
        result = self.reconciler.reconcile(
            previous_map={},
            new_widget_root=tree_to_reconcile,
            parent_html_id="root-container"
        )

        # Update the framework's internal state with the new data
        self.reconciler.context_maps["main"] = result.new_rendered_map
        for cb_id, cb_func in result.registered_callbacks.items():
            self.api.register_callback(cb_id, cb_func)
        
        # 4. --- PREPARE SCRIPTS FOR THE BROWSER ---
        # Generate the new CSS stylesheet
        css_rules = self._generate_css_from_details(result.active_css_details)
        css_update_script = self._generate_css_update_script(css_rules)

        # Generate the new HTML content for the entire root container
        root_key = tree_to_reconcile.get_unique_id() if tree_to_reconcile else None
        html_content = self._generate_html_from_map(root_key, result.new_rendered_map)
        escaped_html = json.dumps(html_content)[1:-1].replace("`", "\\`").replace("${", "\\${")

        # Generate the script for any necessary JS initializers (e.g., ClipPath, SimpleBar)
        initializer_script_tag = self._generate_initial_js_script(result)
        initializers_js = initializer_script_tag.replace("<script type=\"module\">", "").replace("import { PythraSlider } from './js/slider.js';", "").replace("</script>","").replace("document.addEventListener('DOMContentLoaded', () => {", "").replace("});//end event listener", "")
        # print("initializer_script_tag: ", initializer_script_tag)
        
        # We need to extract just the JS commands from inside the <script> tag
        # to run them after the innerHTML has been set.
        # import re
        # match = re.search(r"document\.addEventListener\('DOMContentLoaded', \(\) => \{(.+?)\}\);", initializer_script_tag, re.DOTALL)
        # initializers_js = match.group(1).strip() if match else ""
        # print("initializers_js: ", initializers_js)

        # --- THIS IS THE FIX ---
        # Get the source code for our core JS utility functions.
        js_utilities = self._get_js_utility_functions()
        # --- END OF FIX ---

        # 5. --- ASSEMBLE AND EXECUTE THE FINAL RESTART SCRIPT ---
        # This script performs the update in a safe, atomic order.
        restart_script = f"""
            // Step 1: Update the styles to the new stylesheet.
            {css_update_script}

            // Step 2: Atomically replace the entire DOM content of the root container.
            // This is faster and more reliable than thousands of individual patches.
            var rootContainer = document.getElementById('root-container');
            if (rootContainer) {{
                rootContainer.innerHTML = `{escaped_html}`;
            }}

            // Step 3: Defer the JavaScript initializers to run AFTER the new DOM
            // has been fully parsed and is ready.
            setTimeout(() => {{
                try {{
                    // DEFINE THE MISSING FUNCTIONS
                    {js_utilities}
                    // NOW, RUN THE INITIALIZERS
                    console.log(`Tring hot restart`);
                    {initializers_js}
                }} catch (e) {{
                    console.error("Error running Hot Restart initializers:", e);
                }}
            }}, 0);
        """
        
        print(f"Applying full UI rebuild for Hot Restart...")
        self.window.evaluate_js(self.id, restart_script)

        print(f"--- Hot Restart Complete (Total: {time.time() - start_time:.4f}s) ---")
        # --- PROFILER REPORTING ---
        # profiler.disable()
        # s = io.StringIO()
        # # Sort stats by 'cumulative time' to see the biggest bottlenecks at the top
        # ps = pstats.Stats(profiler, stream=s).sort_stats('cumulative')
        # ps.print_stats(20) # Print the top 20 most time-consuming functions

        print("\n--- cProfile Report ---")
        print(s.getvalue())
        print("--- End of Report ---\n")
        # --- END PROFILER REPORTING ---



    # Place this new helper method somewhere in the Framework class
    def _get_js_utility_functions(self) -> str:
        """Reads core JS utility files and returns them as a single string."""
        js_files = [
            "web/js/pathGenerator.js",
            "web/js/clipPathUtils.js",
            "web/js/slider.js",
            "web/js/dropdown.js",
            "web/js/gesture_detector.js",
            "web/js/gradient_border.js", 
            "web/js/virtual_list.js",  # <-- ADD THIS LINE
        ]
        all_js_code = []
        for file_path in js_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    # We need to remove the 'export' keyword so they become
                    # simple global functions within our script's scope.
                    content = f.read().replace('export function', 'function').replace('export class', 'class').replace("import { generateRoundedPath } from './pathGenerator.js';", "")
                    all_js_code.append(content)
            except FileNotFoundError:
                print(f"Warning: JS utility file not found: {file_path}")
        return "\n".join(all_js_code)

    def request_reconciliation(self, state_instance: State):
        """Called by State.setState to schedule a UI update."""
        self._pending_state_updates.add(state_instance)

        if not self._reconciliation_requested:
            self._reconciliation_requested = True
            QTimer.singleShot(0, self._process_reconciliation)


    def _process_reconciliation(self):
        """
        Performs a targeted, high-performance reconciliation cycle for only the
        widgets whose state has changed.
        """

        # --- PROFILER SETUP ---
        profiler = cProfile.Profile()
        profiler.enable()
        # --- END PROFILER SETUP ---

        self._reconciliation_requested = False
        if not self.window:
            print("Error: Window not available for reconciliation.")
            return

        print("\n--- Framework: Processing Granular Reconciliation Cycle ---")
        start_time = time.time()

        # Get the full map of the currently rendered UI for the main context.
        main_context_map = self.reconciler.get_map_for_context("main")

        # --- NEW ARCHITECTURE: SURGICAL UPDATES ---
        all_patches = []
        all_new_callbacks = {}
        all_active_css_details = {} # To track if CSS might have changed

        # Process each pending state update individually.
        for state_instance in self._pending_state_updates:
            widget_to_rebuild = state_instance.get_widget()
            if not widget_to_rebuild:
                print(f"Warning: Widget for state {state_instance} lost. Skipping update.")
                continue

            widget_key = widget_to_rebuild.get_unique_id()
            old_widget_data = main_context_map.get(widget_key)

            if not old_widget_data:
                # Special case for the root widget
                if widget_to_rebuild is self.root_widget:
                    parent_html_id = "root-container"
                else:
                    print(f"Error: Could not find previous state for widget {widget_key}. A full rebuild may be required.")
                    continue
            else:
                parent_html_id = old_widget_data["parent_html_id"]

            print(f"Reconciling subtree for: {widget_to_rebuild.__class__.__name__} (Key: {widget_key})")

            # 1. Build ONLY the subtree for the dirty widget.
            # This is fast because it doesn't traverse the whole application.
            new_subtree = self._build_widget_tree(widget_to_rebuild)

            # 2. Reconcile ONLY that specific subtree.
            subtree_result = self.reconciler.reconcile(
                previous_map=main_context_map,
                new_widget_root=new_subtree,
                parent_html_id=parent_html_id,
                old_root_key=widget_key, # Tell the reconciler exactly where to start
                is_partial_reconciliation=True # CRITICAL: Prevents deleting the rest of the app
            )

            # 3. Aggregate the patches, callbacks, and CSS details from this subtree.
            all_patches.extend(subtree_result.patches)
            all_new_callbacks.update(subtree_result.registered_callbacks)
            all_active_css_details.update(subtree_result.active_css_details)

            # 4. CRITICAL: Update the main context map in-place with the changes.
            # This keeps the framework's "memory" of the UI consistent.
            main_context_map.update(subtree_result.new_rendered_map)

        # --- Optimized CSS and Script Generation ---

        # Register any new callbacks that might have been created in the rebuild.
        for cb_id, cb_func in all_new_callbacks.items():
            self.api.register_callback(cb_id, cb_func)

        # Implement CSS memoization check
        # NOTE: self._last_css_keys should be initialized to set() in Framework.__init__
        new_css_keys = set(all_active_css_details.keys())
        css_update_script = ""
        if not hasattr(self, '_last_css_keys') or self._last_css_keys != new_css_keys:
             print("Framework: CSS classes may have changed. Regenerating stylesheet.")
             # We need to generate CSS from the *entire* app's styles, not just the subtree.
             # We can get this by iterating over the updated main_context_map.
             full_css_details = {
                 data['props']['css_class']: (type(data['widget_instance']).generate_css_rule, data['widget_instance'].style_key)
                 for data in main_context_map.values()
                 if 'css_class' in data['props'] and hasattr(data['widget_instance'], 'style_key')
             }
             css_rules = self._generate_css_from_details(full_css_details)
             css_update_script = self._generate_css_update_script(css_rules)
             self._last_css_keys = new_css_keys
        else:
             print("Framework: CSS classes are unchanged. Skipping CSS generation.")

        # Generate the DOM patch script from our aggregated patches.
        # No new JS initializers are expected during a partial update.
        dom_patch_script = self._generate_dom_patch_script(all_patches, js_initializers=[])

        combined_script = (css_update_script + "\n" + dom_patch_script).strip()
        if combined_script:
            print(f"Framework: Executing {len(all_patches)} DOM patches.")
            # print("Patches:", all_patches)
            self.window.evaluate_js(self.id, combined_script)
        else:
            print("Framework: No DOM changes detected.")

        self._pending_state_updates.clear()
        print(
            f"--- Framework: Reconciliation Complete (Total: {time.time() - start_time:.4f}s) ---"
        )

        # --- PROFILER REPORTING ---
        # profiler.disable()
        s = io.StringIO()
        # Sort stats by 'cumulative time' to see the biggest bottlenecks at the top
        ps = pstats.Stats(profiler, stream=s).sort_stats('cumulative')
        ps.print_stats(20) # Print the top 20 most time-consuming functions

        print("\n--- cProfile Report ---")
        print(s.getvalue())
        print("--- End of Report ---\n")
        # --- END PROFILER REPORTING ---

    # --- Widget Tree Building ---
    def _build_widget_tree(self, widget: Optional[Widget]) -> Optional[Widget]:
        """
        Recursively builds the widget tree, calling build() on StatefulWidget instances.
        This version correctly preserves the StatefulWidget in the tree structure.
        """
        if widget is None:
            return None

        # --- THIS IS THE FIX ---
        # Handle StatelessWidget and StatefulWidget with the same pattern.
        if isinstance(widget, StatelessWidget):
            # 1. Build the child widget from the StatelessWidget.
            built_child = widget.build()
            # 2. Recursively process the built child to build its own subtree.
            processed_child = self._build_widget_tree(built_child)
            # 3. CRITICAL: The StatelessWidget's children list becomes the processed child.
            #    This keeps the StatelessWidget in the tree as the parent.
            widget._children = [processed_child] if processed_child else []
            return widget # Return the original StatelessWidget
        # --- END OF FIX ---

        # If it's a StatefulWidget, we need to build its child and replace it in the tree.
        if isinstance(widget, StatefulWidget):
            state = widget.get_state()
            if not state:
                return None  # Or return an error widget

            # Build the child widget from the state.
            built_child = state.build()

            # Recursively process the built child to build its own subtree.
            processed_child = self._build_widget_tree(built_child)

            # CRITICAL: The StatefulWidget's children list becomes the *single* processed child.
            # This keeps the StatefulWidget as the parent node in the tree.
            widget._children = [processed_child] if processed_child else []

            # Return the original StatefulWidget, now with its subtree correctly built.
            return widget

        # For regular widgets, just recurse on their children.
        else:
            if hasattr(widget, "get_children"):
                new_children = []
                for child in widget.get_children():
                    # Recursively build each child.
                    built_child = self._build_widget_tree(child)
                    if built_child:
                        new_children.append(built_child)
                # Replace the old children list with the newly built one.
                widget._children = new_children
            return widget

    # --- HTML and CSS Generation ---

    # --- ADD THIS NEW METHOD ---
    def find_ancestor_state_of_type(self, start_widget: Widget, state_type: type) -> Optional[State]:
        """
        Traverses up the widget tree from a given widget to find the state
        of the nearest ancestor that is an instance of a specific StatefulWidget type,
        or whose State is of state_type.
        """
        main_context_map = self.reconciler.get_map_for_context("main")
        if not main_context_map:
            return None

        current_key = start_widget.get_unique_id()
        
        # Loop up the tree using parent references stored in the reconciler's map
        while current_key in main_context_map:
            node_data = main_context_map[current_key]
            widget_instance = node_data.get('widget_instance')

            # Check if the current widget's state is the type we're looking for
            if isinstance(widget_instance, StatefulWidget):
                state = widget_instance.get_state()
                if isinstance(state, state_type):
                    return state

            # Move up to the parent
            parent_key = node_data.get('parent_key') # We'll need to add this to the map
            if not parent_key:
                break
            current_key = parent_key
            
        return None

    def _generate_html_from_map(
        self, root_key: Optional[Union[Key, str]], rendered_map: Dict
    ) -> str:
        """Generates the full HTML string by recursively traversing the flat rendered_map."""
        if root_key is None or root_key not in rendered_map:
            return ""

        node_data = rendered_map.get(root_key)
        if not node_data:
            return ""

        # A StatefulWidget doesn't render itself, so we render its child.
        if node_data["widget_type"] == "StatefulWidget":
            child_keys = node_data.get("children_keys", [])
            if child_keys:
                return self._generate_html_from_map(child_keys[0], rendered_map)
            return ""

        html_id = node_data["html_id"]
        props = node_data["props"]
        widget_instance = node_data["widget_instance"]

        stub = self.reconciler._generate_html_stub(widget_instance, html_id, props)
        # print("stub: ", stub)

        children_html = "".join(
            self._generate_html_from_map(child_key, rendered_map)
            for child_key in node_data.get("children_keys", [])
        )

        if ">" in stub and "</" in stub:
            tag = self.reconciler._get_widget_render_tag(widget_instance)
            closing_tag = f"</{tag}>"
            if stub.endswith(closing_tag):
                content_part = stub[: -len(closing_tag)]
                return f"{content_part}{children_html}{closing_tag}"

        return stub

    def _generate_css_from_details(
        self, css_details: Dict[str, Tuple[Callable, Any]]
    ) -> str:
        """Generates CSS rules directly from the details collected by the Reconciler."""
        all_rules = []
        for css_class, (generator_func, style_key) in css_details.items():
            try:
                rule = generator_func(style_key, css_class)
                if rule:
                    all_rules.append(rule)
                    # print("Rule: ",rule)
            except Exception as e:
                import traceback

                print(f"ERROR generating CSS for class '{css_class}': {e}")
                traceback.print_exc()

        print(f"Generated CSS for {len(all_rules)} active shared classes.")
        return "\n".join(all_rules)

    # --- Script Generation and File Writing ---

    def _generate_css_update_script(self, css_rules: str) -> str:
        """Generates JS to update the <style id="dynamic-styles"> tag."""
        escaped_css = json.dumps(css_rules).replace("`", "\\`")
        return f"""
            var styleSheet = document.getElementById('dynamic-styles');
            var newCss = {escaped_css};
            if (styleSheet.textContent !== newCss) {{
                 styleSheet.textContent = newCss;
            }}
        """

    def _build_path_from_commands(self, commands_data: List[Dict]) -> str:
        """
        Builds an SVG path data string from serialized command data.
        This is the Python-side logic that mirrors your JS path generators.
        """
        return ""
        # path_parts = []
        # for cmd_data in commands_data:
        #     print("CMD DATA CORE: ", cmd_data)
        #     cmd_type = cmd_data.get("type")
        #     if cmd_type == "RoundedPolygon":
        #         # This is a simplified version of your JS logic for Python
        #         # It uses Quadratic Curves for rounding.
        #         vertices = cmd_data.get("verts", [])
        #         radius = cmd_data.get("radius", 0)
        #         if not vertices or radius <= 0:
        #             continue

        #         num_vertices = len(vertices)
        #         for i in range(num_vertices):
        #             p1 = vertices[i]
        #             p0 = vertices[i - 1]
        #             p2 = vertices[(i + 1) % num_vertices]
        #             v1 = (p0[0] - p1[0], p0[1] - p1[1])
        #             v2 = (p2[0] - p1[0], p2[1] - p1[1])
        #             len_v1 = math.sqrt(v1[0] ** 2 + v1[1] ** 2)
        #             len_v2 = math.sqrt(v2[0] ** 2 + v2[1] ** 2)
        #             if len_v1 == 0 or len_v2 == 0:
        #                 continue

        #             clamped_radius = min(radius, len_v1 / 2, len_v2 / 2)
        #             arc_start_x = p1[0] + (v1[0] / len_v1) * clamped_radius
        #             arc_start_y = p1[1] + (v1[1] / len_v1) * clamped_radius
        #             arc_end_x = p1[0] + (v2[0] / len_v2) * clamped_radius
        #             arc_end_y = p1[1] + (v2[1] / len_v2) * clamped_radius

        #             if i == 0:
        #                 path_parts.append(f"M {arc_start_x} {arc_start_y}")
        #             else:
        #                 path_parts.append(f"L {arc_start_x} {arc_start_y}")
        #             path_parts.append(f"Q {p1[0]} {p1[1]} {arc_end_x} {arc_end_y}")
        #         path_parts.append("Z")

        #     elif cmd_type == "MoveTo":
        #         path_parts.append(f"M {cmd_data['x']} {cmd_data['y']}")
        #     elif cmd_type == "LineTo":
        #         path_parts.append(f"L {cmd_data['x']} {cmd_data['y']}")
        #     elif cmd_type == "ClosePath":
        #         path_parts.append("Z")
        #     # ... add other command types as needed ...

        # return " ".join(path_parts)

    # In pythra/core.py
    # In pythra/core.py, inside the Framework class

    def _sanitize_for_json(self, data: Any) -> Any:
        """
        Recursively removes non-serializable values from a data structure
        before it's passed to json.dumps.
        """
        if isinstance(data, dict):
            # Create a new dict, excluding keys with function values or widget instances
            return {
                k: self._sanitize_for_json(v)
                for k, v in data.items()
                if not callable(v) and not isinstance(v, Widget)
            }
        elif isinstance(data, list):
            return [self._sanitize_for_json(item) for item in data]
        # Allow basic types that are JSON-serializable
        elif isinstance(data, (str, int, float, bool, type(None))):
            return data
        else:
            # For any other complex object, return its string representation
            # This is a safe fallback.
            return str(data)

    def _generate_dom_patch_script(self, patches: List[Patch], js_initializers=None) -> str:
        """Converts the list of Patch objects from the reconciler into executable JavaScript."""
        js_commands = []
        old_id = None
        new_id = None

        count = 0
        for patch in patches:

            action, target_id, data = patch.action, patch.html_id, patch.data

            # --- THIS IS THE FIX ---
            # Create a sanitized version of the data for logging.
            sanitized_data_for_log = self._sanitize_for_json(data)
            loggable_data_str = json.dumps(sanitized_data_for_log)
            # --- END OF FIX ---

            command_js = ""

            # print("Patch details: ",action, target_id, data)

            if action == "INSERT":
                parent_id, html_stub, props, before_id = (
                    data["parent_html_id"],
                    data["html"],
                    data["props"],
                    data["before_id"],
                )
                # Escape the HTML for safe injection into a JS template literal
                final_escaped_html = (
                    json.dumps(html_stub)[1:-1]
                    .replace("`", "\\`")
                    .replace("${", "\\${")
                )
                before_id_js = (
                    f"document.getElementById('{before_id}')" if before_id else "null"
                )
                command_js = f"""
                    var parentEl = document.getElementById('{parent_id}');
                    if (parentEl) {{
                        // Create a temporary, disconnected container
                        var tempContainer = document.createElement('div');
                        // Use trim() to remove leading/trailing whitespace from the HTML string
                        tempContainer.innerHTML = `{final_escaped_html}`.trim(); 
                        
                        // Use `firstElementChild` which ignores whitespace text nodes
                        var insertedEl = tempContainer.firstElementChild; 

                        if (insertedEl) {{
                            parentEl.insertBefore(insertedEl, {before_id_js});
                            // Now we can safely apply props because 'insertedEl' is guaranteed to be an element
                            {self._generate_prop_update_js(target_id, props, is_insert=True)}
                        }}
                    }}
                """
                props = data.get("props", {})

                # --- ADD THIS BLOCK ---
                if props.get("init_gradient_clip_border"):
                    options_json = json.dumps(props.get("gradient_clip_options", {}))
                    command_js += f"""
                        setTimeout(() => {{
                            if (typeof PythraGradientClipPath !== 'undefined') {{
                                window._pythra_instances['{target_id}'] = new PythraGradientClipPath('{target_id}', {options_json});
                            }}
                        }}, 0);
                    """
                # --- END OF BLOCK ---

                # --- ADD THIS BLOCK ---
                if props.get("init_gesture_detector"):
                    options_json = json.dumps(props.get("gesture_options", {}))
                    command_js += f"""
                        setTimeout(() => {{
                            if (typeof PythraGestureDetector !== 'undefined') {{
                                window._pythra_instances['{target_id}'] = new PythraGestureDetector('{target_id}', {options_json});
                            }}
                        }}, 0);
                    """
                # --- END OF BLOCK ---

                # --- ADD THIS BLOCK ---
                # print("Props: ", props)
                if props.get("init_dropdown"):
                    print("---- dropdown init ----", target_id)
                    options_json = json.dumps(props.get("dropdown_options", {}))
                    command_js += f"""
                        setTimeout(() => {{
                            console.log("Initializig dropdown");
                            if (typeof PythraDropdown !== 'undefined') {{
                                console.log("Initializig the dropdown");
                                if (!window._pythra_instances['{target_id}']) {{
                                    window._pythra_instances['{target_id}'] = new PythraDropdown('{target_id}', {options_json});
                                }}
                            }}
                        }}, 0);
                    """
                # --- END OF BLOCK ---

                if props.get("init_slider"):
                    options_json = json.dumps(props.get("slider_options", {}))
                    command_js += f"""
                        setTimeout(() => {{
                            if (typeof PythraSlider !== 'undefined') {{
                                if (!window._pythra_instances['{target_id}']) {{
                                    console.log('Initializing dynamically inserted PythraSlider for #{target_id}');
                                    window._pythra_instances['{target_id}'] = new PythraSlider('{target_id}', {options_json});
                                }}
                            }}
                        }}, 0);
                    """
                # --- END ADDITION ---
                if props.get("init_simplebar"):
                    options_json = json.dumps(props.get("simplebar_options", {}))
                    command_js += f"""
                    setTimeout(() => {{
                        var el_{target_id} = document.getElementById('{target_id}');
                        if (el_{target_id} && !el_{target_id}.simplebar) {{
                            new SimpleBar(el_{target_id}, {options_json} );
                            console.log(el_{target_id}.simplebar);
                        }}
                        }}, 0);
                    """
                    # print("new SimpleBar: ", options_json)

                # --- ADD THIS BLOCK ---
                if props.get("init_virtual_list"):
                    options = props.get("virtual_list_options", {})
                    options_json = json.dumps(options)
                    # We need to wait for SimpleBar to initialize first, so we defer this.
                    js_commands.append(f"""
                    setTimeout(() => {{
                        if (typeof PythraVirtualList !== 'undefined' && document.getElementById('{target_id}').simplebar) {{
                            window._pythra_instances['{target_id}_vlist'] = new PythraVirtualList('{target_id}', {options_json});
                        }}
                    }}, 0);
                    """)
                # --- END OF BLOCK ---

                if 'responsive_clip_path' in props:
                    # print("INITIALIZERS: ", js_initializers)
                    if target_id != new_id:
                        old_id, new_id = new_id, target_id
                    initializer_data = {
                        'type': 'ResponsiveClipPath',
                        'target_id': target_id,
                        'data': props['responsive_clip_path'],
                        'before_id': old_id
                    }
                    # js_initializers.append(initializer_data) if js_initializers else print("no js_initializers found")
                    # print("INITIALIZERS:AFTER: ", js_initializers)
                    # target_id = initializer_data["target_id"]
                    clip_data = initializer_data["data"]
                    # print("target id: ", target_id, "Data: ", clip_data, "before_id: ", initializer_data["before_id"] if initializer_data["before_id"] else None)

                    # Serialize the Python data into JSON strings for JS
                    points_json = json.dumps(clip_data["points"])
                    radius_json = json.dumps(clip_data["radius"])
                    ref_w_json = json.dumps(clip_data["viewBox"][0])
                    ref_h_json = json.dumps(clip_data["viewBox"][1])

                    # This JS code performs the exact two-step process you described.
                    # commands_js = 


                    js_commands.append(f"""
                    setTimeout(() => {{
                        // Step 0: Convert Python's array-of-arrays to JS's array-of-objects
                        const pointsForGenerator_{target_id} = {points_json}.map(p => ({{x: p[0], y: p[1]}}));
                        
                        // Step 1: Call generateRoundedPath with the points and radius
                        const initialPathString_{target_id} = generateRoundedPath(pointsForGenerator_{target_id}, {radius_json});
                        
                        // Step 2: Feed the generated path into ResponsiveClipPath
                        window._pythra_instances['{initializer_data["before_id"] if initializer_data["before_id"] else target_id}'] = new ResponsiveClipPath(
                            '{initializer_data["before_id"] if initializer_data["before_id"] else target_id}', 
                            initialPathString_{target_id}, 
                            {ref_w_json}, 
                            {ref_h_json}, 
                            {{ uniformArc: true, decimalPlaces: 2 }}
                        );
                        }}, 0);
                    """)
                    
                    
                

            elif action == "REMOVE":
                command_js = f"""
                    var el_to_remove = document.getElementById('{target_id}');
                    if (el_to_remove) {{
                        // Check if it was a SimpleBar instance before removing.
                        if (el_to_remove.simplebar) {{
                            // This is crucial to prevent memory leaks from ResizeObserver.
                            el_to_remove.simplebar.unMount();
                        }}
                        el_to_remove.remove();
                    }}
                """
                command_js = f'var el = document.getElementById("{target_id}"); if(el) el.remove();'
            elif action == "UPDATE":
                # Pass the element's ID to the prop updater, not the element itself
                prop_update_js = self._generate_prop_update_js(target_id, data["props"])
                if prop_update_js:
                    command_js = f'var elToUpdate = document.getElementById("{target_id}"); if (elToUpdate) {{ {prop_update_js} }}'

                # new_scrollbar_props = data.get('props', {}).get('custom_scrollbar_props')
                # old_scrollbar_props = data.get('old_props', {}).get('custom_scrollbar_props')

                # if new_scrollbar_props != old_scrollbar_props:
                #      command_js += f"""
                #         import('./js/customScrollBar.js').then((module) => {{
                #            window._pythra_instances = window._pythra_instances || {{}};
                #            if (window._pythra_instances['{target_id}_sb']) {{
                #                window._pythra_instances['{target_id}_sb'].destroy();
                #            }}
                #            if ({json.dumps(new_scrollbar_props)} !== null) {{ // Re-create only if new props exist
                #                window._pythra_instances['{target_id}_sb'] = new module.CustomScrollBar(
                #                    '{target_id}',
                #                    {json.dumps(new_scrollbar_props)}
                #                );
                #            }}
                #         }});
                #      """
            elif action == "MOVE":
                parent_id, before_id = data["parent_html_id"], data["before_id"]
                before_id_js = (
                    f"document.getElementById('{before_id}')" if before_id else "null"
                )
                command_js = f"""
                    var el = document.getElementById('{target_id}');
                    var p = document.getElementById('{parent_id}');
                    if (el && p) p.insertBefore(el, {before_id_js});
                """

            # --- ADD THIS NEW BLOCK ---
            elif action == "REPLACE":
                new_html_stub = data["new_html"]
                new_props = data["new_props"]
                
                # Use a robust replacement method. `outerHTML` is simple and effective.
                # It replaces the entire element, including the element itself.
                escaped_html = json.dumps(new_html_stub)[1:-1].replace("`", "\\`")

                command_js = f"""
                    var oldEl = document.getElementById('{target_id}');
                    if (oldEl) {{
                        oldEl.outerHTML = `{escaped_html}`;
                        // After replacement, we may need to apply props to the NEW element.
                        // The new element's ID is embedded in the escaped_html, so we need to find it.
                        // NOTE: This part is tricky. A simpler way for now is to bake initial props
                        // into the HTML stub (like inline styles), which our stub generator does.
                        // Complex JS initializers (like SimpleBar) would need more handling here.
                    }}
                """
                # --- ADD THIS NEW LOGIC ---
                # After replacing the HTML, we must check if the NEW widget
                # needs a JS engine and initialize it.
                
                # Check for Dropdown
                if new_props.get("init_dropdown"):
                    options_json = json.dumps(new_props.get("dropdown_options", {}))
                    # The element ID is the same, but the element itself is new.
                    command_js += f"""
                        setTimeout(() => {{
                            if (typeof PythraDropdown !== 'undefined') {{
                                console.log('Re-initializing Dropdown for #{target_id} after replacement.');
                                window._pythra_instances['{target_id}'] = new PythraDropdown('{target_id}', {options_json});
                            }}
                        }}, 0);
                    """
            # --- END OF NEW BLOCK ---
                

            elif action == "SVG_INSERT":
                parent_id = data.get("parent_html_id")  # e.g., 'svg-defs'
                html_stub = data.get("html")
                final_escaped_html = json.dumps(html_stub)[1:-1]

                command_js = f"""
                    var svgDefs = document.getElementById('{parent_id}');
                    if (svgDefs) {{
                        // Don't add if it already exists
                        if (!document.getElementById('{target_id}')) {{
                            svgDefs.insertAdjacentHTML('beforeend', `{final_escaped_html}`);
                        }}
                    }} else {{
                        console.warn('SVG defs container #{parent_id} not found for INSERT of {target_id}');
                    }}
                """
            # ... (any other patch types like SVG_INSERT) ...

            if command_js:
                # --- THIS IS THE FIX FOR THE TypeError ---
                # Helper function to recursively clean a dictionary for JSON serialization.
                def make_loggable(obj):
                    if isinstance(obj, dict):
                        # Create a new dict, processing each value.
                        return {k: make_loggable(v) for k, v in obj.items()}
                    if isinstance(obj, list):
                        # Create a new list, processing each item.
                        return [make_loggable(i) for i in obj]
                    # Replace non-serializable types with a descriptive string.
                    if (
                        callable(obj)
                        or isinstance(obj, Widget)
                        or isinstance(obj, weakref.ReferenceType)
                    ):
                        return f"<{type(obj).__name__}>"
                    # Return all other (presumably serializable) types as is.
                    return obj

                # # Create the log-safe string representation of the data.
                # loggable_data_str = json.dumps(make_loggable(data))

                is_textfield_patch = False
                if "props" in data and isinstance(data["props"], dict):
                    if "onChangedName" in data["props"]:
                        is_textfield_patch = True

                # Use the sanitized string in the catch block.
                # TODO: RECHECK AND FIX THE TRY CATCH BLOCK CAUSING UI BREAKAGE
                # print(f"Loggable Data str: [{loggable_data_str}]")
                js_commands.append(
                    
                    f"try {{ {command_js} }} catch (e) {{ console.error('Error applying patch {action} {target_id}:', e, {loggable_data_str}); }};"
                )

        if not self.called:

            self.called = True
            js_commands.insert(0, f"""
                        var vec = (p1, p2) => ({{ x: p2.x - p1.x, y: p2.y - p1.y }});
                        var magnitude = (v) => Math.sqrt(v.x ** 2 + v.y ** 2);
                        var dot = (v1, v2) => v1.x * v2.x + v1.y * v2.y;
                        var cross = (v1, v2) => v1.x * v2.y - v1.y * v2.x;
                        var round = (val) => Math.round(val * 100) / 100; // Round to 2 decimal places

                        function generateRoundedPath(points, radius) {{
                            const numPoints = points.length;
                            const cornerData = [];

                            console.log(`>>>>>> Generator Initiated <<<<<<`)

                            for (let i = 0; i < numPoints; i++) {{
                                const p_prev = points[(i + numPoints - 1) % numPoints];
                                const p_curr = points[i];
                                const p_next = points[(i + 1) % numPoints];

                                const v1 = vec(p_curr, p_prev);
                                const v2 = vec(p_curr, p_next);
                                const v1_mag = magnitude(v1);
                                const v2_mag = magnitude(v2);

                                if (v1_mag === 0 || v2_mag === 0) {{
                                    cornerData.push({{ t1: p_curr, t2: p_curr, radius: 0 }});
                                    continue;
                                }}

                                const angle = Math.acos(Math.max(-1, Math.min(1, dot(v1, v2) / (v1_mag * v2_mag))));
                                let tangentDist = radius / Math.tan(angle / 2);
                                tangentDist = Math.min(tangentDist, v1_mag / 2, v2_mag / 2);
                                const clampedRadius = Math.abs(tangentDist * Math.tan(angle / 2));

                                const t1 = {{ x: p_curr.x + (v1.x / v1_mag) * tangentDist, y: p_curr.y + (v1.y / v1_mag) * tangentDist }};
                                const t2 = {{ x: p_curr.x + (v2.x / v2_mag) * tangentDist, y: p_curr.y + (v2.y / v2_mag) * tangentDist }};

                                const sweepFlag = cross(v1, v2) < 0 ? 1 : 0;

                                cornerData.push({{ t1, t2, radius: clampedRadius, sweepFlag }});
                            }}

                            const pathCommands = [];
                            pathCommands.push(`M ${{round(cornerData[numPoints - 1].t2.x)}} ${{round(cornerData[numPoints - 1].t2.y)}}`);
                            for (let i = 0; i < numPoints; i++) {{
                                const corner = cornerData[i];
                                pathCommands.push(`L ${{round(corner.t1.x)}} ${{round(corner.t1.y)}}`);
                                pathCommands.push(`A ${{round(corner.radius)}} ${{round(corner.radius)}} 0 0 ${{corner.sweepFlag}} ${{round(corner.t2.x)}} ${{round(corner.t2.y)}}`);
                            }}
                            pathCommands.push('Z');
                            console.log(pathCommands.join(' '));
                            return pathCommands.join(' ');
                        }}


                        function scalePathAbsoluteMLA(pathStr, refW, refH, targetW, targetH, options = {{}}) {{
                        const rw = targetW / refW;
                        const rh = targetH / refH;
                        const uniformArc = !!options.uniformArc;
                        const decimalPlaces = typeof options.decimalPlaces === 'number' ? options.decimalPlaces : null;
                        const rScale = uniformArc ? Math.min(rw, rh) : null;

                        const fmt = (num) => {{
                            return decimalPlaces !== null
                            ? Number(num.toFixed(decimalPlaces)).toString()
                            : Number(num).toString();
                        }};

                        // Normalize the string
                        const s = pathStr
                            .replace(/,/g, ' ')
                            .replace(/([0-9])-/g, '$1 -')
                            .replace(/\s+/g, ' ')
                            .trim();

                        const tokenRegex = /([MLAZHV])|(-?\d*\.?\d+(?:e[-+]?\d+)?)/gi;
                        const tokens = [];
                        let match;
                        while ((match = tokenRegex.exec(s)) !== null) {{
                            tokens.push(match[1] || match[2]);
                        }}

                        const out = [];
                        let i = 0;
                        while (i < tokens.length) {{
                            const cmd = tokens[i++];
                            out.push(cmd);

                            switch (cmd) {{
                            case 'M':
                            case 'L':
                                while (i + 1 < tokens.length && !/^[MLAZHV]$/.test(tokens[i])) {{
                                const x = parseFloat(tokens[i++]) * rw;
                                const y = parseFloat(tokens[i++]) * rh;
                                out.push(fmt(x), fmt(y));
                                }}
                                break;

                            case 'A':
                                while (i + 6 < tokens.length && !/^[MLAZHV]$/.test(tokens[i])) {{
                                const rx = parseFloat(tokens[i++]);
                                const ry = parseFloat(tokens[i++]);
                                const rot = tokens[i++];
                                const laf = tokens[i++];
                                const sf = tokens[i++];
                                const x = parseFloat(tokens[i++]);
                                const y = parseFloat(tokens[i++]);

                                out.push(
                                    fmt(uniformArc ? rx * rScale : rx * rw),
                                    fmt(uniformArc ? ry * rScale : ry * rh),
                                    rot,
                                    laf,
                                    sf,
                                    fmt(x * rw),
                                    fmt(y * rh)
                                );
                                }}
                                break;

                            case 'H':
                                while (i < tokens.length && !/^[MLAZHV]$/.test(tokens[i])) {{
                                const x = parseFloat(tokens[i++]) * rw;
                                out.push(fmt(x));
                                }}
                                break;

                            case 'V':
                                while (i < tokens.length && !/^[MLAZHV]$/.test(tokens[i])) {{
                                const y = parseFloat(tokens[i++]) * rh;
                                out.push(fmt(y));
                                }}
                                break;

                            case 'Z':
                                // No coordinates to scale
                                break;

                            default:
                                console.warn('Unsupported or unexpected token:', cmd);
                            }}
                        }}

                        return out.join(' ');
                        }}

                        class ResponsiveClipPath {{
                        constructor(target, originalPath, refW, refH, options = {{}}) {{
                            this.elements = [];
                            this.orig = originalPath.trim();
                            this.refW = refW;
                            this.refH = refH;
                            this.options = options;
                            this.currentPath = "";  // ⬅️ Store last computed path string
                            this.update = this.update.bind(this);
                            this.roList = [];

                            if (typeof target === 'string') {{
                            let selector = target;
                            if (!selector.startsWith('#') && !selector.startsWith('.')) {{
                                const byId = document.getElementById(selector);
                                selector = byId ? `#${{selector}}` : `.${{selector}}`;
                            }}
                            const nodeList = document.querySelectorAll(selector);
                            if (nodeList.length === 0) {{
                                console.warn(`ResponsiveClipPath: no elements found for selector "${{selector}}"`);
                            }}
                            nodeList.forEach(el => this.elements.push(el));
                            }} else if (target instanceof HTMLElement) {{
                            this.elements.push(target);
                            }} else {{
                            console.warn('ResponsiveClipPath: invalid target', target);
                            }}

                            this.elements.forEach(el => this.initElement(el));
                        }}

                        initElement(el) {{
                            this.applyClip(el);
                            if (window.ResizeObserver) {{
                            const ro = new ResizeObserver(() => this.applyClip(el));
                            ro.observe(el);
                            this.roList.push({{ el, ro }});
                            }} else {{
                            window.addEventListener('resize', this.update);
                            }}
                        }}

                        applyClip(el) {{
                            const rect = el.getBoundingClientRect();
                            const newPath = scalePathAbsoluteMLA(
                            this.orig,
                            this.refW,
                            this.refH,
                            rect.width,
                            rect.height,
                            this.options
                            );
                            this.currentPath = `path("${{newPath}}")`;  // ⬅️ Save it
                            el.style.clipPath = this.currentPath;
                            el.style.webkitClipPath = this.currentPath;
                        }}

                        update() {{
                            this.elements.forEach(el => this.applyClip(el));
                        }}

                        disconnect() {{
                            this.roList.forEach(({{ el, ro }}) => ro.unobserve(el));
                            this.roList = [];
                            window.removeEventListener('resize', this.update);
                        }}

                        // ✅ Your new method
                        getResponsivePath() {{
                            return this.currentPath;
                        }}
                        }}

                        class PythraDropdown {{
                            constructor(elementId, options) {{
                                this.container = document.getElementById(elementId);
                                if (!this.container) {{
                                    console.error(`Dropdown container with ID #${{elementId}} not found.`);
                                    return;
                                }}

                                console.log(`✅ PythraDropdown engine is initializing for #${{elementId}}`);

                                this.options = options;
                                this.valueContainer = this.container.querySelector('.dropdown-value-container');
                                this.menu = this.container.querySelector('.dropdown-menu');
                                this.items = this.menu.querySelectorAll('.dropdown-item');

                                // Bind 'this' to maintain context in event handlers
                                this.toggleMenu = this.toggleMenu.bind(this);
                                this.handleItemClick = this.handleItemClick.bind(this);
                                this.handleClickOutside = this.handleClickOutside.bind(this);

                                // Attach event listeners
                                this.valueContainer.addEventListener('click', this.toggleMenu);
                                this.items.forEach(item => {{
                                    item.addEventListener('click', this.handleItemClick);
                                }});
                            }}

                            toggleMenu(event) {{
                                event.stopPropagation(); // Prevent click from bubbling to the document
                                const isCurrentlyOpen = this.container.classList.toggle('open');
                                console.log("Value container Clicked");
                                
                                if (isCurrentlyOpen) {{
                                    // If we just opened the menu, listen for clicks outside to close it
                                    document.addEventListener('click', this.handleClickOutside);
                                }} else {{
                                    // If we just closed it, stop listening
                                    document.removeEventListener('click', this.handleClickOutside);
                                }}
                            }}

                            handleItemClick(event) {{
                                const selectedValue = event.currentTarget.dataset.value;
                                const selectedLabel = event.currentTarget.textContent;

                                console.log("Dropdown option Clicked");
                                
                                // 1. Update the display value immediately for instant feedback
                                this.valueContainer.querySelector('span').textContent = selectedLabel;
                                
                                // 2. Send the selected *value* back to the Python backend
                                if (window.pywebview && this.options.onChangedName) {{
                                    window.pywebview.on_input_changed(this.options.onChangedName, selectedValue);
                                }}
                                
                                // 3. Close the menu
                                this.closeMenu();
                            }}
                            
                            closeMenu() {{
                                if (this.container.classList.contains('open')) {{
                                    this.container.classList.remove('open');
                                    document.removeEventListener('click', this.handleClickOutside);
                                }}
                            }}

                            handleClickOutside(event) {{
                                // If the click is outside the main container, close the menu
                                if (!this.container.contains(event.target)) {{
                                    this.closeMenu();
                                }}
                            }}

                            destroy() {{
                                // Cleanup to prevent memory leaks
                                if (!this.container) return;
                                this.valueContainer.removeEventListener('click', this.toggleMenu);
                                this.items.forEach(item => {{
                                    item.removeEventListener('click', this.handleItemClick);
                                }});
                                document.removeEventListener('click', this.handleClickOutside);
                            }}
                        }}
                        /**
                        * PythraGestureDetector: A client-side engine for a feature-rich gesture detector.
                        *
                        * It uses Pointer Events to handle mouse and touch统一. It disambiguates between
                        * taps, double taps, long presses, and panning gestures.
                        */
                        class PythraGestureDetector {{
                            constructor(elementId, options) {{
                                this.element = document.getElementById(elementId);
                                if (!this.element) {{
                                    console.error(`GestureDetector element with ID #${{elementId}} not found.`);
                                    return;
                                }}

                                this.options = options;

                                // --- Gesture State ---
                                this.lastTapTime = 0;
                                this.tapTimeout = null;
                                this.longPressTimeout = null;
                                this.isPanning = false;
                                this.panStartPoint = {{ x: 0, y: 0 }};
                                this.panThreshold = 5; // Pixels to move before a pan is detected

                                // --- Bind Handlers ---
                                this.handlePointerDown = this.handlePointerDown.bind(this);
                                this.handlePointerMove = this.handlePointerMove.bind(this);
                                this.handlePointerUp = this.handlePointerUp.bind(this);
                                this.fireTap = this.fireTap.bind(this);
                                this.fireLongPress = this.fireLongPress.bind(this);

                                // Attach the entry-point event listener
                                this.element.addEventListener('pointerdown', this.handlePointerDown);
                            }}

                            handlePointerDown(event) {{
                                // Only respond to the primary button (e.g., left mouse click)
                                if (event.button !== 0) return;

                                const currentTime = Date.now();

                                // --- Double Tap Detection ---
                                if (currentTime - this.lastTapTime < 300) {{ // 300ms window for double tap
                                    clearTimeout(this.tapTimeout);
                                    this.tapTimeout = null;
                                    this.lastTapTime = 0;
                                    if (this.options.onDoubleTapName) {{
                                        window.pywebview.on_gesture_event(this.options.onDoubleTapName, {{}});
                                    }}
                                    return;
                                }}
                                
                                this.lastTapTime = currentTime;
                                this.panStartPoint = {{ x: event.clientX, y: event.clientY }};

                                // --- Long Press Detection ---
                                if (this.options.onLongPressName) {{
                                    this.longPressTimeout = setTimeout(() => this.fireLongPress(), 500); // 500ms for long press
                                }}

                                // --- Single Tap Detection (will be fired later if not cancelled) ---
                                if (this.options.onTapName) {{
                                    this.tapTimeout = setTimeout(() => this.fireTap(), 300);
                                }}

                                // Listen for move/up on the entire document for robust dragging
                                document.addEventListener('pointermove', this.handlePointerMove);
                                document.addEventListener('pointerup', this.handlePointerUp);
                                document.addEventListener('pointercancel', this.handlePointerUp); // Treat cancel like up
                            }}

                            handlePointerMove(event) {{
                                if (this.isPanning) {{
                                    // --- Continue Panning ---
                                    const dx = event.clientX - this.panStartPoint.x;
                                    const dy = event.clientY - this.panStartPoint.y;
                                    if (this.options.onPanUpdateName) {{
                                        window.pywebview.on_gesture_event(this.options.onPanUpdateName, {{ dx, dy }});
                                    }}
                                }} else {{
                                    // --- Check if a Pan has Started ---
                                    const dx = event.clientX - this.panStartPoint.x;
                                    const dy = event.clientY - this.panStartPoint.y;
                                    if (Math.sqrt(dx * dx + dy * dy) > this.panThreshold) {{
                                        this.isPanning = true;
                                        // A pan gesture cancels tap and long press
                                        clearTimeout(this.tapTimeout);
                                        this.tapTimeout = null;
                                        clearTimeout(this.longPressTimeout);
                                        this.longPressTimeout = null;
                                        
                                        if (this.options.onPanStartName) {{
                                            window.pywebview.on_gesture_event(this.options.onPanStartName, {{}});
                                        }}
                                    }}
                                }}
                            }}

                            handlePointerUp(event) {{
                                // Clean up document-level listeners immediately
                                document.removeEventListener('pointermove', this.handlePointerMove);
                                document.removeEventListener('pointerup', this.handlePointerUp);
                                document.removeEventListener('pointercancel', this.handlePointerUp);

                                // Always clear a pending long press if pointer is lifted
                                clearTimeout(this.longPressTimeout);
                                this.longPressTimeout = null;
                                
                                if (this.isPanning) {{
                                    // --- End Panning ---
                                    this.isPanning = false;
                                    if (this.options.onPanEndName) {{
                                        window.pywebview.on_gesture_event(this.options.onPanEndName, {{}});
                                    }}
                                }}
                            }}

                            fireTap() {{
                                if (this.tapTimeout){{ // Ensure it wasn't cancelled
                                    this.tapTimeout = null;
                                    if (this.options.onTapName) {{
                                        window.pywebview.on_gesture_event(this.options.onTapName, {{}});
                                    }}
                                }}
                            }}
                            
                            fireLongPress() {{
                                // A long press cancels a single tap
                                clearTimeout(this.tapTimeout);
                                this.tapTimeout = null;
                                this.lastTapTime = 0; // Prevent next tap from being a double tap
                                
                                if (this.longPressTimeout) {{
                                    this.longPressTimeout = null;
                                    if (this.options.onLongPressName) {{
                                        window.pywebview.on_gesture_event(this.options.onLongPressName, {{}});
                                    }}
                                }}
                            }}

                            destroy() {{
                                if (!this.element) return;
                                this.element.removeEventListener('pointerdown', this.handlePointerDown);
                                this.handlePointerUp(); // Ensure document listeners are cleaned up
                                clearTimeout(this.tapTimeout);
                                clearTimeout(this.longPressTimeout);
                            }}
                        }}
                        /**
                        * PythraGradientClipPath: Client-side engine for creating an animated
                        * gradient border around a complex clip-path shape.
                        */
                        //import {{ generateRoundedPath }} from './pathGenerator.js';

                        // Helper function for basic vector math
                        const vec_gradient_border = (p1, p2) => ({{ x: p2.x - p1.x, y: p2.y - p1.y }});
                        const magnitude_gradient_border = (v) => Math.sqrt(v.x * v.x + v.y * v.y);
                        const normalize_gradient_border = (v) => {{
                            const mag = magnitude_gradient_border(v);
                            return mag > 0 ? {{ x: v.x / mag, y: v.y / mag }} : {{ x: 0, y: 0 }};
                        }};
                        const dot_gradient_border = (v1, v2) => v1.x * v2.x + v1.y * v2.y;

                        /**
                        * Calculates a new set of points offset outwards from the original polygon.
                        * @param {{Array<Object>}} points - The original points, e.g., [{{x: 0, y: 0}}, ...].
                        * @param {{number}} offset - The distance to offset the points outwards.
                        * @returns {{Array<Object>}} The new, offset points.
                        */
                        function offsetPoints(points, offset) {{
                            const numPoints = points.length;
                            if (numPoints < 3) return points;

                            const offsetPoints = [];

                            for (let i = 0; i < numPoints; i++) {{
                                const p_prev = points[(i + numPoints - 1) % numPoints];
                                const p_curr = points[i];
                                const p_next = points[(i + 1) % numPoints];

                                const v1 = normalize_gradient_border(vec_gradient_border(p_curr, p_prev));
                                const v2 = normalize_gradient_border(vec_gradient_border(p_curr, p_next));

                                // Calculate the angle bisector vector (points outwards for convex shapes)
                                const bisector = normalize_gradient_border({{ x: v1.x + v2.x, y: v1.y + v2.y }});

                                // Calculate the angle between the two edge vectors
                                const angle = Math.acos(dot_gradient_border(v1, v2));

                                // Use trigonometry to find the length to move along the bisector
                                // to achieve the desired perpendicular offset distance.
                                const distance = offset / Math.sin(angle / 2);

                                if (isNaN(distance) || !isFinite(distance)) {{
                                    // Handle collinear points (angle is ~PI), just move along the normal
                                    const normal = {{ x: -v1.y, y: v1.x }};
                                    offsetPoints.push({{ x: p_curr.x + normal.x * offset, y: p_curr.y + normal.y * offset }});
                                }} else {{
                                    offsetPoints.push({{ x: p_curr.x + bisector.x * distance, y: p_curr.y + bisector.y * distance }});
                                }}
                            }}
                            return offsetPoints;
                        }}


                        class PythraGradientClipPath {{
                            constructor(elementId, options) {{
                                this.container = document.getElementById(elementId);
                                if (!this.container) {{
                                    console.error(`GradientClipPath container with ID #${{elementId}} not found.`);
                                    return;
                                }}

                                console.log(`✅ PythraGradientClipPath engine is initializing for #${{elementId}}`);
                                
                                // --- Setup DOM Structure ---
                                // The reconciler placed the child widget inside our container.
                                // We need to wrap it and add a background element.
                                this.backgroundEl = document.createElement('div');
                                this.backgroundEl.className = 'gradient-clip-background';
                                
                                this.contentHost = document.createElement('div');
                                this.contentHost.className = 'gradient-clip-content-host';

                                // Move the original child from the container into the new host
                                while (this.container.firstChild) {{
                                    this.contentHost.appendChild(this.container.firstChild);
                                }}
                                
                                this.container.appendChild(this.backgroundEl);
                                this.container.appendChild(this.contentHost);
                                
                                // --- Generate and Apply Paths ---
                                this.options = options;
                                this.update = this.update.bind(this);
                                
                                // Use a ResizeObserver to make it fully responsive
                                this.ro = new ResizeObserver(this.update);
                                this.ro.observe(this.container);
                                
                                // Initial update
                                this.update();
                            }}

                            update() {{
                                const rect = this.container.getBoundingClientRect();
                                if (rect.width === 0 || rect.height === 0) return;

                                const {{ points, radius, viewBox, borderWidth }} = this.options;
                                const jsPoints = points.map(p => ({{ x: p[0], y: p[1] }}));

                                // 1. Generate the inner path for the content
                                const innerPathStr = generateRoundedPath(jsPoints, radius);
                                const innerClipPath = `path("${{innerPathStr}}")`;

                                // 2. Calculate offset points and a larger radius for the outer path
                                const offset_points = offsetPoints(jsPoints, borderWidth);
                                const outerRadius = radius + borderWidth;
                                const outerPathStr = generateRoundedPath(offset_points, outerRadius);
                                const outerClipPath = `path("${{outerPathStr}}")`;

                                // 3. Apply the responsive clip-paths to the elements
                                // We don't need ResponsiveClipPath class here because we update on every resize.
                                this.contentHost.style.clipPath = innerClipPath;
                                this.contentHost.style.webkitClipPath = innerClipPath;
                                
                                this.backgroundEl.style.clipPath = outerClipPath;
                                this.backgroundEl.style.webkitClipPath = outerClipPath;
                            }}

                            destroy() {{
                                if (this.ro && this.container) {{
                                    this.ro.unobserve(this.container);
                                }}
                            }}
                        }}
                        /**
                        * PythraVirtualList: A client-side engine for virtual scrolling. (Final Version)
                        *
                        * This engine creates its own SimpleBar instance to avoid race conditions.
                        * It handles pre-rendered initial items (HTML and CSS) for an instant first paint.
                        * It asynchronously fetches additional items from Python as the user scrolls.
                        * Most importantly, it dynamically attaches event listeners to both pre-rendered
                        * and asynchronously loaded content to ensure full interactivity.
                        */
                        class PythraVirtualList {{
                            constructor(elementId, options) {{
                                this.container = document.getElementById(elementId);
                                if (!this.container) {{
                                    console.error(`VirtualList Error: Container element #${{elementId}} not found.`);
                                    return;
                                }}

                                console.log(`✅ PythraVirtualList engine is initializing for #${{elementId}}`);
                                
                                this.options = options;
                                this.simplebar = new SimpleBar(this.container, this.options.simplebarOptions || {{}});
                                this.scrollEl = this.simplebar.getScrollElement();
                                this.contentEl = this.simplebar.getContentElement();
                                
                                this.itemCache = {{}}; // Cache will ONLY store HTML strings.
                                this.visibleItemElements = [];

                                // Process the initialItems object from Python.
                                if (this.options.initialItems) {{
                                    const initialCss = new Set();
                                    for (const index in this.options.initialItems) {{
                                        const itemData = this.options.initialItems[index];
                                        // 1. Store ONLY the HTML string in the cache.
                                        this.itemCache[index] = itemData.html;
                                        // 2. Collect all unique CSS rules.
                                        if (itemData.css) {{
                                            initialCss.add(itemData.css);
                                        }}
                                    }}
                                    // 3. Inject all collected CSS into the dynamic stylesheet in one go.
                                    if (initialCss.size > 0) {{
                                        const styleSheet = document.getElementById('dynamic-styles');
                                        if (styleSheet) {{
                                            styleSheet.textContent += `\n${{[...initialCss].join('\\n')}}`;
                                        }}
                                    }}
                                }}

                                // Setup DOM for virtualization
                                this.sizer = document.createElement('div');
                                this.sizer.style.position = 'absolute';
                                this.sizer.style.top = '0';
                                this.sizer.style.left = '0';
                                this.sizer.style.width = '1px';
                                this.sizer.style.height = `${{this.options.itemCount * this.options.itemExtent}}px`;
                                this.contentEl.appendChild(this.sizer);
                                this.contentEl.style.position = 'relative';

                                this.render = this.render.bind(this);
                                this.scrollEl.addEventListener('scroll', this.render);
                                
                                this.render();
                            }}

                            /**
                            * Scans a newly rendered HTML fragment and attaches reliable event listeners
                            * to elements that have an inline `onclick` attribute from the Python side.
                            * @param {{HTMLElement}} element - The container element whose children to scan (e.g., the recycled list item div).
                            */
                            attachEventListeners(element) {{
                                const clickableElements = element.querySelectorAll('[onclick]');
                                clickableElements.forEach(clickable => {{
                                    const onclickAttr = clickable.getAttribute('onclick');
                                    
                                    // Regex to parse out the callback name from "handleClick('callback_name')"
                                    const match = onclickAttr.match(/handleClick\('([^']+)'\)/);

                                    if (match && match[1]) {{
                                        const callbackName = match[1];
                                        // 1. Remove the inline attribute, as it's now redundant and less reliable.
                                        clickable.removeAttribute('onclick');
                                        // 2. Add a proper, trusted event listener.
                                        clickable.addEventListener('click', () => {{
                                            if (window.pywebview && typeof handleClick === 'function') {{
                                                // 3. Call the global handleClick function that communicates with Python.
                                                handleClick(callbackName);
                                            }}
                                        }});
                                    }}
                                }});
                            }}

                            render() {{
                                const scrollTop = this.scrollEl.scrollTop;
                                const viewportHeight = this.scrollEl.clientHeight;

                                const startIndex = Math.max(0, Math.floor(scrollTop / this.options.itemExtent));
                                const endIndex = Math.min(
                                    this.options.itemCount - 1,
                                    Math.ceil((scrollTop + viewportHeight) / this.options.itemExtent)
                                );
                                
                                const itemsToRender = [];
                                for (let i = startIndex; i <= endIndex; i++) {{
                                    itemsToRender.push({{ index: i, top: i * this.options.itemExtent }});
                                }}
                                
                                for (let i = 0; i < itemsToRender.length; i++) {{
                                    const item = itemsToRender[i];
                                    let el = this.visibleItemElements[i];

                                    if (!el) {{
                                        el = document.createElement('div');
                                        el.style.position = 'absolute';
                                        el.style.width = '100%';
                                        el.style.height = `${{this.options.itemExtent}}px`;
                                        el.style.left = '0';
                                        this.contentEl.appendChild(el);
                                        this.visibleItemElements.push(el);
                                    }}

                                    el.style.transform = `translateY(${{item.top}}px)`;
                                    
                                    if (el.dataset.index !== String(item.index)) {{
                                        el.dataset.index = item.index;
                                        
                                        if (this.itemCache[item.index]) {{
                                            // Item was pre-rendered or fetched before.
                                            el.innerHTML = this.itemCache[item.index];
                                            // IMPORTANT: We must re-attach listeners every time we set innerHTML.
                                            this.attachEventListeners(el);
                                        }} else {{
                                            // Item needs to be fetched from Python.
                                            el.innerHTML = '<div>Loading...</div>';
                                            if (window.pywebview && this.options.itemBuilderName) {{
                                                window.pywebview.build_list_item(this.options.itemBuilderName, item.index)
                                                    .then(response => {{
                                                        const {{ html, css }} = response;
                                                        this.itemCache[item.index] = html;

                                                        if (css) {{
                                                            const styleSheet = document.getElementById('dynamic-styles');
                                                            if (styleSheet && !styleSheet.textContent.includes(css)) {{
                                                                styleSheet.textContent += `\n${{css}}`;
                                                            }}
                                                        }}
                                                        
                                                        if (el.dataset.index === String(item.index)) {{
                                                            el.innerHTML = html;
                                                            // Attach event listeners to the newly created DOM nodes.
                                                            this.attachEventListeners(el);
                                                        }}
                                                    }})
                                                    .catch(e => {{
                                                        console.error(`Error building virtual item ${{item.index}}:`, e);
                                                        if (el.dataset.index === String(item.index)) {{
                                                            el.innerHTML = '<div>Error</div>';
                                                        }}
                                                    }});
                                            }}
                                        }}
                                    }}
                                }}
                                
                                for (let i = itemsToRender.length; i < this.visibleItemElements.length; i++) {{
                                    this.visibleItemElements[i].style.transform = 'translateY(-9999px)';
                                }}
                            }}

                            /**
                            * Called from Python when the underlying data for the list has changed.
                            * Clears the cache and forces a re-render of all visible items.
                            */
                            refresh() {{
                                console.log(`Refreshing VirtualList for #${{this.container.id}}`);
                                // 1. Clear the entire HTML cache.
                                this.itemCache = {{}};
                                
                                // 2. Mark all currently visible DOM elements as "dirty" by resetting their data-index.
                                this.visibleItemElements.forEach(el => {{
                                    el.dataset.index = '-1'; // Set to an invalid index
                                }});
                                
                                // 3. Trigger a render to fetch the new, updated content.
                                this.render();
                            }}

                            /**
                            * Refreshes specific items by their indices. Highly efficient.
                            * @param {{Array<number>}} indices - An array of item indices to refresh.
                            */
                            refreshItems(indices) {{
                                if (!Array.isArray(indices)) return;
                                console.log(`Refreshing specific items for #${{this.container.id}}:`, indices);

                                indices.forEach(index => {{
                                    // 1. Invalidate the cache for this specific item.
                                    if (this.itemCache[index]) {{
                                        delete this.itemCache[index];
                                    }}
                                    
                                    // 2. Find if this item is currently visible in the DOM.
                                    const visibleElement = this.visibleItemElements.find(el => el.dataset.index === String(index));
                                    
                                    if (visibleElement) {{
                                        // 3. If it's visible, mark it as dirty so the next render pass will update it.
                                        visibleElement.dataset.index = '-1';
                                    }}
                                }});

                                // 4. Trigger a render pass to update any newly dirtied elements.
                                this.render();
                            }}
                            
                            // --- END OF NEW LOGIC ---

                            destroy() {{
                                if (this.simplebar && typeof this.simplebar.unMount === 'function') {{
                                    this.simplebar.unMount();
                                }}
                            }}
                        }}
                        """)
                # js_commands.append(f"console.log('Applying patch {action} {target_id}:', {loggable_data_str});")
                # --- END OF FIX ---
            # print(js_commands)
        return "\n".join(js_commands)

    def _generate_prop_update_js(
        self, target_id: str, props: Dict, is_insert: bool = False
    ) -> str:
        """Generates specific JS commands for updating element properties."""
        js_prop_updates = []
        style_updates = {}
        element_var = "insertedEl" if is_insert else "elToUpdate"

        # --- Special handling for TextField value to prevent cursor jumping ---
        # if props.get('onChangedName'): # A good heuristic for input-like elements
        #      new_value = props.get('value', '')
        #      # Only update the value if it's different. This is crucial for focus.
        #      js_prop_updates.append(f"if ({element_var}.value !== {json.dumps(new_value)}) {{ console.log({element_var}); {element_var}.value = {json.dumps(new_value)}; }};")
        # ---

        for key, value in props.items():
            # if key == 'value' and 'onChangedName' in props:
            #     # For TextField, we target the inner <input> element directly.
            #     input_element_selector = f"document.getElementById('{target_id}_input')"
            #     js_prop_updates.append(f"var inputEl = {input_element_selector}; if(inputEl) inputEl.value = {json.dumps(value)};")
            # print("Props:", props)

            if key == "data":
                js_prop_updates.append(
                    f"{element_var}.textContent = {json.dumps(str(value))};"
                )
                # print("data: ",value)
            # --- THIS IS THE NEW, INTELLIGENT CLASS UPDATE LOGIC ---
            elif key == "css_class":
                # We need the old shared class to remove it. This must be passed in the patch.
                # Let's assume the patch data for an UPDATE now contains:
                # data['props']['css_class'] -> new_class
                # data['old_props']['css_class'] -> old_class
                
                old_class = props.get("old_shared_class") # We'll need to add this to the patch
                new_class = value # The new shared class

                # This JS is robust: it works even if classes are None or the same.
                js_prop_updates.append(f"""
                    if ("{old_class}" !== "{new_class}") {{
                        if ("{old_class}" && {element_var}.classList.contains("{old_class}")) {{
                            {element_var}.classList.remove("{old_class}");
                        }}
                        if ("{new_class}") {{
                            {element_var}.classList.add("{new_class}");
                        }}
                    }}
                """)
            # --- END OF NEW LOGIC ---
            elif key == "src":
                js_prop_updates.append(f"{element_var}.src = {json.dumps(value)};")
            elif key == "tooltip":
                js_prop_updates.append(f"{element_var}.title = {json.dumps(value)};")
            
            elif key == "value" and "textfield" in props.get(
                "css_class", ""
            ):
                # This is a value update for a TextField. Target the inner input.
                
                input_id = f"{target_id}_input"
                # --- ADD DETAILED LOGGING ---
                js_prop_updates.append(f"""
                    var inputEl = document.getElementById('{input_id}');
                    if (inputEl) {{
                        console.log('--- TextField Update Patch ---');
                        console.log('Target Input ID:', '{input_id}');
                        console.log('Current Browser Value:', inputEl.value);
                        console.log('New Value from Python:', {json.dumps(str(value))});
                        if (inputEl.value !== {json.dumps(str(value))}) {{
                            console.log('Values are different. Applying update.');
                            inputEl.value = {json.dumps(str(value))};
                        }} else {{
                            console.log('Values are the same. Skipping update to prevent cursor jump.');
                        }}
                    }} else {{
                        console.error('Could not find input element with ID:', '{input_id}');
                    }}
                """)
                # --- END OF LOGGING ---

            elif key == "errorText" and "textfield-root-container" in props.get(
                "css_class", ""
            ):
                # This is an errorText update for a TextField. Target the helper div.
                helper_id = f"{target_id}_helper"
                js_prop_updates.append(
                    f"var helperEl = document.getElementById('{helper_id}'); if(helperEl) helperEl.textContent = {json.dumps(str(value))};"
                )

            # elif key == 'value' and 'onChangedName' in props: # Check if it's a TextField
            #         input_element = f"document.getElementById('{target_id}_input')" if not is_insert else f"{element_var}.querySelector('.textfield-input')"
            #         js_prop_updates.append(f"var inputEl = {input_element}; if(inputEl && inputEl.value !== {json.dumps(value)}) {{ inputEl.value = {json.dumps(value)}; }}")

            # Direct style props (use sparingly)
            elif key == "color":
                style_updates["color"] = value
            elif key == "backgroundColor":
                style_updates["backgroundColor"] = value
            elif key == "width" and value is not None:
                style_updates["width"] = (
                    f"{value}px" if isinstance(value, (int, float)) else value
                )
            elif key == "height" and value is not None:
                style_updates["height"] = (
                    f"{value}px" if isinstance(value, (int, float)) else value
                )
            elif key == "aspectRatio":
                style_updates["aspect-ratio"] = value
            elif key == "clip_path_string":
                style_updates["clip-path"] = value

        # Handle the 'style' dictionary passed from render_props
        if "style" in props and isinstance(props["style"], dict):
            for style_key, style_value in props["style"].items():
                # print("style_key: ",style_key,"style_value: ",style_value)
                # Convert camelCase to kebab-case for CSS
                css_prop_kebab = "".join(
                    ["-" + c.lower() if c.isupper() else c for c in style_key]
                ).lstrip("")
                # print("css_prop_kebab: ", css_prop_kebab, f"{json.dumps(style_value)}")
                if css_prop_kebab == "--slider-percentage" and props["isDragEnded"]:
                    print("drag css", props["isDragEnded"])
                    js_prop_updates.append(
                        f"{element_var}.style.setProperty('{css_prop_kebab}', {json.dumps(style_value)});"
                    )
                elif css_prop_kebab == "--slider-percentage" and not props["isDragEnded"]:
                    print("drag css", props["isDragEnded"])
                elif css_prop_kebab != "--slider-percentage" and "isDragEnded" not in props:
                    js_prop_updates.append(
                        f"{element_var}.style.setProperty('{css_prop_kebab}', {json.dumps(style_value)});"
                    )
        # --- END OF ADDITION ---

        # --- NEW: Apply _style_override from the widget instance ---
        # We need the widget instance to get the override
        # This assumes the reconciler includes it in the patch data (we'll ensure this next)
        widget_instance = props.get("widget_instance")
        if widget_instance and hasattr(widget_instance, "_style_override"):
            for style_key, style_value in widget_instance._style_override.items():
                style_updates[style_key] = style_value
                # print("Style Value Init: ", style_value)

        # Handle style dict passed from widgets like ListTile
        if "style" in props and isinstance(props["style"], dict):
            for style_key, style_value in props["style"].items():
                style_updates[style_key] = style_value

        if style_updates:
            for prop, val in style_updates.items():
                css_prop_kebab = "".join(
                    ["-" + c.lower() if c.isupper() else c for c in prop]
                ).lstrip("-")
                js_prop_updates.append(
                    f"{element_var}.style.setProperty('{css_prop_kebab}', {json.dumps(val)});"
                )

        return "\n".join(js_prop_updates)

    def _generate_initial_js_script(self, result: 'ReconciliationResult') -> str:
        """Generates a script tag to run initializations after the DOM loads."""
        if not result.js_initializers:
            return ""

        js_commands = []
        imports = set()

        for node_data in result.new_rendered_map.values():
            props = node_data.get("props", {})
            html_id = node_data.get("html_id")
            # print(">>>init_slider<<<", html_id)
            widget_instance = node_data.get("widget_instance")

            # --- THE FIX ---
            # Use the widget's key for a stable instance name.
            if widget_instance and widget_instance.key:
                widget_key_val = widget_instance.key.value
            else:
                # Fallback, though widgets with controllers should always have keys.
                widget_key_val = html_id
            # --- END OF FIX ---

            # --- ADD THIS BLOCK ---
            if props.get("init_gradient_clip_border"):
                imports.add("import { PythraGradientClipPath } from './js/gradient_border.js';")
                imports.add("import { generateRoundedPath } from './js/pathGenerator.js';")
                options = props.get("gradient_clip_options", {})
                options_json = json.dumps(options)
                js_commands.append(f"window._pythra_instances['{html_id}'] = new PythraGradientClipPath('{html_id}', {options_json});")
            # --- END OF BLOCK ---

            # --- ADD THIS BLOCK ---
            # --- SIMPLIFIED VLIST LOGIC ---
            if props.get("init_virtual_list"):
                imports.add("import { PythraVirtualList } from './js/virtual_list.js';")
                options = props.get("virtual_list_options", {})
                options_json = json.dumps(options)
                # Use the stable key for the instance name
                instance_name = f"{widget_key_val}_vlist"
                # No more checks or timeouts. We just instantiate our engine.
                js_commands.append(f"window._pythra_instances['{instance_name}'] = new PythraVirtualList('{html_id}', {options_json});")
            # --- END OF CHANGE ---
            # --- END OF BLOCK ---

            # --- ADD THIS BLOCK ---
            if props.get("init_gesture_detector"):
                imports.add("import { PythraGestureDetector } from './js/gesture_detector.js';")
                options = props.get("gesture_options", {})
                options_json = json.dumps(options)
                print("options: ", options_json)
                js_commands.append(f"window._pythra_instances['{html_id}'] = new PythraGestureDetector('{html_id}', {options_json});")
            # --- END OF BLOCK ---

            # --- ADD THIS BLOCK ---
            if props.get("init_dropdown"):
                imports.add("import { PythraDropdown } from './js/dropdown.js';")
                options = props.get("dropdown_options", {})
                options_json = json.dumps(options)
                js_commands.append(f"window._pythra_instances['{html_id}'] = new PythraDropdown('{html_id}', {options_json});")
            # --- END OF BLOCK ---

            # Check for our new Slider's flag
            if props.get("init_slider"):
                # print(">>>init_slider<<<", html_id)
                imports.add("import { PythraSlider } from './js/slider.js';")
                options = props.get("slider_options", {})
                options_json = json.dumps(options)
                
                # Generate the JS command to instantiate the slider engine
                js_commands.append(f"""
                    if (typeof PythraSlider !== 'undefined') {{
                        // Make sure we don't re-initialize if it somehow already exists
                        if (!window._pythra_instances['{html_id}']) {{
                            console.log('Initializing PythraSlider for #{html_id}');
                            window._pythra_instances['{html_id}'] = new PythraSlider('{html_id}', {options_json});
                        }}
                    }} else {{
                        console.error('PythraSlider class not found. Make sure slider.js is included.');
                    }}
                """)
        # --- END OF NEW LOGIC ---
        # Your initializer logic for ClipPath etc. goes here if needed
        for init in result.js_initializers:
            # --- ADD THIS BLOCK FOR SIMPLEBAR ---
            if init["type"] == "SimpleBar":
                target_id = init["target_id"]
                # We can pass options from Python to the SimpleBar constructor
                options_json = json.dumps(init.get("options", {}))
                js_commands.append(
                    f"""
                    const el_{target_id} = document.getElementById('{target_id}');
                    if (el_{target_id} && !el_{target_id}.simplebar) {{ // Check if not already initialized
                        new SimpleBar(el_{target_id}, {options_json} );
                        console.log('SimpleBar initialized for #{target_id}');
                        //console.log(!el_{target_id}.simplebar);
                    }};
                    
                """
                )
            # --- END OF NEW BLOCK ---

             # --- ADD THIS NEW BLOCK for the slider ---
            if init.get("type") == "_RenderableSlider":
                
                target_id = init["target_id"]
                options_json = json.dumps(init.get("options", {}))
                # This JS command creates a new instance of our slider engine
                js_commands.append(f"""
                    if (typeof PythraSlider !== 'undefined') {{
                        window._pythra_instances['{target_id}'] = new PythraSlider('{target_id}', {options_json});
                    }} else {{
                        console.error('PythraSlider class not found. Make sure slider.js is included.');
                    }}
                """)
            # --- END OF NEW SLIDER BLOCK ---

            if init["type"] == "VirtualList":
                target_id = init["target_id"]
                estimated_height = init["estimated_height"]
                item_count = init["item_count"]
                js_commands.append(
                    f"""
                    const VlistId = "{target_id}";          // same key used above
                    const count = {item_count};             // reconciler can inject this
                    const estimate = {estimated_height};                        // same as Python

                    new VirtualList(
                    VlistId,
                    count,
                    estimate,
                    (i) => {{
                        // reconciler will create the actual DOM for row `i`
                        // we just need the component to be ready; reconciler patches
                        // the inner content later.
                        const div = document.createElement("div");
                        div.dataset.index = i;
                        return div;
                    }}
                    );
                """
                )

            if init["type"] == "ResponsiveClipPath":
                imports.add(
                    "import { generateRoundedPath } from './js/pathGenerator.js';"
                )
                imports.add(
                    "import { ResponsiveClipPath } from './js/clipPathUtils.js';"
                )
                target_id = init["target_id"]
                clip_data = init["data"]
                # print("target id: ", target_id, "Data: ", clip_data)

                # Serialize the Python data into JSON strings for JS
                points_json = json.dumps(clip_data["points"])
                radius_json = json.dumps(clip_data["radius"])
                ref_w_json = json.dumps(clip_data["viewBox"][0])
                ref_h_json = json.dumps(clip_data["viewBox"][1])

                # This JS code performs the exact two-step process you described.
                js_commands.append(
                    f"""
                    // Step 0: Convert Python's array-of-arrays to JS's array-of-objects
                    const pointsForGenerator_{target_id} = {points_json}.map(p => ({{x: p[0], y: p[1]}}));
                    
                    // Step 1: Call generateRoundedPath with the points and radius
                    const initialPathString_{target_id} = generateRoundedPath(pointsForGenerator_{target_id}, {radius_json});
                    
                    // Step 2: Feed the generated path into ResponsiveClipPath
                    window._pythra_instances['{target_id}'] = new ResponsiveClipPath(
                        '{target_id}', 
                        initialPathString_{target_id}, 
                        {ref_w_json}, 
                        {ref_h_json}, 
                        {{ uniformArc: true, decimalPlaces: 2 }}
                    );
                """
                )

            # elif init['type'] == 'ScrollBar':
            #     imports.add("import { CustomScrollBar } from './js/scrollBar.js';")
            #     target_id = init['target_id']
            #     scroll_bar_id = init['data']['scroll_bar_id']
            #     scroll_thumb_id = init['data']['scroll_thumb_id']

            #     js_commands.append(f"""
            #         window._pythra_instances['{scroll_bar_id}'] = new CustomScrollBar(
            #             '{target_id}',
            #             '{scroll_bar_id}',
            #             '{scroll_thumb_id}'
            #         );
            #     """)
        # 2. --- THIS IS THE NEW, SMARTER LOGIC ---
        #    Iterate through the entire rendered map to find any widget that
        #    has declared it needs JS initialization via a flag in its render_props.
        # print("mapp: ",result.new_rendered_map.values())
        

        # 1. Get the combined source code of all utility JS files.
        js_utilities = self._get_js_utility_functions()
        # Wrap all commands in a DOMContentLoaded listener.
        # We now import BOTH of your utility modules.
        # print("utilities: ", js_utilities)
        full_script = f"""
        <script type="module">
            // Import JS modules if needed (e.g., for ClipPath)
            // import {{ ... }} from './js/....js';
            // import {{ generateRoundedPath }} from './js/pathGenerator.js';
            // import {{ ResponsiveClipPath }} from './js/clipPathUtils.js';
            import {{ PythraSlider }} from './js/slider.js';
            import {{ PythraDropdown }} from './js/dropdown.js';
            // import {{ PythraVirtuaList }} from './js/virtual_list.js';
            

            document.addEventListener('DOMContentLoaded', () => {{
                window._pythra_instances = window._pythra_instances || {{}};
                try {{
                     // First, DEFINE all our JS classes and functions
                    {js_utilities}

                    // Then, RUN the initialization commands
                    {''.join(js_commands)}
                }} catch (e) {{
                    console.error("Error running Pythra initializers:", e);
                }}
            }});//end event listener
        </script>
        """
        return full_script

    def _write_initial_files(
        self, title: str, html_content: str, initial_css_rules: str, initial_js: str
    ):
        # --- THIS IS THE NEW FONT DEFINITION CSS ---
        font_face_rules = f"""
         /* Define the Material Symbols fonts hosted by our server */
         @font-face {{
           font-family: 'Material Symbols Outlined';
           font-style: normal;
           font-weight: 100 700; /* The range of weights the variable font supports */
           src: url(http://localhost:{self.config.get('assets_server_port')}/{self.config.get('assets_dir')}/fonts/MaterialSymbolsOutlined.ttf) format('truetype');
         }}

         @font-face {{
           font-family: 'Material Symbols Rounded';
           font-style: normal;
           font-weight: 100 700;
           src: url(http://localhost:{self.config.get('assets_server_port')}/{self.config.get('assets_dir')}/fonts/MaterialSymbolsRounded.ttf) format('truetype');
         }}

         @font-face {{
           font-family: 'Material Symbols Sharp';
           font-style: normal;
           font-weight: 100 700;
           src: url(http://localhost:{self.config.get('assets_server_port')}/{self.config.get('assets_dir')}/fonts/MaterialSymbolsSharp.ttf) format('truetype');
         }}
         """
        # --- END OF NEW FONT CSS ---
        base_css = """
         body { margin: 0; font-family: sans-serif; background-color: #f0f0f0; overflow: hidden;}
         * { box-sizing: border-box; }
         #root-container, #overlay-container { height: 100vh; width: 100vw; overflow: hidden; position: relative;}
         #overlay-container { position: absolute; top: 0; left: 0; pointer-events: none; }
         #overlay-container > * { pointer-events: auto; }
         .custom-scrollbar::-webkit-scrollbar {
             display: none; /* for Chrome, Safari, and Opera */
         }
         .custom-scrollbar {
             -ms-overflow-style: none;  /* for IE and Edge */
             scrollbar-width: none;  /* for Firefox */
         }
         """
        try:
            with open(self.css_file_path, "w", encoding="utf-8") as c:
                c.write(base_css + font_face_rules)
            with open(self.html_file_path, "w", encoding="utf-8") as f:
                f.write(
                    f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{html.escape(title)}</title>
    <!-- ADD SIMPLEBAR CSS -->
    <link rel="stylesheet" href="./js/scroll-bar/simplebar.min.css" />
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css">
    <link id="base-stylesheet" type="text/css" rel="stylesheet" href="styles.css?v={int(time.time())}">
    <style id="dynamic-styles">{initial_css_rules}</style>
    {self._get_js_includes()}
</head>
<body>
    <div id="root-container">{html_content}</div>
    <div id="overlay-container"></div>

    <!-- ADD SIMPLEBAR JS -->
    <script src="./js/scroll-bar/simplebar.min.js"></script>
    <!-- ADD THE NEW SLIDER JS ENGINE -->
    {initial_js}
</body>
</html>"""
                )
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
            function handleClickWithArgs(callback_name, ...args) {{
                if (window.pywebview) {{
                    console.log("index", args);
                    window.pywebview.on_pressed(callback_name, ...args).then(function(response) {{
                        console.log(response);
                    }}).catch(function(error) {{
                        console.error(error);
                    }});
                }} else {{
                    console.error('pywebview is not defined');
                }}
            }}
            function handleItemTap(name, index) {{ if(window.pywebview) window.pywebview.on_item_tap(name, index, ()=>{{}}); }}
            function handleInput(name, value) {{
                if(window.pywebview) {{
                    window.pywebview.on_input_changed(name, value, ()=>{{}});
                }}
            }}
        </script>
        <script>
        function PythraSlider(elementId, options) {{
    // The 'this' keyword refers to the new object being created.
    this.container = document.getElementById(elementId);
    if (!this.container) {{
        console.error(`Slider container with ID #${{elementId}} not found.`);
        return;
    }}

    console.log(`✅ PythraSlider engine is initializing for #${{elementId}}`);

    this.options = options;

    // Find child elements
    this.track = this.container.querySelector('.slider-track');
    this.thumb = this.container.querySelector('.slider-thumb');
    
    // Bind 'this' context for event handlers
    this.handleDragStart = this.handleDragStart.bind(this);
    this.handleDragMove = this.handleDragMove.bind(this);
    this.handleDragEnd = this.handleDragEnd.bind(this);

    // Attach initial event listeners
    this.container.addEventListener('mousedown', this.handleDragStart);
    this.container.addEventListener('touchstart', this.handleDragStart, {{ passive: false }}); // passive: false to allow preventDefault
}}

PythraSlider.prototype.handleDragStart = function(event) {{
    event.preventDefault();
    this.container.classList.add('active');
    
    document.addEventListener('mousemove', this.handleDragMove);
    document.addEventListener('mouseup', this.handleDragEnd);
    document.addEventListener('touchmove', this.handleDragMove);
    document.addEventListener('touchend', this.handleDragEnd);

    this.updatePosition(event);
}};

PythraSlider.prototype.handleDragMove = function(event) {{
    this.updatePosition(event);
}};

PythraSlider.prototype.handleDragEnd = function() {{
    this.container.classList.remove('active');
    
    document.removeEventListener('mousemove', this.handleDragMove);
    document.removeEventListener('mouseup', this.handleDragEnd);
    document.removeEventListener('touchmove', this.handleDragMove);
    document.removeEventListener('touchend', this.handleDragEnd);
}};

PythraSlider.prototype.updatePosition = function(event) {{
    if (!this.track) return;
    const rect = this.track.getBoundingClientRect();
    const clientX = event.touches ? event.touches[0].clientX : event.clientX;
    
    let positionX = clientX - rect.left;
    let percentage = (positionX / rect.width) * 100;
    
    percentage = Math.max(0, Math.min(100, percentage));
    
    this.container.style.setProperty('--slider-percentage', `${{percentage}}%`);
    
    const range = this.options.max - this.options.min;
    const newValue = this.options.min + (percentage / 100) * range;
    
    if (window.pywebview && this.options.onChangedName) {{
        window.pywebview.on_drag_update(this.options.onChangedName, newValue);
    }}
}};

PythraSlider.prototype.destroy = function() {{
    if (!this.container) return;
    this.container.removeEventListener('mousedown', this.handleDragStart);
    this.container.removeEventListener('touchstart', this.handleDragStart);
    this.handleDragEnd(); 
}};
        </script>
        """


