#!/usr/bin/env python3
"""
Quick test to verify state update reconciliation works with Rust reconciler
"""
import sys
from pathlib import Path

# Add pythra to path
pythra_root = Path(__file__).parent
sys.path.insert(0, str(pythra_root))

from pythra.core import Framework
from pythra.base import Widget, Key

# Create a simple test widget
class TestWidget(Widget):
    def __init__(self, key_val, style_class="test-class"):
        super().__init__()
        self.key = Key(key_val)
        self._style_class = style_class
    
    def get_unique_id(self):
        return self.key
    
    def render_props(self):
        return {
            "css_class": self._style_class,
            "data": f"Widget {self.key.value}"
        }
    
    def get_children(self):
        return []

# Use Framework's reconciler (which is RustReconcilerAdapter)
framework = Framework.instance()
reconciler = framework.reconciler

print(f"DEBUG: Reconciler type: {type(reconciler).__name__}")
print(f"DEBUG: Has context_maps attr: {hasattr(reconciler, 'context_maps')}")

# Build initial map using framework's reconciler
root = TestWidget("root_widget")
initial_result = reconciler.reconcile(
    previous_map={},
    new_widget_root=root,
    parent_html_id="root-container"
)

print(f"✓ Initial reconciliation: {len(initial_result.new_rendered_map)} widgets")
print(f"  new_rendered_map keys: {list(initial_result.new_rendered_map.keys())}")

# Now simulate what _perform_initial_render does
print("\n--- Simulating _perform_initial_render context_maps update ---")
try:
    reconciler.context_maps["main"] = initial_result.new_rendered_map
except (AttributeError, TypeError):
    if not hasattr(reconciler, "context_maps"):
        setattr(reconciler, "context_maps", {})
    reconciler.context_maps["main"] = initial_result.new_rendered_map

print(f"✓ Context_maps attached: {hasattr(reconciler, 'context_maps')}")
context_map = reconciler.get_map_for_context("main")
print(f"  get_map_for_context('main') returned {len(context_map)} entries")
print(f"  Keys: {list(context_map.keys())}")

if context_map:
    print("\n✓ SUCCESS: Context map is populated and accessible for state updates!")
else:
    print("\n✗ FAILED: Context map is empty")

