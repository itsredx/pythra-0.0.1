# pythra/fast_diff.pxd

# distutils: language = c++

# Forward declare the VNode class
cdef class VNode

# Define the public API of the VNode class for efficient access
cdef class VNode:
    cdef public object py_key
    cdef public str widget_type
    cdef public str html_id
    cdef public list children
    cdef public dict props
    cdef public object widget_instance

     # --- THE FIX: Declare the constructor ---
    def __cinit__(self, object py_key, str widget_type, str html_id, list children, dict props, object widget_instance)

# Define the C-level function signatures
cdef list diff_trees(VNode old_root, VNode new_root, str parent_html_id)
cdef void _diff_children(VNode old_parent, VNode new_parent, list patches, str parent_html_id)

# Declare the function with its full, correct signature including the optional argument.
cdef void _diff_recursive(VNode old_node, VNode new_node, list patches, str parent_html_id, str before_id=*)

# Continue with the rest of the declarations
cdef VNode build_vnode_from_widget(widget)
cdef VNode build_vnode_from_map(dict old_map, str parent_html_id)
cdef VNode _build_vnode_from_map_recursive(dict old_map, object key)
cdef dict diff_props_py(dict old_props, dict new_props)
cdef str _find_next_stable_html_id(int start_index, list new_children, dict old_key_map)