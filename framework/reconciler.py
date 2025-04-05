# framework/reconciler.py

import uuid
from typing import Any, Dict, List, Optional, Tuple, Union, Set, TYPE_CHECKING

# Avoid circular import for type hints if Reconciler needs specific widget types later
if TYPE_CHECKING:
    from .base import Widget, Key
    from .widgets import Container, Text # Example imports if needed

# --- Key Class (Can live here or in base.py) ---
# If moving from base.py, update imports elsewhere
class Key:
    def __init__(self, value):
        self.value = value

    def __eq__(self, other):
        # Basic comparison, assumes value is comparable
        return isinstance(other, Key) and self.value == other.value

    def __hash__(self):
        # Basic hash, assumes value is hashable
        # Add error handling or conversion for unhashable types if needed
        try:
            return hash((self.__class__, self.value))
        except TypeError:
            print(f"Warning: Key value {self.value!r} of type {type(self.value)} is not hashable.")
            return hash((self.__class__, str(self.value))) # Fallback to string hash

    def __repr__(self):
        return f"Key({self.value!r})"

# --- Simple ID Generator ---
class IDGenerator:
    def __init__(self):
        self._count = 0

    def next_id(self):
        self._count += 1
        return f"fw_id_{self._count}" # Prefix to avoid potential HTML ID conflicts

# --- Patch Definition ---
Patch = Tuple[str, str, Dict[str, Any]] # (ACTION, target_html_id, data)

