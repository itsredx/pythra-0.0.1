# pythra/tests/test_reconciler.py
import unittest
import html
from typing import Any, Dict, List, Optional, Tuple, Union, Set, Callable, Literal

# --- Definitions for Patch and NodeData ---
PatchAction = Literal['INSERT', 'REMOVE', 'UPDATE', 'MOVE']
class Patch:
    def __init__(self, action: PatchAction, html_id: str, data: Dict[str, Any]):
        self.action = action; self.html_id = html_id; self.data = data
    def __eq__(self, other): return isinstance(other, Patch) and self.action == other.action and self.html_id == other.html_id and self.data == other.data
    def __repr__(self): return f"Patch(action='{self.action}', html_id='{self.html_id}', data={self.data})"
NodeData = Dict[str, Any]

class Key:
    def __init__(self, value: Any):
        original_value_for_error_msg = value
        try: hash(value)
        except TypeError:
            def _mvh(i):
                if isinstance(i, list): return tuple(_mvh(x) for x in i)
                if isinstance(i, dict): return tuple(sorted((k, _mvh(v)) for k,v in i.items()))
                if isinstance(i, set): return tuple(sorted(_mvh(x) for x in i))
                try: hash(i); return i
                except TypeError: return str(i)
            value = _mvh(value)
        self.value = value
        try: hash(self.value)
        # Using original_value_for_error_msg for clearer error if self.value (processed) still fails
        except TypeError: raise TypeError(f"Key value {original_value_for_error_msg!r} (type: {type(original_value_for_error_msg)}) could not be made hashable.")
    def __eq__(self, o): return isinstance(o, Key) and self.value == o.value
    def __hash__(self): return hash((self.__class__, self.value))
    def __repr__(self): return f"Key({self.value!r})"

class IDGenerator:
    def __init__(self): self._count = 0
    def next_id(self) -> str: self._count += 1; return f"fw_id_{self._count}"

mock_widget_id_generator = IDGenerator() # Global for MockWidget default IDs

class MockWidget:
    def __init__(self, key_val=None, children: Optional[List['MockWidget']] = None, **props):
        self.props = props
        self._key = Key(key_val) if key_val is not None else None
        self._internal_id = mock_widget_id_generator.next_id()
        self._children = children if children is not None else []
    def render_props(self) -> Dict[str, Any]: return self.props.copy()
    def get_unique_id(self) -> Union[Key, str]: return self._key if self._key is not None else self._internal_id
    def get_children(self) -> List['MockWidget']: return self._children
    def set_children(self, children: List['MockWidget']): self._children = children
    def __repr__(self): return f"{type(self).__name__}(uid={self.get_unique_id()!r}, props={self.props}, children={len(self._children)})"

class MockTextWidget(MockWidget): pass
class MockContainerWidget(MockWidget): pass
class MockPaddingWidget(MockWidget): pass
class MockImageWidget(MockWidget): pass
class MockIconWidget(MockWidget): pass


