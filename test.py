class Alignment:
    """
    Represents alignment for widgets using flexbox concepts (justify-content, align-items).
    Ensures compatibility with reconciliation by being hashable.

    Attributes:
        justify_content (str): CSS value for justify-content (main axis alignment).
        align_items (str): CSS value for align-items (cross axis alignment).
    """
    def __init__(self, justify_content: str, align_items: str):
        """
        Initializes Alignment. It's recommended to use the static methods
        like Alignment.center(), Alignment.top_left(), etc.

        Args:
            justify_content (str): CSS value like 'flex-start', 'center', 'flex-end',
                                  'space-between', 'space-around', 'space-evenly'.
            align_items (str): CSS value like 'flex-start', 'center', 'flex-end',
                                'stretch', 'baseline'.
        """
        # Consider adding validation for allowed CSS values if needed
        self.justify_content = justify_content
        self.align_items = align_items

    # --- Static Constructors (Convenience Methods) ---
    @staticmethod
    def center():
        return Alignment('center', 'center')

    @staticmethod
    def top_left():
        return Alignment('flex-start', 'flex-start')

    @staticmethod
    def top_center():
        return Alignment('center', 'flex-start')

    @staticmethod
    def top_right():
        return Alignment('flex-end', 'flex-start')

    @staticmethod
    def center_left():
        return Alignment('flex-start', 'center')

    @staticmethod
    def center_right():
        return Alignment('flex-end', 'center')

    @staticmethod
    def bottom_left():
        return Alignment('flex-start', 'flex-end')

    @staticmethod
    def bottom_center():
        return Alignment('center', 'flex-end')

    @staticmethod
    def bottom_right():
        return Alignment('flex-end', 'flex-end')

    # Add others if needed, e.g., space_between variants
    @staticmethod
    def space_between_center(): # Example
        return Alignment('space-between', 'center')

    # --- Compatibility Methods ---

    def to_css_dict(self) -> dict:
        """
        Returns alignment properties as a dictionary suitable for CSS generation
        or applying as inline styles. Includes display:flex.
        """
        return {
            'display': 'flex',
            'justify-content': self.justify_content,
            'align-items': self.align_items
        }

    def to_css(self) -> str:
        """
        Converts the Alignment object to a CSS string snippet for flexbox layout.
        Includes display: flex.
        """
        return f"display: flex; justify-content: {self.justify_content}; align-items: {self.align_items};"

    # --- Add __eq__ and __hash__ for compatibility with style keys ---
    def __eq__(self, other):
        if not isinstance(other, Alignment):
            return NotImplemented
        return (self.justify_content == other.justify_content and
                self.align_items == other.align_items)

    def __hash__(self):
        # Hash a tuple of the relevant attributes
        return hash((self.justify_content, self.align_items))

    # --- Optional: Add representation for debugging ---
    def __repr__(self):
         # Try to find matching static method name for cleaner repr (optional)
         for name, method in Alignment.__dict__.items():
             if isinstance(method, staticmethod):
                 try:
                     instance = method.__func__() # Call the static method
                     if instance == self:
                          return f"Alignment.{name}()"
                 except Exception: # Catch potential errors during static method call
                     pass
         # Fallback representation
         return f"Alignment(justify_content='{self.justify_content}', align_items='{self.align_items}')"

    # --- Optional: Add method for reconciler prop representation ---
    def to_dict(self):
         """Returns a simple dictionary representation."""
         return {'justify_content': self.justify_content, 'align_items': self.align_items}

    # --- Optional: Add method for hashable tuple representation ---
    def to_tuple(self):
         """Returns a hashable tuple representation."""
         return (self.justify_content, self.align_items)


print(Alignment.center().to_css())