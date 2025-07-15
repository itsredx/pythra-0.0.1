# pythra/fast_diff.pyx

# distutils: language = c++

# Import the C-level definitions for our classes
from .fast_diff cimport VNode
from .base_widgets cimport MockWidget, Text # Import the fast widget types

# ==============================================================================
# VNode Class Definition with Constructor
# ==============================================================================
cdef class VNode:
    def __cinit__(self, object py_key, str widget_type, str html_id, list children, dict props, object widget_instance):
        self.py_key = py_key
        self.widget_type = widget_type
        self.html_id = html_id
        self.children = children
        self.props = props
        self.widget_instance = widget_instance

# ==============================================================================
# Top-level Entry Point
# ==============================================================================

def fast_diff(dict old_map, new_widget, str parent_html_id, id_generator):
    cdef VNode old_root = build_vnode_from_map(old_map, parent_html_id)
    cdef VNode new_root = build_vnode_from_widget(new_widget)
    cdef list patches = diff_trees(old_root, new_root, parent_html_id)
    for patch in patches:
        if patch['action'] == 'INSERT':
            patch['html_id'] = id_generator.next_id()
    return patches

# ==============================================================================
# VNode Tree Construction Logic (ULTRA OPTIMIZED)
# ==============================================================================

cdef VNode build_vnode_from_widget(MockWidget widget):
    if widget is None: return None

    # OPTIMIZATION: Direct C-level access to the ._children list
    cdef list children = widget._children
    cdef list children_vnodes = []
    cdef MockWidget child

    # This loop is now extremely fast as it avoids all Python method calls
    for child in children:
        children_vnodes.append(build_vnode_from_widget(child))

    # OPTIMIZATION: Build the props dictionary at C-speed, avoiding .render_props()
    cdef dict props
    cdef str widget_type_name = type(widget).__name__
    if widget_type_name == 'Text':
        # Direct C-level access to .text attribute after casting
        props = {'type': 'Text', 'data': (<Text>widget).text}
    else: # For Container and other potential widgets
        props = {'type': widget_type_name}

    return VNode(
        # OPTIMIZATION: Direct C-level access to the .key attribute
        py_key=widget.key,
        widget_type=widget_type_name,
        html_id=None,
        children=children_vnodes,
        props=props,
        widget_instance=widget
    )

cdef VNode build_vnode_from_map(dict old_map, str parent_html_id):
    cdef object root_key = None
    if not old_map: return None
    for key, data in old_map.items():
        if data.get('parent_html_id') == parent_html_id:
            root_key = key
            break
    if root_key is None: return None
    return _build_vnode_from_map_recursive(old_map, root_key)

cdef VNode _build_vnode_from_map_recursive(dict old_map, object key):
    cdef dict node_data = old_map.get(key)
    if node_data is None: return None
    cdef list children_keys = node_data.get('children_keys', [])
    cdef list children_vnodes = []
    cdef object child_key
    for child_key in children_keys:
        children_vnodes.append(_build_vnode_from_map_recursive(old_map, child_key))
    return VNode(
        py_key=key,
        widget_type=node_data.get('widget_type'),
        html_id=node_data.get('html_id'),
        children=children_vnodes,
        props=node_data.get('props'),
        widget_instance=node_data.get('widget_instance')
    )

# ==============================================================================
# Core Diffing Logic (Unchanged)
# ==============================================================================

cdef list diff_trees(VNode old_root, VNode new_root, str parent_html_id):
    cdef list patches = []
    _diff_recursive(old_root, new_root, patches, parent_html_id, None)
    return patches

cdef void _diff_recursive(VNode old_node, VNode new_node, list patches, str parent_html_id, str before_id=None):
    cdef str new_parent_id_placeholder
    cdef bint same_key
    cdef bint same_type
    cdef dict prop_changes

    if new_node is None:
        if old_node is not None:
            patches.append({'action': 'REMOVE', 'html_id': old_node.html_id, 'data': {}})
        return

    if old_node is None:
        patches.append({
            'action': 'INSERT', 'html_id': None,
            'data': {'widget_instance': new_node.widget_instance, 'parent_html_id': parent_html_id, 'props': new_node.props, 'before_id': before_id}
        })
        new_parent_id_placeholder = "placeholder_for_" + str(new_node.py_key)
        for child_node in new_node.children:
            _diff_recursive(None, child_node, patches, new_parent_id_placeholder, None)
        return

    same_key = (old_node.py_key == new_node.py_key)
    same_type = (old_node.widget_type == new_node.widget_type)
    if not (same_key and same_type):
        _diff_recursive(old_node, None, patches, parent_html_id, None)
        _diff_recursive(None, new_node, patches, parent_html_id, before_id)
        return

    new_node.html_id = old_node.html_id
    prop_changes = diff_props_py(old_node.props, new_node.props)
    if prop_changes:
        patches.append({
            'action': 'UPDATE', 'html_id': old_node.html_id,
            'data': {'props': new_node.props, 'old_props': old_node.props}
        })
    _diff_children(old_node, new_node, patches, old_node.html_id)

cdef void _diff_children(VNode old_parent, VNode new_parent, list patches, str parent_html_id):
    cdef list old_children = old_parent.children
    cdef list new_children = new_parent.children
    if not old_children and not new_children: return
    cdef dict old_key_to_node = {child.py_key: child for child in old_children}
    cdef set new_keys = {child.py_key for child in new_children}
    for old_child in old_children:
        if old_child.py_key not in new_keys:
            _diff_recursive(old_child, None, patches, parent_html_id, None)
    cdef VNode old_node
    cdef dict old_key_to_idx = {child.py_key: i for i, child in enumerate(old_children)}
    cdef int last_placed_old_idx = -1
    cdef int new_idx = 0
    for new_child in new_children:
        old_idx = old_key_to_idx.get(new_child.py_key)
        before_id = _find_next_stable_html_id(new_idx + 1, new_children, old_key_to_idx)
        if old_idx is None:
            _diff_recursive(None, new_child, patches, parent_html_id, before_id)
        else:
            old_node = old_children[old_idx]
            if old_idx < last_placed_old_idx:
                patches.append({
                    'action': 'MOVE', 'html_id': old_node.html_id,
                    'data': {'parent_html_id': parent_html_id, 'before_id': before_id}
                })
            last_placed_old_idx = max(last_placed_old_idx, old_idx)
            _diff_recursive(old_node, new_child, patches, parent_html_id, None)
        new_idx += 1

cdef str _find_next_stable_html_id(int start_index, list new_children, dict old_key_map):
    cdef int i
    for i in range(start_index, len(new_children)):
        key = new_children[i].py_key
        if key in old_key_map and new_children[i].html_id is not None:
            return new_children[i].html_id
    return None

cdef dict diff_props_py(dict old_props, dict new_props):
    if old_props is None and new_props is None: return None
    if old_props is None: return new_props
    if new_props is None: return {}
    if old_props == new_props: return None
    changes = {}
    all_keys = set(old_props.keys()) | set(new_props.keys())
    for key in all_keys:
        old_val = old_props.get(key)
        new_val = new_props.get(key)
        if old_val != new_val:
            changes[key] = new_val
    return changes if changes else None