# framework/reconciler.py

import uuid
import html # For escaping text content
from typing import Any, Dict, List, Optional, Tuple, Union, Set, TYPE_CHECKING, Callable

# Avoid circular import for type hints
if TYPE_CHECKING:
    from .base import Widget, Key

# --- Key Class ---
class Key:
    """Provides a stable identity for widgets across rebuilds."""
    def __init__(self, value):
        try:
            hash(value)
            self.value = value
        except TypeError:
            if isinstance(value, list): self.value = tuple(value)
            elif isinstance(value, dict): self.value = tuple(sorted(value.items()))
            else: self.value = str(value)
            try: hash(self.value)
            except TypeError: raise TypeError(f"Key value {value!r} could not be made hashable.")

    def __eq__(self, other):
        return isinstance(other, Key) and self.value == other.value

    def __hash__(self):
        return hash((self.__class__, self.value))

    def __repr__(self):
        return f"Key({self.value!r})"

# --- Simple ID Generator ---
class IDGenerator:
    """Generates unique HTML IDs."""
    def __init__(self):
        self._count = 0

    def next_id(self) -> str:
        self._count += 1
        return f"fw_id_{self._count}"

# --- Patch Definition ---
# ACTION: 'INSERT', 'REMOVE', 'UPDATE', 'MOVE'
Patch = Tuple[str, str, Dict[str, Any]]

# --- Helper Type for Node Data ---
NodeData = Dict[str, Any]