# --- Reconciler Class ---
class Reconciler:
    def __init__(self):
        # Maps unique widget ID (Key or internal str) -> rendered data....
        self.rendered_elements_map: Dict[Union['Key', str], Dict[str, Any]] = {}
        self.id_generator = IDGenerator()
        print("Reconciler Initialized")

    def _diff_props(self, old_props: Dict, new_props: Dict) -> Optional[Dict]:
        """Compares property dictionaries and returns changes (new values)."""
        changes = {}
        all_keys = set(old_props.keys()) | set(new_props.keys())
        for key in all_keys:
            old_val = old_props.get(key)
            new_val = new_props.get(key)
            if old_val != new_val:
                changes[key] = new_val # Store the new value for the patch
        return changes if changes else None

    def _generate_html_stub(self, widget: 'Widget', html_id: str) -> str:
        """
        Generates a basic HTML stub for insertion.
        Needs to be aware of basic widget types or have widgets provide tag info.
        """
        # Import locally ONLY if necessary and Widget base doesn't provide tag info
        # from .widgets import Text, Container, Column # Example

        tag = "div" # Default tag
        content = ""
        classes = getattr(widget, 'css_class', '') # Get css_class if widget has it

        # Determine tag based on type (This is simplified)
        widget_type_name = type(widget).__name__
        if widget_type_name == 'Text':
            tag = "p"
            content = getattr(widget, 'data', '') # Get text data
        elif widget_type_name == 'Container':
            tag = "div"
        elif widget_type_name == 'Column': # Or Row, etc.
            tag = "div"
        # Add more specific tag mappings as needed

        # Escape content for HTML safety
        import html
        escaped_content = html.escape(str(content)) if content else ''

        return f'<{tag} id="{html_id}" class="{classes}">{escaped_content}</{tag}>' # Use assigned classes

    def reconcile(self, new_widget: Optional['Widget'], parent_html_id: Optional[str] = None) -> List[Patch]:
        """Main reconciliation entry point, returns patches."""
        print("\n--- Reconciliation Start ---")
        from .base import Widget # Import locally to ensure Widget definition is available

        patches: List[Patch] = []
        new_rendered_map: Dict[Union['Key', str], Dict[str, Any]] = {}
        root_parent_target = parent_html_id if parent_html_id is not None else 'root-container' # Default target

        # Map old keys/ids to their corresponding node key in the old map
        old_keys_map = {data['html_id']: key for key, data in self.rendered_elements_map.items()}
        # Find the key for the root of the *previous* tree, if it existed
        old_root_key = None
        # Simple approach: assume first element without explicit parent was root
        # A better approach might involve tracking the root key explicitly.
        for key, data in self.rendered_elements_map.items():
             if data.get('parent_html_id') == root_parent_target: # Check against the same root target
                  old_root_key = key
                  break
             # Fallback if parent IDs weren't tracked well initially
             if not old_root_key and len(self.rendered_elements_map) == 1:
                 old_root_key = key

        # Start recursive diffing
        self._diff_node(
            old_node_key=old_root_key,
            new_widget=new_widget,
            parent_html_id=root_parent_target,
            patches=patches,
            new_rendered_map=new_rendered_map
        )

        # --- Removal Phase ---
        # Identify removals: Elements in the old map that weren't added to the new map
        old_unique_keys = set(self.rendered_elements_map.keys())
        new_unique_keys = set(new_rendered_map.keys())
        removed_unique_keys = old_unique_keys - new_unique_keys

        for removed_key in removed_unique_keys:
            removed_data = self.rendered_elements_map[removed_key]
            # Check if element wasn't already removed by a parent's outerHTML update (harder to track)
            patches.append(('REMOVE', removed_data['html_id'], {}))
            print(f"  [Patch] REMOVE: html_id={removed_data['html_id']} (key={removed_key})")

        # Update the main map for the next cycle
        self.rendered_elements_map = new_rendered_map
        print(f"--- Reconciliation End. Patches: {len(patches)} ---")
        return patches

    def _diff_node(self,
                   old_node_key: Optional[Union['Key', str]],
                   new_widget: Optional['Widget'],
                   parent_html_id: str,
                   patches: List[Patch],
                   new_rendered_map: Dict):
        """Recursive diffing function."""
        # Import locally to ensure Widget definition is available
        from .base import Widget, Key

        old_data = self.rendered_elements_map.get(old_node_key) if old_node_key else None
        new_widget_unique_id = new_widget.get_unique_id() if new_widget else None

        # --- Base Cases ---
        # 1. Both are None: Nothing to do
        if new_widget is None and old_data is None:
            return
        # 2. Removal: New is None, Old exists (Handled by map comparison later)
        if new_widget is None:
            # No immediate patch, mark old_data for potential removal later
            print(f"  [Diff] Node Removal Candidate: key={old_node_key}, html_id={old_data['html_id']}")
            return
        # 3. Insertion: New exists, Old is None
        if old_data is None:
            self._insert_node(new_widget, parent_html_id, patches, new_rendered_map)
            return

        # --- Update / Replace Cases ---
        old_html_id = old_data['html_id']
        old_type = old_data['widget_type']
        new_type = type(new_widget).__name__
        old_key = old_data.get('key')
        new_key = getattr(new_widget, 'key', None) # Access key directly

        # 4. Replace: Keys differ OR Types differ
        #    (Note: Key comparison is primary. Type comparison is fallback if no keys)
        should_replace = False
        if new_key is not None and old_key != new_key:
             should_replace = True
        elif new_key is None and old_key is not None: # Old had key, new doesn't
             should_replace = True
        elif new_key is None and old_key is None and old_type != new_type: # No keys, types differ
             should_replace = True

        if should_replace:
            print(f"  [Diff] Node Replace: old_key={old_key}, new_key={new_key}, old_type={old_type}, new_type={new_type}")
            # Treat as insertion of the new node. Removal of old node handled later.
            self._insert_node(new_widget, parent_html_id, patches, new_rendered_map)
            return

        # 5. Update: Keys match (or both None) AND Types match
        print(f"  [Diff] Node Update Check: key={new_key or old_key}, type={new_type}, html_id={old_html_id}")
        # Compare props
        new_props = new_widget.render_props()
        prop_changes = self._diff_props(old_data['props'], new_props)
        if prop_changes:
            patches.append(('UPDATE', old_html_id, {'props': prop_changes}))
            print(f"    [Patch] UPDATE: html_id={old_html_id}, changes={prop_changes}")

        # Record updated node in the new map (reuse html_id)
        new_map_entry = {
            'html_id': old_html_id,
            'widget_type': new_type,
            'key': new_key,
            'internal_id': getattr(new_widget, '_internal_id', None),
            'props': new_props, # Store new props
            'parent_html_id': parent_html_id,
            'children_keys': [c.get_unique_id() for c in new_widget.get_children()]
        }
        new_rendered_map[new_widget_unique_id] = new_map_entry

        # --- Diff Children (Keyed Reconciliation) ---
        self._diff_children(
             old_data.get('children_keys', []),
             new_widget.get_children(),
             old_html_id, # Parent HTML ID for children is the current node's ID
             patches,
             new_rendered_map
        )

    def _insert_node(self, new_widget: 'Widget', parent_html_id: str, patches: List[Patch], new_rendered_map: Dict):
        """Handles node insertion logic."""
        # Import locally to ensure Widget definition is available
        from .base import Widget, Key

        new_widget_unique_id = new_widget.get_unique_id()
        html_id = self.id_generator.next_id()
        widget_props = new_widget.render_props()

        # Add to the *new* map immediately
        new_map_entry = {
            'html_id': html_id,
            'widget_type': type(new_widget).__name__,
            'key': getattr(new_widget, 'key', None),
            'internal_id': getattr(new_widget, '_internal_id', None),
            'props': widget_props,
            'parent_html_id': parent_html_id,
            'children_keys': [c.get_unique_id() for c in new_widget.get_children()]
        }
        # Use the widget's unique ID (key or internal) as the map key
        new_rendered_map[new_widget_unique_id] = new_map_entry

        # Create INSERT patch
        patch_data = {
            'html': self._generate_html_stub(new_widget, html_id),
            'parent_html_id': parent_html_id,
            # 'before_id': None # TODO: Add sibling order logic if needed
        }
        patches.append(('INSERT', html_id, patch_data))
        print(f"  [Patch] INSERT: html_id={html_id} into {parent_html_id} (key={getattr(new_widget, 'key', None)})")

        # Recursively diff children of the newly inserted node
        # Children are inserted relative to the new node's html_id
        for child_widget in new_widget.get_children():
             # Old node key for children of a new node is always None
            self._diff_node(None, child_widget, html_id, patches, new_rendered_map)

    def _diff_children(self,
                       old_children_keys: List[Union['Key', str]],
                       new_children_widgets: List['Widget'],
                       parent_html_id: str,
                       patches: List[Patch],
                       new_rendered_map: Dict):
        """
        Diffs two lists of children using keys for matching.
        Generates insert, remove, update, and potentially reorder patches.
        """
        from .base import Widget, Key # Import locally

        # --- Preparation ---
        old_children_map = {key: self.rendered_elements_map.get(key) for key in old_children_keys if self.rendered_elements_map.get(key)}
        new_key_to_widget_map = {widget.get_unique_id(): widget for widget in new_children_widgets}
        old_key_set = set(old_children_keys)
        new_key_set = set(new_key_to_widget_map.keys())

        processed_old_keys = set() # Track old keys that found a match

        # --- Iterate through NEW children to find updates/inserts ---
        last_inserted_html_id = None # Track for ordering inserts
        for i, new_widget in enumerate(new_children_widgets):
            new_key = new_widget.get_unique_id()

            if new_key in old_key_set: # Match found based on key/internal ID
                old_data = old_children_map.get(new_key)
                if old_data: # Ensure old data actually existed
                     print(f"    [Child Diff] Match found for key={new_key}")
                     self._diff_node(new_key, new_widget, parent_html_id, patches, new_rendered_map)
                     processed_old_keys.add(new_key)
                     # TODO: Handle reordering - if index changed, generate MOVE patch
                     # This requires comparing old index vs new index.
                     last_inserted_html_id = new_rendered_map[new_key]['html_id'] # Track last processed element for insertion order
                else:
                     # Key existed in list but not in map? Data inconsistency. Insert.
                      print(f"    [Child Diff] Key {new_key} in old list but not map. Inserting.")
                      self._insert_node(new_widget, parent_html_id, patches, new_rendered_map)
                      # Need to add 'before_id' logic to INSERT patch for correct order
                      last_inserted_html_id = new_rendered_map[new_key]['html_id']
            else: # New key not in old set -> Insert
                 print(f"    [Child Diff] New child key={new_key}. Inserting.")
                 self._insert_node(new_widget, parent_html_id, patches, new_rendered_map)
                 # TODO: Add 'before_id' logic to INSERT patch based on 'last_inserted_html_id'
                 last_inserted_html_id = new_rendered_map[new_key]['html_id']


        # --- Identify Removals ---
        # Any old child key not in processed_old_keys needs to be removed.
        # Removal patches are handled globally at the end of reconcile().
        # No specific patches needed here, rely on the main map comparison.