# framework/reconciler.py

"""
Handles the reconciliation process for the PyThra framework.
It compares the new widget tree with the previously rendered state and generates
a complete ReconciliationResult containing DOM patches, CSS details, and
callback details to efficiently update the UI.
"""

import uuid
from typing import Any, Dict, List, Optional, Tuple, Union, Callable, Literal
from dataclasses import dataclass, field

# It's good practice to import from your own project modules for type hints
# This helps static analysis tools and clarifies dependencies.
# TYPE_CHECKING block prevents circular import errors at runtime.
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .base import Widget, Key


# --- Key Class (A simple, robust implementation) ---
class Key:
    """A unique identifier for a widget to help distinguish it across rebuilds."""
    def __init__(self, value: Any):
        # This implementation ensures the key's value is always hashable.
        try:
            hash(value)
            self.value = value
        except TypeError:
            if isinstance(value, list):
                self.value = tuple(value)
            elif isinstance(value, dict):
                # Convert dict to a sorted tuple of items for consistent hashing
                self.value = tuple(sorted(value.items()))
            else:
                # As a last resort, convert to string, but raise if that also fails
                self.value = str(value)
                try:
                    hash(self.value)
                except TypeError:
                    raise TypeError(f"Key value {value!r} (type: {type(value)}) could not be made hashable for Key.")

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Key) and self.value == other.value

    def __hash__(self) -> int:
        # Include the class in the hash to distinguish Key(1) from just 1
        return hash((self.__class__, self.value))

    def __repr__(self) -> str:
        return f"Key({self.value!r})"


# --- ID Generator ---
class IDGenerator:
    """Generates unique, sequential HTML IDs for new elements."""
    def __init__(self):
        self._count = 0

    def next_id(self) -> str:
        self._count += 1
        return f"fw_id_{self._count}"


# --- Data Structures for Reconciliation ---

PatchAction = Literal['INSERT', 'REMOVE', 'UPDATE', 'MOVE']

@dataclass
class Patch:
    """Represents a single atomic change to be made to the DOM."""
    action: PatchAction
    html_id: str
    data: Dict[str, Any]

NodeData = Dict[str, Any]

@dataclass
class ReconciliationResult:
    """A complete, self-contained result of a reconciliation cycle."""
    patches: List[Patch] = field(default_factory=list)
    new_rendered_map: Dict[Union[Key, str], NodeData] = field(default_factory=dict)
    active_css_details: Dict[str, Tuple[Callable, Any]] = field(default_factory=dict)
    registered_callbacks: Dict[str, Callable] = field(default_factory=dict)


# --- The Reconciler Class ---

