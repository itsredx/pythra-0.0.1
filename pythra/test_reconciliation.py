# test_reconciliation.py

import time
import uuid

# --- Mock Widget Infrastructure ---
# We create minimal versions of the widgets to avoid depending on the whole UI framework.

class MockWidget:
    def __init__(self, key=None, children=None):
        self.key = key
        # Use a stable but unique identifier for keyless widgets for testing purposes
        self._id = str(id(self))
        if key is None:
            self.key = self._id
            
        self._children = children if children is not None else []

    def get_children(self):
        return self._children

    def get_unique_id(self):
        return self.key
    
    def render_props(self):
        return {'type': self.__class__.__name__}

class Container(MockWidget):
    def __init__(self, children, key=None):
        super().__init__(key=key, children=children)

class Text(MockWidget):
    def __init__(self, text, key=None):
        super().__init__(key=key)
        self.text = text

    def render_props(self):
        props = super().render_props()
        props['data'] = self.text
        return props

# --- Mock Framework Objects ---

class MockIDGenerator:
    def __init__(self):
        self._count = 0
    def next_id(self):
        self._count += 1
        return f"mock_id_{self._count}"

# This is where we import our compiled module!
try:
    import fast_diff
    CYTHON_ENABLED = True
    print("✅ Cython `fast_diff` module loaded successfully.")
except ImportError as e:
    print(f"❌ ERROR: Could not import Cython module. {e}")
    print("Ensure you have run 'python setup.py build_ext --inplace'")
    fast_diff = None
    CYTHON_ENABLED = False


# --- The Test Runner ---

def run_test(name, old_tree, new_tree):
    print("-" * 60)
    print(f"Running Test: {name}")
    print("-" * 60)

    # Setup
    id_generator = MockIDGenerator()
    old_map, _ = build_map_from_tree(old_tree, "root", id_generator)
    
    if not CYTHON_ENABLED:
        print("Skipping Cython test as module is not available.")
        return

    # --- Run Cython Test ---
    start_time = time.perf_counter()
    patches = fast_diff.fast_diff(old_map, new_tree, "root", MockIDGenerator())
    end_time = time.perf_counter()
    
    print(f"🚀 Cython Result ({end_time - start_time:.6f} seconds):")
    for patch in patches:
        # Simplify data for printing
        if 'widget_instance' in patch.get('data', {}):
            del patch['data']['widget_instance']
        print(f"  - {patch}")
    print("\n")
    return patches


# --- Helper to build the 'previous_map' for tests ---

def build_map_from_tree(widget, parent_html_id, id_gen):
    if widget is None:
        return {}, None

    html_id = id_gen.next_id()
    key = widget.get_unique_id()
    
    node_data = {
        'html_id': html_id,
        'widget_type': type(widget).__name__,
        'key': widget.key,
        'widget_instance': widget,
        'props': widget.render_props(),
        'parent_html_id': parent_html_id,
        'children_keys': [child.get_unique_id() for child in widget.get_children()]
    }
    
    rendered_map = {key: node_data}
    
    for child in widget.get_children():
        child_map, _ = build_map_from_tree(child, html_id, id_gen)
        rendered_map.update(child_map)
        
    return rendered_map, html_id


# ==============================================================================
# TEST CASES
# ==============================================================================

# 1. Simple INSERT
old_tree_1 = Container([], key="root_container")
new_tree_1 = Container([Text("Hello")], key="root_container")
patches = run_test("Simple INSERT", old_tree_1, new_tree_1)
assert len(patches) == 1 and patches[0]['action'] == 'INSERT'

# 2. Simple REMOVE
old_tree_2 = Container([Text("Hello")], key="root_container")
new_tree_2 = Container([], key="root_container")
patches = run_test("Simple REMOVE", old_tree_2, new_tree_2)
assert len(patches) == 1 and patches[0]['action'] == 'REMOVE'

# 3. Simple UPDATE
old_tree_3 = Container([Text("Hello", key="A")], key="root_container")
new_tree_3 = Container([Text("Goodbye", key="A")], key="root_container")
patches = run_test("Simple UPDATE", old_tree_3, new_tree_3)
assert len(patches) == 1 and patches[0]['action'] == 'UPDATE'

