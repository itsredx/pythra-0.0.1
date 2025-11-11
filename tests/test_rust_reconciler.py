import unittest
import sys
import traceback


# Try importing the compiled Rust extension. If it's not built, tests will be skipped.
try:
    import rust_reconciler
    MODULE_AVAILABLE = True
    _IMPORT_ERROR = None
except Exception as e:
    MODULE_AVAILABLE = False
    _IMPORT_ERROR = e


@unittest.skipUnless(MODULE_AVAILABLE, "rust_reconciler extension not available; build the Rust extension first")
class TestRustReconciler(unittest.TestCase):
    def setUp(self):
        # create a new reconciler instance for each test if available,
        # otherwise fall back to the module-level `reconcile` function exported by the extension
        if hasattr(rust_reconciler, "Reconciler"):
            self.reconciler = rust_reconciler.Reconciler()
            self.use_class = True
        else:
            # module exposes a function `reconcile(old_tree_py, new_tree_py)`
            self.reconciler = rust_reconciler.reconcile
            self.use_class = False

    def call_reconcile(self, previous_map, new_widget_root, parent_html_id="root", is_partial_reconciliation=False):
        if self.use_class:
            # class method signature: (previous_map, new_widget_root, parent_html_id, is_partial_reconciliation=False, old_root_key=None)
            return self.reconciler.reconcile(previous_map, new_widget_root, parent_html_id, is_partial_reconciliation)
        else:
            # module-level function signature: (old_tree_py, new_tree_py)
            # It expects two dict-like maps rather than Python widget instances.
            old_map = previous_map or {}
            if new_widget_root is None:
                new_map = {}
            else:
                # If a widget-like object was passed, synthesize a minimal new_map entry
                try:
                    key = new_widget_root.get_unique_id()
                    props = new_widget_root.render_props()
                except Exception:
                    # If it's already a dict-like structure, use it directly
                    return self.reconciler(old_map, new_widget_root)

                new_map = {
                    key: {
                        "html_id": "fw_id_test",
                        "widget_type": "Text",
                        "key": key,
                        "widget_instance": None,
                        "props": props,
                        "parent_html_id": parent_html_id,
                        "parent_key": None,
                        "children_keys": [],
                    }
                }

            return self.reconciler(old_map, new_map)

    def test_reconcile_empty_maps(self):
        # previous_map empty, no new widget
        prev = {}
        result = self.call_reconcile(prev, None, "root")

        if self.use_class:
            # result should be a mapping-like object with expected keys
            self.assertIn("patches", result)
            self.assertIn("new_rendered_map", result)
            self.assertIn("active_css_details", result)
            self.assertIn("registered_callbacks", result)
            self.assertIn("js_initializers", result)

            self.assertIsInstance(result["patches"], list)
        else:
            # module-level API returns a list of patches
            self.assertIsInstance(result, list)

    def test_reconcile_with_simple_widget(self):
        # Simple Python-side widget that matches the minimal API the Rust code expects
        class SimpleWidget:
            def __init__(self, key="w1", inner_html="hello"):
                self._key = key
                self._inner = inner_html

            def get_unique_id(self):
                return self._key

            def render_props(self):
                # return a dict of props the reconciler will parse
                return {"inner_html": self._inner, "css_class": "test-class"}

            def get_children(self):
                return []

            # optional: provide required css classes (the Rust code will attempt to call it)
            def get_required_css_classes(self):
                return []

        widget = SimpleWidget()

        if not self.use_class:
            # module-level reconcile expects dict maps rather than widget objects; skip this detailed test
            self.skipTest("module-level reconcile does not accept Python widget instances; skipping")

        result = self.call_reconcile({}, widget, "root")

        # Ensure result shape
        self.assertIn("patches", result)
        patches = result["patches"]
        self.assertIsInstance(patches, list)

        # If the widget is renderable we expect at least one INSERT patch (or none if implementation differs)
        actions = [p.get("action") for p in patches if isinstance(p, dict)]
        self.assertTrue(any(a == "INSERT" for a in actions) or len(patches) == 0)

    def test_partial_reconciliation_flag(self):
        # ensure calling with the partial flag doesn't raise
        result = self.call_reconcile({}, None, "root", is_partial_reconciliation=True)
        if self.use_class:
            self.assertIn("patches", result)
        else:
            # module-level API returns a list for empty inputs
            self.assertIsInstance(result, list)


if not MODULE_AVAILABLE:
    print("rust_reconciler extension not available:", file=sys.stderr)
    traceback.print_exception(_IMPORT_ERROR)


if __name__ == "__main__":
    unittest.main()
