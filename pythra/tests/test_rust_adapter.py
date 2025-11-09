"""Unit tests for RustReconcilerAdapter to verify behavior matches Python reconciler."""

import unittest
from unittest.mock import MagicMock, patch
from ..reconciler import Reconciler, ReconciliationResult, Patch
from ..base import Widget
from ..rust_reconciler_adapter import RustReconcilerAdapter

class TestWidget(Widget):
    def __init__(self, key=None, props=None, children=None):
        super().__init__()
        self._key = key
        self._props = props or {}
        self._children = children or []
    
    def get_unique_id(self):
        return self._key
    
    def render_props(self):
        return self._props
    
    def get_children(self):
        return self._children

class TestRustReconcilerAdapter(unittest.TestCase):
    def setUp(self):
        self.reconciler = Reconciler()
        self.adapter = RustReconcilerAdapter(self.reconciler)
        
        # Mock the Rust module for controlled testing
        self.rust_mock = MagicMock()
        self.adapter._rust_mod = self.rust_mock
    
    def test_fallback_when_rust_not_available(self):
        """Should use Python reconciler when Rust module not available."""
        self.adapter._rust_mod = None
        widget = TestWidget(key="root")
        previous_map = {}
        
        with patch.object(self.reconciler, 'reconcile') as mock_reconcile:
            self.adapter.reconcile(previous_map, widget, "parent")
            mock_reconcile.assert_called_once()
    
    def test_simple_insert(self):
        """Should correctly translate Rust INSERT patch to framework format."""
        widget = TestWidget(key="root", props={"color": "blue"})
        previous_map = {}
        
        # Mock Rust reconciler to return an INSERT patch
        mock_patch = MagicMock()
        mock_patch.action = "INSERT"
        mock_patch.target_id = "root"
        mock_patch.data = {"before_id": None}
        self.rust_mock.reconcile.return_value = [mock_patch]
        
        # Mock HTML stub generation
        self.reconciler._generate_html_stub = MagicMock(return_value="<div>stub</div>")
        self.reconciler.id_generator.next_id = MagicMock(return_value="html_1")
        
        result = self.adapter.reconcile(previous_map, widget, "parent")
        
        self.assertEqual(len(result.patches), 1)
        patch = result.patches[0]
        self.assertEqual(patch.action, "INSERT")
        self.assertEqual(patch.html_id, "html_1")
        self.assertEqual(patch.data["html"], "<div>stub</div>")
        self.assertEqual(patch.data["props"], {"color": "blue"})
    
    def test_move_children(self):
        """Should correctly handle the LIS test case with moves."""
        # Create initial tree: root -> [a, b, c, d, e]
        old_children = [
            TestWidget(key=k) for k in ["a", "b", "c", "d", "e"]
        ]
        old_root = TestWidget(key="root", children=old_children)
        
        # Create new tree: root -> [a, d, c, f, b]
        new_children = [
            TestWidget(key=k) for k in ["a", "d", "c", "f", "b"]
        ]
        new_root = TestWidget(key="root", children=new_children)
        
        # Setup previous map with html IDs
        previous_map = {
            "root": {"html_id": "root_1", "widget_type": "TestWidget", "children_keys": ["a","b","c","d","e"]},
            "a": {"html_id": "a_1", "widget_type": "TestWidget"},
            "b": {"html_id": "b_1", "widget_type": "TestWidget"},
            "c": {"html_id": "c_1", "widget_type": "TestWidget"},
            "d": {"html_id": "d_1", "widget_type": "TestWidget"},
            "e": {"html_id": "e_1", "widget_type": "TestWidget"},
        }
        
        # Mock Rust reconciler to return expected patches
        mock_patches = [
            MagicMock(action="REMOVE", target_id="e", data=None),
            MagicMock(action="INSERT", target_id="f", data={"before_id": "b"}),
            MagicMock(action="MOVE", target_id="c", data={"before_id": "f"}),
            MagicMock(action="MOVE", target_id="d", data={"before_id": "c"}),
        ]
        self.rust_mock.reconcile.return_value = mock_patches
        
        # Mock HTML generation for new node
        self.reconciler._generate_html_stub = MagicMock(return_value="<div>f</div>")
        self.reconciler.id_generator.next_id = MagicMock(return_value="f_1")
        
        result = self.adapter.reconcile(previous_map, new_root, "parent")
        
        # Verify patches
        # framework Patch uses html_id as identifier
        actions = [(p.action, p.html_id) for p in result.patches]
        expected = [
            ("REMOVE", "e_1"),
            ("INSERT", "f_1"),
            ("MOVE", "c_1"),
            ("MOVE", "d_1")
        ]
        self.assertEqual(actions, expected)

        # Verify move patch details
        moves = [p for p in result.patches if p.action == "MOVE"]
        self.assertEqual(moves[0].data["before_id"], "f_1")  # c before f
        self.assertEqual(moves[1].data["before_id"], "c_1")  # d before c

    def test_update_props(self):
        """Should correctly handle property updates."""
        widget = TestWidget(key="root", props={"color": "red"})
        previous_map = {
            "root": {
                "html_id": "root_1",
                "widget_type": "TestWidget",
                "props": {"color": "blue"}
            }
        }
        
        mock_patch = MagicMock()
        mock_patch.action = "UPDATE"
        mock_patch.target_id = "root"
        mock_patch.data = {}  # Let framework compute diff
        self.rust_mock.reconcile.return_value = [mock_patch]
        
        result = self.adapter.reconcile(previous_map, widget, "parent")
        
        self.assertEqual(len(result.patches), 1)
        patch = result.patches[0]
        self.assertEqual(patch.action, "UPDATE")
        self.assertEqual(patch.html_id, "root_1")
        self.assertEqual(patch.data, {"color": "red"})

if __name__ == '__main__':
    unittest.main()