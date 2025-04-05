import weakref
import uuid
from typing import Any, Dict, List, Optional, Set, Tuple, Union

# --- Key Class (from previous example) ---
class Key:
    """
    A unique identifier for a widget to help distinguish it across rebuilds.

    :param value: Any hashable value to uniquely represent the widget.
    """
    def __init__(self, value):
        self.value = value

    def __eq__(self, other):
        return isinstance(other, Key) and self.value == other.value

    def __hash__(self):
        """
        Return a hash for the key. Converts mutable types like lists to hashable ones.
        """
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
    """
    Converts a given value to a hashable representation, useful for comparing widget style props.

    :param value: Any value or style object (EdgeInsets, BoxDecoration, etc.)
    :return: A hashable version of the value.
    """
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
    """
    The base class for all widgets in the framework.

    Every visual element inherits from `Widget` and implements its rendering logic.

    :param key: Optional Key to uniquely identify this widget in the widget tree.
    :param children: Optional list of child widgets (used for layout and nesting).

    :attr _children: List of child widgets.
    :attr _internal_id: Internal ID generated if no `Key` is provided.
    """
    # Keep framework ref for potential *State* access, but not ID generation
    _framework_ref = None

    @classmethod
    def set_framework(cls, framework):
        """
        Store a weak reference to the framework instance.
        Useful for widgets needing to communicate with the framework.

        :param framework: The root framework instance.
        """
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
        """
        Returns a unique identifier for the widget (Key if set, else internal UUID).

        :return: Key or string UUID
        """
        return self.key if self.key is not None else self._internal_id

    def get_children(self) -> List['Widget']:
        """
        Returns the list of child widgets.

        :return: List of widgets
        """
        return self._children

    def render_props(self) -> Dict[str, Any]:
        """
        Return a dictionary of properties relevant for rendering/diffing.

        Subclasses should override this to return important style/layout values
        that will be used to compare and determine UI updates.

        :return: Dict of render properties
        """
        return {}

    def get_required_css_classes(self) -> Set[str]:
        """
        Return a set of required CSS class names for this widget.

        This helps the framework collect all needed styles for rendering.

        :return: Set of class names as strings
        """
        return set()

    def _get_render_safe_prop(self, prop_value):
        """
        Convert a property to a format safe for inclusion in `render_props()`.

        Handles complex objects (like EdgeInsets, BoxDecoration) by converting
        them to dicts or tuples where possible.

        :param prop_value: The original property value
        :return: A safe, serializable version of the property
        """
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