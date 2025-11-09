"""
Adapter to use the Rust-based reconciler as an optional performance boost.
Preserves the PyThra framework's widget/patch API while using Rust for the core diffing.
"""
import time

from typing import Dict, List, Optional, Union, Any
from dataclasses import dataclass, field
import importlib.util

from .base import Widget
from .reconciler import Reconciler, ReconciliationResult, Patch

class RustReconcilerAdapter:
    def __init__(self, reconciler: Reconciler):
        """Initialize with reference to main Reconciler for helper methods."""
        self.reconciler = reconciler
        self._rust_mod = None
        try:
            # Try a normal import of the rust module. Wrap in broad Exception handler
            # because a faulty installed package may raise inside its package __init__.
            self._rust_mod = importlib.import_module('rust_reconciler')
            print("✨ Rust reconciler loaded for performance boost")
        except Exception as e:
            # If any error occurs during import (including NameError inside package __init__),
            # fall back to Python reconciler and print a helpful message.
            print("⚠️ Rust reconciler import failed; falling back to pure Python. Error:", e)
            self._rust_mod = None

    def is_available(self) -> bool:
        """Check if the Rust reconciler is available."""
        return self._rust_mod is not None

    def _build_old_tree_map(self, previous_map: Dict) -> Dict:
        """Convert framework's previous_map to Rust-compatible old_tree format."""
        old_tree = {}
        for key, data in previous_map.items():
            # Only include serializable data the Rust reconciler needs
            old_tree[key] = {
                "key": key,
                "type": data.get("widget_type"),
                "props": data.get("props", {}),
                "children": data.get("children_keys", []),
            }
        return old_tree

    def _build_new_tree_map(self, root_widget: Widget) -> tuple[Dict, Dict[str, Widget]]:
        """Convert Widget tree to Rust-compatible format and build lookup map."""
        new_tree = {}
        widget_lookup = {}  # For generating HTML stubs later

        def walk(widget: Optional[Widget]) -> None:
            if widget is None:
                return
            key = widget.get_unique_id()
            props = widget.render_props()
            children = [c.get_unique_id() for c in widget.get_children()]
            
            new_tree[key] = {
                "key": key,
                "type": type(widget).__name__,
                "props": props,
                "children": children
            }
            widget_lookup[key] = widget
            for child in widget.get_children():
                walk(child)

        walk(root_widget)
        # print(f'New tree: {new_tree}, \nWidget lookup: {widget_lookup}')
        return new_tree, widget_lookup

    def reconcile(
        self,
        previous_map: Dict,
        new_widget_root: Optional[Widget],
        parent_html_id: str,
        old_root_key: Optional[Union[str, Any]] = None,
        is_partial_reconciliation: bool = False
    ) -> ReconciliationResult:
        """
        Use Rust reconciler for diffing but preserve PyThra's patch format and HTML generation.
        Falls back to Python implementation if Rust module not available.
        """
        if not self.is_available() or new_widget_root is None:
            # Fallback to pure Python if Rust not available or for edge cases
            return self.reconciler.reconcile(
                previous_map, new_widget_root, parent_html_id,
                old_root_key, is_partial_reconciliation
            )

        # Convert to Rust-compatible formats
        t0 = time.perf_counter()
        old_tree = self._build_old_tree_map(previous_map)
        t1 = time.perf_counter()
        new_tree, widget_lookup = self._build_new_tree_map(new_widget_root)
        t2 = time.perf_counter()

        # Call Rust reconciler
        rust_call_start = time.perf_counter()
        rust_patches = self._rust_mod.reconcile(old_tree, new_tree)
        rust_call_end = time.perf_counter()


        # Initialize result with framework's format
        result = ReconciliationResult()
        new_html_ids = {}  # Track html_ids for new nodes

        # Copy existing entries to new_rendered_map (for html_id lookups)
        for k, d in previous_map.items():
            result.new_rendered_map[k] = dict(d)

        # Convert Rust patches to framework Patch objects
        for rust_patch in rust_patches:
            action, key, patch_data = (
                rust_patch.action,
                rust_patch.target_id,
                None if rust_patch.data is None else dict(rust_patch.data)
            )

            if action == "REMOVE":
                # Simple removal - just map key to html_id
                old_html = previous_map[key]["html_id"]
                result.patches.append(Patch(
                    action="REMOVE",
                    html_id=old_html,
                    data={}
                ))
                result.new_rendered_map.pop(key, None)

            elif action == "INSERT":
                # Generate HTML stub and track new node
                widget = widget_lookup[key]
                new_html_id = self.reconciler.id_generator.next_id()
                props = widget.render_props()
                
                # Use framework's HTML generation
                stub = self.reconciler._generate_html_stub(widget, new_html_id, props)
                
                # Map before_id from widget key to html_id
                before_key = patch_data.get("before_id") if patch_data else None
                before_html = (
                    previous_map.get(before_key, {}).get("html_id")
                    if before_key else None
                )

                # Create framework-style INSERT patch
                result.patches.append(Patch(
                    action="INSERT",
                    html_id=new_html_id,
                    data={
                        "html": stub,
                        "parent_html_id": parent_html_id,
                        "props": props,
                        "before_id": before_html
                    }
                ))

                # Track in new_rendered_map for children
                result.new_rendered_map[key] = {
                    "html_id": new_html_id,
                    "widget_type": type(widget).__name__,
                    "key": getattr(widget, 'key', None),
                    "widget_instance": widget,
                    "props": props,
                    "parent_html_id": parent_html_id,
                    "parent_key": None,  # Parent relation tracked elsewhere
                    "children_keys": [c.get_unique_id() for c in widget.get_children()],
                }
                new_html_ids[key] = new_html_id

            elif action == "MOVE":
                # Map widget keys to html_ids for move operation
                html_id = (
                    previous_map.get(key, {}).get("html_id") or
                    new_html_ids.get(key)
                )
                before_key = patch_data.get("before_id") if patch_data else None
                before_html = (
                    previous_map.get(before_key, {}).get("html_id") or
                    new_html_ids.get(before_key)
                )
                
                result.patches.append(Patch(
                    action="MOVE",
                    html_id=html_id,
                    data={"before_id": before_html} if before_html else None
                ))

            elif action == "UPDATE":
                # Property updates - compute diffs using framework helper
                html_id = previous_map[key]["html_id"]
                widget = widget_lookup[key]
                new_props = widget.render_props()
                old_props = previous_map[key].get("props", {})
                
                # Use framework's prop diffing
                prop_changes = self.reconciler._diff_props(old_props, new_props)
                if prop_changes:
                    result.patches.append(Patch(
                        action="UPDATE",
                        html_id=html_id,
                        data=prop_changes
                    ))
                    if key in result.new_rendered_map:
                        result.new_rendered_map[key]["props"] = new_props

        t_done = time.perf_counter()

        # Record and print timings for diagnostics
        timings = {
            "build_old_tree_ms": (t1 - t0) * 1000.0,
            "build_new_tree_ms": (t2 - t1) * 1000.0,
            "rust_call_ms": (rust_call_end - rust_call_start) * 1000.0,
            "translate_ms": (t_done - rust_call_end) * 1000.0,
            "total_ms": (t_done - t0) * 1000.0,
        }
        print("[rust_adapter timings] build_old={:.3f}ms build_new={:.3f}ms rust={:.3f}ms translate={:.3f}ms total={:.3f}ms".format(
            timings["build_old_tree_ms"], timings["build_new_tree_ms"],
            timings["rust_call_ms"], timings["translate_ms"], timings["total_ms"]
        ))
        # Attach timings into result for programmatic inspection
        result.new_rendered_map["__rust_adapter_timing__"] = timings
        # Handle framework-specific updates (lifecycle, CSS, callbacks)
        self.reconciler._collect_details(new_widget_root, new_widget_root.render_props(), result)

        # print(f'Result: {result}')

        return result