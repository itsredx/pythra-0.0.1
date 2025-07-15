# This file implements our mock widgets as fast cdef classes

from .base_widgets cimport MockWidget, Container, Text

cdef class MockWidget:
    def __init__(self, key=None, children=None):
        self.key = key if key is not None else str(id(self))
        self._children = children if children is not None else []
    
    # We keep these as Python-callable methods for compatibility
    def get_children(self):
        return self._children
    
    def get_unique_id(self):
        return self.key
    
    def render_props(self):
        return {'type': self.__class__.__name__}

cdef class Container(MockWidget):
    def __init__(self, children, key=None):
        # Cython doesn't have a direct super() in __init__ for cdef classes
        # We call the base __init__ explicitly.
        MockWidget.__init__(self, key=key, children=children)

cdef class Text(MockWidget):
    def __init__(self, text, key=None):
        MockWidget.__init__(self, key=key, children=[])
        self.text = text
    
    def render_props(self):
        return {'type': 'Text', 'data': self.text}