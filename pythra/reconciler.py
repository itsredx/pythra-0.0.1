# =============================================================================
# PYTHRA RECONCILER - The "Smart UI Updater" That Makes Apps Fast
# =============================================================================
"""
PyThra Reconciler - The "Intelligence" Behind Fast UI Updates

This is the "smart brain" that makes PyThra apps fast and efficient. Instead of
rebuilding the entire web page every time something changes (which would be slow),
the Reconciler figures out exactly what changed and updates only those parts.

**What is Reconciliation?**
Reconciliation is like having a "smart editor" that compares two versions of a document
and highlights only the differences. But instead of documents, it compares widget trees.

**Real-world analogy:**
Think of the Reconciler like a movie director doing retakes:
- OLD WAY: "Everyone off set! Rebuild the entire scene from scratch!" (slow)
- SMART WAY: "Just move the actor 2 steps left and change that prop" (fast)

The Reconciler is the "smart way" - it identifies exactly what changed and updates
only those elements, leaving everything else untouched.

**How it works:**
1. **Compare**: Look at the old widget tree vs. the new widget tree
2. **Find Differences**: Identify what widgets were added, removed, or changed
3. **Generate Patches**: Create precise instructions for updating the web page
4. **Apply Updates**: Send those instructions to the browser to update the UI

**Types of Changes it Handles:**
- **INSERT**: Add new widgets ("Add a button here")
- **REMOVE**: Delete widgets that are gone ("Remove this text")
- **UPDATE**: Modify existing widgets ("Change button color to red")
- **MOVE**: Reposition widgets ("Move this image to the left")
- **REPLACE**: Swap one widget for a completely different one

**Key Benefits:**
1. **Speed**: Only updates what actually changed (not the whole page)
2. **Smooth UX**: No flickering or page reloads
3. **Efficiency**: Uses less CPU and memory
4. **State Preservation**: Form inputs, scroll positions, etc. stay intact

**Example of what the Reconciler does:**
```python
# User clicks a counter button...
# OLD TREE: Button(text="Count: 5", color="blue")
# NEW TREE: Button(text="Count: 6", color="blue")

# Reconciler thinks: "Only the text changed, color stayed the same"
# Creates patch: {"action": "UPDATE", "element_id": "btn_123", "changes": {"text": "Count: 6"}}
# Browser receives: "Just change the text of element btn_123 to 'Count: 6'"
# Result: Lightning-fast update without rebuilding anything else!
```

**This file contains:**
- ReconciliationResult: The "instruction manual" for updating the UI
- Reconciler class: The "smart brain" that generates those instructions
- Patch system: The "precise change commands" sent to the browser
- ID management: The "naming system" for tracking elements
"""

import uuid
import html
import json
import sys
from typing import Any, Dict, List, Optional, Tuple, Union, Callable, Literal
from dataclasses import dataclass, field
from collections import defaultdict
# near top imports if not already present
# from collections import defaultdict


from .widgets import Scrollbar
from .state import StatefulWidget
from .base import Widget, Key

# It's good practice to import from your own project modules for type hints.
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .base import Widget, Key
    from .drawing import PathCommandWidget


# --- Key Class, IDGenerator, Data Structures (Unchanged) ---
class Key:
    def __init__(self, value: Any):
        try:
            hash(value)
            self.value = value
        except TypeError:
            if isinstance(value, list):
                self.value = tuple(value)
            elif isinstance(value, dict):
                self.value = tuple(sorted(value.items()))
            else:
                self.value = str(value)
                try:
                    hash(self.value)
                except TypeError:
                    raise TypeError(
                        f"Key value {value!r} of type {type(value)} could not be made hashable."
                    )

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Key) and self.value == other.value

    def __hash__(self) -> int:
        return hash((self.__class__, self.value))

    def __repr__(self) -> str:
        return f"Key({self.value!r})"


class IDGenerator:
    def __init__(self):
        self._count = 0

    def next_id(self) -> str:
        self._count += 1
        return f"fw_id_{self._count}"


PatchAction = Literal["INSERT", "REMOVE", "UPDATE", "MOVE", "REPLACE"]


@dataclass
class Patch:
    action: PatchAction
    html_id: str
    data: Dict[str, Any]


NodeData = Dict[str, Any]


@dataclass
class ReconciliationResult:
    patches: List[Patch] = field(default_factory=list)
    new_rendered_map: Dict[Union[Key, str], NodeData] = field(default_factory=dict)
    active_css_details: Dict[str, Tuple[Callable, Any]] = field(default_factory=dict)
    registered_callbacks: Dict[str, Callable] = field(default_factory=dict)
    js_initializers: List[Dict] = field(default_factory=list)


