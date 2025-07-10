# pythra/reconciler.py

"""
Handles the indexed reconciliation process for the Pythra framework.

This reconciler uses an indexed diffing strategy, maintaining a registry of all
rendered nodes keyed by their unique `html_id`. This allows for highly efficient
updates by directly comparing the new widget state against the rendered state,
minimizing tree traversal and generating a precise list of DOM patches.
"""

import uuid
import html
import weakref
from typing import Any, Dict, List, Optional, Tuple, Union, Callable, Literal, Set
from dataclasses import dataclass, field

from .base import make_hashable

# It's good practice to import from your own project modules for type hints.
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .base import Widget, Key
    from .drawing import PathCommandWidget


# --- Core Data Structures ---

PatchAction = Literal['INSERT', 'REMOVE', 'UPDATE', 'MOVE', 'SVG_INSERT']

@dataclass
class Patch:
    """Represents a single DOM mutation operation to be sent to the frontend."""
    action: PatchAction
    html_id: str
    data: Dict[str, Any]

@dataclass
class RenderedNode:
    """Stores the state of a widget as it was last rendered to the DOM."""
    key: Union['Key', str]
    widget_type: str
    props_hash: int
    parent_html_id: str
    # Use a weak reference to the widget to prevent memory leaks.
    widget_instance_ref: weakref.ReferenceType
    # Store the html_ids of children to diff against on the next cycle.
    children_html_ids: List[str] = field(default_factory=list)

@dataclass
class ReconciliationResult:
    """Holds the complete result of a reconciliation cycle for a given context."""
    patches: List[Patch] = field(default_factory=list)
    # The new map is built during reconciliation and replaces the old one.
    new_rendered_map: Dict[Union['Key', str], Dict] = field(default_factory=dict)
    active_css_details: Dict[str, Tuple[Callable, Any]] = field(default_factory=dict)
    registered_callbacks: Dict[str, Callable] = field(default_factory=dict)
    js_initializers: List[Dict] = field(default_factory=list)


# --- The Reconciler Class ---

