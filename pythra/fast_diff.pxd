# pythra/fast_diff.pxd

# distutils: language = c++

from pythra.base_widgets cimport MockWidget

cdef class VNode:
    cdef public object py_key
    cdef public str widget_type
    cdef public str html_id
    cdef public list children
    cdef public dict props
    cdef public object widget_instance

# expose the API for cimport
cdef VNode build_vnode_from_map(dict old_map, str parent_html_id)
cdef VNode build_vnode_from_widget(MockWidget widget)
cdef list diff_trees(VNode old_root, VNode new_root, str parent_html_id)