# --- The Reconciler Class ---
class Reconciler:
    def __init__(self):
        self.context_maps: Dict[str, Dict[Union[Key, str], NodeData]] = {"main": {}}
        self.id_generator = IDGenerator()
        self._external_js_init_queue: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self._registered_js_initializers: Dict[str, Dict[str, Dict[str, Any]]] = defaultdict(dict)

        print("🪄  PyThra Framework | Reconciler Initialized")

    def get_map_for_context(self, context_key: str) -> Dict[Union[Key, str], NodeData]:
        return self.context_maps.setdefault(context_key, {})

    def clear_context(self, context_key: str):
        if context_key in self.context_maps:
            del self.context_maps[context_key]

    def clear_all_contexts(self):
        """Resets all stored render maps."""
        print("Reconciler: Clearing all contexts.")
        self.context_maps.clear()
        self.context_maps['main'] = {}

    def reconcile(
        self,
        previous_map: Dict,
        new_widget_root: Optional["Widget"],
        parent_html_id: str,
        old_root_key: Optional[Union[Key, str]] = None,
        is_partial_reconciliation: bool = False
    ) -> ReconciliationResult:
        """
        Compares a new widget tree with the previous state and generates patches.
        """
        result = ReconciliationResult()

        # Auto-delegate to Rust adapter if available for better performance.
        try:
            from .rust_reconciler_adapter import RustReconcilerAdapter
            adapter = RustReconcilerAdapter(self)
            if adapter.is_available():
                print("🪄  Rust adapter available.")
                try:
                    rs_result = adapter.reconcile(
                        previous_map, new_widget_root, parent_html_id,
                        old_root_key, is_partial_reconciliation
                    )
                    # Let the adapter produce a full ReconciliationResult
                    print(f'Rust reconciler: {rs_result}')

                    return rs_result
                except Exception:
                    pass
                # pass
        except Exception:
            # Any import or adapter error should not prevent normal Python flow
            pass

        if old_root_key is None:
            # Find the root key from the previous map if not provided.
            for key, data in previous_map.items():
                if data.get("parent_html_id") == parent_html_id and data.get("parent_key") is None:
                    old_root_key = key
                    break
        
        # Start the recursive diffing process, passing `None` as the initial parent_key.
        self._diff_node_recursive(
            old_node_key=old_root_key,
            new_widget=new_widget_root,
            parent_html_id=parent_html_id,
            parent_key=None,  # The root has no parent widget.
            result=result,
            previous_map=previous_map
        )

        if not is_partial_reconciliation:
            old_keys = set(previous_map.keys())
            new_keys = set(result.new_rendered_map.keys())
            removed_keys = old_keys - new_keys
            for key in removed_keys:
                data = previous_map.get(key, {})
                if not data: continue
                if isinstance(data.get("widget_instance"), StatefulWidget):
                    state = data["widget_instance"].get_state()
                    if state: state.dispose()
                if data.get("html_id"):
                    result.patches.append(Patch(action="REMOVE", html_id=data["html_id"], data={}))

        # --- Inject any external JS initializers queued by register_js_initializer ---
        queued = self._external_js_init_queue.get("main", [])  # change context if you pass context
        if queued:
            # copy them so the result owns its copy
            result.js_initializers.extend([dict(q) for q in queued])
            # clear the queue for that context after pushing to result
            self._external_js_init_queue["main"].clear()

        print(f'Python reconciler: {result}')

        return result

    def _diff_node_recursive(
        self, old_node_key, new_widget, parent_html_id, parent_key, result, previous_map
    ):
        """Compares a new widget with its old version."""
        if new_widget is None:
            # If the new widget is None, it will be handled as a removal
            # in the _diff_children_recursive function.
            return

        old_data = previous_map.get(old_node_key)
        new_widget_key = new_widget.get_unique_id()

        if old_data is None:
            # The widget is new, insert it and its entire subtree.
            self._insert_node_recursive(new_widget, parent_html_id, parent_key, result, previous_map)
            return
            
        new_type = type(new_widget).__name__
        old_type = old_data.get("widget_type")
        new_props = new_widget.render_props()
        self._collect_details(new_widget, new_props, result)
        
        # If the type or key has changed, it's a replacement.
        if old_type != new_type or new_widget.key != old_data.get("key"):
            # The reconciler will treat this as a REMOVE and an INSERT
            # during the child diffing phase. We generate a specific REPLACE patch
            # to handle this more efficiently.
            new_props = new_widget.render_props()
            self._collect_details(new_widget, new_props, result)
            
            # CRITICAL: First, recursively remove all old descendants to avoid duplication
            # This ensures that when we insert the new widget's children, the old ones
            # are already cleaned up from the DOM tree.
            self._remove_descendants_recursive(old_data.get("children_keys", []), previous_map, result)
            
            # Insert the new node and its children into the map first.
            self._insert_node_recursive(new_widget, parent_html_id, parent_key, result, previous_map)

            # Then, create a REPLACE patch. The `html_id` is the old one to replace.
            new_html_stub = self._generate_html_stub(new_widget, old_data["html_id"], new_props)
            result.patches.append(
                Patch(action="REPLACE", html_id=old_data["html_id"], data={
                    "new_html": new_html_stub,
                    "new_props": new_props
                })
            )
            return

        # --- UPDATE PATH ---
        html_id = old_data["html_id"]
        new_props = new_widget.render_props()
        self._collect_details(new_widget, new_props, result)
        old_props_from_map = old_data.get("props", {})
        prop_changes = self._diff_props(old_props_from_map, new_props)

        widget_type_name = type(new_widget).__name__

        # --- THIS IS THE NEW LIFECYCLE HOOK ---
        if widget_type_name == "StatefulWidget" and prop_changes:
            old_widget_instance = old_data.get("widget_instance")
            state = new_widget.get_state()
            if state and old_widget_instance:
                # Call the lifecycle method, passing the old and new widget configs.
                state.didUpdateWidget(old_widget_instance, new_widget)
        # --- END OF NEW LIFECYCLE HOOK ---

        # ONLY generate an UPDATE patch for renderable widgets.
        if widget_type_name not in ["StatefulWidget", "StatelessWidget"]:
            old_props_from_map = old_data.get("props", {})
            prop_changes = self._diff_props(old_props_from_map, new_props)
            if prop_changes:
                patch_data = {"props": new_props, "old_props": old_props_from_map}
                if 'css_class' in prop_changes:
                    patch_data["props"]["old_shared_class"] = old_props_from_map.get("css_class")
                result.patches.append(Patch(action="UPDATE", html_id=html_id, data=patch_data))
        
        # Update the map with the new widget data, including the parent_key.
        result.new_rendered_map[new_widget_key] = {
            "html_id": html_id,
            "widget_type": new_type,
            "key": new_widget.key,
            "widget_instance": new_widget,
            "props": new_props,
            "parent_html_id": parent_html_id,
            "parent_key": parent_key, # Store the parent's unique key
            "children_keys": [c.get_unique_id() for c in new_widget.get_children()],
        }

        # Recurse on children, passing the current widget's key as their parent_key.
        child_parent_html_id = html_id if widget_type_name not in ["StatefulWidget", "StatelessWidget"] else parent_html_id
        self._diff_children_recursive(
            old_data.get("children_keys", []),
            new_widget.get_children(),
            child_parent_html_id, # <-- Pass the correct parent HTML ID
            new_widget.get_unique_id(),
            result,
            previous_map,
        )

    def _insert_node_recursive(
        self, new_widget, parent_html_id, parent_key, result, previous_map, before_id=None
    ):
        """Recursively handles the insertion of a new widget and its children."""
        if new_widget is None:
            return

        html_id = self.id_generator.next_id()
        new_props = new_widget.render_props()
        self._collect_details(new_widget, new_props, result)
        key = new_widget.get_unique_id()

        old_id = None
        new_id = None

        # --- ADD THIS BLOCK TO TRIGGER SIMPLEBAR INITIALIZATION ---
        if type(new_widget).__name__ == "Scrollbar":
            initializer = {
                "type": "SimpleBar",
                "target_id": html_id,
                "options": new_props.get("simplebar_options", {}),
            }
            result.js_initializers.append(initializer)
        # --- END OF NEW BLOCK ---

        # if type(new_widget).__name__ == "VirtualListView":
        #     result.js_initializers.append(
        #         {
        #             "type": "VirtualList",
        #             "target_id": new_widget.css_class,
        #             "item_count": new_widget.item_count,
        #             "estimated_height": new_widget.estimated_height,
        #         }
        #     )

        # --- NEW: Check for responsive clip path and add to initializers ---
        if "responsive_clip_path" in new_props:
            if html_id != new_id:
                old_id, new_id = new_id, html_id
            initializer_data = {
                "type": "ResponsiveClipPath",
                "target_id": html_id,
                "data": new_props["responsive_clip_path"],
                "before_id": old_id,
            }
            result.js_initializers.append(initializer_data)


        if "init_dropdown" in new_props:
            print("DROPDOWN INIT")
            if html_id != new_id:
                old_id, new_id = new_id, html_id
            initializer_data = {
                "type": "dropdown",
                "target_id": html_id,
                "data": new_props,
                "before_id": old_id,
            }
            result.js_initializers.append(initializer_data)

        if "type" in new_props and "init_slider" in new_props:
            print("SLIDER INIT")
            if html_id != new_id:
                old_id, new_id = new_id, html_id
            initializer_data = {
                "type": "slider",
                "target_id": html_id,
                "data": new_props,
                "before_id": old_id,
            }
            result.js_initializers.append(initializer_data)

        if "init_gesture_detector" in new_props:
            print("GESTURE-DETECTOR INIT")
            if html_id != new_id:
                old_id, new_id = new_id, html_id
            initializer_data = {
                "type": "gesture_detector",
                "target_id": html_id,
                "data": new_props,
                "before_id": old_id,
            }
            result.js_initializers.append(initializer_data)

        if "init_virtual_list" in new_props:
            print("VIRTUAL-LIST INIT: for ", html_id)
            if html_id != new_id:
                old_id, new_id = new_id, html_id
            initializer_data = {
                "type": "virtual_list",
                "target_id": html_id,
                "data": new_props,
                "before_id": old_id,
            }
            result.js_initializers.append(initializer_data)

        if "init_gradient_clip_border" in new_props:
            print("GRADIENT-CLIP-BORDER INIT")
            if html_id != new_id:
                old_id, new_id = new_id, html_id
            initializer_data = {
                "type": "gradient_clip_border",
                "target_id": html_id,
                "data": new_props,
                "before_id": old_id,
            }
            result.js_initializers.append(initializer_data)
        

        # --- END NEW ---

        # --- THIS IS THE NEW GENERIC INITIALIZER LOGIC ---
        js_init_data = new_props.get("_js_init")
        if js_init_data and isinstance(js_init_data, dict):
            # We don't need the html_id here, as the framework will have it
            # when it processes the initializer list.
            result.js_initializers.append({
                "widget_key": new_widget.get_unique_id(), # Use the widget's key for stable reference
                "data": js_init_data,
                "type": js_init_data['engine'],
                "target_id": html_id,
                "before_id": old_id,
            })
        # --- END OF NEW LOGIC ---
        
        # --- THIS IS THE FIX ---
        widget_type_name = type(new_widget).__name__
        
        # Store the node in the map, regardless of its type.
        result.new_rendered_map[key] = {
            "html_id": html_id,
            "widget_type": widget_type_name,
            "key": new_widget.key,
            "widget_instance": new_widget,
            "props": new_props,
            "parent_html_id": parent_html_id,
            "parent_key": parent_key,
            "children_keys": [c.get_unique_id() for c in new_widget.get_children()],
        }

        # ONLY generate a patch for renderable widgets.
        # StatefulWidget and StatelessWidget are hosts, not renderable elements.
        if widget_type_name not in ["StatefulWidget", "StatelessWidget"]:
            stub_html = self._generate_html_stub(new_widget, html_id, new_props)
            result.patches.append(Patch(action="INSERT", html_id=html_id, data={
                "html": stub_html, "parent_html_id": parent_html_id,
                "props": new_props, "before_id": before_id,
            }))
        # --- END OF FIX ---

        # Recurse for children, passing the current widget's key as their parent_key.
        for child in new_widget.get_children():
            # If the parent is composable (Stateless/Stateful), its children are rendered
            # into the same parent DOM element. Otherwise, they are rendered inside the parent's new DOM element.
            child_parent_html_id = parent_html_id if widget_type_name in ["StatefulWidget", "StatelessWidget"] else html_id
            self._insert_node_recursive(child, child_parent_html_id, key, result, previous_map)

    def _remove_descendants_recursive(
        self,
        children_keys: List[Union[Key, str]],
        previous_map: Dict,
        result: ReconciliationResult,
    ):
        """
        Recursively removes all descendants (and their descendants) from the patch list.
        This ensures that when we replace a widget, all its old children are properly
        removed from the DOM before new children are inserted.
        """
        for key in children_keys:
            if key not in previous_map:
                continue
            
            old_data = previous_map[key]
            
            # First, recursively remove this node's children
            self._remove_descendants_recursive(
                old_data.get("children_keys", []),
                previous_map,
                result
            )
            
            # Then, remove this node itself
            result.patches.append(Patch(action="REMOVE", html_id=old_data["html_id"], data={}))
            
            # Dispose of stateful widgets
            if isinstance(old_data.get("widget_instance"), StatefulWidget):
                state = old_data["widget_instance"].get_state()
                if state:
                    state.dispose()

    def _diff_children_recursive(
        self,
        old_children_keys: List[Union[Key, str]],
        new_children_widgets: List["Widget"],
        parent_html_id: str,
        parent_key: str, # Accept the parent's key
        result: ReconciliationResult,
        previous_map: Dict,
    ):
        """Efficiently diffs a list of child widgets."""
        if not old_children_keys and not new_children_widgets:
            return

        old_key_to_data = {key: previous_map[key] for key in old_children_keys if key in previous_map}
        new_key_to_widget = {widget.get_unique_id(): widget for widget in new_children_widgets}
        old_keys_set = set(old_key_to_data.keys())
        new_keys_set = set(new_key_to_widget.keys())

        # Identify and patch removals.
        keys_to_remove = old_keys_set - new_keys_set
        for key in keys_to_remove:
            old_data = old_key_to_data[key]
            result.patches.append(Patch(action="REMOVE", html_id=old_data["html_id"], data={}))
            if isinstance(old_data.get("widget_instance"), StatefulWidget):
                state = old_data["widget_instance"].get_state()
                if state: state.dispose()

        # Handle updates, inserts, and moves.
        last_placed_old_idx = -1
        old_key_to_index = {key: i for i, key in enumerate(old_children_keys)}

        for i, new_widget in enumerate(new_children_widgets):
            new_key = new_widget.get_unique_id()

            if new_key in old_keys_set:
                # It's an existing widget, so diff it, passing the parent_key.
                self._diff_node_recursive(new_key, new_widget, parent_html_id, parent_key, result, previous_map)
                
                # Check for moves.
                old_idx = old_key_to_index[new_key]
                if old_idx < last_placed_old_idx:
                    moved_html_id = result.new_rendered_map[new_key]["html_id"]
                    before_id = self._find_next_stable_html_id(i + 1, new_children_widgets, old_key_to_index, result.new_rendered_map)
                    result.patches.append(Patch("MOVE", moved_html_id, {"parent_html_id": parent_html_id, "before_id": before_id}))
                last_placed_old_idx = max(last_placed_old_idx, old_idx)
            else:
                # It's a new widget, so insert it, passing the parent_key.
                before_id = self._find_next_stable_html_id(i + 1, new_children_widgets, old_key_to_index, result.new_rendered_map)
                self._insert_node_recursive(new_widget, parent_html_id, parent_key, result, previous_map, before_id=before_id)

    def _find_next_stable_html_id(self, start_index, new_widgets, old_key_map, new_rendered_map):
        for j in range(start_index, len(new_widgets)):
            key = new_widgets[j].get_unique_id()
            if key in old_key_map and key in new_rendered_map:
                return new_rendered_map[key]["html_id"]
        return None

    def _collect_details(self, widget, props, result):
        """Collects CSS classes and callbacks."""
        # Collect CSS classes
        css_classes = props.get("css_class", "").split()
        if hasattr(widget, "get_required_css_classes"):
            css_classes.extend(widget.get_required_css_classes())
        for css_class in set(css_classes):
            if css_class and css_class not in result.active_css_details:
                if hasattr(type(widget), "generate_css_rule") and hasattr(widget, "style_key"):
                    result.active_css_details[css_class] = (
                        getattr(type(widget), "generate_css_rule"),
                        getattr(widget, "style_key"),
                    )

        # Unified callback registration
        for prop_name, callback_name_value in props.items():
            if prop_name.endswith("Name") and callback_name_value or prop_name == 'onDragName' and callback_name_value:
                function_prop_name = prop_name[:-4]
                if hasattr(widget, function_prop_name):
                    callback_function = getattr(widget, function_prop_name)
                    if callable(callback_function):
                        result.registered_callbacks[callback_name_value] = callback_function
                        # print(f"Successfully registered callback for [{callback_name_value}] with function: [{callback_function}]\n")
                if function_prop_name == 'onDrag':
                    callback_function = props[function_prop_name]
                    # print(f'callback_function: {callback_function}')
                    if callable(callback_function):
                        result.registered_callbacks[callback_name_value] = callback_function
                        # print(f"Successfully registered callback for [{callback_name_value}] with function: [{callback_function}]\n")


        # --- THIS IS THE NEW GENERIC INITIALIZER LOGIC ---
        # js_init_data = props.get("_js_init")
        # if js_init_data and isinstance(js_init_data, dict):
        #     # We don't need the html_id here, as the framework will have it
        #     # when it processes the initializer list.
        #     result.js_initializers.append({
        #         "widget_key": widget.get_unique_id(), # Use the widget's key for stable reference
        #         "data": js_init_data
        #     })
        # --- END OF NEW LOGIC ---

    # ... (the rest of your file: _get_widget_render_tag, _generate_html_stub, _diff_props) ...
    # No changes are needed in the methods below this point.

    def _get_widget_render_tag(self, widget: "Widget") -> str:
        widget_type_name = type(widget).__name__
        tag_map = {
            "Text": "p",
            "Image": "img",
            "Icon": "i",
            "Spacer": "div",
            "SizedBox": "div",
            "TextButton": "button",
            "ElevatedButton": "button",
            "IconButton": "button",
            "FloatingActionButton": "button",
            "SnackBarAction": "button",
            "ListTile": "div",
            "Divider": "div",
            "Dialog": "div",
            "AspectRatio": "div",
            "ClipPath": "div",
        }
        if widget_type_name == "Icon" and getattr(widget, "custom_icon_source", None):
            return "img"
        return tag_map.get(widget_type_name, "div")

    def _generate_html_stub(self, widget: "Widget", html_id: str, props: Dict) -> str:
        tag, classes = self._get_widget_render_tag(widget), props.get("css_class", "")

        widget_type_name = type(widget).__name__

        inline_styles = {}

        if hasattr(type(widget), "_generate_html_stub"):
            return type(widget)._generate_html_stub(widget, html_id, props)

        # --- MODIFICATION TO HANDLE GENERIC ATTRIBUTES ---
        attrs = ""
        # Add attributes from a dedicated 'attributes' prop if it exists
        if "attributes" in props:
            for attr_name, attr_value in props["attributes"].items():
                attrs += f' {html.escape(attr_name)}="{html.escape(str(attr_value), quote=True)}"'
        # --- END MODIFICATION ---

        inner_html = ""

        if widget_type_name == "VirtualListView":
            return f"""
            <div id="{html_id}" class="{props.get('css_class','')}" style="color: peach;">
            <div class="viewport" id="{html_id}_viewport">
                <div class="phantom"></div>
            </div>
            </div>
            """

        # --- THIS IS THE FIX ---
        # Special handling for Font Awesome icons.
        if widget_type_name == "Icon":
            icon_name = props.get("data")
            if icon_name:
                # Prepend the necessary Font Awesome classes.
                inner_html = f"{icon_name}".strip()
                # print("Icon FA: ", icon_name)
            # else:
            #     print("Data: ",props.get('data'))
        # --- END OF FIX ---

        if widget_type_name == "ClipPath":
            if "width" in props:
                inline_styles["width"] = props["width"]
            if "height" in props:
                # print(f"height: {props["height"]}")
                inline_styles["height"] = props["height"]
            if "clip_path_string" in props:
                inline_styles["clip-path"] = props["clip_path_string"]
            # print("CLIP-PATH STRING: ", props)
            if (
                "aspectRatio" in props and props["aspectRatio"] is not None
            ):  # <-- ADD THIS
                inline_styles["aspect-ratio"] = props["aspectRatio"]
        elif widget_type_name == "SizedBox":
            if (w := props.get("width")) is not None:
                inline_styles["width"] = f"{w}px" if isinstance(w, (int, float)) else w
            if (h := props.get("height")) is not None:
                inline_styles["height"] = f"{h}px" if isinstance(h, (int, float)) else h
        elif widget_type_name == "Divider":
            if "height" in props:
                inline_styles["height"] = f"{props['height']}px"
            if "color" in props:
                inline_styles["background-color"] = props["color"]
            if "margin" in props:
                inline_styles["margin"] = props["margin"]
        elif widget_type_name == "AspectRatio":
            if "aspectRatio" in props:
                inline_styles["aspect-ratio"] = props["aspectRatio"]

        # --- THIS IS THE ARCHITECTURAL FIX ---
        # Generic handling for a 'style' dictionary from render_props.
        # This makes the initial render consistent with the update patcher.
        if "style" in props and isinstance(props["style"], dict):
            for key, value in props["style"].items():
                # print("css kebab-case: ",props["style"].items())
                # Convert python camelCase to css kebab-case
                css_key = "".join(["-" + c.lower() if c.isupper() else c for c in key]).lstrip("-")
                inline_styles[css_key] = value
        # --- END OF FIX ---

        if 'position_type' in props:
            # print("position_type:", props["position_type"])
            inline_styles["position"] = props["position_type"]

        if widget_type_name == "Positioned":
            inline_styles["height"] = props["height"] if props["height"] else ""
            inline_styles["width"] = props["width"] if props["width"] else ""
            inline_styles["bottom"] = props["bottom"] if props["bottom"] else ""
            inline_styles["top"] = props["top"] if props["top"] else ""
            inline_styles["right"] = props["right"] if props["right"] else ""
            inline_styles["left"] = props["left"] if props["left"] else ""
            # print(props, " with attrs: ", attrs," with inline_styles: ", inline_styles)

        if inline_styles:
            style_str = "; ".join(
                f"{k.replace('_','-')}: {v}"
                for k, v in inline_styles.items()
                if v is not None
            )
            if style_str:
                attrs += f' style="{html.escape(style_str, quote=True)}"'

        # Add event handlers
        if "onPressedName" in props and props.get("enabled", True):
            
            if cb_name := props["onPressedName"]:
                if props["onPressedArgs"] != []:
                    # [print("arg: ", x) for x in props["onPressedArgs"]]
                    # print("ARGS: ",props["onPressedArgs"] if props["onPressedArgs"] else 'None') #["onPressedArgs"] if props["onPressedArgs"] else 'None'
                    attrs += (
                        f" onclick=\"handleClickWithArgs('{html.escape(cb_name, quote=True)}', {props['onPressedArgs']})\""
                    )
                else:
                    attrs += (
                        f" onclick=\"handleClick('{html.escape(cb_name, quote=True)}')\""
                    )
        elif "onTapName" in props and props.get("enabled", True):
            if cb_name := props.get("onTapName"):
                if props["onTapArg"] != []:
                    # [print("arg: ", x) for x in props["onPressedArgs"]]
                    # print("ARGS: ",props["onPressedArgs"] if props["onPressedArgs"] else 'None') #["onPressedArgs"] if props["onPressedArgs"] else 'None'
                    attrs += (
                        f" onclick=\"handleClickWithArgs('{html.escape(cb_name, quote=True)}', {props['onTapArg']})\""
                    )
                else:
                    attrs += (
                        f" onclick=\"handleClick('{html.escape(cb_name, quote=True)}')\""
                    )
        elif "onItemTapName" in props and props.get("enabled", True):
            if cb_name := props.get("onItemTapName"):
                attrs += f' onclick="handleItemTap(\'{html.escape(cb_name, quote=True)}\', {props.get("item_index", -1)})"'

        if props.get("tooltip"):
            attrs += f' title="{html.escape(props["tooltip"], quote=True)}"'

        if widget_type_name == "Text":
            inner_html = html.escape(str(props.get("data", "")))
            # print("Text style props: ",props.get('style'))
        elif widget_type_name == "Image":
            attrs += f' src="{html.escape(props.get("src", ""), quote=True)}" alt=""'
        elif widget_type_name == "Icon" and props.get("render_type") == "img":
            attrs += f' src="{html.escape(props.get("custom_icon_src", ""), quote=True)}" alt=""'


        

        # if hasattr(type(widget), '_generate_html_stub'):
        #     return type(widget)._generate_html_stub(widget, html_id, props)

        if tag in ["img", "hr", "br"]:
            return f'<{tag} id="{html_id}" class="{classes}"{attrs}>'
        return f'<{tag} id="{html_id}" class="{classes}"{attrs}>{inner_html}</{tag}>'

    # def _diff_props(self, old_props: Dict, new_props: Dict) -> Optional[Dict]:
    #     changes = {}
    #     all_keys = set(old_props.keys()) | set(new_props.keys())
    #     for key in all_keys:
    #         old_val, new_val = old_props.get(key), new_props.get(key)
    #         if old_val != new_val:
    #             changes[key] = new_val
    #     return changes if changes else None

    def _diff_props(self, old_props: Dict, new_props: Dict) -> Optional[Dict]:
        changes = {}
        # --- THIS IS THE FIX ---
        # Define a set of properties to ignore during the diffing process.
        # These are typically function references that are re-created on every build.
        ignored_keys = {'widget_instance', 'itemBuilder', 'onChanged', 'onPressed', 'onTap', 'onDrag'}
        # --- END OF FIX ---
            # Combine keys, but exclude 'widget_instance' from the check
        all_keys = (set(old_props.keys()) | set(new_props.keys())) - ignored_keys

        for key in all_keys:
            old_val, new_val = old_props.get(key), new_props.get(key)
            if old_val != new_val:
                # This check is crucial for mutable types like lists/dicts in props
                if isinstance(old_val, (list, dict)) and old_val == new_val:
                    continue
                changes[key] = new_val
        return changes if changes else None

    def register_js_initializer(self, initializer: Dict[str, Any], context_key: str = "main") -> str:
        """
        Register an external JS initializer to be emitted on the next reconcile call.

        Example usage:
            self.framework.reconciler.register_js_initializer({
                'type': 'PythraMarkdownEditor',
                'targetId': self._container_html_id or 'fw_id_8',
                'options': {'callback': self._callback_name, 'instanceId': instance_id}
            })

        Returns:
            initializer_id (str): an opaque id for this registered initializer.
        """
        if not isinstance(initializer, dict):
            raise TypeError("initializer must be a dict")

        # Normalize common key names
        init = dict(initializer)  # shallow copy to avoid mutating caller object
        # Accept both camelCase and snake_case for target id
        if "targetId" in init:
            init["target_id"] = init.pop("targetId")
        elif "target_id" not in init:
            # we allow missing target_id (some init types may set target later) but warn
            # raise ValueError("initializer must include 'targetId' or 'target_id'")
            init.setdefault("target_id", None)

        # Validate 'type'
        if "type" not in init or not init["type"]:
            raise ValueError("initializer must include a non-empty 'type' field")

        # Ensure options key exists
        init.setdefault("options", {})

        # Generate stable initializer id
        initializer_id = f"js_init_{uuid.uuid4().hex[:8]}"
        init["_id"] = initializer_id
        init["_registered_at"] = True

        # Save into per-context registry and queue
        self._registered_js_initializers[context_key][initializer_id] = init
        self._external_js_init_queue[context_key].append(init)

        print(f"Registered JS initializer [{initializer_id}] for context [{context_key}]: {init}")

        # Return the id so the caller can reference or cancel later
        return initializer_id

    def unregister_js_initializer(self, initializer_id: str, context_key: str = "main") -> bool:
        """
        Unregister a previously registered initializer. Returns True if removed.
        """
        if initializer_id in self._registered_js_initializers.get(context_key, {}):
            # remove from registry
            del self._registered_js_initializers[context_key][initializer_id]
            # remove from queue if present
            q = self._external_js_init_queue.get(context_key, [])
            self._external_js_init_queue[context_key] = [i for i in q if i.get("_id") != initializer_id]
            return True
        return False