# --- TestableReconciler class ---
class TestableReconciler:
    def __init__(self):
        self.id_generator = IDGenerator()
        self.active_css_details: Dict[str, Tuple[Callable, Tuple]] = {}
        self.mock_child_diff_calls = []
        self.context_maps: Dict[str, Dict[Union[Key, str], NodeData]] = {}

    def get_map_for_context(self, context_key: str) -> Dict[Union[Key, str], NodeData]:
        return self.context_maps.setdefault(context_key, {})

    def clear_context(self, context_key: str):
         if context_key in self.context_maps: del self.context_maps[context_key]

    def _get_widget_render_tag(self, widget: MockWidget) -> str:
        name = type(widget).__name__.replace("Mock","").replace("Widget","")
        tag_map = {'Text':'p', 'Image':'img', 'Container':'div', 'Padding':'div', 'Icon':'i'}
        return tag_map.get(name, 'div')

    def _generate_html_stub(self, widget: MockWidget, html_id: str, props: Dict) -> str:
        tag = self._get_widget_render_tag(widget)
        name = type(widget).__name__.replace("Mock","").replace("Widget","")
        content = ""
        attrs = ""
        css_class_val = props.get("css_class","")

        if name == 'Text': content = html.escape(str(props.get('data','')))
        elif name == 'Image': attrs += f' src=\"{html.escape(str(props.get("src","")), quote=True)}\" alt=\"\"'
        elif name == 'Icon':
            if props.get('render_type') == 'img':
                attrs += f' src=\"{html.escape(str(props.get("custom_icon_src","")), quote=True)}\" alt=\"\"'
                tag = 'img'
            else:
                css_class_val = f"fa fa-{props.get('icon_name', 'question-circle')} {css_class_val}".strip()

        if tag in ['img']: return f'<{tag} id="{html_id}" class="{css_class_val}"{attrs}>'
        return f'<{tag} id="{html_id}" class="{css_class_val}"{attrs}>{content}</{tag}>'

    def _diff_props(self, old: Dict, new: Dict) -> Optional[Dict]:
        c = {}; keys = set(old.keys())|set(new.keys())
        for k in keys:
            ov, nv = old.get(k), new.get(k)
            if ov != nv: c[k] = nv
        return c if c else None

    def _insert_node_recursive(self, new_w: MockWidget, p_id: str, ps: List[Patch], n_map: Dict, prev_map: Dict, layout_override=None, before_id=None):
        if new_w is None: return
        uid = new_w.get_unique_id(); html_id = self.id_generator.next_id(); props = new_w.render_props()
        if layout_override: props['layout_override'] = layout_override

        current_props_copy = props.copy()
        n_map[uid] = {'html_id':html_id, 'widget_type':type(new_w).__name__, 'key':new_w._key,
                      'internal_id':new_w._internal_id, 'props':current_props_copy,
                      'parent_html_id':p_id, 'children_keys':[c.get_unique_id() for c in new_w.get_children()]}
        ps.append(Patch('INSERT', html_id, {'html':self._generate_html_stub(new_w,html_id,props),
                                           'parent_html_id':p_id, 'props':current_props_copy, 'before_id':before_id}))
        # Children of a newly inserted node are also new.
        self._diff_children_recursive([],new_w.get_children(),html_id,ps,n_map,prev_map)

    def _diff_node_recursive(self, old_key: Optional[Union[Key,str]], new_w: Optional[MockWidget], p_id: str, ps: List[Patch], n_map: Dict, prev_map: Dict):
        layout_override=None; actual_new_w = new_w; w_type = type(new_w).__name__ if new_w else None
        is_passthrough_layout_widget_type = w_type in ["MockPaddingWidget"]
        if is_passthrough_layout_widget_type and new_w:
            layout_override = new_w.render_props(); children = new_w.get_children()
            actual_new_w = children[0] if children else None
            if actual_new_w is None: return

        uid = actual_new_w.get_unique_id() if actual_new_w else None
        old_data = prev_map.get(old_key) if old_key else None

        if actual_new_w is None: return
        if old_data is None: self._insert_node_recursive(actual_new_w, p_id, ps, n_map, prev_map, layout_override); return

        old_html_id=old_data['html_id']; old_type=old_data['widget_type']; new_type=type(actual_new_w).__name__
        old_k=old_data.get('key'); new_k=actual_new_w._key

        replace = (new_k is not None and old_k != new_k) or \
                  (old_k is not None and new_k is None) or \
                  (new_k is None and old_k is None and old_type != new_type) or \
                  (new_k is not None and old_k is not None and new_k == old_k and old_type != new_type)
        if replace: self._insert_node_recursive(actual_new_w, p_id, ps, n_map, prev_map, layout_override); return

        current_props = actual_new_w.render_props().copy()
        if layout_override: current_props['layout_override'] = layout_override

        prop_c = self._diff_props(old_data['props'], current_props)
        patch_data_update = {'props': prop_c if prop_c else {}} # Ensure props is a dict
        if layout_override: patch_data_update['layout_override'] = layout_override

        if prop_c: ps.append(Patch('UPDATE', old_html_id, patch_data_update))

        n_map[uid] = {'html_id':old_html_id, 'widget_type':new_type, 'key':new_k,
                      'internal_id':actual_new_w._internal_id, 'props':current_props,
                      'parent_html_id':p_id, 'children_keys':[c.get_unique_id() for c in actual_new_w.get_children()]}
        self._diff_children_recursive(old_data.get('children_keys',[]), actual_new_w.get_children(), old_html_id, ps, n_map, prev_map)

    def _diff_children_recursive(self, old_children_keys: List[Union[Key, str]], new_children_widgets: List[MockWidget], parent_html_id: str, patches: List[Patch], new_rendered_map: Dict, previous_map_for_context: Dict):
        self.mock_child_diff_calls.append({"p_id": parent_html_id, "old_len": len(old_children_keys), "new_len": len(new_children_widgets)})
        if not old_children_keys and not new_children_widgets: return
        old_key_to_index: Dict[Union[Key, str], int] = {key: i for i, key in enumerate(old_children_keys)}

        new_children_info: List[Dict[str, Any]] = []
        last_matched_old_idx = -1

        for i, new_widget in enumerate(new_children_widgets):
            new_key = new_widget.get_unique_id(); old_idx = old_key_to_index.get(new_key)
            node_info = {'key': new_key, 'widget': new_widget, 'new_idx': i, 'old_idx': old_idx}
            if old_idx is not None: # Keyed node found in old children
                old_data_for_key = previous_map_for_context.get(new_key)
                if old_data_for_key and old_data_for_key.get('parent_html_id') == parent_html_id:
                    self._diff_node_recursive(new_key, new_widget, parent_html_id, patches, new_rendered_map, previous_map_for_context)
                    if new_key in new_rendered_map: node_info['html_id'] = new_rendered_map[new_key]['html_id']
                    if old_idx < last_matched_old_idx: node_info['moved'] = True
                    else: last_matched_old_idx = old_idx
                else: node_info['is_new'] = True
            else: node_info['is_new'] = True
            new_children_info.append(node_info)

        next_stable_sibling_html_id = None
        for i in range(len(new_children_widgets) - 1, -1, -1):
            node_info = new_children_info[i]
            new_key = node_info['key']; new_widget = node_info['widget']
            current_html_id_in_map = new_rendered_map.get(new_key, {}).get('html_id')

            if node_info.get('is_new'):
                if new_key not in new_rendered_map:
                    self._diff_node_recursive(None, new_widget, parent_html_id, patches, new_rendered_map, previous_map_for_context)
                current_html_id_in_map = new_rendered_map.get(new_key, {}).get('html_id') # Re-fetch after potential insert
                if current_html_id_in_map:
                    for patch_obj in patches:
                        if patch_obj.action == 'INSERT' and patch_obj.html_id == current_html_id_in_map: # Check existing INSERT patch
                            if patch_obj.data.get('before_id') != next_stable_sibling_html_id: # Update if different
                                patch_obj.data['before_id'] = next_stable_sibling_html_id
                            break
                next_stable_sibling_html_id = current_html_id_in_map
            elif node_info.get('moved'):
                moved_html_id = node_info.get('html_id')
                if moved_html_id: patches.append(Patch('MOVE', moved_html_id, {'parent_html_id': parent_html_id, 'before_id': next_stable_sibling_html_id}))
                next_stable_sibling_html_id = moved_html_id
            else: # Stable node
                next_stable_sibling_html_id = node_info.get('html_id') # This should be already in new_rendered_map

    def reconcile_subtree(self, current_subtree_root: Optional[MockWidget], parent_html_id: str, context_key: str = 'main') -> List[Patch]:
        patches: List[Patch] = []
        new_rendered_map: Dict[Union[Key, str], NodeData] = {}
        previous_map_for_context = self.get_map_for_context(context_key).copy()

        if context_key == 'main': self.active_css_details.clear()

        old_root_key = None
        if current_subtree_root: # If there's a new root
            new_root_uid = current_subtree_root.get_unique_id()
            # Case 1: New root's key/uid was the old root's key/uid
            if new_root_uid in previous_map_for_context and \
               previous_map_for_context[new_root_uid].get('parent_html_id') == parent_html_id:
                old_root_key = new_root_uid
        elif previous_map_for_context: # No new root, but there was an old tree for this parent_html_id
            # Find any old node that was a direct child of parent_html_id; this is a heuristic for single root node.
            for key, data in previous_map_for_context.items():
                if data.get('parent_html_id') == parent_html_id:
                    old_root_key = key
                    break

        self._diff_node_recursive(
            old_root_key, current_subtree_root, parent_html_id,
            patches, new_rendered_map, previous_map_for_context
        )

        old_keys_in_context_for_parent = {
            k for k, v in previous_map_for_context.items()
            if v.get('parent_html_id') == parent_html_id or k == old_root_key
        }
        new_keys_processed_for_parent = { # Not used in the corrected logic below
            k for k, v in new_rendered_map.items()
            # if v.get('parent_html_id') == parent_html_id or \ # This was too restrictive
            #    (current_subtree_root and k == current_subtree_root.get_unique_id())
        }

        # Corrected removal logic:
        # If a key was in the old context map and not in the new one (built from current_subtree_root), it's removed.
        removed_keys = set(previous_map_for_context.keys()) - set(new_rendered_map.keys())

        for removed_key in removed_keys:
            removed_data = previous_map_for_context[removed_key]
            patches.append(Patch(action='REMOVE', html_id=removed_data['html_id'], data={}))

        self.context_maps[context_key] = new_rendered_map
        return patches

