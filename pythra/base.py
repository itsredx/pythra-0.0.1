# BASE.PY
import weakref
import uuid
from typing import Any, Dict, List, Optional, Set, Union

# =============================================================================
# KEY CLASS - The "ID Card" System for PyThra Widgets
# =============================================================================

class Key:
    """
    Think of this as an "ID card" for widgets in your PyThra app!
    
    **Why do we need Keys?**
    Imagine you have a list of 100 buttons, and you delete the 50th one.
    Without keys, PyThra might get confused and think you deleted a different button!
    Keys help PyThra keep track of which widget is which, even when things change.
    
    **Real-world analogy:**
    - Like student ID numbers in a classroom roster
    - Like license plates on cars
    - Like barcodes on products in a store
    
    **When to use Keys:**
    - Lists of widgets that can change (add/remove items)
    - Widgets that hold important state (like form inputs)
    - Any widget you want to "remember" across UI updates
    
    **Example:**
    ```python
    # Without keys - PyThra might mix up which button is which
    for name in names:
        Button(text=name, onClick=delete_person)
    
    # With keys - PyThra knows exactly which button belongs to which person  
    for name in names:
        Button(key=Key(name), text=name, onClick=delete_person)
    ```
    
    Args:
        value: Any unique identifier (string, number, etc.) that represents this widget
    """
    def __init__(self, value):
        self.value = value

    def __eq__(self, other):
        return isinstance(other, Key) and self.value == other.value

    def __hash__(self):
        """
        Creates a "fingerprint" number for this Key so Python can use it efficiently.
        
        **Why is this needed?**
        Python needs to be able to quickly compare keys and store them in dictionaries.
        This method converts your key value into a number (hash) for fast lookups.
        
        **Special handling:**
        - Lists get converted to tuples (because lists can change, tuples can't)
        - This ensures your key works even if you use complex data structures
        """
        # Ensure value is hashable or convert to a hashable type
        if isinstance(self.value, (list, dict)):
            # Example: convert list to tuple for hashing
            return hash(tuple(self.value))
        return hash(self.value)

    def __repr__(self):
        return f"Key({self.value!r})"

    def __str_key__(self) -> str:
        return self.value

# =============================================================================
# HASHABLE HELPER - The "Style Comparator" for PyThra
# =============================================================================

def make_hashable(value):
    """
    The "Universal Converter" - makes any value comparable for PyThra's style system.
    
    **What's the problem this solves?**
    PyThra needs to compare widget styles to know when to update the UI.
    But some style objects (like colors, margins, etc.) are complex and can't be 
    compared directly. This function converts them into a format that can be compared.
    
    **Real-world analogy:**
    Like converting different currencies to USD so you can compare prices.
    This converts different data types to a "standard format" so PyThra can compare them.
    
    **What it handles:**
    - Style objects (EdgeInsets, BoxDecoration, etc.) → Convert using their to_tuple() method
    - Lists → Convert to tuples (lists can change, tuples can't)
    - Dictionaries → Convert to sorted tuples
    - Basic types (strings, numbers) → Use as-is
    - Complex objects → Try to convert, fall back to string if needed
    
    Args:
        value: Any style value that needs to be made comparable
        
    Returns:
        A "fingerprint" version of the value that can be compared efficiently
        
    Example:
        ```python
        # These two padding objects can now be compared:
        padding1 = EdgeInsets.all(10)
        padding2 = EdgeInsets.all(20)
        hash1 = make_hashable(padding1)  # Returns: (10, 10, 10, 10)
        hash2 = make_hashable(padding2)  # Returns: (20, 20, 20, 20)
        # Now PyThra can tell they're different!
        ```
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

# =============================================================================
# WIDGET CLASS - The "Building Block" of All PyThra UI Elements
# =============================================================================

class Widget:
    """
    The "DNA" of every UI element in PyThra - every button, text, image inherits from this!
    
    **Think of Widget like:**
    - The "base template" for all UI components
    - Like a "parent class" that gives all widgets common superpowers
    - The foundation that every visual element is built on
    
    **What does Widget provide?**
    1. **Identity System**: Each widget gets a unique ID (like a social security number)
    2. **Parent-Child Relationships**: Widgets can contain other widgets (like folders contain files)
    3. **Style Management**: Handles how the widget looks (colors, sizes, etc.)
    4. **Communication**: Provides ways for widgets to talk to the main framework
    
    **Real-world analogy:**
    Think of Widget like the "blueprint" for building LEGO pieces:
    - Every LEGO piece (widget) has connectors (parent-child relationships)
    - Every piece has an identity (unique ID)
    - Every piece has properties (color, size, shape = styles)
    - Every piece can connect to the main structure (framework)
    
    **The Widget Family Tree:**
    ```
    Widget (this class)
    ├─ Button (clickable widget)
    ├─ Text (displays words)
    ├─ Image (shows pictures)
    ├─ Container (holds other widgets)
    └─ ... (hundreds of other widget types)
    ```
    
    Args:
        key: Optional "ID card" for this widget (helps PyThra track it)
        children: Optional list of widgets that go "inside" this widget
    
    Attributes:
        _children: The widgets contained inside this widget
        _internal_id: Auto-generated backup ID if no key is provided
        framework: Reference to the main PyThra system
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
        # --- THIS IS THE FIX ---
        # Every widget, upon creation, gets a direct reference to the framework.
        self.framework: Optional['Framework'] = self._framework_ref() if self._framework_ref else None # type: ignore
        # --- END OF FIX ---

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

    def get_static_css_classes(self) -> Set[str]:
        """
        Returns a set of static CSS classes that are part of this widget's
        fundamental structure and should never be removed on update.
        """
        return set()

    def get_shared_css_class(self) -> Optional[str]:
        """
        Returns the single, dynamically generated shared style class, if any.
        """
        return getattr(self, 'css_class', None)

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