# --- Reconciler Class ---
class Reconciler:
    """
    Compares widget trees and generates DOM patches, including moves.
    Manages rendered state across multiple contexts.
    """
    def __init__(self):
        self.context_maps: Dict[str, Dict[Union[Key, str], NodeData]] = {'main': {}}
        self.id_generator = IDGenerator()
        self.active_css_details: Dict[str, Tuple[Callable, Tuple]] = {}
        print("Reconciler Initialized")

    # --- Context Management ---
    def get_map_for_context(self, context_key: str) -> Dict[Union[Key, str], NodeData]:
        """Gets or creates the element map for a specific rendering context."""
        return self.context_maps.setdefault(context_key, {})

    def clear_context(self, context_key: str):
         if context_key in self.context_maps: del self.context_maps[context_key]; print(f"Reconciler context '{context_key}' cleared.")

    # --- HTML Stub / Tag Generation ---
    def _get_widget_render_tag(self, widget: 'Widget') -> str:
        # ... (implementation as before) ...
        widget_type_name = type(widget).__name__
        tag_map = { # Keep this map updated
              'Text': 'p', 'Image': 'img', 'Icon': 'i',
              'TextButton': 'button', 'ElevatedButton': 'button', 'IconButton': 'button',
              'FloatingActionButton': 'button', 'SnackBarAction': 'button',
              # Default others to div
         }
        if widget_type_name == 'Icon' and getattr(widget, 'custom_icon_source', None): return 'img'
        return tag_map.get(widget_type_name, 'div')


    def _generate_html_stub(self, widget: 'Widget', html_id: str, props: Dict) -> str:
        """Generates a basic HTML stub for INSERT patch, including essential props."""
        from .base import Widget # Local import
        import html # Ensure html module is imported

        tag = self._get_widget_render_tag(widget)
        classes = props.get('css_class', '')
        content = ""
        attrs = ""
        widget_type_name = type(widget).__name__

        # --- Handle specific widget types / props ---
        if widget_type_name == 'Text':
            content = html.escape(str(props.get('data', '')))
        elif widget_type_name == 'Image':
            attrs += f" src=\"{html.escape(props.get('src', ''), quote=True)}\""
            attrs += f" alt=\"\"" # Add empty alt for accessibility
            tag = 'img'
        elif widget_type_name == 'Icon':
            if props.get('render_type') == 'img':
                attrs += f" src=\"{html.escape(props.get('custom_icon_src', ''), quote=True)}\""
                attrs += f" alt=\"\""
                tag = 'img'
            else: # Font icon
                base_fa_class = "fa" # Or other icon library prefix
                icon_name_class = f"fa-{props.get('icon_name', 'question-circle')}" # Default icon
                classes = f"{base_fa_class} {icon_name_class} {classes}".strip()
                tag = 'i'
        elif widget_type_name == 'Placeholder':
            if not props.get('has_child'):
                content = html.escape(props.get('fallbackText', 'Placeholder'))
            else:
                 content = '' # Content comes from child reconciliation
        # --- CORRECTED BUTTON HANDLING ---
        elif widget_type_name in ['TextButton', 'ElevatedButton', 'IconButton', 'FloatingActionButton', 'SnackBarAction']:
            tag = 'button'
            # Content comes from child reconciliation (label/icon)

            # Handle onclick attribute
            cb_name = props.get('onPressedName')
            if cb_name:
                # Escape for JS single quotes used in the HTML attribute value
                cb_name_escaped = cb_name.replace("'", "\\'")
                attrs += f' onclick="handleClick(\'{cb_name_escaped}\')"'

            # Handle tooltip (title attribute)
            tooltip_text = props.get('tooltip')
            if tooltip_text:
                attrs += f' title="{html.escape(tooltip_text, quote=True)}"'
        # --- END OF CORRECTION ---
        elif widget_type_name == 'ListTile':
            attrs += ' role="listitem"' # Accessibility
            cb_name = props.get('onTapName')
            # Apply onclick only if enabled
            if cb_name and props.get('enabled', True):
                cb_name_escaped = cb_name.replace("'", "\\'")
                attrs += f' onclick="handleItemTap(\'{cb_name_escaped}\')"' # Assumes handleItemTap exists
        elif widget_type_name == 'Divider':
            tag = 'div' # Use div for easier styling than <hr>
            attrs += ' role="separator"'
        elif widget_type_name == 'Dialog':
             attrs += ' role="dialog" aria-modal="true" aria-hidden="true"' # Start hidden
        # Add specific attributes for other widgets if needed (e.g., role, aria-*)


        # Basic self-closing tags
        if tag in ['img', 'hr', 'br']:
            return f'<{tag} id="{html_id}" class="{classes}"{attrs}>'
        else:
            return f'<{tag} id="{html_id}" class="{classes}"{attrs}>{content}</{tag}>'

    # --- Rest of Reconciler class ---
    # ... (init, _diff_props, reconcile_subtree, _diff_node_recursive, etc.) ...

    # --- Property Diffing ---
    def _diff_props(self, old_props: Dict, new_props: Dict) -> Optional[Dict]:
        # ... (implementation as before) ...
        changes = {}
        all_keys = set(old_props.keys()) | set(new_props.keys())
        for key in all_keys:
            old_val = old_props.get(key); new_val = new_props.get(key)
            if old_val != new_val: changes[key] = new_val
        return changes if changes else None

    # --- Main Reconciliation Entry Point ---
    def reconcile_subtree(self, current_subtree_root: Optional['Widget'], parent_html_id: str, context_key: str = 'main') -> List[Patch]:
        """Reconciles a specific widget subtree within a given context."""
        print(f"\n--- Reconciling Subtree (Context: '{context_key}', Parent: '{parent_html_id}') ---")
        from .base import Widget # Local import

        patches: List[Patch] = []
        new_rendered_map: Dict[Union[Key, str], NodeData] = {}
        previous_map = self.get_map_for_context(context_key)

        # Clear CSS details for this cycle (only if reconciling the 'main' context, or manage per context?)
        # Let's clear globally for now, assuming CSS applies globally.
        if context_key == 'main': # Or maybe always clear? Check CSS scope.
             self.active_css_details.clear()

        old_root_key = None
        for key, data in previous_map.items():
            if data.get('parent_html_id') == parent_html_id: old_root_key = key; break

        self._diff_node_recursive(
            old_node_key=old_root_key,
            new_widget=current_subtree_root,
            parent_html_id=parent_html_id,
            patches=patches,
            new_rendered_map=new_rendered_map,
            previous_context_map=previous_map
        )

        # Removal Phase (Specific to this context)
        old_keys = set(previous_map.keys())
        new_keys = set(new_rendered_map.keys())
        removed_keys = old_keys - new_keys
        for removed_key in removed_keys:
            removed_data = previous_map[removed_key]
            patches.append(('REMOVE', removed_data['html_id'], {}))
            print(f"  [Patch] REMOVE ({context_key}): html_id={removed_data['html_id']} (key={removed_key})")

        self.context_maps[context_key] = new_rendered_map
        print(f"--- Subtree Reconciliation End ({context_key}). Patches: {len(patches)} ---")
        return patches

    # --- Recursive Diffing ---
    def _diff_node_recursive(self, old_node_key: Optional[Union['Key', str]], new_widget: Optional['Widget'], parent_html_id: str, patches: List[Patch], new_rendered_map: Dict, previous_context_map: Dict):
        """Recursive diffing function - handles layout widgets, populates CSS details."""
        from .base import Widget, Key # Local import

        layout_props_override = None
        actual_new_widget = new_widget
        widget_type_name = type(new_widget).__name__ if new_widget else None
        layout_widget_types = [ # Keep this list updated
             'Padding', 'Align', 'Center', 'Expanded', 'Spacer',
             'Positioned', 'AspectRatio', 'FittedBox', 'FractionallySizedBox'
        ]

        if widget_type_name in layout_widget_types:
            if widget_type_name == 'Placeholder' and getattr(new_widget, 'child', None) is not None: actual_new_widget = new_widget.child
            elif widget_type_name != 'Placeholder':
                layout_props_override = new_widget.render_props()
                actual_new_widget = new_widget.get_children()[0] if new_widget.get_children() else None

        new_widget_unique_id = actual_new_widget.get_unique_id() if actual_new_widget else None
        old_data = previous_context_map.get(old_node_key) if old_node_key else None

        # Base Cases
        if actual_new_widget is None and old_data is None: return
        if actual_new_widget is None: return # Removal handled later
        if old_data is None: self._insert_node_recursive(actual_new_widget, parent_html_id, patches, new_rendered_map, previous_context_map, layout_props_override); return # Insertion

        # Update / Replace Cases
        old_html_id = old_data['html_id']; old_type = old_data['widget_type']
        new_type = type(actual_new_widget).__name__
        old_key = old_data.get('key'); new_key = getattr(actual_new_widget, 'key', None)

        should_replace = False
        if new_key is not None and old_key != new_key: should_replace = True
        elif old_key is not None and new_key is None: should_replace = True
        elif new_key is None and old_key is None and old_type != new_type: should_replace = True

        if should_replace:
            print(f"  [Diff] Node Replace: old_key={old_key}, new_key={new_key}, old_type={old_type}, new_type={new_type}")
            self._insert_node_recursive(actual_new_widget, parent_html_id, patches, new_rendered_map, previous_context_map, layout_props_override)
            return

        # --- Update ---
        print(f"  [Diff] Node Update Check: key={new_key or old_key}, type={new_type}, html_id={old_html_id}")
        new_props = actual_new_widget.render_props()
        if layout_props_override: new_props['layout_override'] = layout_props_override

        # Store CSS Details
        css_class = new_props.get('css_class')
        if css_class and hasattr(actual_new_widget, 'style_key') and hasattr(actual_new_widget, 'generate_css_rule'):
             if css_class not in self.active_css_details:
                  gen_func = getattr(type(actual_new_widget), 'generate_css_rule')
                  style_key = getattr(actual_new_widget, 'style_key')
                  self.active_css_details[css_class] = (gen_func, style_key)

        # Diff Props
        prop_changes = self._diff_props(old_data['props'], new_props)
        if prop_changes:
            patch_data = {'props': prop_changes}
            if layout_props_override: patch_data['layout_override'] = layout_props_override
            patches.append(('UPDATE', old_html_id, patch_data))
            print(f"    [Patch] UPDATE: html_id={old_html_id}, changes={list(prop_changes.keys())}")

        # Record updated node in new map
        new_map_entry = {
            'html_id': old_html_id, 'widget_type': new_type, 'key': new_key,
            'internal_id': getattr(actual_new_widget, '_internal_id', None),
            'props': new_props, 'parent_html_id': parent_html_id,
            'children_keys': [c.get_unique_id() for c in actual_new_widget.get_children()]
        }
        new_rendered_map[new_widget_unique_id] = new_map_entry

        # --- Diff Children ---
        self._diff_children_recursive(
             old_data.get('children_keys', []),
             actual_new_widget.get_children(),
             old_html_id, # Parent HTML ID for children is current node's ID
             patches, new_rendered_map, previous_context_map
        )

    # --- Insertion Logic ---
    def _insert_node_recursive(self, new_widget: 'Widget', parent_html_id: str, patches: List[Patch], new_rendered_map: Dict, previous_context_map: Dict, layout_props_override: Optional[Dict] = None, before_id: Optional[str] = None):
        """Handles node insertion, including storing CSS details and before_id."""
        from .base import Widget, Key # Local import

        new_widget_unique_id = new_widget.get_unique_id()
        html_id = self.id_generator.next_id()
        widget_props = new_widget.render_props()
        if layout_props_override: widget_props['layout_override'] = layout_props_override

        # Store CSS Details
        css_class = widget_props.get('css_class')
        if css_class and hasattr(new_widget, 'style_key') and hasattr(new_widget, 'generate_css_rule'):
            if css_class not in self.active_css_details:
                gen_func = getattr(type(new_widget), 'generate_css_rule'); style_key = getattr(new_widget, 'style_key')
                self.active_css_details[css_class] = (gen_func, style_key)

        # Add to new map
        new_map_entry = { # ... (create entry as before) ... }
            'html_id': html_id, 'widget_type': type(new_widget).__name__, 'key': getattr(new_widget, 'key', None),
            'internal_id': getattr(new_widget, '_internal_id', None), 'props': widget_props,
            'parent_html_id': parent_html_id,
            'children_keys': [c.get_unique_id() for c in new_widget.get_children()]
        }
        new_rendered_map[new_widget_unique_id] = new_map_entry

        # Create INSERT patch with before_id
        patch_data = {
            'html': self._generate_html_stub(new_widget, html_id, widget_props),
            'parent_html_id': parent_html_id,
            'props': widget_props,
            'before_id': before_id # <<< Pass the calculated before_id
        }
        patches.append(('INSERT', html_id, patch_data))
        print(f"  [Patch] INSERT: html_id={html_id} into {parent_html_id} (key={getattr(new_widget, 'key', None)})" + (f" before {before_id}" if before_id else ""))

        # Recurse for children (passing maps)
        for child_widget in new_widget.get_children():
            self._diff_node_recursive(None, child_widget, html_id, patches, new_rendered_map, previous_context_map)


    # --- Child Diffing with Moves and Ordered Insert ---
    def _diff_children_recursive(self, old_children_keys: List[Union['Key', str]], new_children_widgets: List['Widget'], parent_html_id: str, patches: List[Patch], new_rendered_map: Dict, previous_context_map: Dict):
        """Diffs child lists using keys, handling inserts, updates, moves, and removals."""
        from .base import Widget, Key # Local import

        if not old_children_keys and not new_children_widgets: return

        print(f"    [Child Diff] Parent: {parent_html_id}, Old keys#: {len(old_children_keys)}, New widgets#: {len(new_children_widgets)}")

        # --- Preparation ---
        old_key_to_index = {key: i for i, key in enumerate(old_children_keys)}
        new_widgets_map = {widget.get_unique_id(): widget for widget in new_children_widgets}
        new_key_to_index = {key: i for i, key in enumerate(new_widgets_map.keys())} # Index in the *new* list

        processed_old_keys = set() # Old keys matched in the new list
        moved_keys = set() # Keys identified as needing a MOVE patch

        # --- Pass 1: Identify Updates and Stable/Moved Nodes ---
        last_old_index_processed = -1 # Track old list order for move detection
        for i, new_widget in enumerate(new_children_widgets):
            new_key = new_widget.get_unique_id()
            old_index = old_key_to_index.get(new_key)

            if old_index is not None: # Key match found -> Update node, check for move
                processed_old_keys.add(new_key)
                old_data = previous_context_map.get(new_key) # Get old node data

                if old_data:
                    # Diff the node itself
                    self._diff_node_recursive(new_key, new_widget, parent_html_id, patches, new_rendered_map, previous_context_map)

                    # Check for moves relative to previously processed stable nodes
                    if old_index < last_old_index_processed:
                        moved_keys.add(new_key)
                        print(f"      [Child Diff] Marked key={new_key} for MOVE (Old:{old_index}, LastProcessed:{last_old_index_processed})")
                    else:
                         last_old_index_processed = old_index # Update last stable position
                # else: Handle inconsistency (key exists but no data?) - treat as insert?

        # --- Pass 2: Handle Inserts and Moves ---
        # Iterate new children again to place inserts/moves correctly relative to stable nodes
        current_dom_index = 0 # Tracks the conceptual index in the target DOM parent
        processed_new_keys_for_placement = set()

        while current_dom_index < len(new_children_widgets):
            new_widget = new_children_widgets[current_dom_index]
            new_key = new_widget.get_unique_id()

            if new_key in processed_new_keys_for_placement:
                 current_dom_index += 1
                 continue # Already placed this node

            # Find the next *stable* (unmoved, existing) node *after* current index in the new list
            next_stable_node_html_id = None
            for j in range(current_dom_index + 1, len(new_children_widgets)):
                 lookup_key = new_children_widgets[j].get_unique_id()
                 if lookup_key in old_key_to_index and lookup_key not in moved_keys:
                      # Found the next stable node, get its HTML ID from the *old* map
                      old_node_data = previous_context_map.get(lookup_key)
                      if old_node_data:
                           next_stable_node_html_id = old_node_data['html_id']
                           break

            # Now process the current new_key
            old_index = old_key_to_index.get(new_key)

            if old_index is None: # --- Handle INSERT ---
                print(f"      [Child Diff] Inserting key={new_key} at index {current_dom_index} before {next_stable_node_html_id or 'end'}")
                # Pass layout overrides if applicable (needs parent info)
                parent_override = new_rendered_map.get(parent_html_id, {}).get('props', {}).get('layout_override')
                self._insert_node_recursive(new_widget, parent_html_id, patches, new_rendered_map, previous_context_map, parent_override, before_id=next_stable_node_html_id)
                processed_new_keys_for_placement.add(new_key)
                current_dom_index += 1 # Move to next position

            elif new_key in moved_keys: # --- Handle MOVE ---
                 print(f"      [Child Diff] Moving key={new_key} before {next_stable_node_html_id or 'end'}")
                 moved_html_id = new_rendered_map.get(new_key, {}).get('html_id') # Get html_id from new map (already processed in Pass 1)
                 if moved_html_id:
                      patches.append(('MOVE', moved_html_id, {'parent_html_id': parent_html_id, 'before_id': next_stable_node_html_id}))
                      print(f"        [Patch] MOVE: html_id={moved_html_id} into {parent_html_id}" + (f" before {next_stable_node_html_id}" if next_stable_node_html_id else ""))
                 processed_new_keys_for_placement.add(new_key)
                 current_dom_index += 1 # Move to next position
            else: # --- Stable Node ---
                 # Already updated in Pass 1, just mark as placed and move index
                 processed_new_keys_for_placement.add(new_key)
                 current_dom_index += 1


        # --- Removals ---
        # Handled globally by reconcile_subtree comparing the full context maps.