# --- Test Classes ---
class TestKey(unittest.TestCase):
    def test_creation(self): self.assertEqual(Key("k").value, "k")
class TestIDGenerator(unittest.TestCase):
    def test_starts_at_1(self): global mock_widget_id_generator; mock_widget_id_generator=IDGenerator(); self.assertEqual(IDGenerator().next_id(), "fw_id_1")
class TestDiffProps(unittest.TestCase):
    def test_no_changes(self): self.assertIsNone(TestableReconciler()._diff_props({},{}))
class TestGenerateHtmlStub(unittest.TestCase):
    def test_text(self): self.assertIn("Hello", TestableReconciler()._generate_html_stub(MockTextWidget(data="Hello"),"id1",{"data":"Hello"}))
class TestNodeReconciliation(unittest.TestCase):
    def setUp(self): global mock_widget_id_generator; mock_widget_id_generator=IDGenerator(); self.r = TestableReconciler(); self.p=[]; self.nm={}; self.om={}
    def test_insert_new(self): w=MockTextWidget(data="H"); self.r._diff_node_recursive(None,w,"r",self.p,self.nm,self.om); self.assertEqual(len(self.p),1)
class TestChildReconciliation(unittest.TestCase):
    def setUp(self): global mock_widget_id_generator; mock_widget_id_generator=IDGenerator(); self.r = TestableReconciler(); self.p=[]; self.nm={}; self.om={}
    def _setup_prev(self, ws, p_id):
        k=[]
        for w in ws:
            uid=w.get_unique_id()
            h_id=f"prev_{uid.value}" if isinstance(uid,Key) else f"prev_{uid}"
            k.append(uid)
            self.om[uid]={
                'html_id':h_id,
                'widget_type':type(w).__name__,
                'key':w._key,
                'props':w.render_props(),
                'parent_html_id':p_id,
                'children_keys':[] # Simplified for this helper
            }
        return k
    def test_add_children(self): new_c=[MockTextWidget(key_val="k1",data="A")];self.r._diff_children_recursive([],new_c,"p1",self.p,self.nm,self.om);self.assertEqual(len(self.p),1)

