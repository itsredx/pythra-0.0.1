# framework/reconciler.py

"""
Handles the reconciliation process for the PyThra framework.
It compares the new widget tree with the previously rendered state and generates
a list of DOM patches (INSERT, UPDATE, REMOVE, MOVE) to efficiently update the UI.
It also collects details for CSS generation.
"""

import uuid
import html
import sys
from typing import Any, Dict, List, Optional, Tuple, Union, Set, TYPE_CHECKING, Callable, Literal
from dataclasses import dataclass

if TYPE_CHECKING:
    from .base import Widget, Key
    # from .widgets import ... # Import specific widgets if needed for isinstance checks

# --- Key Class ---
class Key:
    def __init__(self, value: Any):
        try: hash(value); self.value = value
        except TypeError:
            if isinstance(value, list): self.value = tuple(value)
            elif isinstance(value, dict): self.value = tuple(sorted(value.items()))
            else: self.value = str(value)
            try: hash(self.value)
            except TypeError: raise TypeError(f"Key value {value!r} (type: {type(value)}) could not be made hashable for Key.")
    def __eq__(self, other: object) -> bool: return isinstance(other, Key) and self.value == other.value
    def __hash__(self) -> int: return hash((self.__class__, self.value))
    def __repr__(self) -> str: return f"Key({self.value!r})"

# --- ID Generator ---
class IDGenerator:
    def __init__(self): self._count = 0
    def next_id(self) -> str: self._count += 1; return f"fw_id_{self._count}"

# --- Patch Definition ---
PatchAction = Literal['INSERT', 'REMOVE', 'UPDATE', 'MOVE']
@dataclass
class Patch:
    action: PatchAction
    html_id: str
    data: Dict[str, Any]

