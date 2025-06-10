# framework/reconciler.py

"""
Handles the reconciliation process for the PyThra framework.
It compares the new widget tree with the previously rendered state and generates
a list of DOM patches (INSERT, UPDATE, REMOVE, MOVE) to efficiently update the UI.
It also collects details for CSS generation.
"""

import uuid
import html
from typing import Any, Dict, List, Optional, Tuple, Union, Set, TYPE_CHECKING, Callable, Literal
from dataclasses import dataclass

if TYPE_CHECKING:
    from .base import Widget, Key
    # from .widgets import ... # Import specific widgets if needed for isinstance checks

# --- Key Class ---
class Key:
    """Provides a stable identity for widgets across rebuilds."""
    def __init__(self, value: Any):
        try:
            hash(value)
            self.value = value
        except TypeError:
            if isinstance(value, list): self.value = tuple(value)
            elif isinstance(value, dict): self.value = tuple(sorted(value.items()))
            else: self.value = str(value)
            try: hash(self.value)
            except TypeError: raise TypeError(f"Key value {value!r} (type: {type(value)}) could not be made hashable for Key.")

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Key) and self.value == other.value

    def __hash__(self) -> int:
        return hash((self.__class__, self.value))

    def __repr__(self) -> str:
        return f"Key({self.value!r})"

# --- ID Generator ---
class IDGenerator:
    """Generates unique HTML IDs prefixed with 'fw_id_'."""
    def __init__(self):
        self._count = 0

    def next_id(self) -> str:
        self._count += 1
        return f"fw_id_{self._count}"

# --- Patch Definition (using dataclass) ---
PatchAction = Literal['INSERT', 'REMOVE', 'UPDATE', 'MOVE']
@dataclass
class Patch:
    action: PatchAction
    html_id: str # Target element's ID for UPDATE/REMOVE/MOVE, or new ID for INSERT
    data: Dict[str, Any]

NodeData = Dict[str, Any] # html_id, widget_type, key, props, parent_html_id, children_keys

