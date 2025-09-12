# pythra/core.py

# --- ADD THESE IMPORTS AT THE TOP OF THE FILE ---
import cProfile
import pstats
import io
import logging
# --- END OF IMPORTS ---

import os
from pathlib import Path
import importlib
import sys
import re
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
from .package_manager import PackageManager
from .package_system import PackageType


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

        # --- NEW: Enhanced Package Management System ---
        self.package_manager = PackageManager(self.project_root)
        self.package_manager.set_framework(self)
        
        # Legacy compatibility - will be populated by PackageManager
        self.plugins = {}  # For backward compatibility
        self.plugin_js_modules = {}  # Managed by PackageManager
        
        # Discover and load packages
        print("🔎 Discovering packages...")
        discovered_packages = self.package_manager.discover_all_packages()
        
        # Auto-load local packages (plugins in plugins/ directory)
        local_packages = [name for name, packages in discovered_packages.items() 
                         if any(pkg.path.parent.name == "plugins" for pkg in packages)]
        
        if local_packages:
            loaded_packages, warnings = self.package_manager.resolve_and_load_packages(local_packages)
            for warning in warnings:
                print(f"⚠️ Package warning: {warning}")
            
            print(f"✅ Loaded {len(loaded_packages)} packages: {list(loaded_packages.keys())}")
        
        # The asset server now serves from the project's asset directory
        package_asset_dirs = self.package_manager.get_asset_server_dirs()
        self.asset_server = AssetServer(
            directory=str(self.assets_dir),
            port=self.config.get("assets_server_port"),
            # Pass the package asset directories to the server
            extra_serve_dirs=package_asset_dirs
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

    # Package management methods are now handled by PackageManager
    # Legacy methods kept for backward compatibility if needed
    
    def get_loaded_packages(self) -> Dict[str, Any]:
        """Get information about loaded packages"""
        return self.package_manager.get_loaded_packages()
    
    def list_packages(self, package_type: Optional[PackageType] = None) -> List[Any]:
        """List all discovered packages, optionally filtered by type"""
        return self.package_manager.list_packages(package_type)

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

        # 4. Analyze required JS engines for optimization
        required_engines = self._analyze_required_js_engines(built_tree_root, result)
        print(f"🔍 Analysis complete: {len(required_engines)} JS engines required: {required_engines}")
        
        # 5. Generate initial HTML, CSS, and JS with optimized loading
        root_key = initial_tree_to_reconcile.get_unique_id() if initial_tree_to_reconcile else None
        html_content = self._generate_html_from_map(root_key, result.new_rendered_map)
        css_rules = self._generate_css_from_details(result.active_css_details)
        js_script = self._generate_initial_js_script(result, required_engines)

        # 6. Write files
        self._write_initial_files(title, html_content, css_rules, js_script)
        
        # 7. Set flag to prevent re-injection during reconciliation
        self.called = True  # JS utilities are already included in initial render

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


    # Place this new helper method somewhere in the Framework class
    def _get_js_utility_functions(self, required_engines: set = None) -> str:
        """
        Reads only the required JS engine and utility files based on actual usage.
        
        :param required_engines: Set of engine names that are actually needed
        :return: Combined JavaScript code string
        """
        # --- MAPPING OF ENGINES TO FILES ---
        engine_to_file_map = {
            'generateRoundedPath': "web/js/pathGenerator.js",
            'ResponsiveClipPath': "web/js/clipPathUtils.js", 
            'scalePathAbsoluteMLA': "web/js/clipPathUtils.js",
            'PythraSlider': "web/js/slider.js",
            'PythraDropdown': "web/js/dropdown.js",
            'PythraGestureDetector': "web/js/gesture_detector.js",
            'PythraGradientClipPath': "web/js/gradient_border.js",
            'PythraVirtualList': "web/js/virtual_list.js",
        }
        
        # If no specific engines requested, load all (fallback for compatibility)
        if required_engines is None:
            print("🔧 Loading all JS engines (no optimization applied)")
            files_to_load = set(engine_to_file_map.values())
        else:
            print(f"🎯 Optimized loading: Only loading engines for {required_engines}")
            files_to_load = set()
            for engine in required_engines:
                if engine in engine_to_file_map:
                    files_to_load.add(engine_to_file_map[engine])
                else:
                    print(f"⚠️ Unknown engine requested: {engine}")
        
        all_js_code = []
        loaded_files = set()  # Track loaded files to avoid duplicates
        
        for file_path in files_to_load:
            if file_path in loaded_files:
                continue  # Skip if already loaded
            loaded_files.add(file_path)
            
            try:
                # Use Path for robust path handling
                full_path = self.project_root / file_path
                with full_path.open('r', encoding='utf-8') as f:
                    content = f.read()
                    # --- CLEANUP LOGIC ---
                    content = content.replace('export class', 'class').replace('export function', 'function')
                    content = re.sub(r'import\s+.*\s+from\s+.*?;?\n?', '', content)
                    
                    # Wrap in try-catch but assign classes to global scope
                    wrapped_content = f"""try {{
{content}

// Ensure classes are available globally
if (typeof ResponsiveClipPath !== 'undefined') window.ResponsiveClipPath = ResponsiveClipPath;
if (typeof PythraSlider !== 'undefined') window.PythraSlider = PythraSlider;
if (typeof PythraDropdown !== 'undefined') window.PythraDropdown = PythraDropdown;
if (typeof PythraGestureDetector !== 'undefined') window.PythraGestureDetector = PythraGestureDetector;
if (typeof PythraGradientClipPath !== 'undefined') window.PythraGradientClipPath = PythraGradientClipPath;
if (typeof PythraVirtualList !== 'undefined') window.PythraVirtualList = PythraVirtualList;
if (typeof generateRoundedPath !== 'undefined') window.generateRoundedPath = generateRoundedPath;
if (typeof scalePathAbsoluteMLA !== 'undefined') window.scalePathAbsoluteMLA = scalePathAbsoluteMLA;
}} catch (e) {{
    console.error('Error loading {os.path.basename(file_path)}:', e);
}}"""
                    
                    all_js_code.append(f"// --- Injected from {os.path.basename(file_path)} ---\n{wrapped_content}")
                    print(f"✅ Loaded JS engine: {os.path.basename(file_path)}")
            except FileNotFoundError:
                print(f"⚠️ Warning: JS utility file not found: {full_path}")

        # --- THIS IS THE NEW LOGIC ---
        # 2. Load all DISCOVERED PLUGIN JS files
        for engine_name, module_info in self.plugin_js_modules.items():
            try:
                full_path = Path(module_info['path'])
                with full_path.open('r', encoding='utf-8') as f:
                    content = f.read()
                    content = re.sub(r'import\s+.*\s+from\s+.*?;?\n?', '', content)
                    content = content.replace('export class', 'class').replace('export function', 'function')
                    wrapped_content = f"""try {{
{content}
}} catch (e) {{
    console.error('Error loading plugin {module_info['plugin']} - {os.path.basename(full_path)}:', e);
}}"""
                    all_js_code.append(f"// --- Injected Plugin '{module_info['plugin']}': {os.path.basename(full_path)} ---\n{wrapped_content}")
                    print(f"✅ Loaded plugin JS: {module_info['plugin']} - {os.path.basename(full_path)}")
            except FileNotFoundError:
                print(f"⚠️ Warning: Plugin JS file not found: {full_path}")
        # --- END OF NEW LOGIC ---

        return "\n\n".join(all_js_code)

    def _analyze_required_js_engines(self, widget_tree: Widget, result: 'ReconciliationResult') -> set:
        """
        Analyzes the widget tree and reconciliation result to determine which JS engines are needed.
        
        :param widget_tree: The built widget tree
        :param result: Reconciliation result with rendered map and initializers
        :return: Set of required JS engine names
        """
        required_engines = set()
        
        # Check reconciliation result for JS initializers
        for init in result.js_initializers:
            init_type = init.get("type")
            if init_type == "ResponsiveClipPath":
                required_engines.update(['ResponsiveClipPath', 'generateRoundedPath', 'scalePathAbsoluteMLA'])
            elif init_type == "SimpleBar":
                # SimpleBar is external, no engine needed
                pass
            elif init_type == "_RenderableSlider":
                required_engines.add('PythraSlider')
            elif init_type == "VirtualList":
                required_engines.add('PythraVirtualList')
        
        # Check rendered widgets for engine requirements
        for node_data in result.new_rendered_map.values():
            props = node_data.get("props", {})
            
            # Check for various initialization flags
            if props.get("init_slider"):
                required_engines.add('PythraSlider')
            if props.get("init_dropdown"):
                required_engines.add('PythraDropdown')
            if props.get("init_gesture_detector"):
                required_engines.add('PythraGestureDetector')
            if props.get("init_gradient_clip_border"):
                required_engines.add('PythraGradientClipPath')
            if props.get("init_virtual_list"):
                required_engines.add('PythraVirtualList')
            if props.get("responsive_clip_path"):
                required_engines.update(['ResponsiveClipPath', 'generateRoundedPath', 'scalePathAbsoluteMLA'])
            if props.get("_js_init"):
                engine_name = props["_js_init"].get("engine")
                if engine_name:
                    required_engines.add(engine_name)
        
        # Check for ClipPath widgets (which need ResponsiveClipPath)
        self._check_widget_for_clip_path(widget_tree, required_engines)
        
        return required_engines
    
    def _check_widget_for_clip_path(self, widget: Widget, required_engines: set):
        """
        Recursively checks widget tree for ClipPath widgets that need JS engines.
        """
        if widget is None:
            return
            
        # Check if this is a ClipPath widget
        widget_class_name = widget.__class__.__name__
        if widget_class_name == 'ClipPath':
            # ClipPath widgets need the path generation engines
            required_engines.update(['ResponsiveClipPath', 'generateRoundedPath', 'scalePathAbsoluteMLA'])
        
        # Recursively check children
        if hasattr(widget, 'get_children'):
            for child in widget.get_children():
                self._check_widget_for_clip_path(child, required_engines)

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
            print("Patches:", all_patches)
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
        # print(f"Rules: {all_rules}")
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
                        try {{
                            // Create a temporary, disconnected container
                            var tempContainer = document.createElement('div');
                            // Use trim() to remove leading/trailing whitespace from the HTML string
                            tempContainer.innerHTML = `{final_escaped_html}`.trim(); 
                            
                            // Use `firstElementChild` which ignores whitespace text nodes
                            var insertedEl = tempContainer.firstElementChild; 

                            if (insertedEl) {{
                                // Check if before element exists and is still in DOM
                                var beforeEl = {before_id_js};
                                if (beforeEl && !parentEl.contains(beforeEl)) {{
                                    beforeEl = null; // Element no longer exists, append at end
                                }}
                                parentEl.insertBefore(insertedEl, beforeEl);
                                // Now we can safely apply props because 'insertedEl' is guaranteed to be an element
                                {self._generate_prop_update_js(target_id, props, is_insert=True)}
                            }} else {{
                                console.warn('INSERT: No valid element created from HTML for {target_id}');
                            }}
                        }} catch (e) {{
                            console.error('INSERT: DOM operation failed for {target_id}:', e);
                        }}
                    }} else {{
                        console.error('INSERT: Parent element {parent_id} not found for {target_id}');
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
                            if (typeof window.PythraDropdown !== 'undefined') {{
                                console.log("Initializig the dropdown");
                                if (!window._pythra_instances['{target_id}']){{
                                    window._pythra_instances['{target_id}'] = new window.PythraDropdown('{target_id}', {options_json});
                                }}
                            }}
                        }}, 0);
                    """
                # --- END OF BLOCK ---

                if props.get("init_slider"):
                    options_json = json.dumps(props.get("slider_options", {}))
                    command_js += f"""
                        setTimeout(() => {{
                            if (typeof window.PythraSlider !== 'undefined') {{
                                if (!window._pythra_instances['{target_id}']) {{
                                    console.log('Initializing dynamically inserted PythraSlider for #{target_id}');
                                    window._pythra_instances['{target_id}'] = new window.PythraSlider('{target_id}', {options_json});
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
                        if (typeof window.PythraVirtualList !== 'undefined' && document.getElementById('{target_id}').simplebar) {{
                            window._pythra_instances['{target_id}_vlist'] = new window.PythraVirtualList('{target_id}', {options_json});
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
                        const initialPathString_{target_id} = window.generateRoundedPath(pointsForGenerator_{target_id}, {radius_json});
                        
                        // Step 2: Feed the generated path into ResponsiveClipPath
                        window._pythra_instances['{initializer_data["before_id"] if initializer_data["before_id"] else target_id}'] = new window.ResponsiveClipPath(
                            '{initializer_data["before_id"] if initializer_data["before_id"] else target_id}', 
                            initialPathString_{target_id}, 
                            {ref_w_json}, 
                            {ref_h_json}, 
                            {{ uniformArc: true, decimalPlaces: 2 }}
                        );
                        }}, 0);
                    """)

                # --- GENERIC JS INITIALIZER FOR BOTH INSERT AND REPLACE ---
                js_init_data = props.get("_js_init")
                if js_init_data and isinstance(js_init_data, dict):
                    engine_name = js_init_data.get("engine")
                    instance_name = js_init_data.get("instance_name")
                    options = js_init_data.get("options", {})
                    options_json = json.dumps(options)
                    
                    # We use setTimeout to ensure the element is fully in the DOM.
                    command_js += f"""
                        setTimeout(() => {{
                            if (typeof {engine_name} !== 'undefined') {{
                                if (!window._pythra_instances['{instance_name}']) {{
                                    console.log('Dynamically initializing {engine_name} for {instance_name}');
                                    window._pythra_instances['{instance_name}'] = new {engine_name}('{target_id}', {options_json});
                                }}
                            }} else {{
                                console.error('{engine_name} class not found. Ensure its JS file is loaded.');
                            }}
                        }}, 0);
                    """
                # --- END OF GENERIC LOGIC ---
                    
                    
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
                    command_js = f"""
                        var elToUpdate = document.getElementById("{target_id}");
                        if (elToUpdate) {{
                            try {{
                                {prop_update_js}
                            }} catch (e) {{
                                console.error('UPDATE: Property update failed for {target_id}:', e);
                            }}
                        }} else {{
                            console.error('UPDATE: Element {target_id} not found in DOM');
                        }}
                    """


            elif action == "MOVE":
                parent_id, before_id = data["parent_html_id"], data["before_id"]
                before_id_js = (
                    f"document.getElementById('{before_id}')" if before_id else "null"
                )
                command_js = f"""
                    var el = document.getElementById('{target_id}');
                    var p = document.getElementById('{parent_id}');
                    if (el && p) {{
                        try {{
                            var beforeEl = {before_id_js};
                            // Check if before element still exists and is in the target parent
                            if (beforeEl && !p.contains(beforeEl)) {{
                                beforeEl = null; // Element moved or removed, append at end
                            }}
                            p.insertBefore(el, beforeEl);
                        }} catch (e) {{
                            console.error('MOVE: Failed to move element {target_id}:', e);
                        }}
                    }} else {{
                        if (!el) console.error('MOVE: Element {target_id} not found');
                        if (!p) console.error('MOVE: Parent element {parent_id} not found');
                    }}
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

                # Create the log-safe string representation of the data.
                loggable_data_str = json.dumps(make_loggable(data))

                is_textfield_patch = False
                if "props" in data and isinstance(data["props"], dict):
                    if "onChangedName" in data["props"]:
                        is_textfield_patch = True

                # Use the sanitized string in the catch block.
                # TODO: RECHECK AND FIX THE TRY CATCH BLOCK CAUSING UI BREAKAGE
                # print(f"Loggable Data str: [{loggable_data_str}]")
                js_commands.append(
                    
                    f"try {{ {command_js} }} catch (e) {{ console.error('Error applying patch {action} {target_id}:', e.name + ': ' + e.message, 'Stack:', e.stack, 'Data:', {loggable_data_str}); }};"
                )

         # --- THIS IS THE FIX ---
        # The `self.called` flag is used to ensure we only inject the JS utilities ONCE
        # per application session, on the very first set of patches that gets sent.
        if not self.called:
            self.called = True
            print("🔧 Framework: Injecting JS utilities for the first time during reconciliation")
            # Prepend the combined JS utilities to the list of commands.
            js_utilities = self._get_js_utility_functions()
            js_commands.insert(0, js_utilities)
        else:
            print("🔧 Framework: Skipping JS utilities injection (already loaded)")
        # --- END OF FIX ---


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
                if css_prop_kebab == "--slider-percentage" and props.get("isDragEnded"):
                    print("drag css", props["isDragEnded"])
                    js_prop_updates.append(
                        f"try {{ {element_var}.style.setProperty('{css_prop_kebab}', {json.dumps(style_value)}); }} catch (e) {{ console.warn('Failed to set CSS property {css_prop_kebab}:', e); }}"
                    )
                elif css_prop_kebab == "--slider-percentage" and not props.get("isDragEnded"):
                    print("drag css", props.get("isDragEnded"))
                elif css_prop_kebab != "--slider-percentage" and "isDragEnded" not in props:
                    js_prop_updates.append(
                        f"try {{ {element_var}.style.setProperty('{css_prop_kebab}', {json.dumps(style_value)}); }} catch (e) {{ console.warn('Failed to set CSS property {css_prop_kebab}:', e); }}"
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
                    f"try {{ {element_var}.style.setProperty('{css_prop_kebab}', {json.dumps(val)}); }} catch (e) {{ console.warn('Failed to set style property {css_prop_kebab}:', e); }}"
                )

        return "\n".join(js_prop_updates)

    def _generate_initial_js_script(self, result: 'ReconciliationResult', required_engines: set = None) -> str:
        """Generates a script tag to run initializations after the DOM loads with optimized JS loading."""
        if not result.js_initializers:
            # Even if no initializers, we might need engines for widgets
            if not required_engines:
                return ""

        js_commands = []
        imports = set()

        for node_data in result.new_rendered_map.values():
            props = node_data.get("props", {})
            html_id = node_data.get("html_id")
            # print(">>>init_slider<<<", html_id)
            widget_instance = node_data.get("widget_instance")


            # --- NEW: Generic JS Initializer ---
            js_init_data = props.get("_js_init")
            if js_init_data:
                engine_name = js_init_data.get("engine")
                instance_name = js_init_data.get("instance_name")
                options = js_init_data.get("options", {})
                
                # Find the module path from the plugin manifest
                js_module_info = self._find_js_module(engine_name)
                if js_module_info:
                    imports.add(f"import {{ {engine_name} }} from '{js_module_info['path']}';")
                    options_json = json.dumps(options)
                    js_commands.append(f"window._pythra_instances['{instance_name}'] = new {engine_name}('{html_id}', {options_json});")
                else:
                    print(f"⚠️ Warning: JS engine '{engine_name}' not found in any plugin manifest.")
            # --- END OF NEW LOGIC ---

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
                    const initialPathString_{target_id} = window.generateRoundedPath(pointsForGenerator_{target_id}, {radius_json});
                    
                    // Step 2: Feed the generated path into ResponsiveClipPath
                    window._pythra_instances['{target_id}'] = new window.ResponsiveClipPath(
                        '{target_id}', 
                        initialPathString_{target_id}, 
                        {ref_w_json}, 
                        {ref_h_json}, 
                        {{ uniformArc: true, decimalPlaces: 2 }}
                    );
                """
                )

        # --- INCLUDE JS UTILITIES IN INITIAL RENDER ---
        # Get JS utilities for initial render so all functions are available
        js_utilities = self._get_js_utility_functions()
        
        full_script = f"""
        <script>
            document.addEventListener('DOMContentLoaded', () => {{
                window._pythra_instances = window._pythra_instances || {{}};
                try {{
                    // First, DEFINE all our JS classes and functions
                    {js_utilities}
                    
                    // Then, RUN the initialization commands that were generated
                    {''.join(js_commands)}

                }} catch (e) {{
                    console.error("Error running Pythra initializers:", e);
                }}
            }});
        </script>
        """
        return full_script

    # Helper method to find JS modules from discovered plugins
    def _find_js_module(self, engine_name: str) -> Optional[Dict]:
        for plugin_name, plugin_info in self.plugins.items():
            modules = plugin_info.get("js_modules", {})
            if engine_name in modules:
                return {
                    "plugin": plugin_name,
                    "path": f"/plugins/{plugin_name}/{modules[engine_name]}"
                }
        return None

    def _write_initial_files(
        self, title: str, html_content: str, initial_css_rules: str, initial_js: str
    ):
        # --- THIS IS THE NEW FONT DEFINITION CSS ---
        plugin_css_links = []
        for name, info in self.plugins.items():
            if 'css_files' in info:
                for css_file in info['css_files']:
                    # URL will be like /plugins/pythra_markdown_editor/vendor/tui-editor.min.css
                    # The asset server will handle this.
                    url_path = f"plugins/{name}/{css_file}"
                    plugin_css_links.append(f'<link rel="stylesheet" href="{url_path}">')
        
        plugin_css_str = "\n    ".join(plugin_css_links)

        font_face_rules = f"""
         /* Define the Material Symbols fonts hosted by our server */
         @font-face {{
           font-family: 'Material Symbols Outlined';
           font-style: normal;
           font-weight: 100 700; /* The range of weights the variable font supports */
           src: url(http://localhost:{self.config.get('assets_server_port')}/fonts/MaterialSymbolsOutlined.ttf) format('truetype');
         }}

         @font-face {{
           font-family: 'Material Symbols Rounded';
           font-style: normal;
           font-weight: 100 700;
           src: url(http://localhost:{self.config.get('assets_server_port')}/fonts/MaterialSymbolsRounded.ttf) format('truetype');
         }}

         @font-face {{
           font-family: 'Material Symbols Sharp';
           font-style: normal;
           font-weight: 100 700;
           src: url(http://localhost:{self.config.get('assets_server_port')}/fonts/MaterialSymbolsSharp.ttf) format('truetype');
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
    {plugin_css_str}
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
        """


