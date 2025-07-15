# pythra/fast_diff_engine.pyx

# distutils: language = c++

from .fast_diff cimport build_vnode_from_map, build_vnode_from_widget, diff_trees, VNode
from .base_widgets cimport MockWidget

cdef class DiffEngine:
    cdef public VNode _cached_old_root
    cdef public object _cached_old_map_id

    def __cinit__(self):
        # use None, not NULL
        self._cached_old_root = None
        self._cached_old_map_id = None

    def diff(self,
             dict old_map,
             object new_widget,
             str parent_html_id,
             object id_generator):
        # rebuild & cache old_root only when the map object changes
        if old_map is not self._cached_old_map_id:
            self._cached_old_root = build_vnode_from_map(old_map, parent_html_id)
            self._cached_old_map_id = old_map

        # build new_root (cast to MockWidget so C-level access works)
        cdef VNode new_root = build_vnode_from_widget(<MockWidget>new_widget)

        # diff the two VNode trees
        cdef list patches = diff_trees(self._cached_old_root, new_root, parent_html_id)

        # assign real html_ids on any INSERTs
        for patch in patches:
            if patch['action'] == 'INSERT':
                patch['html_id'] = id_generator.next_id()

        return patches