NodeData = Dict[str, Any]

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


    # framework/reconciler.py (Inside Reconciler class)

    def _generate_html_stub(self, widget: 'Widget', html_id: str, props: Dict) -> str:
        """Generates an HTML stub for the direct element, including simple direct children if appropriate."""
        from .base import Widget # Local import
        import html

        tag = self._get_widget_render_tag(widget)
        classes = props.get('css_class', '')
        attrs = ""
        # This will hold the direct text content for simple tags (Text, Placeholder)
        # OR the pre-rendered HTML of a *single simple child* for composite tags (Button)
        inner_html_for_stub = ""
        widget_type_name = type(widget).__name__

        # --- Handle Attributes for the main widget tag ---
        if widget_type_name in ['TextButton', 'ElevatedButton', 'IconButton', 'FloatingActionButton', 'SnackBarAction']:
            tag = 'button'
            cb_name = props.get('onPressedName')
            if cb_name and isinstance(cb_name, str): attrs += f' onclick="handleClick(\'{cb_name.replace("'", "\\'")}\')"'
            if props.get('tooltip'): attrs += f' title="{html.escape(props["tooltip"], quote=True)}"'
        elif widget_type_name == 'ListTile':
            attrs += ' role="listitem"'
            cb_name = props.get('onTapName')
            if cb_name and isinstance(cb_name, str) and props.get('enabled', True):
                 item_idx = props.get("item_index", -1)
                 attrs += f' onclick="handleItemTap(\'{cb_name.replace("'", "\\'")}\', {item_idx})"'
        elif widget_type_name == 'Image':
            attrs += f" src=\"{html.escape(props.get('src', ''), quote=True)}\" alt=\"\""
            tag = 'img'
        elif widget_type_name == 'Icon':
            if props.get('render_type') == 'img':
                attrs += f" src=\"{html.escape(props.get('custom_icon_src', ''), quote=True)}\" alt=\"\""
                tag = 'img'
            else: # Font icon
                classes = f"fa fa-{props.get('icon_name', 'question-circle')} {classes}".strip()
                tag = 'i'
        elif widget_type_name == 'Divider':
            tag = 'div'; attrs += ' role="separator"'
        elif widget_type_name == 'Dialog':
             attrs += ' role="dialog" aria-modal="true" aria-hidden="true"'

        # --- Handle Inner HTML for the stub ---
        if widget_type_name == 'Text':
            inner_html_for_stub = html.escape(str(props.get('data', '')))
        elif widget_type_name == 'Placeholder' and not props.get('has_child'):
            inner_html_for_stub = html.escape(props.get('fallbackText', 'Placeholder'))
        elif widget_type_name in [
            'ElevatedButton', 'TextButton', 'IconButton', 'FloatingActionButton', 'SnackBarAction'
            # Potentially Placeholder if props.get('has_child') is True
        ] and widget.get_children():
            # These widgets' stubs will embed their *single direct child's* stub
            child_widget = widget.get_children()[0]
            if child_widget:
                child_props = child_widget.render_props()
                # Child's ID in stub is temporary, not the final reconciled one.
                child_html_id_stub = f"{html_id}_child_stub"
                # Recursively call stub for the child, but this child IS part of the parent's HTML.
                # This child does not get its own separate INSERT patch in this initial stub generation.
                # It *will* be added to new_rendered_map by the _insert_node_recursive call for the PARENT.
                inner_html_for_stub = self._generate_html_stub(child_widget, child_html_id_stub, child_props)

        # For other container types (Container, Column, Row, ListTile, Stack, etc.),
        # inner_html_for_stub remains empty. Their children will be added by separate INSERT patches.

        if tag in ['img', 'hr', 'br']: # Self-closing tags
            return f'<{tag} id="{html_id}" class="{classes}"{attrs}>'
        else: # Container tags
            return f'<{tag} id="{html_id}" class="{classes}"{attrs}>{inner_html_for_stub}</{tag}>'

    # Helper to add node to map and collect CSS - THIS IS FOR NODES GETTING THEIR OWN PATCH
    def _add_node_to_map_and_css(self, widget: 'Widget', html_id: str, parent_html_id:str, props: Dict, new_rendered_map: Dict):
        from .base import Key
        widget_unique_id = widget.get_unique_id()
        css_class = props.get('css_class')

        if css_class and hasattr(widget, 'style_key') and \
           hasattr(type(widget), 'generate_css_rule'):
            if css_class not in self.active_css_details:
                generator_func = getattr(type(widget), 'generate_css_rule')
                style_key_val = getattr(widget, 'style_key')
                self.active_css_details[css_class] = (generator_func, style_key_val)
                # print(f"    [CSS Detail STORED] For {widget.__class__.__name__} - Class: {css_class}")

        new_rendered_map[widget_unique_id] = {
            'html_id': html_id, 'widget_type': type(widget).__name__, 'key': getattr(widget, 'key', None),
            'internal_id': getattr(widget, '_internal_id', None), 'props': props,
            'parent_html_id': parent_html_id,
            'children_keys': [c.get_unique_id() for c in widget.get_children()]
        }


    def _diff_props(self, old_props: Dict, new_props: Dict) -> Optional[Dict]:
        changes = {}; all_prop_keys = set(old_props.keys()) | set(new_props.keys())
        for key_prop in all_prop_keys:
            old_val, new_val = old_props.get(key_prop), new_props.get(key_prop)
            if old_val != new_val: changes[key_prop] = new_val
        return changes if changes else None

    def reconcile_subtree(self, current_subtree_root: Optional['Widget'], parent_html_id: str, context_key: str = 'main') -> List[Patch]:
        # ... (implementation as before) ...
        print(f"\n--- Reconciling Subtree (Context: '{context_key}', Target Parent ID: '{parent_html_id}') ---")
        from .base import Widget

        patches: List[Patch] = []
        new_rendered_map: Dict[Union[Key, str], NodeData] = {}
        previous_map_for_context = self.get_map_for_context(context_key)

        if context_key == 'main': self.active_css_details.clear()

        old_root_key = None
        for key_val, data in previous_map_for_context.items():
            if data.get('parent_html_id') == parent_html_id: old_root_key = key_val; break
        if not old_root_key and len(previous_map_for_context) == 1 and current_subtree_root:
             single_old_key = list(previous_map_for_context.keys())[0]; single_old_data = previous_map_for_context[single_old_key]
             new_root_unique_id = current_subtree_root.get_unique_id()
             if new_root_unique_id == single_old_key or \
                (isinstance(single_old_data.get('key'), Key) == isinstance(getattr(current_subtree_root,'key',None), Key) and \
                 single_old_data.get('widget_type') == type(current_subtree_root).__name__): old_root_key = single_old_key
        # print(f"  Old root key for context '{context_key}': {old_root_key}")

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
            # print(f"  [Patch] REMOVE ({context_key}): html_id={removed_data['html_id']} (key={removed_key})")

        self.context_maps[context_key] = new_rendered_map
        # print(f"--- Subtree Reconciliation End ({context_key}). Patches: {len(patches)} ---")
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
            elif widget_type_name != 'Placeholder':
                layout_props_override = new_widget.render_props()
                children_of_layout = new_widget.get_children()
                actual_new_widget = children_of_layout[0] if children_of_layout else None

        new_widget_unique_id = actual_new_widget.get_unique_id() if actual_new_widget else None
        old_data = previous_map_for_context.get(old_node_key) if old_node_key else None

        if actual_new_widget is None and old_data is None: return
        if actual_new_widget is None: return

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
            # print(f"  [Diff] Node Replace: old_key={old_key}, new_key={new_key}, old_type={old_type}, new_type={new_type}")
            self._insert_node_recursive(actual_new_widget, parent_html_id, patches, new_rendered_map, previous_map_for_context, layout_props_override)
            return

        # print(f"  [Diff] Node Update Check: key={new_key or old_key or 'NoKey'}, type={new_type}, html_id={old_html_id}")
        new_props = actual_new_widget.render_props()
        if layout_props_override: new_props['layout_override'] = layout_props_override

        css_class = new_props.get('css_class')
        if css_class and hasattr(actual_new_widget, 'style_key') and hasattr(type(actual_new_widget), 'generate_css_rule'):
             if css_class not in self.active_css_details:
                  gen_func = getattr(type(actual_new_widget), 'generate_css_rule'); style_key_val = getattr(actual_new_widget, 'style_key')
                  self.active_css_details[css_class] = (gen_func, style_key_val)
                  # print(f"    [CSS Detail STORED for Update] For {actual_new_widget.__class__.__name__} - Class: {css_class}")

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

    # framework/reconciler.py (Inside Reconciler class)

    def _insert_node_recursive(self, new_widget: 'Widget', parent_html_id: str, patches: List[Patch], new_rendered_map: Dict, previous_map_for_context: Dict, layout_props_override: Optional[Dict] = None, before_id: Optional[str] = None):
        from .base import Widget, Key
        if new_widget is None: return

        new_widget_unique_id = new_widget.get_unique_id()
        html_id = self.id_generator.next_id() # This is the html_id for new_widget itself
        widget_props = new_widget.render_props()
        if layout_props_override: widget_props['layout_override'] = layout_props_override

        # This adds new_widget to the map and collects its CSS
        self._add_node_to_map_and_css(new_widget, html_id, parent_html_id, widget_props, new_rendered_map)

        patch_data = {
            'html': self._generate_html_stub(new_widget, html_id, widget_props), # Stub is for new_widget
            'parent_html_id': parent_html_id,
            'props': widget_props,
            'before_id': before_id
        }
        patches.append(Patch(action='INSERT', html_id=html_id, data=patch_data))
        # print(f"  [Patch] INSERT: html_id={html_id} into {parent_html_id} (key={new_widget_unique_id})...")

        # --- Children of this NEWLY INSERTED node ---
        widget_type_name = type(new_widget).__name__
        
        # Define types whose stubs already included their *simple, direct* children's HTML
        # These children were part of the parent's `html` in the INSERT patch.
        # They still need to be added to `new_rendered_map` by `_add_node_to_map_and_css`
        # called from _generate_html_stub, but they DON'T need separate INSERT patches here.
        # However, _generate_html_stub was simplified to not modify new_rendered_map.
        # This means all children will be processed by the loop below.
        
        # List of widgets whose stubs are self-contained or whose children are complex
        # and will always be inserted recursively.
        # If a widget's stub ALREADY renders its children (like a Button with Text),
        # then those children should NOT get a separate INSERT patch here.
        # The child's _html_id_ in the stub is temporary. The child will be reconciled
        # properly in the *next* update cycle if it's keyed.
        # This means the child of a button might not have its own props (e.g. CSS class)
        # applied by JS until the next update after initial insert.

        # Corrected logic:
        # If _generate_html_stub INCLUDED children HTML for this widget_type_name,
        # then we should NOT make recursive calls for those *direct* children here.
        # However, if those children themselves are containers, their children would need patches.
        # This is where the design gets very intricate.

        # Simpler model adopted previously: _generate_html_stub creates ONLY the direct element.
        # Therefore, we *always* recurse for children here to create their INSERT patches.
        for child_widget in new_widget.get_children():
            # The old_node_key for these children is None.
            # Their parent_html_id is the `html_id` of the `new_widget` we just inserted.
            self._diff_node_recursive(
                old_node_key=None,
                new_widget=child_widget,
                parent_html_id=html_id, # <<< Children target the newly inserted parent
                patches=patches,
                new_rendered_map=new_rendered_map,
                previous_map_for_context=previous_map_for_context
                # layout_props_override for these children is determined when they are processed
            )

            
    def _diff_children_recursive(self, old_children_keys: List[Union['Key', str]], new_children_widgets: List['Widget'], parent_html_id: str, patches: List[Patch], new_rendered_map: Dict, previous_map_for_context: Dict):
        from .base import Widget, Key

        if not old_children_keys and not new_children_widgets: return
        # print(f"    [Child Diff] Parent: {parent_html_id}, Old keys#: {len(old_children_keys)}, New widgets#: {len(new_children_widgets)}")

        old_key_to_index: Dict[Union[Key, str], int] = {key: i for i, key in enumerate(old_children_keys)}
        new_key_to_widget_map: Dict[Union[Key, str], 'Widget'] = {widget.get_unique_id(): widget for widget in new_children_widgets}
        
        new_children_info: List[Dict[str, Any]] = []
        last_matched_old_idx = -1 
        
        for i, new_widget in enumerate(new_children_widgets):
            new_key = new_widget.get_unique_id()
            old_idx = old_key_to_index.get(new_key)
            node_info = {'key': new_key, 'widget': new_widget, 'new_idx': i, 'old_idx': old_idx, 'html_id': None}

            if old_idx is not None: 
                old_data = previous_map_for_context.get(new_key)
                if old_data and old_data.get('parent_html_id') == parent_html_id:
                    self._diff_node_recursive(new_key, new_widget, parent_html_id, patches, new_rendered_map, previous_map_for_context)
                    if new_key in new_rendered_map: node_info['html_id'] = new_rendered_map[new_key]['html_id']
                    else: print(f"      [Child Diff WARNING] Key {new_key} updated but not in new_rendered_map for html_id retrieval.")
                    
                    if old_idx < last_matched_old_idx: node_info['moved'] = True
                    else: last_matched_old_idx = old_idx
                else: 
                    node_info['is_new'] = True
            else: 
                node_info['is_new'] = True
            new_children_info.append(node_info)
            
        for i, node_info in enumerate(new_children_info):
            new_key = node_info['key']
            new_widget = node_info['widget']
            
            before_id = None
            for j in range(i + 1, len(new_children_info)):
                next_node_in_new_list_info = new_children_info[j]
                if not next_node_in_new_list_info.get('is_new') and not next_node_in_new_list_info.get('moved'):
                     next_key = next_node_in_new_list_info['key']
                     if next_key in new_rendered_map:
                          before_id = new_rendered_map[next_key]['html_id']
                          break
            
            if node_info.get('is_new'):
                # print(f"      [Child Diff] Pass 2 - Inserting new key={new_key} before {before_id or 'end'}")
                # The `new_widget` is the actual widget to be inserted.
                # `layout_props_override` for this direct insertion should be None,
                # as layout properties from its *own* parent (parent_html_id) are already applied
                # to parent_html_id. If `new_widget` is a layout widget, it will apply its
                # own layout_props_override to its children when its _insert_node_recursive is called.
                self._insert_node_recursive(
                    new_widget,
                    parent_html_id,
                    patches,
                    new_rendered_map,
                    previous_map_for_context, # <<< Make sure this is correctly passed
                    layout_props_override=None, # This applies if `new_widget` ITSELF is a layout widget modifying ITS child
                    before_id=before_id
                )
                # Ensure html_id is updated in node_info after insertion
                if new_key in new_rendered_map: # Ensure html_id is updated in node_info if generated
                     node_info['html_id'] = new_rendered_map[new_key]['html_id']

            elif node_info.get('moved'):
                moved_html_id = node_info.get('html_id')
                if moved_html_id:
                    patches.append(Patch(action='MOVE', html_id=moved_html_id, data={'parent_html_id': parent_html_id, 'before_id': before_id}))
                    # print(f"        [Patch] MOVE: html_id={moved_html_id} into {parent_html_id}" + (f" before {before_id}" if before_id else " to end"))
                else:
                    print(f"      [Child Diff] ERROR: Could not find html_id for MOVED key={new_key}")