# --- Optional: Runtime adapter to use the Rust reconciler as a drop-in replacement ---
# If the compiled `rust_reconciler` extension is available, this adapter will
# delegate calls to it and normalize the result to the Python `ReconciliationResult`
# so the rest of the Python codebase can use the same API without changes.
try:
    import rust_reconciler
    _RUST_AVAILABLE = True
except Exception:
    rust_reconciler = None
    _RUST_AVAILABLE = False


if _RUST_AVAILABLE:
    class RustReconcilerAdapter:
        """A thin adapter that exposes the same `Reconciler` API as the
        Python implementation but delegates to the compiled Rust extension.
        """

        def __init__(self):
            # detect whether the extension exposes a Reconciler class or a module-level function
            if hasattr(rust_reconciler, "Reconciler"):
                self._impl = rust_reconciler.Reconciler()
                self._use_class = True
            else:
                # module-level function: reconcile(old_tree_py, new_tree_py)
                self._impl = rust_reconciler.reconcile
                self._use_class = False
            # Also capture the module-level reconcile if present (safe dict-based API)
            self._module_reconcile = getattr(rust_reconciler, "reconcile", None)
        
        def is_available(self) -> bool:
            return True

        def get_map_for_context(self, context_key: str):
            # Check if we have a cached context_maps attribute (set by Framework during initial render)
            if hasattr(self, "context_maps") and isinstance(self.context_maps, dict):
                return self.context_maps.get(context_key, {})
            
            # best-effort: Rust implementation manages its own contexts; if class available, delegate
            if self._use_class and hasattr(self._impl, "get_map_for_context"):
                return self._impl.get_map_for_context(context_key)
            return {}

        def clear_context(self, context_key: str):
            if self._use_class and hasattr(self._impl, "clear_context"):
                return self._impl.clear_context(context_key)

        def clear_all_contexts(self):
            if self._use_class and hasattr(self._impl, "clear_all_contexts"):
                return self._impl.clear_all_contexts()

        def _generate_html_stub(self, widget: "Widget", html_id: str, props: Dict) -> str:
            """Generate HTML for a widget using the Rust helper when available.

            The Rust extension may provide either a module-level `generate_html_stub`
            helper or a method on the `Reconciler` class instance. Try those first
            for performance parity. If neither is available or calling them fails,
            fall back to the original Python implementation that lives above in
            this module (we call the same logic as the Python Reconciler did).
            """
            # Try class-backed implementation
            try:
                if self._use_class and hasattr(self._impl, "generate_html_stub"):
                    result = self._impl.generate_html_stub(widget, html_id, props)
                    return result

                # Try module-level helper
                gen = getattr(rust_reconciler, "generate_html_stub", None)
                if gen is not None:
                    result = gen(widget, html_id, props)
                    print(f"DEBUG: rust_reconciler.generate_html_stub returned: {result[:100] if result else 'None'}")
                    return result
            except Exception as e:
                # Ignore and fall back to Python implementation below
                print(f"DEBUG: Rust stub generator failed: {type(e).__name__}: {e}")
                import traceback
                traceback.print_exc()

            # Fallback: replicate the same behavior as the Python Reconciler's
            # `_generate_html_stub` method defined earlier in this module. We
            # call that method by creating a temporary Python Reconciler instance
            # to reuse its implementation.
            try:
                # The original Python Reconciler class is defined earlier in this
                # file under the name `Reconciler` prior to the adapter override.
                # Import it by its original qualified name via the module's globals.
                OriginalReconciler = globals().get("Reconciler")
                if OriginalReconciler and hasattr(OriginalReconciler, "_generate_html_stub"):
                    # Instantiate a throwaway Reconciler to reuse the method implementation
                    temp = OriginalReconciler.__new__(OriginalReconciler)
                    # Call the unbound method with the temp as self
                    return OriginalReconciler._generate_html_stub(temp, widget, html_id, props)
            except Exception:
                pass

            # As a final safety net produce a minimal stub
            tag = getattr(type(widget), "__name__", "div")
            return f'<div id="{html_id}" class="{props.get("css_class", "")}"></div>'

        def _get_widget_render_tag(self, widget: "Widget") -> str:
            """Delegate to the original Python reconciler's tag resolver."""
            OriginalReconciler = globals().get("Reconciler")
            try:
                if OriginalReconciler and hasattr(OriginalReconciler, "_get_widget_render_tag"):
                    temp = OriginalReconciler.__new__(OriginalReconciler)
                    return OriginalReconciler._get_widget_render_tag(temp, widget)
            except Exception:
                pass
            # Basic fallback
            return getattr(type(widget), "__name__", "div")

        def _diff_props(self, old_props: Dict, new_props: Dict) -> Optional[Dict]:
            """Delegate property diffing to the original implementation."""
            OriginalReconciler = globals().get("Reconciler")
            try:
                if OriginalReconciler and hasattr(OriginalReconciler, "_diff_props"):
                    temp = OriginalReconciler.__new__(OriginalReconciler)
                    return OriginalReconciler._diff_props(temp, old_props, new_props)
            except Exception:
                pass
            # Naive fallback
            changes = {}
            all_keys = set(old_props.keys()) | set(new_props.keys())
            for k in all_keys:
                if old_props.get(k) != new_props.get(k):
                    changes[k] = new_props.get(k)
            return changes or None

        def _collect_details(self, widget, props, result):
            """Collect CSS, callbacks and other details via Python implementation."""
            OriginalReconciler = globals().get("Reconciler")
            try:
                if OriginalReconciler and hasattr(OriginalReconciler, "_collect_details"):
                    temp = OriginalReconciler.__new__(OriginalReconciler)
                    return OriginalReconciler._collect_details(temp, widget, props, result)
            except Exception:
                pass
            return None

        def reconcile(
            self,
            previous_map: Dict,
            new_widget_root: Optional["Widget"],
            parent_html_id: str,
            old_root_key: Optional[Union[Key, str]] = None,
            is_partial_reconciliation: bool = False,
        ) -> ReconciliationResult:
            # Normalize previous_map
            old_map = previous_map or {}

            if self._use_class:
                # Ensure keys and certain nested fields are converted to strings so the Rust side
                # (which expects JSON-serializable dicts with string keys) can accept them.
                def _prepare_map_for_rust(m: Dict) -> Dict:
                    if not isinstance(m, dict):
                        return {}
                    out = {}
                    # Helper to sanitize props into JSON-safe values
                    def _sanitize_value(val):
                        import inspect
                        import json
                        
                        # Basic types are JSON-serializable
                        if val is None or isinstance(val, (str, int, float, bool)):
                            return val
                        
                        # Check if it's ANY kind of callable (functions, methods, lambdas, etc)
                        if callable(val) or inspect.ismethod(val) or inspect.isfunction(val) or inspect.isbuiltin(val):
                            return None
                        
                        # Lists/tuples: sanitize elements
                        if isinstance(val, (list, tuple)):
                            return [_sanitize_value(v) for v in val]
                        
                        # Dicts: sanitize keys and values recursively
                        if isinstance(val, dict):
                            return {str(k): _sanitize_value(v) for k, v in val.items()}
                        
                        # Try to JSON serialize - this is the final test
                        try:
                            json.dumps(val)
                            return val
                        except (TypeError, ValueError):
                            # Not JSON-serializable, convert to string
                            return str(val) if val is not None else None
                    def _stringify_key(obj):
                        # Prefer an explicit __str_key__ hook if present
                        try:
                            hook = getattr(obj, "__str_key__", None)
                            if callable(hook):
                                return hook()
                        except Exception:
                            pass

                        # Fall back to value attribute if present (common Key implementations)
                        try:
                            if hasattr(obj, "value"):
                                print("Key value: ", str(obj.value))
                                return str(obj.value)
                        except Exception:
                            pass

                        # Last resort: use str()
                        try:
                            return str(obj)
                        except Exception:
                            return repr(obj)

                    for k, v in m.items():
                        ks = _stringify_key(k)

                        if isinstance(v, dict):
                            nv = {}
                            for nk, nv_val in v.items():
                                # convert embedded keys used by the reconciler
                                if nk in ("key", "parent_key"):
                                    # Rust expects string values for these fields. Convert None -> ""
                                    # and stringify any non-str keys to avoid passing NoneType to Rust.
                                    if nv_val is None:
                                        nv[nk] = ""
                                    elif isinstance(nv_val, str):
                                        nv[nk] = nv_val
                                    else:
                                        nv[nk] = _stringify_key(nv_val)
                                elif nk == "widget_instance":
                                    # Do not pass live Python objects to Rust; use null
                                    nv[nk] = None
                                elif nk == "props":
                                    # Sanitize props dict to JSON-safe values
                                    try:
                                        if isinstance(nv_val, dict):
                                            nv[nk] = {str(pk): _sanitize_value(pv) for pk, pv in nv_val.items()}
                                        else:
                                            nv[nk] = _sanitize_value(nv_val)
                                    except Exception:
                                        nv[nk] = {}
                                else:
                                    # Sanitize generic values to avoid method/function serialization
                                    try:
                                        nv[nk] = _sanitize_value(nv_val)
                                    except Exception:
                                        nv[nk] = None
                            out[ks] = nv
                        else:
                            # Non-dict entries in the map are unexpected; coerce to safe empty dict
                            out[ks] = {}
                    return out
                    # Quick self-check: ensure the prepared map is JSON-serializable.
                    try:
                        import json as _json
                        _json.dumps(out)
                    except Exception as _e:
                        # Attempt to find the first non-serializable entry for diagnostics
                        def _find_bad(path, val):
                            if val is None or isinstance(val, (str, int, float, bool)):
                                return None
                            if isinstance(val, (list, tuple)):
                                for i, v in enumerate(val):
                                    res = _find_bad(f"{path}[{i}]", v)
                                    if res:
                                        return res
                                return None
                            if isinstance(val, dict):
                                for k, v in val.items():
                                    res = _find_bad(f"{path}.{k}", v)
                                    if res:
                                        return res
                                return None
                            return (path, type(val).__name__)

                        bad = _find_bad("root", out)
                        print("Sanitizer: json.dumps failed when preparing map for Rust:", _e)
                        print("Sanitizer: first non-serializable entry:", bad)
                        # fall through and return out anyway; diagnostics will be in logs

                rust_old_map = _prepare_map_for_rust(old_map)

                # For safety prefer the dict-based module reconcile when possible.
                # This avoids passing Python widget instances (which may return Key objects)
                # into Rust's `extract::<String>()` calls.
                if self._module_reconcile is not None:
                    # synthesize a minimal new_map from the Python widget tree (stringify keys)
                    if new_widget_root is None:
                        rust_new_map = {}
                    elif isinstance(new_widget_root, dict):
                        rust_new_map = _prepare_map_for_rust(new_widget_root)
                    else:
                        # walk the root widget and create a basic node entry
                        try:
                            root_key = new_widget_root.get_unique_id()
                        except Exception:
                            root_key = "root"
                        try:
                            props = new_widget_root.render_props()
                        except Exception:
                            props = {}

                        rust_new_map = {
                            str(root_key): {
                                "html_id": "fw_id_adapter",
                                "widget_type": getattr(new_widget_root, "__class__", type(new_widget_root)).__name__,
                                "key": str(root_key),
                                "widget_instance": None,
                                "props": props,
                                "parent_html_id": parent_html_id,
                                "parent_key": None,
                                "children_keys": [],
                            }
                        }

                    # Sanitize the synthesized new map before passing to the Rust module
                    try:
                        rust_new_map = _prepare_map_for_rust(rust_new_map)
                    except Exception:
                        # Fallback: ensure it's at least a dict of strings
                        rust_new_map = {str(k): {} for k in rust_new_map.keys()}

                    rust_result = self._module_reconcile(rust_old_map, rust_new_map)
                else:
                    # Fallback: call the class method, attempting to sanitize widget ids
                    # NOTE: Widget.render_props is already patched globally to return sanitized props
                    rust_new_widget = new_widget_root
                    try:
                        uniq = None
                        if rust_new_widget is not None:
                            uniq = rust_new_widget.get_unique_id()
                        if uniq is not None and not isinstance(uniq, str):
                            uniq_str = _prepare_map_for_rust({uniq: None})
                            if isinstance(uniq_str, dict):
                                uniq_str = next(iter(uniq_str.keys()))
                            else:
                                uniq_str = str(uniq)

                            class _WidgetProxy:
                                def __init__(self, w, ks):
                                    self._w = w
                                    self._ks = ks

                                def get_unique_id(self):
                                    return self._ks

                                def __getattr__(self, name):
                                    return getattr(self._w, name)

                            rust_new_widget = _WidgetProxy(new_widget_root, uniq_str)
                    except Exception as e:
                        print(f"DEBUG: _WidgetProxy creation failed: {e}")
                        rust_new_widget = new_widget_root

                    print("rust_new_widget key:", rust_new_widget.get_unique_id() if rust_new_widget else 'None')
                    print("rust_old_map keys:", list(rust_old_map.keys()))
                    print("parent_html_id:", parent_html_id)
                    print("is_partial_reconciliation:", is_partial_reconciliation)
                    print("old_root_key:", old_root_key)

                    rust_result = self._impl.reconcile(rust_old_map, rust_new_widget, parent_html_id, is_partial_reconciliation, old_root_key)
                # The Rust class implementation returns a mapping-like object with keys similar to the Python one
                return _convert_rust_result_to_py(rust_result)

            # Module-level function case: expects two dict-like maps and returns either a list of patches or a dict
            if new_widget_root is None:
                new_map = {}
            elif isinstance(new_widget_root, dict):
                new_map = new_widget_root
            else:
                # Synthesize a minimal new_map entry from the Python widget object
                try:
                    key = new_widget_root.get_unique_id()
                    props = new_widget_root.render_props()
                except Exception:
                    # If we can't extract widget shape, fall back to empty map
                    key = "root"
                    props = {}

                new_map = {
                    key: {
                        "html_id": "fw_id_adapter",
                        "widget_type": getattr(new_widget_root, "__class__", type(new_widget_root)).__name__,
                        "key": key,
                        "widget_instance": None,
                        "props": props,
                        "parent_html_id": parent_html_id,
                        "parent_key": None,
                        "children_keys": [],
                    }
                }

            out = self._impl(old_map, new_map)
            return _convert_rust_result_to_py(out)


    def _convert_rust_result_to_py(raw):
        """Normalize what the Rust extension returns into the Python
        ReconciliationResult dataclass used by the codebase.

        The Rust side may return:
        - a list of patch dicts (module-level `reconcile`), or
        - a mapping-like object with keys: 'patches', 'new_rendered_map',
          'active_css_details', 'registered_callbacks', 'js_initializers'
        """
        try:
            from collections.abc import Mapping
        except Exception:
            Mapping = dict

        if isinstance(raw, list):
            patches = []
            for p in raw:
                try:
                    patches.append(Patch(action=p.get("action"), html_id=p.get("html_id"), data=p.get("data", {})))
                except Exception:
                    # best-effort: skip malformed entries
                    continue
            return ReconciliationResult(patches=patches)

        if isinstance(raw, Mapping):
            patches_raw = raw.get("patches", [])
            patches = []
            for p in patches_raw:
                try:
                    patches.append(Patch(action=p.get("action"), html_id=p.get("html_id"), data=p.get("data", {})))
                except Exception:
                    continue

            new_map = raw.get("new_rendered_map", {})

            result_kwargs = {"patches": patches}
            # If the ReconciliationResult dataclass contains new_rendered_map, include it
            if "new_rendered_map" in ReconciliationResult.__annotations__:
                result_kwargs["new_rendered_map"] = new_map

            # === DEBUG: Print what we got from Rust ===
            print(f"\n=== DEBUG: Rust returned new_rendered_map with {len(new_map)} entries ===")
            for key in list(new_map.keys())[:5]:
                print(f"  Key: {key}, HTML len: {len(new_map[key].get('html', ''))}")
            print("=== END DEBUG ===\n")

            # Convert active_css_details (class -> (generator_callable, style_key))
            active_css_raw = raw.get("active_css_details", {}) or {}
            active_css = {}
            try:
                for css_class, val in active_css_raw.items():
                    # val is expected to be a 2-tuple (callable, style_key)
                    try:
                        gen_callable, style_key = val
                        active_css[css_class] = (gen_callable, style_key)
                    except Exception:
                        # best-effort: skip invalid entries
                        continue
            except Exception:
                active_css = {}

            if "active_css_details" in ReconciliationResult.__annotations__:
                # If Rust didn't provide active_css_details, try to synthesize them
                # from the returned new_rendered_map by inspecting widget instances
                if active_css:
                    result_kwargs["active_css_details"] = active_css
                else:
                    fallback_css = {}
                    try:
                        for node in new_map.values():
                            try:
                                props = node.get("props", {}) or {}
                                css_list = (props.get("css_class", "") or "").split()
                                widget_instance = node.get("widget_instance")
                                if not widget_instance:
                                    continue
                                for css_class in css_list:
                                    if not css_class:
                                        continue
                                    if css_class in fallback_css:
                                        continue
                                    # Prefer class-level generator if available
                                    gen = None
                                    style_key = None
                                    try:
                                        wt = type(widget_instance)
                                        if hasattr(wt, "generate_css_rule"):
                                            gen = getattr(wt, "generate_css_rule")
                                        if hasattr(widget_instance, "style_key"):
                                            style_key = getattr(widget_instance, "style_key")
                                    except Exception:
                                        gen = None
                                        style_key = None
                                    if gen and style_key is not None:
                                        fallback_css[css_class] = (gen, style_key)
                            except Exception:
                                continue
                    except Exception:
                        fallback_css = {}
                    result_kwargs["active_css_details"] = fallback_css

            # Registered callbacks (string -> callable)
            callbacks_raw = raw.get("registered_callbacks", {}) or {}
            callbacks = {}
            try:
                for name, cb in callbacks_raw.items():
                    try:
                        callbacks[name] = cb
                    except Exception:
                        continue
            except Exception:
                callbacks = {}

            if "registered_callbacks" in ReconciliationResult.__annotations__:
                result_kwargs["registered_callbacks"] = callbacks

            # JS initializers (list)
            js_inits = raw.get("js_initializers", []) or []
            if "js_initializers" in ReconciliationResult.__annotations__:
                result_kwargs["js_initializers"] = list(js_inits)

            return ReconciliationResult(**result_kwargs)

    # Replace the module-level Reconciler name so other imports get the adapter transparently
    Reconciler = RustReconcilerAdapter

