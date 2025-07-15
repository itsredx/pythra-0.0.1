# # test_reconciliation.py

# import time
# import uuid

# # --- Mock Widget Infrastructure ---
# # NOW WE IMPORT THE FAST CYTHON WIDGETS
# try:
#     from pythra.base_widgets import Container, Text
#     print("✅ Cython `base_widgets` module loaded successfully.")
# except ImportError as e:
#     print(f"❌ ERROR: Could not import Cython widgets. {e}")
#     # Define Python fallbacks if compilation fails
#     class MockWidget:
#         def __init__(self, key=None, children=None):
#             self.key = key if key is not None else str(id(self))
#             self._children = children if children is not None else []
#         def get_children(self): return self._children
#         def get_unique_id(self): return self.key
#         def render_props(self): return {'type': self.__class__.__name__}
#     class Container(MockWidget):
#         def __init__(self, children, key=None): super().__init__(key=key, children=children)
#     class Text(MockWidget):
#         def __init__(self, text, key=None): super().__init__(key=key); self.text = text
#         def render_props(self): return {'type': 'Text', 'data': self.text}

# # --- Mock Framework Objects ---
# class MockIDGenerator:
#     def __init__(self): self._count = 0
#     def next_id(self): self._count += 1; return f"mock_id_{self._count}"

# try:
#     # Use the package-relative import
#     from pythra import fast_diff
#     CYTHON_ENABLED = True
#     print("✅ Cython `fast_diff` module loaded successfully.")
# except ImportError as e:
#     # ... (rest of the file is the same as before)
#     print(f"❌ ERROR: Could not import Cython module. {e}")
#     print("Ensure you have run 'python setup.py build_ext --inplace'")
#     fast_diff = None
#     CYTHON_ENABLED = False


# # --- The Test Runner ---
# def run_test(name, old_tree, new_tree):
#     print("-" * 60); print(f"Running Test: {name}"); print("-" * 60)
#     id_generator = MockIDGenerator(); old_map, _ = build_map_from_tree(old_tree, "root", id_generator)
#     if not CYTHON_ENABLED: print("Skipping Cython test as module is not available."); return
#     start_time = time.perf_counter(); patches = fast_diff.fast_diff(old_map, new_tree, "root", MockIDGenerator()); end_time = time.perf_counter()
#     print(f"🚀 Cython Result ({end_time - start_time:.6f} seconds):")
#     for patch in patches:
#         if 'widget_instance' in patch.get('data', {}): del patch['data']['widget_instance']
#         print(f"  - {patch}")
#     print("\n"); return patches

# # --- Helper to build the 'previous_map' for tests ---
# def build_map_from_tree(widget, parent_html_id, id_gen):
#     if widget is None: return {}, None
#     html_id = id_gen.next_id(); key = widget.get_unique_id()
#     node_data = {
#         'html_id': html_id, 'widget_type': type(widget).__name__, 'key': widget.key,
#         'widget_instance': widget, 'props': widget.render_props(), 'parent_html_id': parent_html_id,
#         'children_keys': [child.get_unique_id() for child in widget.get_children()]
#     }
#     rendered_map = {key: node_data}
#     for child in widget.get_children():
#         child_map, _ = build_map_from_tree(child, html_id, id_gen)
#         rendered_map.update(child_map)
#     return rendered_map, html_id

# # ==============================================================================
# # TEST CASES (The test cases themselves do not need to change)
# # ==============================================================================
# # 1. Simple INSERT
# old_tree_1 = Container([], key="root_container"); new_tree_1 = Container([Text("Hello")], key="root_container"); patches = run_test("Simple INSERT", old_tree_1, new_tree_1); assert len(patches) == 1 and patches[0]['action'] == 'INSERT'
# # 2. Simple REMOVE
# old_tree_2 = Container([Text("Hello")], key="root_container"); new_tree_2 = Container([], key="root_container"); patches = run_test("Simple REMOVE", old_tree_2, new_tree_2); assert len(patches) == 1 and patches[0]['action'] == 'REMOVE'
# # 3. Simple UPDATE
# old_tree_3 = Container([Text("Hello", key="A")], key="root_container"); new_tree_3 = Container([Text("Goodbye", key="A")], key="root_container"); patches = run_test("Simple UPDATE", old_tree_3, new_tree_3); assert len(patches) == 1 and patches[0]['action'] == 'UPDATE'
# # 4. Keyed MOVE (Reorder)
# old_tree_4 = Container([Text("A", key="A"), Text("B", key="B"), Text("C", key="C")], key="root_container"); new_tree_4 = Container([Text("C", key="C"), Text("B", key="B"), Text("A", key="A")], key="root_container"); patches = run_test("Keyed MOVE (Reorder)", old_tree_4, new_tree_4); move_actions = [p['action'] for p in patches]; assert len(patches) == 2 and move_actions.count('MOVE') == 2
# # 5. Mixed Operations
# old_tree_5 = Container([Text("A", key="A"), Text("B", key="B"), Text("C", key="C"), Text("D", key="D")], key="root_container"); new_tree_5 = Container([Text("D", key="D"), Text("E", key="E"), Text("C", key="C"), Text("B", key="B")], key="root_container"); patches = run_test("Mixed Keyed Operations", old_tree_5, new_tree_5); actions = sorted([p['action'] for p in patches]); assert actions == ['INSERT', 'MOVE', 'MOVE', 'REMOVE']
# # 6. Replace Node
# old_tree_6 = Container([Text("I am old", key="child")], key="root_container"); new_tree_6 = Container([Container([], key="child")], key="root_container"); patches = run_test("Replace Node (Different Type, Same Key)", old_tree_6, new_tree_6); actions = sorted([p['action'] for p in patches]); assert actions == ['INSERT', 'REMOVE']