# 4. Keyed MOVE (Reorder)
old_tree_4 = Container([
    Text("A", key="A"), Text("B", key="B"), Text("C", key="C"),
], key="root_container")
new_tree_4 = Container([
    Text("C", key="C"), Text("B", key="B"), Text("A", key="A"),
], key="root_container")
patches = run_test("Keyed MOVE (Reorder)", old_tree_4, new_tree_4)
# We expect two moves: C to the front, A to the back. A smart diff might only do one.
# Our diff will generate two moves based on its algorithm.
move_actions = [p['action'] for p in patches]
assert len(patches) == 2 and move_actions.count('MOVE') == 2

# 5. Mixed Operations (Insert, Move, Remove)
old_tree_5 = Container([
    Text("A", key="A"), Text("B", key="B"), Text("C", key="C"), Text("D", key="D"),
], key="root_container")
new_tree_5 = Container([
    Text("D", key="D"), Text("E", key="E"), Text("C", key="C"), Text("B", key="B"),
], key="root_container")
patches = run_test("Mixed Keyed Operations", old_tree_5, new_tree_5)
actions = sorted([p['action'] for p in patches])
# Expect: REMOVE 'A', INSERT 'E', MOVE 'D', MOVE 'B'
assert actions == ['INSERT', 'MOVE', 'MOVE', 'REMOVE']

# 6. Replace Node
old_tree_6 = Container([Text("I am old", key="child")], key="root_container")
new_tree_6 = Container([Container([], key="child")], key="root_container")
patches = run_test("Replace Node (Different Type, Same Key)", old_tree_6, new_tree_6)
# Should generate one REMOVE and one INSERT for the child
actions = sorted([p['action'] for p in patches])
assert actions == ['INSERT', 'REMOVE']


# ==============================================================================
# STRESS TEST
# ==============================================================================

def run_stress_test(num_elements):
    print("=" * 60)
    print(f"STRESS TEST: Diffing a list of {num_elements} elements.")
    print("=" * 60)

    # --- Setup ---
    # Create a large list of keyed text widgets
    old_list = [Text(f"Item {i}", key=i) for i in range(num_elements)]
    
    # Create a new list where one item in the middle is updated
    new_list = [Text(f"Item {i}", key=i) for i in range(num_elements)]
    updated_key = num_elements // 2
    new_list[updated_key] = Text("UPDATED ITEM", key=updated_key)

    old_tree = Container(old_list, key="root_container")
    new_tree = Container(new_list, key="root_container")

    id_generator = MockIDGenerator()
    old_map, _ = build_map_from_tree(old_tree, "root", id_generator)

    if not CYTHON_ENABLED:
        print("Skipping stress test as Cython module is not available.")
        return

    # --- Time Cython (UPDATE) ---
    start_cy = time.perf_counter()
    patches_cy = fast_diff.fast_diff(old_map, new_tree, "root", MockIDGenerator())
    end_cy = time.perf_counter()
    
    print(f"🚀 Cython (UPDATE) took {end_cy - start_cy:.6f} seconds")
    print(f"   - Generated {len(patches_cy)} patches.")
    assert len(patches_cy) == 1
    assert patches_cy[0]['action'] == 'UPDATE'
    
    # --- Time Cython (REORDER) ---
    new_list_reordered = list(new_list)
    item_to_move = new_list_reordered.pop(1) # Move the second item
    new_list_reordered.insert(-2, item_to_move) # to the second-to-last position
    new_tree_reordered = Container(new_list_reordered, key="root_container")
    
    start_cy_move = time.perf_counter()
    patches_cy_move = fast_diff.fast_diff(old_map, new_tree_reordered, "root", MockIDGenerator())
    end_cy_move = time.perf_counter()

    print(f"🚀 Cython (REORDER) took {end_cy_move - start_cy_move:.6f} seconds")
    print(f"   - Generated {len(patches_cy_move)} patches.")
    # We expect 1 MOVE and 1 UPDATE (because the reordered list still has the updated item)
    actions = sorted([p['action'] for p in patches_cy_move])
    assert actions == ['MOVE', 'UPDATE']


if __name__ == "__main__":
    if CYTHON_ENABLED:
        run_stress_test(10000)
        print("\n✅ All tests completed.")