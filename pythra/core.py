# pythra/core.py

import os
import time
import json
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
        self.reconciler = Reconciler() # Using the new Indexed Reconciler
        self.root_widget: Optional[Widget] = None
        self.window = None
        self.id = "main_window_id"

        # State Management / Reconciliation Control
        self._reconciliation_requested: bool = False

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
        print("Framework Initialized with new Indexed Reconciler.")

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

        # 1. Build the full widget tree.
        built_tree_root = self._build_widget_tree(self.root_widget)
        initial_tree_to_reconcile = self._get_renderable_tree(built_tree_root)

        # 2. Perform initial reconciliation. The `previous_map` is empty.
        initial_result = self.reconciler.reconcile(
            previous_map={},
            new_widget_root=initial_tree_to_reconcile,
            parent_html_id="root-container",
        )
        
        # 3. Update framework state from the initial result.
        self.reconciler.context_maps["main"] = initial_result.new_rendered_map
        for cb_id, cb_func in initial_result.registered_callbacks.items():
            self.api.register_callback(cb_id, cb_func)

        # 4. Generate initial HTML, CSS, and JS from the reconciliation result.
        root_key = initial_tree_to_reconcile.get_unique_id() if initial_tree_to_reconcile else None
        initial_html_content = self._generate_html_from_map(root_key, initial_result.new_rendered_map)
        initial_css_rules = self._generate_css_from_details(initial_result.active_css_details)
        initial_js_script = self._generate_initial_js_script(initial_result.js_initializers)

        # 5. Write files and create the application window.
        self._write_initial_files(title, initial_html_content, initial_css_rules, initial_js_script)
        self.window = webwidget.create_window(
            title, self.id, self.html_file_path, self.api, width, height,
            frameless=frameless, maximized=maximized, fixed_size=fixed_size
        )

        # 6. Start the application event loop.
        print("Framework: Starting application event loop...")
        webwidget.start(window=self.window, debug=bool(self.config.get("Debug", False)))

    def close(self):
        if self.window: self.window.close_window()
        self.asset_server.stop()

    def minimize(self):
        if self.window: self.window.minimize()

    # --- State Update and Reconciliation Cycle ---

    def request_reconciliation(self, state_instance: State):
        """Called by State.setState to schedule a UI update."""
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

        # 1. Build the new widget tree based on the current application state.
        built_tree_root = self._build_widget_tree(self.root_widget)

        # 2. Reconcile the main content area.
        main_tree_to_reconcile = self._get_renderable_tree(built_tree_root)
        old_main_map = self.reconciler.get_map_for_context("main")
        main_result = self.reconciler.reconcile(old_main_map, main_tree_to_reconcile, "root-container")

        # 3. Handle Declarative Overlays (Dialogs, SnackBars, etc.)
        dialog_widget = getattr(built_tree_root, "dialog", None)
        built_dialog_widget = self._build_widget_tree(dialog_widget)
        old_dialog_map = self.reconciler.get_map_for_context("dialog")
        dialog_result = self.reconciler.reconcile(old_dialog_map, built_dialog_widget, "overlay-container")

        snackbar_widget = getattr(built_tree_root, "snackBar", None)
        built_snackbar_widget = self._build_widget_tree(snackbar_widget)
        old_snackbar_map = self.reconciler.get_map_for_context("snackbar")
        snackbar_result = self.reconciler.reconcile(old_snackbar_map, built_snackbar_widget, "overlay-container")

        # 4. Combine results and update framework state.
        all_patches = main_result.patches + dialog_result.patches + snackbar_result.patches
        all_css_details = {**main_result.active_css_details, **dialog_result.active_css_details, **snackbar_result.active_css_details}
        all_callbacks = {**main_result.registered_callbacks, **dialog_result.registered_callbacks, **snackbar_result.registered_callbacks}
        all_js_initializers = main_result.js_initializers + dialog_result.js_initializers + snackbar_result.js_initializers

        # Update the context maps with the new state for the next cycle.
        self.reconciler.context_maps["main"] = main_result.new_rendered_map
        self.reconciler.context_maps["dialog"] = dialog_result.new_rendered_map
        self.reconciler.context_maps["snackbar"] = snackbar_result.new_rendered_map

        for cb_id, cb_func in all_callbacks.items():
            self.api.register_callback(cb_id, cb_func)

        # 5. Generate and execute UI update scripts.
        css_rules = self._generate_css_from_details(all_css_details)
        css_update_script = self._generate_css_update_script(css_rules)
        dom_patch_script = self._generate_dom_patch_script(all_patches, all_js_initializers)

        combined_script = (css_update_script + "\n" + dom_patch_script).strip()
        if combined_script:
            print(f"Framework: Executing {len(all_patches)} DOM patches and CSS update.")
            self.window.evaluate_js(self.id, combined_script)
        else:
            print("Framework: No DOM or CSS changes detected.")

        print(f"--- Framework: Reconciliation Complete (Total: {time.time() - start_time:.4f}s) ---")

    def _get_renderable_tree(self, widget: Optional[Widget]) -> Optional[Widget]:
        """If the root is a StatefulWidget, we reconcile what it *builds*."""
        if isinstance(widget, StatefulWidget):
            children = widget.get_children()
            return children[0] if children else None
        return widget

    def _build_widget_tree(self, widget: Optional[Widget]) -> Optional[Widget]:
        """
        Recursively builds the widget tree, calling build() on StatefulWidget instances.
        This version correctly preserves the StatefulWidget in the tree structure.
        """
        if widget is None:
            return None

        if isinstance(widget, StatefulWidget):
            state = widget.get_state()
            if not state:
                return None
            built_child = state.build()
            processed_child = self._build_widget_tree(built_child)
            widget._children = [processed_child] if processed_child else []
            return widget
        else:
            if hasattr(widget, "get_children"):
                new_children = [self._build_widget_tree(child) for child in widget.get_children() if child]
                widget._children = [c for c in new_children if c]
            return widget

    def _generate_html_from_map(self, root_key: Optional[Union[Key, str]], rendered_map: Dict) -> str:
        """Generates the full HTML string by recursively traversing the flat rendered_map."""
        if root_key is None or root_key not in rendered_map:
            return ""
        node_data = rendered_map.get(root_key)
        if not node_data:
            return ""
        if node_data["widget_type"] == "StatefulWidget":
            child_keys = node_data.get("children_keys", [])
            return self._generate_html_from_map(child_keys[0], rendered_map) if child_keys else ""
        widget_instance_ref = node_data.get("widget_instance_ref")
        if not widget_instance_ref: return ""
        widget_instance = widget_instance_ref()
        if not widget_instance: return ""
        html_id, props = node_data["html_id"], node_data["props"]
        stub = self.reconciler._generate_html_stub(widget_instance, html_id, props)
        children_html = "".join(self._generate_html_from_map(child_key, rendered_map) for child_key in node_data.get("children_keys", []))
        if ">" in stub and "</" in stub:
            tag = self.reconciler._get_widget_render_tag(widget_instance)
            closing_tag = f"</{tag}>"
            if stub.endswith(closing_tag):
                return f"{stub[:-len(closing_tag)]}{children_html}{closing_tag}"
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
        escaped_css = json.dumps(css_rules).replace("`", "\\`")
        return f"""
            var styleSheet = document.getElementById('dynamic-styles');
            if (styleSheet && styleSheet.textContent !== {escaped_css}) {{
                 styleSheet.textContent = {escaped_css};
            }}
        """

    def _sanitize_for_json(self, data: Any) -> Any:
        """Recursively removes non-serializable values from a data structure."""
        if isinstance(data, dict):
            return {
                k: self._sanitize_for_json(v)
                for k, v in data.items()
                if not callable(v) and not isinstance(v, (Widget, weakref.ReferenceType))
            }
        elif isinstance(data, list):
            return [self._sanitize_for_json(item) for item in data]
        elif isinstance(data, (str, int, float, bool, type(None))):
            return data
        return str(data)

    def _generate_dom_patch_script(self, patches: List[Patch], js_initializers: List[Dict]) -> str:
        """Converts the list of Patch objects from the reconciler into executable JavaScript."""
        js_commands = []
        for patch in patches:
            action, target_id, data = patch.action, patch.html_id, patch.data
            sanitized_data = self._sanitize_for_json(data)
            loggable_data_str = json.dumps(sanitized_data)
            command_js = ""

            if action == "INSERT":
                parent_id, html_stub, props, before_id = data["parent_html_id"], data["html"], data["props"], data["before_id"]
                escaped_html = json.dumps(html_stub)[1:-1].replace("`", "\\`").replace("${", "\\${")
                before_id_js = f"document.getElementById('{before_id}')" if before_id else "null"
                command_js = f"""
                    var parentEl = document.getElementById('{parent_id}');
                    if (parentEl) {{
                        var tempContainer = document.createElement('div');
                        tempContainer.innerHTML = `{escaped_html}`;
                        var insertedEl = tempContainer.firstChild;
                        if (insertedEl) {{
                            parentEl.insertBefore(insertedEl, {before_id_js});
                            {self._generate_prop_update_js(target_id, props, is_insert=True)}
                        }}
                    }}
                """
            elif action == "REMOVE":
                command_js = f"""
                    var el = document.getElementById('{target_id}');
                    if (el) {{
                        if (el.simplebar) el.simplebar.unMount(); // Cleanup SimpleBar
                        el.remove();
                    }}
                """
            elif action == "UPDATE":
                prop_update_js = self._generate_prop_update_js(target_id, data["props"])
                if prop_update_js:
                    command_js = f'var elToUpdate = document.getElementById("{target_id}"); if (elToUpdate) {{ {prop_update_js} }}'
            elif action == "MOVE":
                parent_id, before_id = data["parent_html_id"], data["before_id"]
                before_id_js = f"document.getElementById('{before_id}')" if before_id else "null"
                command_js = f"""
                    var el = document.getElementById('{target_id}');
                    var p = document.getElementById('{parent_id}');
                    if (el && p) p.insertBefore(el, {before_id_js});
                """
            elif action == "SVG_INSERT":
                # Handle SVG specific insertions if necessary
                pass

            if command_js:
                js_commands.append(f"try {{ {command_js} }} catch (e) {{ console.error('Error applying patch {action} {target_id}:', e, {loggable_data_str}); }}")
        
        # Append initializer scripts after all patches have been applied.
        js_commands.append(self._generate_initializers_script_for_patch(js_initializers))
        
        return "\n".join(js_commands)

    def _generate_prop_update_js(self, target_id: str, props: Dict, is_insert: bool = False) -> str:
        """Generates specific JS commands for updating element properties."""
        js_prop_updates = []
        style_updates = {}
        element_var = "insertedEl" if is_insert else "elToUpdate"

        for key, value in props.items():
            if key == "data":
                js_prop_updates.append(f"{element_var}.textContent = {json.dumps(str(value))};")
            elif key == "css_class":
                js_prop_updates.append(f"{element_var}.className = {json.dumps(value)};")
            elif key == "src":
                js_prop_updates.append(f"{element_var}.src = {json.dumps(value)};")
            elif key == "tooltip":
                js_prop_updates.append(f"{element_var}.title = {json.dumps(value)};")
            elif key == "value" and "textfield-root-container" in props.get("css_class", ""):
                input_id = f"{target_id}_input"
                js_prop_updates.append(f"var i = document.getElementById('{input_id}'); if (i && i.value !== {json.dumps(str(value))}) i.value = {json.dumps(str(value))};")
            elif key == "errorText" and "textfield-root-container" in props.get("css_class", ""):
                helper_id = f"{target_id}_helper"
                js_prop_updates.append(f"var h = document.getElementById('{helper_id}'); if(h) h.textContent = {json.dumps(str(value))};")
            elif key.startswith('--'): # Handle CSS Variables for dynamic styling
                style_updates[key] = value

        # Apply inline style overrides from widgets like Scrollbar
        if 'widget_instance' in props and hasattr(props['widget_instance'], '_style_override'):
             for style_key, style_value in props['widget_instance']._style_override.items():
                style_updates[style_key] = style_value

        if style_updates:
            for prop, val in style_updates.items():
                css_prop_kebab = "".join(['-' + c.lower() if c.isupper() else c for c in prop]).lstrip("-")
                js_prop_updates.append(f"{element_var}.style.setProperty('{css_prop_kebab}', {json.dumps(val)});")

        return "\n".join(js_prop_updates)

    def _generate_initializers_script_for_patch(self, initializers: List[Dict]) -> str:
        """Generates JS to run initializations for newly inserted elements."""
        commands = []
        for init in initializers:
            target_id = init.get("target_id")
            if not target_id: continue
            
            command = ""
            if init["type"] == "SimpleBar":
                options_json = json.dumps(init.get("options", {}))
                command = f"""
                    var el = document.getElementById('{target_id}');
                    if (el && !el.simplebar) new SimpleBar(el, {options_json});
                """
            elif init["type"] == "ResponsiveClipPath":
                clip_data = init["data"]
                points_json = json.dumps(clip_data["points"])
                radius_json = json.dumps(clip_data["radius"])
                ref_w_json = json.dumps(clip_data["viewBox"][0])
                ref_h_json = json.dumps(clip_data["viewBox"][1])
                command = f"""
                    const points_{target_id} = {points_json}.map(p => ({{x: p[0], y: p[1]}}));
                    const path_{target_id} = generateRoundedPath(points_{target_id}, {radius_json});
                    if (!window._pythra_instances['{target_id}']) {{
                        window._pythra_instances['{target_id}'] = new ResponsiveClipPath('{target_id}', path_{target_id}, {ref_w_json}, {ref_h_json}, {{ uniformArc: true, decimalPlaces: 2 }});
                    }}
                """
            if command:
                commands.append(f"try {{ {command} }} catch(e) {{ console.error('Initializer failed for {target_id}', e); }}")
                
        return "\n".join(commands)

    def _generate_initial_js_script(self, initializers: List[Dict]) -> str:
        """Generates a script tag to run initializations after the initial DOM loads."""
        # This can reuse the patch initializer logic.
        init_script = self._generate_initializers_script_for_patch(initializers)
        return f"""
        <script type="module">
            document.addEventListener('DOMContentLoaded', () => {{
                window._pythra_instances = window._pythra_instances || {{}};
                {init_script}
            }});
        </script>
        """

    def _write_initial_files(self, title: str, html_content: str, initial_css_rules: str, initial_js: str):
        # ... (This method is largely unchanged, but now includes the main JS helpers) ...
        # I will include it in full for completeness.
        font_face_rules = f"""
         @font-face {{ font-family: 'Material Symbols Outlined'; font-style: normal; font-weight: 100 700; src: url(http://localhost:{self.config.get('assets_server_port')}/{self.config.get('assets_dir')}/fonts/MaterialSymbolsOutlined.ttf) format('truetype'); }}
         @font-face {{ font-family: 'Material Symbols Rounded'; font-style: normal; font-weight: 100 700; src: url(http://localhost:{self.config.get('assets_server_port')}/{self.config.get('assets_dir')}/fonts/MaterialSymbolsRounded.ttf) format('truetype'); }}
         @font-face {{ font-family: 'Material Symbols Sharp'; font-style: normal; font-weight: 100 700; src: url(http://localhost:{self.config.get('assets_server_port')}/{self.config.get('assets_dir')}/fonts/MaterialSymbolsSharp.ttf) format('truetype'); }}
         """
        base_css = """
         body { margin: 0; font-family: sans-serif; background-color: #f0f0f0; overflow: hidden;}
         * { box-sizing: border-box; }
         #root-container, #overlay-container { height: 100vh; width: 100vw; overflow: hidden; position: relative;}
         #overlay-container { position: absolute; top: 0; left: 0; pointer-events: none; }
         #overlay-container > * { pointer-events: auto; }
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
    <link rel="stylesheet" href="./js/scroll-bar/simplebar.min.css" />
    <link rel="stylesheet" href="styles.css?v={int(time.time())}">
    <style id="dynamic-styles">{initial_css_rules}</style>
    {self._get_js_includes()}
</head>
<body>
    <div id="root-container">{html_content}</div>
    <div id="overlay-container"></div>
    <script src="./js/scroll-bar/simplebar.min.js"></script>
    {self._get_main_js_helpers()}
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
            function handleClick(name) {{ if(window.pywebview) window.pywebview.on_pressed_str(name); }}
            function handleItemTap(name, index) {{ if(window.pywebview) window.pywebview.on_pressed(name, index); }}
            function handleInput(name, value) {{ if(window.pywebview) window.pywebview.on_input_changed(name, value); }}
        </script>
        """

    def _get_main_js_helpers(self):
        """Embeds essential, non-patch-related JS helper functions into the main HTML."""
        return f"""
        <script>
            // This script block contains core helper functions that are always needed.
            // Embedding them here avoids re-sending them with every patch.
            
            // --- Responsive Clip Path Engine ---
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
        </script>
        """