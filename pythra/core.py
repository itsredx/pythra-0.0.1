# pythra/core.py

import os
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
from .state import State, StatefulWidget
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
        self.id = "main_window_id"

        self.called = False

        # State Management / Reconciliation Control
        self._reconciliation_requested: bool = False
        self._pending_state_updates: Set[State] = set()

        self._result = None

        # Asset Management
        self.html_file_path = os.path.abspath("web/index.html")
        self.css_file_path = os.path.abspath("web/styles.css")
        self.asset_server = AssetServer(
            directory=self.config.get("assets_dir"),
            port=self.config.get("assets_server_port"),
        )
        self.asset_server.start()
        os.makedirs("web", exist_ok=True)

        Widget.set_framework(self)
        StatefulWidget.set_framework(self)
        print("Framework Initialized with new Reconciler architecture.")

    def set_root(self, widget: Widget):
        """Sets the root widget for the application."""
        self.root_widget = widget

    def run(
        self,
        title: str = config.get("app_name"),
        width: int = config.get("win_width"),
        height: int = config.get("win_height"),
        frameless: bool = config.get("frameless"),
        maximized: bool = config.get("maximixed"),
        fixed_size: bool = config.get("fixed_size"),
    ):
        """
        Builds the initial UI, writes necessary files, creates the window, and starts the app.
        """
        if not self.root_widget:
            raise ValueError("Root widget not set. Use set_root() before run().")

        print("\n>>> Framework: Performing Initial Render <<<")

        # 1. Build the full widget tree, which will include the StatefulWidget at the root.
        built_tree_root = self._build_widget_tree(self.root_widget)

        # 2. <<< THE FIX >>>
        # If the root is a StatefulWidget, we reconcile what it *builds*, not the widget itself.
        initial_tree_to_reconcile = built_tree_root
        if isinstance(built_tree_root, StatefulWidget):
            children = built_tree_root.get_children()
            initial_tree_to_reconcile = children[0] if children else None

        # 3. Perform initial reconciliation on the *renderable* tree.
        result = self.reconciler.reconcile(
            previous_map={},
            new_widget_root=initial_tree_to_reconcile,
            parent_html_id="root-container",
        )

        self._result = result
        

        # 4. Update framework state from the initial result.
        self.reconciler.context_maps["main"] = result.new_rendered_map
        for cb_id, cb_func in result.registered_callbacks.items():
            self.api.register_callback(cb_id, cb_func)

        # 5. Generate initial HTML from the map created by the reconciler.
        root_key = (
            initial_tree_to_reconcile.get_unique_id()
            if initial_tree_to_reconcile
            else None
        )
        initial_html_content = self._generate_html_from_map(
            root_key, result.new_rendered_map
        )

        # 6. Generate initial CSS from the details collected by the reconciler.
        initial_css_rules = self._generate_css_from_details(result.active_css_details)

        # 7. Generate the initial JS script for things like responsive clip paths.
        initial_js_script = self._generate_initial_js_script(result.js_initializers)

        # 8. Write files and create the application window.
        self._write_initial_files(
            title, initial_html_content, initial_css_rules, initial_js_script
        )

        self.window = webwidget.create_window(
            title,
            self.id,
            self.html_file_path,
            self.api,
            width,
            height,
            frameless=frameless,
            maximized = maximized,
            fixed_size = fixed_size
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

        # 1. Build the full widget tree based on the current application state.
        built_tree_root = self._build_widget_tree(self.root_widget)

        # 2. <<< THE FIX >>>
        # If the root is a StatefulWidget, "look through" it to get the renderable child tree.
        main_tree_to_reconcile = built_tree_root
        if isinstance(built_tree_root, StatefulWidget):
            children = built_tree_root.get_children()
            main_tree_to_reconcile = children[0] if children else None

        # 3. Reconcile the main renderable tree.
        old_main_map = self.reconciler.get_map_for_context("main")
        main_result = self.reconciler.reconcile(
            old_main_map, main_tree_to_reconcile, "root-container"
        )

        # 4. Handle Declarative Overlays (Dialogs, SnackBars, etc.)
        # We check for overlays on the full built tree root (the Scaffold/StatefulWidget instance).
        scaffold_instance = built_tree_root

        # Reconcile Dialog
        dialog_widget = (
            getattr(scaffold_instance, "dialog", None) if scaffold_instance else None
        )
        built_dialog_widget = self._build_widget_tree(
            dialog_widget
        )  # Build subtree for the dialog
        old_dialog_map = self.reconciler.get_map_for_context("dialog")
        dialog_result = self.reconciler.reconcile(
            old_dialog_map, built_dialog_widget, "overlay-container"
        )

        # Reconcile SnackBar
        snackbar_widget = (
            getattr(scaffold_instance, "snackBar", None) if scaffold_instance else None
        )
        built_snackbar_widget = self._build_widget_tree(
            snackbar_widget
        )  # Build subtree for the snackbar
        old_snackbar_map = self.reconciler.get_map_for_context("snackbar")
        snackbar_result = self.reconciler.reconcile(
            old_snackbar_map, built_snackbar_widget, "overlay-container"
        )

        # 5. Combine results from all reconciliation contexts.
        all_patches = (
            main_result.patches + dialog_result.patches + snackbar_result.patches
        )
        all_css_details = {
            **main_result.active_css_details,
            **dialog_result.active_css_details,
            **snackbar_result.active_css_details,
        }
        all_callbacks = {
            **main_result.registered_callbacks,
            **dialog_result.registered_callbacks,
            **snackbar_result.registered_callbacks,
        }

        # 6. Update the framework's state maps and register callbacks.
        self.reconciler.context_maps["main"] = main_result.new_rendered_map
        self.reconciler.context_maps["dialog"] = dialog_result.new_rendered_map
        self.reconciler.context_maps["snackbar"] = snackbar_result.new_rendered_map

        for cb_id, cb_func in all_callbacks.items():
            self.api.register_callback(cb_id, cb_func)

        # 7. Generate payloads from the combined results.
        css_rules = self._generate_css_from_details(all_css_details)
        css_update_script = self._generate_css_update_script(css_rules)
        dom_patch_script = self._generate_dom_patch_script(all_patches, self._result.js_initializers)

        # 8. Execute JS to apply updates to the UI.
        combined_script = (css_update_script + "\n" + dom_patch_script).strip()
        if combined_script:
            print(
                f"Framework: Executing {len(all_patches)} DOM patches and CSS update."
            )
            self.window.evaluate_js(self.id, combined_script)
        else:
            print("Framework: No DOM or CSS changes detected.")

        self._pending_state_updates.clear()
        print(
            f"--- Framework: Reconciliation Complete (Total: {time.time() - start_time:.4f}s) ---"
        )

    # --- Widget Tree Building ---
    def _build_widget_tree(self, widget: Optional[Widget]) -> Optional[Widget]:
        """
        Recursively builds the widget tree, calling build() on StatefulWidget instances.
        This version correctly preserves the StatefulWidget in the tree structure.
        """
        if widget is None:
            return None

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
                        var tempContainer = document.createElement('div');
                        tempContainer.innerHTML = `{final_escaped_html}`;
                        var insertedEl = tempContainer.firstChild;
                        if (insertedEl) {{
                            parentEl.insertBefore(insertedEl, {before_id_js});
                            {self._generate_prop_update_js(target_id, props, is_insert=True)}
                        }}
                    }}
                """
                props = data.get("props", {})
                if 'responsive_clip_path' in props:
                    print("INITIALIZERS: ", js_initializers)
                    if target_id != new_id:
                        old_id, new_id = new_id, target_id
                    initializer_data = {
                        'type': 'ResponsiveClipPath',
                        'target_id': target_id,
                        'data': props['responsive_clip_path'],
                        'before_id': old_id
                    }
                    # js_initializers.append(initializer_data) if js_initializers else print("no js_initializers found")
                    print("INITIALIZERS:AFTER: ", js_initializers)
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


                    js_commands.append(f"""// Step 0: Convert Python's array-of-arrays to JS's array-of-objects
                        const pointsForGenerator_{target_id} = {points_json}.map(p => ({{x: p[0], y: p[1]}}));
                        
                        // Step 1: Call generateRoundedPath with the points and radius
                        const initialPathString_{target_id} = generateRoundedPath(pointsForGenerator_{target_id}, {radius_json});
                        
                        // Step 2: Feed the generated path into ResponsiveClipPath
                        window._pythra_instances['{initializer_data["before_id"]}'] = new ResponsiveClipPath(
                            '{initializer_data["before_id"]}', 
                            initialPathString_{target_id}, 
                            {ref_w_json}, 
                            {ref_h_json}, 
                            {{ uniformArc: true, decimalPlaces: 2 }}
                        );
                    """)
                    
                    
                # if "responsive_clip_path" in props:
                #     print("PROPS: ",props)
                #     # imports.add(
                #     #     "import { generateRoundedPath } from './js/pathGenerator.js';"
                #     # )
                #     # imports.add(
                #     #     "import { ResponsiveClipPath } from './js/clipPathUtils.js';"
                #     # )
                #     target_id = target_id
                #     clip_data = props["responsive_clip_path"]

                #     # Serialize the Python data into JSON strings for JS
                #     points_json = json.dumps(clip_data["points"])
                #     radius_json = json.dumps(clip_data["radius"])
                #     ref_w_json = json.dumps(clip_data["viewBox"][0])
                #     ref_h_json = json.dumps(clip_data["viewBox"][1])

                #     # This JS code performs the exact two-step process you described.
                #     js_commands.append(
                #         f"""
                #         // Step 0: Convert Python's array-of-arrays to JS's array-of-objects
                #         const pointsForGenerator_{target_id} = {points_json}.map(p => ({{x: p[0], y: p[1]}}));
                        
                #         // Step 1: Call generateRoundedPath with the points and radius
                #         const initialPathString_{target_id} = generateRoundedPath(pointsForGenerator_{target_id}, {radius_json});
                        
                #         // Step 2: Feed the generated path into ResponsiveClipPath
                #         window._pythra_instances['{target_id}'] = new ResponsiveClipPath(
                #             '{target_id}', 
                #             initialPathString_{target_id}, 
                #             {ref_w_json}, 
                #             {ref_h_json}, 
                #             {{ uniformArc: true, decimalPlaces: 2 }}
                #         );
                #     """
                #     )
                if props.get("init_simplebar"):
                    options_json = json.dumps(props.get("simplebar_options", {}))
                    command_js += f"""
                        var el_{target_id} = document.getElementById('{target_id}');
                        if (el_{target_id} && !el_{target_id}.simplebar) {{
                            new SimpleBar(el_{target_id}, {options_json});
                        }}
                    """
                    print("new SimpleBar: ", options_json)

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
                        }}""")
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

            if key == "data":
                js_prop_updates.append(
                    f"{element_var}.textContent = {json.dumps(str(value))};"
                )
                # print("data: ",value)
            elif key == "css_class":
                js_prop_updates.append(
                    f"{element_var}.className = {json.dumps(value)};"
                )
            elif key == "src":
                js_prop_updates.append(f"{element_var}.src = {json.dumps(value)};")
            elif key == "tooltip":
                js_prop_updates.append(f"{element_var}.title = {json.dumps(value)};")

            elif key == "value" and "textfield-root-container" in props.get(
                "css_class", ""
            ):
                # This is a value update for a TextField. Target the inner input.
                input_id = f"{target_id}_input"
                js_prop_updates.append(
                    f"var inputEl = document.getElementById('{input_id}'); if (inputEl && inputEl.value !== {json.dumps(str(value))}) inputEl.value = {json.dumps(str(value))};"
                )

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

        # --- NEW: Apply _style_override from the widget instance ---
        # We need the widget instance to get the override
        # This assumes the reconciler includes it in the patch data (we'll ensure this next)
        widget_instance = props.get("widget_instance")
        if widget_instance and hasattr(widget_instance, "_style_override"):
            for style_key, style_value in widget_instance._style_override.items():
                style_updates[style_key] = style_value
                print("Style Value Init: ", style_value)

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

    def _generate_initial_js_script(self, initializers: List[Dict]) -> str:
        """Generates a script tag to run initializations after the DOM loads."""
        if not initializers:
            return ""

        js_commands = []
        imports = set()
        # Your initializer logic for ClipPath etc. goes here if needed
        for init in initializers:
            # --- ADD THIS BLOCK FOR SIMPLEBAR ---
            if init["type"] == "SimpleBar":
                target_id = init["target_id"]
                # We can pass options from Python to the SimpleBar constructor
                options_json = json.dumps(init.get("options", {}))
                js_commands.append(
                    f"""
                    const el_{target_id} = document.getElementById('{target_id}');
                    if (el_{target_id} && !el_{target_id}.simplebar) {{ // Check if not already initialized
                        new SimpleBar(el_{target_id}, {options_json});
                        console.log('SimpleBar initialized for #{target_id}');
                    }};
                """
                )
            # --- END OF NEW BLOCK ---

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

        # Wrap all commands in a DOMContentLoaded listener.
        # We now import BOTH of your utility modules.
        full_script = f"""
        <script type="module">
            // Import JS modules if needed (e.g., for ClipPath)
            // import {{ ... }} from './js/....js';
            import {{ generateRoundedPath }} from './js/pathGenerator.js';
            import {{ ResponsiveClipPath }} from './js/clipPathUtils.js';
            

            document.addEventListener('DOMContentLoaded', () => {{
                window._pythra_instances = window._pythra_instances || {{}};
                try {{
                    {''.join(js_commands)}
                }} catch (e) {{
                    console.error("Error running Pythra initializers:", e);
                }}
            }});
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
            function handleItemTap(name, index) {{ if(window.pywebview) window.pywebview.on_item_tap(name, index, ()=>{{}}); }}
            function handleInput(name, value) {{
                if(window.pywebview) {{
                    window.pywebview.on_input_changed(name, value, ()=>{{}});
                }}
            }}
        </script>
        """