class Reconciler:
    def __init__(self):
        self.context_maps: Dict[str, Dict[Union[Key, str], NodeData]] = {'main': {}}
        self.id_generator = IDGenerator()
        self.active_css_details: Dict[str, Tuple[Callable, Tuple]] = {}
        print("Reconciler Initialized")

    def get_map_for_context(self, context_key: str) -> Dict[Union[Key, str], NodeData]:
        return self.context_maps.setdefault(context_key, {})

    def clear_context(self, context_key: str):
         if context_key in self.context_maps: del self.context_maps[context_key]; print(f"Reconciler context '{context_key}' cleared.")

    def _get_widget_render_tag(self, widget: 'Widget') -> str:
        widget_type_name = type(widget).__name__
        tag_map = {
              'Text': 'p', 'Image': 'img', 'Icon': 'i',
              'TextButton': 'button', 'ElevatedButton': 'button', 'IconButton': 'button',
              'FloatingActionButton': 'button', 'SnackBarAction': 'button',
              'ListTile': 'div', 'Divider': 'div', 'Dialog': 'div',
         }
        if widget_type_name == 'Icon' and getattr(widget, 'custom_icon_source', None): return 'img'
        return tag_map.get(widget_type_name, 'div')

    def _generate_html_stub(self, widget: 'Widget', html_id: str, props: Dict) -> str:
        from .base import Widget # Local import

        tag = self._get_widget_render_tag(widget)
        classes = props.get('css_class', '')
        content = ""
        attrs = ""
        widget_type_name = type(widget).__name__

        if widget_type_name == 'Text': content = html.escape(str(props.get('data', '')))
        elif widget_type_name == 'Image': attrs += f" src=\"{html.escape(props.get('src', ''), quote=True)}\" alt=\"\""; tag = 'img'
        elif widget_type_name == 'Icon':
            if props.get('render_type') == 'img': attrs += f" src=\"{html.escape(props.get('custom_icon_src', ''), quote=True)}\" alt=\"\""; tag = 'img'
            else: classes = f"fa fa-{props.get('icon_name', 'question-circle')} {classes}".strip(); tag = 'i'
        elif widget_type_name == 'Placeholder' and not props.get('has_child'): content = html.escape(props.get('fallbackText', 'Placeholder'))
        elif widget_type_name in ['TextButton', 'ElevatedButton', 'IconButton', 'FloatingActionButton', 'SnackBarAction']:
            tag = 'button'
            # In render_props, buttons should provide the string name of the callback
            # under 'onPressedName' or a similar consistent key.
            cb_name = props.get('onPressedName') # Prefer specific ID key from render_props
            if cb_name and isinstance(cb_name, str):
                attrs += f' onclick="handleClick(\'{cb_name.replace("'", "\\'")}\')"'
            if props.get('tooltip'): attrs += f' title="{html.escape(props["tooltip"], quote=True)}"'
        elif widget_type_name == 'ListTile':
            attrs += ' role="listitem"'
            cb_name = props.get('onTapName') # From ListTile's render_props
            if cb_name and isinstance(cb_name, str) and props.get('enabled', True):
                attrs += f' onclick="handleItemTap(\'{cb_name.replace("'", "\\'")}\', {props.get("item_index", -1)})"'
        elif widget_type_name == 'Divider': tag = 'div'; attrs += ' role="separator"'
        elif widget_type_name == 'Dialog': attrs += ' role="dialog" aria-modal="true" aria-hidden="true"'

        if tag in ['img', 'hr', 'br']: return f'<{tag} id="{html_id}" class="{classes}"{attrs}>'
        else: return f'<{tag} id="{html_id}" class="{classes}"{attrs}>{content}</{tag}>'

    def _diff_props(self, old_props: Dict, new_props: Dict) -> Optional[Dict]:
        changes = {}; all_prop_keys = set(old_props.keys()) | set(new_props.keys())
        for key_prop in all_prop_keys:
            old_val, new_val = old_props.get(key_prop), new_props.get(key_prop)
            if old_val != new_val: changes[key_prop] = new_val
        return changes if changes else None

    def reconcile_subtree(self, current_subtree_root: Optional['Widget'], parent_html_id: str, context_key: str = 'main') -> List[Patch]:
        print(f"\n--- Reconciling Subtree (Context: '{context_key}', Target Parent ID: '{parent_html_id}') ---")
        from .base import Widget

        patches: List[Patch] = []
        new_rendered_map: Dict[Union[Key, str], NodeData] = {}
        previous_map_for_context = self.get_map_for_context(context_key)

        if context_key == 'main': self.active_css_details.clear()

        old_root_key = None
        for key_val, data in previous_map_for_context.items(): # Corrected variable name
            if data.get('parent_html_id') == parent_html_id: old_root_key = key_val; break
        if not old_root_key and len(previous_map_for_context) == 1 and current_subtree_root:
             single_old_key = list(previous_map_for_context.keys())[0]
             single_old_data = previous_map_for_context[single_old_key]
             new_root_unique_id = current_subtree_root.get_unique_id()
             if new_root_unique_id == single_old_key or \
                (isinstance(single_old_data.get('key'), Key) == isinstance(getattr(current_subtree_root,'key',None), Key) and \
                 single_old_data.get('widget_type') == type(current_subtree_root).__name__):
                  old_root_key = single_old_key
        print(f"  Old root key for context '{context_key}': {old_root_key}")

        self._diff_node_recursive(
            old_node_key=old_root_key, new_widget=current_subtree_root,
            parent_html_id=parent_html_id, patches=patches,
            new_rendered_map=new_rendered_map, previous_map_for_context=previous_map_for_context
        )

        old_keys = set(previous_map_for_context.keys()); new_keys = set(new_rendered_map.keys())
        removed_keys = old_keys - new_keys
        for removed_key in removed_keys:
            removed_data = previous_map_for_context[removed_key]
            patches.append(Patch(action='REMOVE', html_id=removed_data['html_id'], data={}))
            print(f"  [Patch] REMOVE ({context_key}): html_id={removed_data['html_id']} (key={removed_key})")

        self.context_maps[context_key] = new_rendered_map
        print(f"--- Subtree Reconciliation End ({context_key}). Patches: {len(patches)} ---")
        return patches

    def _diff_node_recursive(self, old_node_key: Optional[Union['Key', str]], new_widget: Optional['Widget'], parent_html_id: str, patches: List[Patch], new_rendered_map: Dict, previous_map_for_context: Dict):
        from .base import Widget, Key

        layout_props_override = None
        actual_new_widget = new_widget
        widget_type_name = type(new_widget).__name__ if new_widget else None
        layout_widget_types = ['Padding', 'Align', 'Center', 'Expanded', 'Spacer', 'Positioned', 'AspectRatio', 'FittedBox', 'FractionallySizedBox']

        if widget_type_name in layout_widget_types:
            if widget_type_name == 'Placeholder' and getattr(new_widget, 'child', None) is not None:
                actual_new_widget = new_widget.child
                if actual_new_widget is None: # If child of placeholder is None, render placeholder box
                    widget_type_name = 'Placeholder_Box' # Special type to render placeholder box
                    # No, this is not right. If Placeholder has child=None, it *is* the placeholder box.
                    # If Placeholder.child is not None, we render the child.
                    # The actual_new_widget is the one to render.
            elif widget_type_name != 'Placeholder': # All other layout widgets
                layout_props_override = new_widget.render_props()
                children_of_layout = new_widget.get_children()
                actual_new_widget = children_of_layout[0] if children_of_layout else None

        new_widget_unique_id = actual_new_widget.get_unique_id() if actual_new_widget else None
        old_data = previous_map_for_context.get(old_node_key) if old_node_key else None

        if actual_new_widget is None and old_data is None: return
        if actual_new_widget is None: return # Removal is handled by map comparison at the end of reconcile_subtree

        if old_data is None:
            self._insert_node_recursive(actual_new_widget, parent_html_id, patches, new_rendered_map, previous_map_for_context, layout_props_override)
            return

        old_html_id, old_type = old_data['html_id'], old_data['widget_type']
        new_type = type(actual_new_widget).__name__
        old_key, new_key = old_data.get('key'), getattr(actual_new_widget, 'key', None)

        should_replace = (new_key is not None and old_key != new_key) or \
                         (old_key is not None and new_key is None) or \
                         (new_key is None and old_key is None and old_type != new_type) or \
                         (new_key is not None and old_key is not None and old_key == new_key and old_type != new_type)

        if should_replace:
            print(f"  [Diff] Node Replace: old_key={old_key}, new_key={new_key}, old_type={old_type}, new_type={new_type}")
            self._insert_node_recursive(actual_new_widget, parent_html_id, patches, new_rendered_map, previous_map_for_context, layout_props_override)
            return

        print(f"  [Diff] Node Update Check: key={new_key or old_key or 'NoKey'}, type={new_type}, html_id={old_html_id}")
        new_props = actual_new_widget.render_props()
        if layout_props_override: new_props['layout_override'] = layout_props_override

        css_class = new_props.get('css_class')
        if css_class and hasattr(actual_new_widget, 'style_key') and hasattr(type(actual_new_widget), 'generate_css_rule'): # Check static method
             if css_class not in self.active_css_details:
                  gen_func = getattr(type(actual_new_widget), 'generate_css_rule'); style_key_val = getattr(actual_new_widget, 'style_key')
                  self.active_css_details[css_class] = (gen_func, style_key_val)
                  # print(f"    [CSS Detail STORED] For {actual_new_widget.__class__.__name__} - Class: {css_class}")

        prop_changes = self._diff_props(old_data['props'], new_props)
        if prop_changes:
            patch_data = {'props': prop_changes}
            if 'layout_override' in new_props: patch_data['layout_override'] = new_props['layout_override']
            patches.append(Patch(action='UPDATE', html_id=old_html_id, data=patch_data))
            # print(f"    [Patch] UPDATE: html_id={old_html_id}, changes={list(prop_changes.keys())}")

        new_map_entry = {
            'html_id': old_html_id, 'widget_type': new_type, 'key': new_key,
            'internal_id': getattr(actual_new_widget, '_internal_id', None),
            'props': new_props, 'parent_html_id': parent_html_id,
            'children_keys': [c.get_unique_id() for c in actual_new_widget.get_children()]
        }
        new_rendered_map[new_widget_unique_id] = new_map_entry

        self._diff_children_recursive(
             old_data.get('children_keys', []), actual_new_widget.get_children(),
             old_html_id, patches, new_rendered_map, previous_map_for_context
        )

    def _insert_node_recursive(self, new_widget: 'Widget', parent_html_id: str, patches: List[Patch], new_rendered_map: Dict, previous_map_for_context: Dict, layout_props_override: Optional[Dict] = None, before_id: Optional[str] = None):
        from .base import Widget, Key

        if new_widget is None: # Should not happen if called correctly
             print(f"Warning: _insert_node_recursive called with None new_widget for parent {parent_html_id}")
             return

        new_widget_unique_id = new_widget.get_unique_id()
        html_id = self.id_generator.next_id()
        widget_props = new_widget.render_props()
        if layout_props_override: widget_props['layout_override'] = layout_props_override

        css_class = widget_props.get('css_class')
        if css_class and hasattr(new_widget, 'style_key') and hasattr(type(new_widget), 'generate_css_rule'):
            if css_class not in self.active_css_details:
                gen_func = getattr(type(new_widget), 'generate_css_rule'); style_key_val = getattr(new_widget, 'style_key')
                self.active_css_details[css_class] = (gen_func, style_key_val)
                # print(f"    [CSS Detail STORED] For Inserted {new_widget.__class__.__name__} - Class: {css_class}")

        new_map_entry = {
            'html_id': html_id, 'widget_type': type(new_widget).__name__, 'key': getattr(new_widget, 'key', None),
            'internal_id': getattr(new_widget, '_internal_id', None), 'props': widget_props,
            'parent_html_id': parent_html_id,
            'children_keys': [c.get_unique_id() for c in new_widget.get_children()]
        }
        new_rendered_map[new_widget_unique_id] = new_map_entry

        patch_data = {
            'html': self._generate_html_stub(new_widget, html_id, widget_props),
            'parent_html_id': parent_html_id,
            'props': widget_props,
            'before_id': before_id
        }
        patches.append(Patch(action='INSERT', html_id=html_id, data=patch_data))
        print(f"  [Patch] INSERT: html_id={html_id} into {parent_html_id} (key={new_widget_unique_id})" + (f" before {before_id}" if before_id else ""))

        for child_widget in new_widget.get_children():
            self._diff_node_recursive(None, child_widget, html_id, patches, new_rendered_map, previous_map_for_context)


    def _diff_children_recursive(self, old_children_keys: List[Union['Key', str]], new_children_widgets: List['Widget'], parent_html_id: str, patches: List[Patch], new_rendered_map: Dict, previous_map_for_context: Dict):
        from .base import Widget, Key

        if not old_children_keys and not new_children_widgets: return
        # print(f"    [Child Diff] Parent: {parent_html_id}, Old keys#: {len(old_children_keys)}, New widgets#: {len(new_children_widgets)}")

        old_key_to_index: Dict[Union[Key, str], int] = {key: i for i, key in enumerate(old_children_keys)}
        new_key_to_widget_map: Dict[Union[Key, str], 'Widget'] = {widget.get_unique_id(): widget for widget in new_children_widgets}
        
        new_children_info: List[Dict[str, Any]] = []
        last_matched_old_idx = -1 
        
        # Pass 1: Diff existing nodes, collect info for new nodes, mark potential moves
        for i, new_widget in enumerate(new_children_widgets):
            new_key = new_widget.get_unique_id()
            old_idx = old_key_to_index.get(new_key)
            node_info = {'key': new_key, 'widget': new_widget, 'new_idx': i, 'old_idx': old_idx, 'html_id': None}

            if old_idx is not None: 
                old_data = previous_map_for_context.get(new_key)
                if old_data and old_data.get('parent_html_id') == parent_html_id:
                    self._diff_node_recursive(new_key, new_widget, parent_html_id, patches, new_rendered_map, previous_map_for_context)
                    if new_key in new_rendered_map: node_info['html_id'] = new_rendered_map[new_key]['html_id']
                    else: print(f"      [Child Diff WARNING] Key {new_key} updated but not in new_rendered_map for html_id retrieval.") # Should not happen
                    
                    if old_idx < last_matched_old_idx: node_info['moved'] = True
                    else: last_matched_old_idx = old_idx
                else: 
                    node_info['is_new'] = True
                    # html_id for new nodes is generated when _insert_node_recursive is called
            else: 
                node_info['is_new'] = True
            new_children_info.append(node_info)
            
        # Pass 2: Generate INSERT and MOVE patches with correct 'before_id'
        for i, node_info in enumerate(new_children_info):
            new_key = node_info['key']
            new_widget = node_info['widget']
            
            before_id = None
            for j in range(i + 1, len(new_children_info)):
                next_node_in_new_list_info = new_children_info[j]
                if not next_node_in_new_list_info.get('is_new'): # Next is stable (or moved but already processed)
                     # Its html_id should be in new_rendered_map (from Pass 1 update or previous insert)
                     next_key = next_node_in_new_list_info['key']
                     if next_key in new_rendered_map:
                          before_id = new_rendered_map[next_key]['html_id']
                          break
            
            if node_info.get('is_new'):
                # print(f"      [Child Diff] Pass 2 - Inserting new key={new_key} before {before_id or 'end'}")
                # Layout override for a new child of parent_html_id:
                # This needs to check if parent_html_id's widget *was* a layout widget.
                # The layout_props_override for the child itself (if it's a layout widget)
                # is handled when _insert_node_recursive calls _diff_node_recursive for its own child.
                parent_widget_data = None
                for k,v in new_rendered_map.items(): # Find parent in new_rendered_map
                    if v.get('html_id') == parent_html_id:
                        parent_widget_data = v
                        break
                parent_layout_override = parent_widget_data.get('props',{}).get('layout_override') if parent_widget_data else None

                self._insert_node_recursive(
                    new_widget, parent_html_id, patches, new_rendered_map, 
                    previous_map_for_context, 
                    layout_props_override=parent_layout_override, # Pass override if parent_html_id had one
                    before_id=before_id
                )
                # Update node_info with html_id if not already set (it should be by _insert_node_recursive)
                if new_key in new_rendered_map:
                     node_info['html_id'] = new_rendered_map[new_key]['html_id']


            elif node_info.get('moved'):
                moved_html_id = node_info.get('html_id')
                if moved_html_id:
                    patches.append(Patch(action='MOVE', html_id=moved_html_id, data={'parent_html_id': parent_html_id, 'before_id': before_id}))
                    # print(f"        [Patch] MOVE: html_id={moved_html_id} into {parent_html_id}" + (f" before {before_id}" if before_id else " to end"))
                else:
                    print(f"      [Child Diff] ERROR: Could not find html_id for MOVED key={new_key}")