class TestReconcileSubtree(unittest.TestCase):
    def setUp(self):
        global mock_widget_id_generator; mock_widget_id_generator = IDGenerator()
        self.reconciler = TestableReconciler()

    def test_initial_render_single_node(self):
        widget = MockTextWidget(data="Initial"); parent_html_id = "app-root"
        patches = self.reconciler.reconcile_subtree(widget, parent_html_id, "main")
        self.assertEqual(len(patches), 1); patch = patches[0]
        self.assertEqual(patch.action, 'INSERT'); self.assertTrue(patch.html_id.startswith("fw_id_"))
        self.assertEqual(patch.data['parent_html_id'], parent_html_id); self.assertIn("Initial", patch.data['html'])
        main_map = self.reconciler.context_maps["main"]
        self.assertIn(widget.get_unique_id(), main_map)
        self.assertEqual(main_map[widget.get_unique_id()]['props']['data'], "Initial")

    def test_no_change_reconciliation(self):
        widget = MockTextWidget(data="NoChange"); parent_html_id = "app-root"
        self.reconciler.reconcile_subtree(widget, parent_html_id, "main")
        patches = self.reconciler.reconcile_subtree(widget, parent_html_id, "main")
        self.assertEqual(len(patches), 0, "Expected no patches for identical tree.")

    def test_add_new_root_widget_replaces_old(self): # Renamed for clarity
        parent_html_id = "app-root"; old_widget = MockTextWidget(key_val="old", data="Old Root")
        initial_patches = self.reconciler.reconcile_subtree(old_widget, parent_html_id, "main")
        old_html_id = ""
        if initial_patches : old_html_id = initial_patches[0].html_id # Get the actual html_id of the old root

        new_widget = MockImageWidget(key_val="new", src="new.png")
        patches = self.reconciler.reconcile_subtree(new_widget, parent_html_id, "main")

        self.assertEqual(len(patches), 2)
        actions = sorted([p.action for p in patches])
        self.assertEqual(actions, ['INSERT', 'REMOVE'])
        remove_patch = next(p for p in patches if p.action == 'REMOVE')
        self.assertEqual(remove_patch.html_id, old_html_id)
        self.assertIn(Key("new"), self.reconciler.context_maps["main"])
        self.assertNotIn(Key("old"), self.reconciler.context_maps["main"])

    def test_update_child_property(self):
        parent_html_id = "app-root"
        child_old = MockTextWidget(key_val="c1", data="Old")
        root_old = MockContainerWidget(key_val="r1", children=[child_old])
        self.reconciler.reconcile_subtree(root_old, parent_html_id, "main")
        child_html_id = self.reconciler.context_maps['main'][Key("c1")]['html_id']

        child_new = MockTextWidget(key_val="c1", data="New")
        root_new = MockContainerWidget(key_val="r1", children=[child_new])
        patches = self.reconciler.reconcile_subtree(root_new, parent_html_id, "main")

        # Expect: UPDATE for child (data changed), no patch for root (props same, children list object changed but content effectively same key)
        # The root's children_keys list will change in the map, but its props won't.
        # If only child props change, only child gets an UPDATE patch.
        self.assertEqual(len(patches), 1, f"Patches: {patches}")
        patch = patches[0]
        self.assertEqual(patch.action, 'UPDATE'); self.assertEqual(patch.html_id, child_html_id)
        self.assertEqual(patch.data['props']['data'], "New")
        main_map = self.reconciler.context_maps["main"]
        self.assertEqual(main_map[Key("c1")]['props']['data'], "New")
        self.assertEqual(main_map[Key("r1")]['props'], root_new.render_props())

    def test_add_new_child_to_existing_parent(self):
        parent_html_id = "app-root"
        child1_old = MockTextWidget(key_val="c1", data="Child1")
        root_old = MockContainerWidget(key_val="r1", children=[child1_old])
        self.reconciler.reconcile_subtree(root_old, parent_html_id, "main")

        child1_kept = MockTextWidget(key_val="c1", data="Child1")
        child2_new = MockTextWidget(key_val="c2", data="Child2_new")
        root_new = MockContainerWidget(key_val="r1", children=[child1_kept, child2_new])
        patches = self.reconciler.reconcile_subtree(root_new, parent_html_id, "main")

        self.assertEqual(len(patches), 1)
        self.assertEqual(patches[0].action, 'INSERT')
        self.assertEqual(patches[0].data['props']['data'], "Child2_new")
        self.assertEqual(self.reconciler.context_maps['main'][Key("r1")]['children_keys'], [Key("c1"), Key("c2")])

    def test_remove_child_from_existing_parent(self):
        parent_html_id = "app-root"
        c1 = MockTextWidget(key_val="c1",data="C1"); c2=MockTextWidget(key_val="c2",data="C2")
        root_old = MockContainerWidget(key_val="r1", children=[c1,c2])
        self.reconciler.reconcile_subtree(root_old, parent_html_id, "main")
        c2_html_id = self.reconciler.context_maps['main'][Key("c2")]['html_id']

        c1_kept = MockTextWidget(key_val="c1",data="C1") # Create new instance for new tree
        root_new = MockContainerWidget(key_val="r1", children=[c1_kept])
        patches = self.reconciler.reconcile_subtree(root_new, parent_html_id, "main")

        self.assertEqual(len(patches), 1); self.assertEqual(patches[0].action, 'REMOVE')
        self.assertEqual(patches[0].html_id, c2_html_id)
        self.assertNotIn(Key("c2"), self.reconciler.context_maps['main'])
        self.assertEqual(self.reconciler.context_maps['main'][Key("r1")]['children_keys'], [Key("c1")])

    def test_reorder_keyed_children_in_subtree(self):
        parent_html_id = "app-root"
        c1=MockTextWidget(key_val="c1",data="C1"); c2=MockTextWidget(key_val="c2",data="C2")
        root_old = MockContainerWidget(key_val="r1", children=[c1,c2])
        self.reconciler.reconcile_subtree(root_old, parent_html_id, "main")
        c1_html_id = self.reconciler.context_maps['main'][Key("c1")]['html_id']
        c2_html_id = self.reconciler.context_maps['main'][Key("c2")]['html_id']


        # Create new instances for the new tree, even if data is same
        c1_new_pos = MockTextWidget(key_val="c1",data="C1")
        c2_new_pos = MockTextWidget(key_val="c2",data="C2")
        root_new = MockContainerWidget(key_val="r1", children=[c2_new_pos, c1_new_pos])
        patches = self.reconciler.reconcile_subtree(root_new, parent_html_id, "main")

        # Expect: k2 is stable, k1 is moved to the end.
        self.assertEqual(len(patches), 1, f"Patches: {patches}")
        self.assertEqual(patches[0].action, 'MOVE')
        self.assertEqual(patches[0].html_id, c1_html_id)
        self.assertIsNone(patches[0].data['before_id'])
        self.assertEqual(self.reconciler.context_maps['main'][Key("r1")]['children_keys'], [Key("c2"), Key("c1")])

    def test_context_isolation(self):
        p_id = "root"
        main_widget = MockTextWidget(key_val="main_w", data="Main Content")
        dialog_widget = MockTextWidget(key_val="dialog_w", data="Dialog Content")

        patches_main = self.reconciler.reconcile_subtree(main_widget, p_id, "main")
        self.assertEqual(len(patches_main), 1)
        self.assertIn(Key("main_w"), self.reconciler.context_maps["main"])
        self.assertNotIn("dialog", self.reconciler.context_maps)

        patches_dialog = self.reconciler.reconcile_subtree(dialog_widget, p_id, "dialog")
        self.assertEqual(len(patches_dialog), 1)
        self.assertIn(Key("dialog_w"), self.reconciler.context_maps["dialog"])
        self.assertIn(Key("main_w"), self.reconciler.context_maps["main"])
        self.assertNotEqual(self.reconciler.context_maps["main"], self.reconciler.context_maps["dialog"])

        self.reconciler.clear_context("dialog")
        self.assertNotIn("dialog", self.reconciler.context_maps)
        self.assertIn("main", self.reconciler.context_maps)


if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(unittest.makeSuite(TestKey))
    # suite.addTest(unittest.makeSuite(TestIDGenerator))
    # suite.addTest(unittest.makeSuite(TestDiffProps))
    # suite.addTest(unittest.makeSuite(TestGenerateHtmlStub))
    # suite.addTest(unittest.makeSuite(TestNodeReconciliation))
    # suite.addTest(unittest.makeSuite(TestChildReconciliation))
    suite.addTest(unittest.makeSuite(TestReconcileSubtree))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