class Reconciler:
    """
    Orchestrates the diffing process between the new widget tree and the
    previously rendered state, producing patches to update the UI.
    """
    def __init__(self):
        # The master registry of all rendered UI contexts (main, dialog, etc.)
        # Each context maps widget keys to their rendered data.
        self.context_maps: Dict[str, Dict[Union['Key', str], Dict]] = {'main': {}}
        self.id_generator = IDGenerator()
        print("Indexed Reconciler Initialized.")

    def get_map_for_context(self, context_key: str) -> Dict[Union['Key', str], Dict]:
        """Retrieves or creates the rendered map for a given UI context."""
        return self.context_maps.setdefault(context_key, {})

    def clear_context(self, context_key: str):
        """Removes a UI context, e.g., when a dialog is closed."""
        if context_key in self.context_maps:
            del self.context_maps[context_key]

    def _hash_props(self, props: Dict) -> int:
        """
        Creates a deterministic hash from a widget's properties dictionary.
        This is the cornerstone of the optimization, allowing for quick checks
        to see if a widget's visual state has changed.
        """
        if not props:
            return 0
        # Sort items to ensure hash is consistent regardless of dict insertion order.
        sorted_items = sorted(props.items())
        # Use the make_hashable helper to convert complex style objects into
        # hashable representations (e.g., tuples).
        try:
            hashable_items = tuple((k, make_hashable(v)) for k, v in sorted_items)
            return hash(hashable_items)
        except TypeError as e:
            print(f"Warning: Could not hash props for widget. {e}. Props: {props}")
            # Fallback to a hash of the string representation (less reliable but won't crash)
            return hash(str(sorted_items))

    def reconcile(
        self,
        previous_map: Dict,
        new_widget_root: Optional['Widget'],
        parent_html_id: str
    ) -> ReconciliationResult:
        """
        The main entry point for a reconciliation cycle.

        Args:
            previous_map: The map of rendered widgets from the last cycle.
            new_widget_root: The root of the new widget tree to render.
            parent_html_id: The DOM element ID where this tree should be mounted.

        Returns:
            A ReconciliationResult containing all necessary UI updates.
        """
        result = ReconciliationResult()
        
        # This set will track all keys from the previous render that are
        # successfully matched and kept in the new render.
        visited_keys = set()

        # Begin the recursive diffing process.
        self._diff_node(
            parent_html_id=parent_html_id,
            new_widget=new_widget_root,
            previous_map=previous_map,
            result=result,
            visited_keys=visited_keys,
            before_id=None
        )

        # After diffing, any key in the old map that wasn't visited
        # corresponds to a widget that has been removed from the tree.
        old_keys = set(previous_map.keys())
        removed_keys = old_keys - visited_keys
        for key in removed_keys:
            if 'html_id' in previous_map[key]:
                result.patches.append(Patch(action='REMOVE', html_id=previous_map[key]['html_id'], data={}))

        return result

    def _diff_node(
        self,
        parent_html_id: str,
        new_widget: Optional['Widget'],
        previous_map: Dict,
        result: ReconciliationResult,
        visited_keys: Set,
        before_id: Optional[str]
    ):
        """
        Compares a new widget against its previously rendered state (if any)
        and generates the required patches.
        """
        # --- Case 1: Widget is removed ---
        if new_widget is None:
            # No new widget exists, so if there was an old one, it's a removal.
            # The cleanup loop in `reconcile` handles this.
            return

        new_key = new_widget.get_unique_id()
        old_data = previous_map.get(new_key)
        visited_keys.add(new_key)

        # --- Case 2: New widget is inserted ---
        if old_data is None:
            self._insert_node(new_widget, parent_html_id, result, before_id=before_id)
            return

        # --- Case 3: Widget might be updated ---
        html_id = old_data['html_id']
        new_props = new_widget.render_props()
        
        # Optimization: Compare props hash to avoid unnecessary updates.
        new_props_hash = self._hash_props(new_props)
        props_are_same = (new_props_hash == old_data.get('props_hash'))
        
        # Also check if widget type is the same. If not, it's a replacement.
        new_type_name = type(new_widget).__name__
        type_is_same = (new_type_name == old_data.get('widget_type'))

        if not type_is_same:
            # Type mismatch means we must replace the node entirely.
            result.patches.append(Patch(action='REMOVE', html_id=html_id, data={}))
            self._insert_node(new_widget, parent_html_id, result, before_id=before_id)
            return

        # If props are different, generate an UPDATE patch.
        if not props_are_same:
            self._collect_details(new_widget, new_props, result)
            patch_data = {'props': new_props, 'old_props': old_data.get('props', {})}
            result.patches.append(Patch(action='UPDATE', html_id=html_id, data=patch_data))
        
        # Update the node in the new rendered map for the next cycle.
        result.new_rendered_map[new_key] = {
            'html_id': html_id,
            'widget_type': new_type_name,
            'key': new_widget.key,
            'widget_instance_ref': weakref.ref(new_widget),
            'props': new_props,
            'props_hash': new_props_hash,
            'parent_html_id': parent_html_id,
            'children_keys': [child.get_unique_id() for child in new_widget.get_children()]
        }
        
        # Always diff children to handle structural changes (add/remove/reorder).
        self._diff_children(
            parent_html_id=html_id,
            new_children=new_widget.get_children(),
            old_children_keys=old_data.get('children_keys', []),
            previous_map=previous_map,
            result=result,
            visited_keys=visited_keys
        )

    def _diff_children(
        self,
        parent_html_id: str,
        new_children: List['Widget'],
        old_children_keys: List[str],
        previous_map: Dict,
        result: ReconciliationResult,
        visited_keys: Set
    ):
        """
        Performs a keyed reconciliation of a list of children to efficiently
        handle additions, removals, and reordering.
        """
        if not new_children and not old_children_keys:
            return

        old_key_to_index = {key: i for i, key in enumerate(old_children_keys)}
        new_key_to_widget = {widget.get_unique_id(): widget for widget in new_children}
        
        # This list tracks the new order of children that were also in the old list.
        # It helps us detect moves.
        new_indices = []
        
        # --- Pass 1: Update and find stable nodes ---
        for new_widget in new_children:
            new_key = new_widget.get_unique_id()
            if new_key in old_key_to_index:
                # This child existed before. Add its old index to our list.
                new_indices.append(old_key_to_index[new_key])

        # A subsequence is increasing if each number is greater than the one before it.
        # e.g., in [0, 3, 1, 4], the LIS is [0, 3, 4] or [0, 1, 4].
        # We find the longest one to minimize the number of MOVE operations.
        is_lis = self._longest_increasing_subsequence(new_indices)
        is_lis_set = set(is_lis)
        
        # --- Pass 2: Patch DOM with inserts and moves ---
        j = 0 # Pointer for the LIS
        for i, new_widget in enumerate(new_children):
            new_key = new_widget.get_unique_id()
            old_index = old_key_to_index.get(new_key)
            
            # Find the DOM element that this new widget should be inserted before.
            next_stable_node_index = i + 1
            while next_stable_node_index < len(new_children):
                next_key = new_children[next_stable_node_index].get_unique_id()
                if next_key in old_key_to_index:
                    break
                next_stable_node_index += 1
            
            before_id = None
            if next_stable_node_index < len(new_children):
                before_key = new_children[next_stable_node_index].get_unique_id()
                before_id = previous_map.get(before_key, {}).get('html_id')

            if old_index is None:
                # --- INSERT new node ---
                self._insert_node(new_widget, parent_html_id, result, before_id=before_id)
            else:
                # --- MOVE or UPDATE existing node ---
                # If the old index is part of our LIS, it doesn't need to move.
                # Otherwise, it's a MOVE operation.
                if old_index not in is_lis_set:
                    html_id = previous_map[new_key]['html_id']
                    result.patches.append(Patch('MOVE', html_id, {'parent_html_id': parent_html_id, 'before_id': before_id}))
                
                # Recursively diff the node itself for prop changes.
                self._diff_node(parent_html_id, new_widget, previous_map, result, visited_keys, before_id)

    def _insert_node(
        self,
        new_widget: 'Widget',
        parent_html_id: str,
        result: ReconciliationResult,
        before_id: Optional[str]
    ):
        """Recursively handles the insertion of a new widget and its descendants."""
        if new_widget is None:
            return

        html_id = self.id_generator.next_id()
        new_key = new_widget.get_unique_id()
        new_props = new_widget.render_props()
        
        self._collect_details(new_widget, new_props, result)

        result.new_rendered_map[new_key] = {
            'html_id': html_id,
            'widget_type': type(new_widget).__name__,
            'key': new_widget.key,
            'widget_instance_ref': weakref.ref(new_widget),
            'props': new_props,
            'props_hash': self._hash_props(new_props),
            'parent_html_id': parent_html_id,
            'children_keys': [child.get_unique_id() for child in new_widget.get_children()]
        }
        
        stub_html = self._generate_html_stub(new_widget, html_id, new_props)
        patch_data = {
            'html': stub_html,
            'parent_html_id': parent_html_id,
            'props': new_props,
            'before_id': before_id
        }
        result.patches.append(Patch(action='INSERT', html_id=html_id, data=patch_data))
        
        # Recursively insert all children of the new node.
        for child in new_widget.get_children():
            self._insert_node(child, html_id, result, before_id=None)

    # --- Utility and Helper Methods ---
    # (These are largely unchanged as they perform essential sub-tasks)

    def _longest_increasing_subsequence(self, nums: List[int]) -> List[int]:
        """Finds the longest increasing subsequence of a list of numbers."""
        if not nums:
            return []
        tails = []
        # `p[i]` stores the predecessor of `nums[i]` in the LIS.
        p = [-1] * len(nums)
        for i, num in enumerate(nums):
            if not tails or num > tails[-1][0]:
                if tails:
                    p[i] = tails[-1][1]
                tails.append((num, i))
            else:
                # Binary search to find the smallest tail element >= num
                l, r = 0, len(tails) - 1
                while l < r:
                    m = (l + r) // 2
                    if tails[m][0] < num:
                        l = m + 1
                    else:
                        r = m
                if tails[l][0] >= num:
                    if l > 0:
                        p[i] = tails[l-1][1]
                    tails[l] = (num, i)
        
        # Reconstruct the LIS from the predecessors array
        res = []
        idx = tails[-1][1]
        while idx != -1:
            res.append(nums[idx])
            idx = p[idx]
        return res[::-1]

    def _collect_details(self, widget, props, result):
        """Collects CSS classes, callbacks, and JS initializers from a widget."""
        css_classes = props.get('css_class', '').split()
        if hasattr(widget, 'get_required_css_classes'):
            css_classes.extend(widget.get_required_css_classes())

        for css_class in set(css_classes):
             if css_class and css_class not in result.active_css_details:
                 if hasattr(type(widget), 'generate_css_rule') and hasattr(widget, 'style_key'):
                     result.active_css_details[css_class] = (getattr(type(widget), 'generate_css_rule'), getattr(widget, 'style_key'))

        # --- SPECIAL CASE: Add initializer for widgets that need JS ---
        if props.get('init_simplebar'):
            result.js_initializers.append({
                'type': 'SimpleBar', 'target_id': props['html_id'], # Assumes html_id is in props
                'options': props.get('simplebar_options', {})
            })
        if 'responsive_clip_path' in props:
            result.js_initializers.append({
                'type': 'ResponsiveClipPath', 'target_id': props['html_id'],
                'data': props['responsive_clip_path']
            })
            
        # --- Register Callbacks ---
        # This can be made more generic, but this covers common cases.
        callback_props = {
            'onPressedName': 'onPressed', 'onTapName': 'onTap', 'onItemTapName': 'onItemTap',
            'onChangedName': 'onChanged',
        }
        for prop_name, func_name in callback_props.items():
            if prop_name in props and hasattr(widget, func_name):
                cb_name = props[prop_name]
                cb_func = getattr(widget, func_name, None)
                if cb_name and cb_func:
                    result.registered_callbacks[cb_name] = cb_func

    def _get_widget_render_tag(self, widget: 'Widget') -> str:
        """Determines the appropriate HTML tag for a given widget."""
        if hasattr(type(widget), '_get_widget_render_tag'):
            return type(widget)._get_widget_render_tag(widget)
            
        widget_type_name = type(widget).__name__
        tag_map = {
            'Text': 'p', 'Image': 'img', 'Icon': 'i', 'Spacer': 'div', 'SizedBox': 'div',
            'TextButton': 'button', 'ElevatedButton': 'button', 'IconButton': 'button',
            'FloatingActionButton': 'button', 'SnackBarAction': 'button',
            'ListTile': 'div', 'Divider': 'div', 'Dialog': 'div', 'AspectRatio': 'div',
            'ClipPath': 'div',
        }
        if widget_type_name == 'Icon' and getattr(widget, 'custom_icon_source', None):
            return 'img'
        return tag_map.get(widget_type_name, 'div')

    def _generate_html_stub(self, widget: 'Widget', html_id: str, props: Dict) -> str:
        """Generates the initial HTML string for a widget."""
        # Check for a custom stub generator on the widget class first.
        if hasattr(type(widget), '_generate_html_stub'):
            return type(widget)._generate_html_stub(widget, html_id, props)
        
        tag = self._get_widget_render_tag(widget)
        classes = props.get('css_class', '')
        attrs = ""
        inner_html = ""

        # Event handlers
        if 'onPressedName' in props and props.get('enabled', True):
            attrs += f' onclick="handleClick(\'{html.escape(props["onPressedName"], quote=True)}\')"'
        elif 'onTapName' in props and props.get('enabled', True):
            # This handles both general tap and item tap (with index)
            if props.get("item_index") is not None:
                attrs += f' onclick="handleItemTap(\'{html.escape(props["onTapName"], quote=True)}\', {props["item_index"]})"'
            else:
                attrs += f' onclick="handleClick(\'{html.escape(props["onTapName"] if props["onTapName"] else "", quote=True)}\')"'

        if props.get('tooltip'):
            attrs += f' title="{html.escape(props["tooltip"], quote=True)}"'

        # Widget-specific content and attributes
        widget_type_name = type(widget).__name__
        if widget_type_name == 'Text':
            inner_html = html.escape(str(props.get('data', '')))
        elif widget_type_name == 'Icon':
            inner_html = html.escape(str(props.get('data', '')))
        elif widget_type_name == 'Image':
            attrs += f' src="{html.escape(props.get("src", ""), quote=True)}" alt=""'
        
        # Apply style overrides from widgets like Scrollbar or Placeholder
        if hasattr(widget, '_style_override'):
             style_dict = widget._style_override
             style_str = " ".join(f"{k.replace('_','-')}: {v};" for k, v in style_dict.items() if v is not None)
             if style_str:
                 attrs += f' style="{html.escape(style_str, quote=True)}"'
        
        # Self-closing tags
        if tag in ['img', 'hr', 'br']:
            return f'<{tag} id="{html_id}" class="{classes}"{attrs}>'
        
        return f'<{tag} id="{html_id}" class="{classes}"{attrs}>{inner_html}</{tag}>'


# Helper class for generating unique IDs, unchanged.
class IDGenerator:
    def __init__(self): self._count = 0
    def next_id(self) -> str: self._count += 1; return f"pythra_id_{self._count}"