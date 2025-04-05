import weakref
import uuid
from typing import Any, Dict, List, Optional, Set, Tuple, Union

# --- Key Class (from previous example) ---
class Key:
    def __init__(self, value):
        self.value = value

    def __eq__(self, other):
        return isinstance(other, Key) and self.value == other.value

    def __hash__(self):
        # Ensure value is hashable or convert to a hashable type
        if isinstance(self.value, (list, dict)):
             # Example: convert list to tuple for hashing
             return hash(tuple(self.value))
        return hash(self.value)

    def __repr__(self):
        return f"Key({self.value!r})"

# --- Hashable Helper for Complex Style Objects ---
# Assume your style objects (EdgeInsets, BoxDecoration, TextStyle)
# have a method like `to_tuple()` that returns a hashable representation.
def make_hashable(value):
    if hasattr(value, 'to_tuple'):
        return value.to_tuple() # Prefer specific method if exists
    elif isinstance(value, (str, int, float, bool, tuple, Key, type(None))):
        return value
    elif isinstance(value, list):
        return tuple(make_hashable(v) for v in value)
    elif isinstance(value, dict):
         # Convert dict to sorted tuple of key-value tuples
         return tuple(sorted((k, make_hashable(v)) for k, v in value.items()))
    # Add handling for other specific types if needed
    # Fallback: Attempt to use object directly, may fail if not hashable
    try:
        hash(value)
        return value
    except TypeError:
        # Or raise an error, or return a placeholder hash
        print(f"Warning: Cannot make type {type(value)} hashable for style key.")
        return str(value) # Fallback to string representation (less reliable)

# --- Base Widget Refactored ---
class Widget:
    # Keep framework ref for potential *State* access, but not ID generation
    _framework_ref = None

    @classmethod
    def set_framework(cls, framework):
        cls._framework_ref = weakref.ref(framework)

    def __init__(self, key: Optional[Key] = None, children: Optional[List['Widget']] = None):
        """
        Initialize base widget. No framework interaction for IDs here.
        """
        self.key = key
        self._children: List['Widget'] = children if children is not None else []
        # Internal ID used if key is None, or for mapping during reconciliation
        self._internal_id: str = str(uuid.uuid4())
        # Note: parent relationship is implicit in the tree built by State.build()

    def get_unique_id(self) -> Union[Key, str]:
        """Returns the Key if available, otherwise an internal unique ID."""
        return self.key if self.key is not None else self._internal_id

    def get_children(self) -> List['Widget']:
        """Get the child widgets defined during build."""
        return self._children

    def render_props(self) -> Dict[str, Any]:
        """
        Return properties relevant for diffing. Override in subclasses.
        These properties will be compared by the reconciler.
        """
        return {}

    def get_required_css_classes(self) -> Set[str]:
        """
        Return a set of CSS class names needed by this widget instance.
        This might include shared classes and potentially instance-specific ones.
        """
        return set()

    def _get_render_safe_prop(self, prop_value):
         """Helper to prepare complex props for the render_props dict."""
         if hasattr(prop_value, 'to_dict'): # Prefer a dict representation
              return prop_value.to_dict()
         elif hasattr(prop_value, 'to_tuple'): # Fallback to tuple
              return prop_value.to_tuple()
         elif isinstance(prop_value, (list, tuple)):
              return [self._get_render_safe_prop(p) for p in prop_value]
         # Return basic types directly
         return prop_value

    def __repr__(self):
        return f"{self.__class__.__name__}(key={self.key})"