class Reconciler:
    """
    The core tree-diffing engine of the framework.
    It is stateless regarding a single reconciliation pass; it takes old state
    and a new tree, and produces a result.
    """
    def __init__(self):
        self.context_maps: Dict[str, Dict[Union[Key, str], NodeData]] = {'main': {}}
        self.id_generator = IDGenerator()
        print("Reconciler Initialized")

    def get_map_for_context(self, context_key: str) -> Dict[Union[Key, str], NodeData]:
        return self.context_maps.setdefault(context_key, {})

    def clear_context(self, context_key: str):
        if context_key in self.context_maps:
            del self.context_maps[context_key]

    # --- THE PUBLIC API ---
    def reconcile(self, previous_map: Dict, new_widget_root: Optional['Widget'], parent_html_id: str) -> ReconciliationResult:
        result = ReconciliationResult()
        
        old_root_key = None
        # Find the root key for this context. A root node is one whose parent is the target of reconciliation.
        for key, data in previous_map.items():
            if data.get('parent_html_id') == parent_html_id:
                old_root_key = key
                break
        
        self._diff_node_recursive(
            old_node_key=old_root_key,
            new_widget=new_widget_root,
            parent_html_id=parent_html_id,
            result=result,
            previous_map=previous_map
        )

        old_keys = set(previous_map.keys())
        new_keys = set(result.new_rendered_map.keys())
        removed_keys = old_keys - new_keys

        for key in removed_keys:
            data = previous_map[key]
            result.patches.append(Patch(action='REMOVE', html_id=data['html_id'], data={}))

        return result

    # --- Core Recursive Functions ---

    def _diff_node_recursive(self, old_node_key, new_widget, parent_html_id, result, previous_map):
        if new_widget is None:
            return

        old_data = previous_map.get(old_node_key)
        
        if old_data is None:
            self._insert_node_recursive(new_widget, parent_html_id, result, previous_map)
            return
        
        # --- THIS IS THE CRITICAL FIX ---
        # Determine if the nodes are compatible for an UPDATE.
        new_type = type(new_widget).__name__
        old_type = old_data.get('widget_type')
        
        # Incompatibility check:
        # 1. The types are different. (e.g., Container -> Row)
        # 2. The explicit developer-provided Keys are different.
        should_replace = (old_type != new_type) or \
                         (isinstance(old_data.get('key'), Key) and old_data.get('key') != new_widget.key)
        
        if should_replace:
            # A replacement is a REMOVE of the old and an INSERT of the new.
            # The REMOVE patch will be generated by the global removal logic at the end.
            self._insert_node_recursive(new_widget, parent_html_id, result, previous_map)
            return
        # --- END OF FIX ---

        # UPDATE PATH. The nodes are compatible; check for property changes.
        html_id = old_data['html_id']
        new_props = new_widget.render_props()

        self._collect_details(new_widget, new_props, result)

        prop_changes = self._diff_props(old_data.get('props', {}), new_props)
        if prop_changes:
            result.patches.append(Patch(action='UPDATE', html_id=html_id, data={'props': prop_changes}))

        # Use the NEW widget's unique ID for the new map key.
        new_key = new_widget.get_unique_id()
        result.new_rendered_map[new_key] = {
            'html_id': html_id, 'widget_type': new_type, 'key': new_widget.key,
            'widget_instance': new_widget, 'props': new_props,
            'parent_html_id': parent_html_id,
            'children_keys': [c.get_unique_id() for c in new_widget.get_children()]
        }

        self._diff_children_recursive(
            old_data.get('children_keys', []), new_widget.get_children(),
            html_id, result, previous_map
        )

    def _insert_node_recursive(self, new_widget, parent_html_id, result, previous_map, before_id=None):
        html_id = self.id_generator.next_id()
        new_props = new_widget.render_props()

        self._collect_details(new_widget, new_props, result)

        key = new_widget.get_unique_id()
        result.new_rendered_map[key] = {
            'html_id': html_id, 'widget_type': type(new_widget).__name__, 'key': new_widget.key,
            'widget_instance': new_widget, 'props': new_props,
            'parent_html_id': parent_html_id,
            'children_keys': [c.get_unique_id() for c in new_widget.get_children()]
        }

        stub_html = self._generate_html_stub(new_widget, html_id, new_props)
        patch_data = {'html': stub_html, 'parent_html_id': parent_html_id, 'props': new_props, 'before_id': before_id}
        result.patches.append(Patch(action='INSERT', html_id=html_id, data=patch_data))
        
        for child in new_widget.get_children():
            self._insert_node_recursive(child, html_id, result, previous_map)

    def _diff_children_recursive(self, old_children_keys, new_children_widgets, parent_html_id, result, previous_map):
        if not old_children_keys and not new_children_widgets: return

        old_key_to_index = {key: i for i, key in enumerate(old_children_keys)}
        
        # Process updates and moves for existing children
        last_placed_old_idx = -1
        processed_new_keys = set()

        for new_idx, new_widget in enumerate(new_children_widgets):
            new_key = new_widget.get_unique_id()
            processed_new_keys.add(new_key)
            old_idx = old_key_to_index.get(new_key)

            if old_idx is not None:
                # This is an existing child, process its updates
                self._diff_node_recursive(new_key, new_widget, parent_html_id, result, previous_map)
                
                # Check for a move
                if old_idx < last_placed_old_idx:
                    moved_html_id = result.new_rendered_map[new_key]['html_id']
                    before_id = self._find_next_stable_html_id(new_idx + 1, new_children_widgets, old_key_to_index, result.new_rendered_map)
                    result.patches.append(Patch('MOVE', moved_html_id, {'parent_html_id': parent_html_id, 'before_id': before_id}))
                else:
                    last_placed_old_idx = old_idx
        
        # Process new insertions
        for new_idx, new_widget in enumerate(new_children_widgets):
            new_key = new_widget.get_unique_id()
            if new_key not in old_key_to_index:
                before_id = self._find_next_stable_html_id(new_idx + 1, new_children_widgets, old_key_to_index, result.new_rendered_map)
                self._insert_node_recursive(new_widget, parent_html_id, result, previous_map, before_id=before_id)

    def _find_next_stable_html_id(self, start_index, new_widgets, old_key_map, new_rendered_map):
        for j in range(start_index, len(new_widgets)):
            key = new_widgets[j].get_unique_id()
            if key in old_key_map:
                if key in new_rendered_map:
                    return new_rendered_map[key]['html_id']
        return None

    # --- Helper and Utility Functions ---

    def _collect_details(self, widget, props, result):
        css_classes = props.get('css_class', '').split()
        if hasattr(widget, 'get_required_css_classes'):
            css_classes.extend(widget.get_required_css_classes())
        
        for css_class in set(css_classes):
             if not css_class: continue
             if css_class not in result.active_css_details:
                 if hasattr(type(widget), 'generate_css_rule') and hasattr(widget, 'style_key'):
                     gen_func = getattr(type(widget), 'generate_css_rule')
                     style_key = getattr(widget, 'style_key')
                     result.active_css_details[css_class] = (gen_func, style_key)
        
        callback_props = {'onPressedName': 'onPressed', 'onTapName': 'onTap'}
        for prop_name, func_name in callback_props.items():
            if prop_name in props and hasattr(widget, func_name):
                cb_name = props[prop_name]
                cb_func = getattr(widget, func_name)
                if cb_name and cb_func:
                    result.registered_callbacks[cb_name] = cb_func

    def _get_widget_render_tag(self, widget: 'Widget') -> str:
        widget_type_name = type(widget).__name__
        tag_map = {
            'Text': 'p', 'Image': 'img', 'Icon': 'i', 'Spacer': 'div',
            'TextButton': 'button', 'ElevatedButton': 'button', 'IconButton': 'button',
            'FloatingActionButton': 'button', 'SnackBarAction': 'button',
            'ListTile': 'div', 'Divider': 'div', 'Dialog': 'div',
        }
        if widget_type_name == 'Icon' and getattr(widget, 'custom_icon_source', None):
            return 'img'
        return tag_map.get(widget_type_name, 'div')

    def _generate_html_stub(self, widget, html_id, props):
        import html
        tag, classes = self._get_widget_render_tag(widget), props.get('css_class', '')
        attrs, inner_html = "", ""
        widget_type_name = type(widget).__name__

        if 'onPressedName' in props and props.get('enabled', True):
            cb_name = props['onPressedName']
            if cb_name: attrs += f' onclick="handleClick(\'{html.escape(cb_name, quote=True)}\')"'
        elif 'onTapName' in props and props.get('enabled', True):
            cb_name, item_idx = props['onTapName'], props.get("item_index", -1)
            if cb_name: attrs += f' onclick="handleItemTap(\'{html.escape(cb_name, quote=True)}\', {item_idx})"'
        
        if props.get('tooltip'): attrs += f' title="{html.escape(props["tooltip"], quote=True)}"'
        
        if widget_type_name == 'Text':
            inner_html = html.escape(str(props.get('data', '')))
        elif widget_type_name == 'Image':
            attrs += f' src="{html.escape(props.get("src", ""), quote=True)}" alt=""'
        elif widget_type_name == 'Icon' and props.get('render_type') == 'img':
            attrs += f' src="{html.escape(props.get("custom_icon_src", ""), quote=True)}" alt=""'

        if tag in ['img', 'hr', 'br']:
            return f'<{tag} id="{html_id}" class="{classes}"{attrs}>'
        else:
            return f'<{tag} id="{html_id}" class="{classes}"{attrs}>{inner_html}</{tag}>'

    def _diff_props(self, old_props, new_props):
        changes = {}
        all_keys = set(old_props.keys()) | set(new_props.keys())
        for key in all_keys:
            old_val, new_val = old_props.get(key), new_props.get(key)
            if old_val != new_val:
                changes[key] = new_val
        return changes if changes else None