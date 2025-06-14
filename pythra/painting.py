# framework/painting.py (or drawing.py)
from typing import Tuple, Any
from .drawing import Path # Assuming Path is in drawing.py

# Conceptual Size class, can be a simple tuple or a dedicated class
Size = Tuple[float, float]

class CustomClipper: # Generic base
    def getClip(self, size: Size) -> Any:
        raise NotImplementedError()

    def shouldReclip(self, oldClipper: 'CustomClipper') -> bool:
        """
        Called when the ClipPath widget is rebuilt with a new clipper instance.
        If this returns true, the clip path will be recomputed.
        Defaults to true if clipper instances are different.
        """
        return self != oldClipper # Basic check by instance or value equality

    def __eq__(self, other):
        # Subclasses should implement this if they have properties affecting the clip
        return isinstance(other, self.__class__)

    def __hash__(self):
        # Subclasses should implement this
        return hash(self.__class__)

    def to_tuple(self): # For make_hashable
         # Subclasses must implement if they have properties
         return (self.__class__,)

class PathClipper(CustomClipper): # Specific for Path
    def getClip(self, size: Size) -> 'Path': # Return our Path object
        raise NotImplementedError()