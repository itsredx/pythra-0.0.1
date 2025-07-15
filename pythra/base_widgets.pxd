# This file defines the C-API for our mock widgets

cdef class MockWidget:
    cdef public object key
    cdef public list _children

cdef class Container(MockWidget):
    pass

cdef class Text(MockWidget):
    cdef public object text