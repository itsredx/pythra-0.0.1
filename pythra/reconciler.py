"""
Handles the reconciliation process for the PyThra framework.
It compares the new widget tree with the previously rendered state and generates
a complete ReconciliationResult containing DOM patches, CSS details, and
callback details to efficiently update the UI.
"""

import uuid
import html
from typing import Any, Dict, List, Optional, Tuple, Union, Callable, Literal
from dataclasses import dataclass, field

from .widgets import Scrollbar
from .state import StatefulWidget

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
        print("Reconciler Initialized")

    def get_map_for_context(self, context_key: str) -> Dict[Union[Key, str], NodeData]:
        return self.context_maps.setdefault(context_key, {})

    def clear_context(self, context_key: str):
        if context_key in self.context_maps:
            del self.context_maps[context_key]

    def reconcile(
        self,
        previous_map: Dict,
        new_widget_root: Optional["Widget"],
        parent_html_id: str,
        # --- NEW PARAMETERS FOR GRANULAR UPDATES ---
        old_root_key: Optional[Union[Key, str]] = None,
        is_partial_reconciliation: bool = False
    ) -> ReconciliationResult:
        """
        Compares a new widget tree (or subtree) with the previous state and
        generates a set of patches to update the UI.

        Args:
            previous_map: The map representing the state of the last render.
            new_widget_root: The root of the new widget tree to reconcile.
            parent_html_id: The HTML ID of the DOM element that will contain this tree.
            old_root_key: The specific key in the previous_map to start diffing from.
                          If None, it's inferred (for full renders).
            is_partial_reconciliation: If True, skips the final cleanup step to
                                       avoid deleting nodes outside the reconciled subtree.
        """
        result = ReconciliationResult()

        # If we are not given a specific key to start from (i.e., a full render),
        # find the old root key based on the parent HTML element.
        if old_root_key is None:
            for key, data in previous_map.items():
                if data.get("parent_html_id") == parent_html_id:
                    old_root_key = key
                    break

        # Start the recursive diffing process from the identified root.
        self._diff_node_recursive(
            old_root_key, new_widget_root, parent_html_id, result, previous_map
        )

        # --- CRITICAL ARCHITECTURAL CHANGE ---
        # Only perform the cleanup (removing old nodes) on a full, top-down reconciliation.
        # This prevents a partial update from incorrectly deleting the rest of the app.
        if not is_partial_reconciliation:
            old_keys = set(previous_map.keys())
            new_keys = set(result.new_rendered_map.keys())
            removed_keys = old_keys - new_keys

            for key in removed_keys:
                data = previous_map.get(key, {})
                if not data:
                    continue

                # Correctly call dispose() on stateful widgets before removing them.
                widget_instance = data.get("widget_instance")
                if widget_instance and isinstance(widget_instance, StatefulWidget):
                    state = widget_instance.get_state()
                    if state:
                        state.dispose()

                if data.get("html_id"):
                    result.patches.append(
                        Patch(action="REMOVE", html_id=data["html_id"], data={})
                    )

        return result

    # ... (rest of the Reconciler class: _diff_node_recursive, etc.) ...


    # In pythra/reconciler.py -> Reconciler class

    # REVERT THIS FUNCTION TO THE PREVIOUS, SIMPLER VERSION
    def _diff_node_recursive(
        self, old_node_key, new_widget, parent_html_id, result, previous_map
    ):
        if new_widget is None:
            return

        old_data = previous_map.get(old_node_key)

        if old_data is None:
            self._insert_node_recursive(
                new_widget, parent_html_id, result, previous_map
            )
            return

        # Check if nodes are fundamentally different (type or key mismatch)
        new_type = type(new_widget).__name__
        old_type = old_data.get("widget_type")
        new_key = new_widget.key
        old_key = old_data.get("key")

        if (old_type != new_type) or (old_key != new_key):
            # This node is a replacement. The _diff_children_recursive function
            # will see it as a REMOVE of the old and an INSERT of the new.
            # We don't need to do anything further here for this node.
            # The new widget will be handled by the parent's child diffing loop.
            return

        # --- UPDATE PATH ---
        # If we get here, the widget is the same, so we update its properties.
        html_id = old_data["html_id"]
        new_props = new_widget.render_props()
        self._collect_details(new_widget, new_props, result)

        old_props_from_map = old_data.get("props", {})
        prop_changes = self._diff_props(old_props_from_map, new_props)

        if prop_changes:
            patch_data = {"props": new_props}
            if 'css_class' in prop_changes:
                patch_data["props"]["old_shared_class"] = old_props_from_map.get("css_class")
            result.patches.append(
                Patch(action="UPDATE", html_id=html_id, data=patch_data)
            )

        # Update the map and recurse on children
        result.new_rendered_map[new_widget.get_unique_id()] = {
            "html_id": html_id,
            "widget_type": new_type,
            "key": new_widget.key,
            "widget_instance": new_widget,
            "props": new_props,
            "parent_html_id": parent_html_id,
            "children_keys": [c.get_unique_id() for c in new_widget.get_children()],
        }

        self._diff_children_recursive(
            old_data.get("children_keys", []),
            new_widget.get_children(),
            html_id,
            result,
            previous_map,
        )

    def _insert_node_recursive(
        self, new_widget, parent_html_id, result, previous_map, before_id=None
    ):

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

        if type(new_widget).__name__ == "VirtualListView":
            result.js_initializers.append(
                {
                    "type": "VirtualList",
                    "target_id": new_widget.css_class,
                    "item_count": new_widget.item_count,
                    "estimated_height": new_widget.estimated_height,
                }
            )

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

        # --- END NEW ---
        result.new_rendered_map[key] = {
            "html_id": html_id,
            "widget_type": type(new_widget).__name__,
            "key": new_widget.key,
            "widget_instance": new_widget,
            "props": new_props,
            "parent_html_id": parent_html_id,
            "children_keys": [c.get_unique_id() for c in new_widget.get_children()],
        }
        stub_html = self._generate_html_stub(new_widget, html_id, new_props)
        patch_data = {
            "html": stub_html,
            "parent_html_id": parent_html_id,
            "props": new_props,  # Pass the direct props for JS generation
            "before_id": before_id,
        }
        result.patches.append(Patch(action="INSERT", html_id=html_id, data=patch_data))
        for child in new_widget.get_children():
            self._insert_node_recursive(child, html_id, result, previous_map)

    # In pythra/reconciler.py -> Reconciler class

    def _diff_children_recursive(
        self,
        old_children_keys: List[Union[Key, str]],
        new_children_widgets: List["Widget"],
        parent_html_id: str,
        result: ReconciliationResult,
        previous_map: Dict,
    ):
        """
        Efficiently diffs a list of child widgets, handling insertions,
        removals, moves, and updates.
        """
        if not old_children_keys and not new_children_widgets:
            return # Nothing to do

        # --- ARCHITECTURAL FIX: A more robust child diffing algorithm ---

        # 1. Create maps for easy lookup of old and new children.
        old_key_to_data = {key: previous_map[key] for key in old_children_keys if key in previous_map}
        new_key_to_widget = {widget.get_unique_id(): widget for widget in new_children_widgets}

        old_keys_set = set(old_key_to_data.keys())
        new_keys_set = set(new_key_to_widget.keys())

        # 2. Identify widgets to be removed.
        # These are widgets that existed in the old list but not the new one.
        keys_to_remove = old_keys_set - new_keys_set
        for key in keys_to_remove:
            old_data = old_key_to_data[key]
            # Generate a REMOVE patch.
            result.patches.append(
                Patch(action="REMOVE", html_id=old_data["html_id"], data={})
            )
            # Also ensure its state is disposed if it was stateful
            widget_instance = old_data.get("widget_instance")
            if widget_instance and isinstance(widget_instance, StatefulWidget):
                state = widget_instance.get_state()
                if state:
                    state.dispose()

        # 3. Iterate through the NEW list to handle updates, inserts, and moves.
        last_placed_old_idx = -1
        old_key_to_index = {key: i for i, key in enumerate(old_children_keys)}

        for i, new_widget in enumerate(new_children_widgets):
            new_key = new_widget.get_unique_id()

            # Check if the widget existed before (update/move case).
            if new_key in old_keys_set:
                # It's an existing widget, so we recursively diff it.
                self._diff_node_recursive(
                    new_key, new_widget, parent_html_id, result, previous_map
                )
                
                # Now, check if it needs to be moved.
                old_idx = old_key_to_index[new_key]
                if old_idx < last_placed_old_idx:
                    # This node has moved forward in the list. Generate a MOVE patch.
                    moved_html_id = result.new_rendered_map[new_key]["html_id"]
                    before_id = self._find_next_stable_html_id(
                        i + 1, new_children_widgets, old_key_to_index, result.new_rendered_map
                    )
                    result.patches.append(
                        Patch(
                            "MOVE",
                            moved_html_id,
                            {"parent_html_id": parent_html_id, "before_id": before_id},
                        )
                    )
                last_placed_old_idx = max(last_placed_old_idx, old_idx)
            
            else:
                # It's a new widget. Generate an INSERT patch.
                before_id = self._find_next_stable_html_id(
                    i + 1, new_children_widgets, old_key_to_index, result.new_rendered_map
                )
                self._insert_node_recursive(
                    new_widget, parent_html_id, result, previous_map, before_id=before_id
                )

    def _find_next_stable_html_id(
        self, start_index, new_widgets, old_key_map, new_rendered_map
    ):
        for j in range(start_index, len(new_widgets)):
            key = new_widgets[j].get_unique_id()
            if key in old_key_map and key in new_rendered_map:
                return new_rendered_map[key]["html_id"]
        return None

    # def _build_svg_path_from_commands(self, commands: List['PathCommandWidget']) -> str:
    #     if not commands: return ""
    #     d_parts, current_pos = [], {'x': 0, 'y': 0}
    #     for command_widget in commands:
    #         if hasattr(command_widget, 'to_svg_command'):
    #             d_parts.append(command_widget.to_svg_command(current_pos))
    #     return " ".join(d_parts)

    def _collect_details(self, widget, props, result):
        css_classes = props.get("css_class", "").split()
        if hasattr(widget, "get_required_css_classes"):
            css_classes.extend(widget.get_required_css_classes())
        for css_class in set(css_classes):
            if css_class and css_class not in result.active_css_details:
                if hasattr(type(widget), "generate_css_rule") and hasattr(
                    widget, "style_key"
                ):
                    result.active_css_details[css_class] = (
                        getattr(type(widget), "generate_css_rule"),
                        getattr(widget, "style_key"),
                    )

        callback_props = {
            "onPressedName": "onPressed",
            "onTapName": "onTap",
            "onItemTapName": "onItemTap",
            "onChangedName": "onChanged",
        }
        for prop_name, func_name in callback_props.items():
            if prop_name in props and hasattr(widget, func_name):
                if (cb_name := props[prop_name]) and (
                    cb_func := getattr(widget, func_name)
                ):
                    result.registered_callbacks[cb_name] = cb_func
                    # print(f"Callback registerd sucssesfully [{cb_name}] with function [{cb_func}]")

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
                attrs += (
                    f" onclick=\"handleClick('{html.escape(cb_name, quote=True)}')\""
                )
        elif "onTapName" in props and props.get("enabled", True):
            if cb_name := props.get("onTapName"):
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
        # Combine keys, but exclude 'widget_instance' from the check
        all_keys = (set(old_props.keys()) | set(new_props.keys())) - {'widget_instance'}

        for key in all_keys:
            old_val, new_val = old_props.get(key), new_props.get(key)
            if old_val != new_val:
                # This check is crucial for mutable types like lists/dicts in props
                if isinstance(old_val, (list, dict)) and old_val == new_val:
                    continue
                changes[key] = new_val
        return changes if changes else None