# # ==============================================================================
# # STRESS TEST
# # ==============================================================================
# def run_stress_test(num_elements):
#     print("=" * 60); print(f"STRESS TEST: Diffing a list of {num_elements} elements."); print("=" * 60)
#     old_list = [Text(f"Item {i}", key=i) for i in range(num_elements)]; updated_key = num_elements // 2
#     new_list = [Text(f"Item {i}", key=i) for i in range(num_elements)]; new_list[updated_key] = Text("UPDATED ITEM", key=updated_key)
#     old_tree = Container(old_list, key="root_container"); new_tree = Container(new_list, key="root_container")
#     id_generator = MockIDGenerator(); old_map, _ = build_map_from_tree(old_tree, "root", id_generator)
#     if not CYTHON_ENABLED: print("Skipping stress test as Cython module is not available."); return
#     start_cy = time.perf_counter(); patches_cy = fast_diff.fast_diff(old_map, new_tree, "root", MockIDGenerator()); end_cy = time.perf_counter()
#     print(f"🚀 Cython (UPDATE) took {end_cy - start_cy:.6f} seconds"); print(f"   - Generated {len(patches_cy)} patches."); assert len(patches_cy) == 1; assert patches_cy[0]['action'] == 'UPDATE'
#     new_list_reordered = list(new_list); item_to_move = new_list_reordered.pop(1); new_list_reordered.insert(-2, item_to_move)
#     new_tree_reordered = Container(new_list_reordered, key="root_container")
#     start_cy_move = time.perf_counter(); patches_cy_move = fast_diff.fast_diff(old_map, new_tree_reordered, "root", MockIDGenerator()); end_cy_move = time.perf_counter()
#     print(f"🚀 Cython (REORDER) took {end_cy_move - start_cy_move:.6f} seconds"); print(f"   - Generated {len(patches_cy_move)} patches."); actions = sorted([p['action'] for p in patches_cy_move]); assert actions == ['MOVE', 'UPDATE']

# if __name__ == "__main__":
#     if CYTHON_ENABLED:
#         run_stress_test(10000)
#         print("\n✅ All tests completed.")
import pytest
import time

from pythra.base_widgets import Container, Text
from pythra.fast_diff_engine import DiffEngine
from pythra.fast_diff import fast_diff

# Helper to build the 'previous_map' for tests
class MockIDGenerator:
    def __init__(self):
        self._count = 0
    def next_id(self):
        self._count += 1
        return f"mock_id_{self._count}"


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


def test_diff_engine_matches_fast_diff():
    """
    Ensure DiffEngine.diff produces the same patches as fast_diff.fast_diff
    for a simple update scenario.
    """
    # Prepare a base tree and updated tree
    base_tree = Container([Text("A", key="A"), Text("B", key="B")], key="root")
    updated_tree = Container([Text("A", key="A"), Text("B modified", key="B")], key="root")

    # Build old_map
    id_gen = MockIDGenerator()
    old_map, root_id = build_map_from_tree(base_tree, "root_parent", id_gen)

    # Run direct fast_diff
    fd_id_gen = MockIDGenerator()
    direct_patches = fast_diff(old_map, updated_tree, root_id, fd_id_gen)

    # Run via DiffEngine
    engine = DiffEngine()
    de_id_gen = MockIDGenerator()
    engine_patches = engine.diff(old_map, updated_tree, root_id, de_id_gen)

    # Normalize and compare actions
    actions_direct = [p['action'] for p in direct_patches]
    actions_engine = [p['action'] for p in engine_patches]
    assert actions_engine == actions_direct


def test_caching_prevents_rebuild():
    """
    Verify that DiffEngine caches the old_root between calls when old_map id remains unchanged.
    """
    # Create a simple tree
    tree = Container([Text("X", key="X")], key="root")

    id_gen = MockIDGenerator()
    old_map, root_id = build_map_from_tree(tree, "root_parent", id_gen)

    engine = DiffEngine()
    # First diff: builds and caches _cached_old_root
    engine.diff(old_map, tree, root_id, MockIDGenerator())
    first_cached = engine._cached_old_root
    assert first_cached is not None

    # Mutate new_widget only (update prop)
    updated_tree = Container([Text("Y", key="X")], key="root")
    engine.diff(old_map, updated_tree, root_id, MockIDGenerator())
    second_cached = engine._cached_old_root

    # The cached old_root object should be reused, not rebuilt
    assert second_cached is first_cached


def test_performance_gain_on_repeated_calls(benchmark):
    """
    Benchmark that repeated calls with the same old_map skip rebuild.
    """
    # Build a larger list to illustrate the effect
    items = [Text(f"Item {i}", key=i) for i in range(1000)]
    tree = Container(items, key="root")

    id_gen = MockIDGenerator()
    old_map, root_id = build_map_from_tree(tree, "root_parent", id_gen)

    engine = DiffEngine()
    
    # First call (incurs full build)
    engine.diff(old_map, tree, root_id, MockIDGenerator())

    # Benchmark subsequent calls (should be faster)
    def repeated_diff():
        engine.diff(old_map, tree, root_id, MockIDGenerator())

    # Use pytest-benchmark to measure
    benchmark(repeated_diff)
