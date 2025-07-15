import pytest
import time

from pythra.base_widgets import Container, Text
from pythra.fast_diff_engine import DiffEngine
from pythra.fast_diff import fast_diff

# Skip performance test if pytest-benchmark is not available
pytest.importorskip("pytest_benchmark")

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
