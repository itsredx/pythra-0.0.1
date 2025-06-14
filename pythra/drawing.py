# framework/drawing.py (or similar)
from typing import List, Tuple, Union, Any


# Conceptual Size class, can be a simple tuple or a dedicated class
Size = Tuple[float, float]


class PathCommand:
    MOVE_TO = 'M'
    LINE_TO = 'L'
    QUADRATIC_BEZIER_TO = 'Q'
    CUBIC_BEZIER_TO = 'C'
    ARC_TO = 'A' # SVG Arc syntax is complex
    CLOSE = 'Z'

class Path:
    def __init__(self):
        self.commands: List[Tuple[str, List[Union[float, int]]]] = []
        self._current_x: float = 0
        self._current_y: float = 0

    def moveTo(self, x: float, y: float):
        self.commands.append((PathCommand.MOVE_TO, [x, y]))
        self._current_x, self._current_y = x, y

    def lineTo(self, x: float, y: float):
        self.commands.append((PathCommand.LINE_TO, [x, y]))
        self._current_x, self._current_y = x, y

    def relativeLineTo(self, dx: float, dy: float):
        self.lineTo(self._current_x + dx, self._current_y + dy)

    def quadraticBezierTo(self, x1: float, y1: float, x2: float, y2: float):
        self.commands.append((PathCommand.QUADRATIC_BEZIER_TO, [x1, y1, x2, y2]))
        self._current_x, self._current_y = x2, y2

    def cubicBezierTo(self, x1: float, y1: float, x2: float, y2: float, x3: float, y3: float):
        self.commands.append((PathCommand.CUBIC_BEZIER_TO, [x1, y1, x2, y2, x3, y3]))
        self._current_x, self._current_y = x3, y3

    # SVG Arc (A rx ry x-axis-rotation large-arc-flag sweep-flag x y) is complex
    # For simplicity, you might start with simpler shapes or require users to construct arc commands
    def arcToPoint(self, x: float, y: float, radiusX: float, radiusY: float,
                   xAxisRotation: float = 0, largeArcFlag: int = 0, sweepFlag: int = 1):
        # This is a simplified mapping, real arcTo in Flutter is more complex (tangent arcs)
        self.commands.append((PathCommand.ARC_TO, [radiusX, radiusY, xAxisRotation, largeArcFlag, sweepFlag, x, y]))
        self._current_x, self._current_y = x, y

    def addRect(self, left: float, top: float, width: float, height: float):
        self.moveTo(left, top)
        self.lineTo(left + width, top)
        self.lineTo(left + width, top + height)
        self.lineTo(left, top + height)
        self.close()

    def addOval(self, left: float, top: float, width: float, height: float):
        # Approximate oval with Bezier curves or use SVG ellipse/path arc commands
        # For simplicity, let's use SVG path arc commands for a full ellipse
        cx, cy = left + width / 2, top + height / 2
        rx, ry = width / 2, height / 2
        self.moveTo(cx + rx, cy)
        self.commands.append((PathCommand.ARC_TO, [rx, ry, 0, 1, 1, cx - rx, cy])) # First half
        self.commands.append((PathCommand.ARC_TO, [rx, ry, 0, 1, 1, cx + rx, cy])) # Second half
        # self.close() # Not strictly needed for full ellipse with two arcs

    def close(self):
        self.commands.append((PathCommand.CLOSE, []))

    def to_svg_path_data(self) -> str:
        """Converts the path commands to an SVG path 'd' attribute string."""
        d_parts = []
        for cmd_type, args in self.commands:
            args_str = " ".join(map(str, args))
            d_parts.append(f"{cmd_type} {args_str}".strip())
        return " ".join(d_parts)

    def __eq__(self, other):
        return isinstance(other, Path) and self.commands == other.commands

    def __hash__(self):
        # Convert list of lists/tuples to tuple of tuples for hashing
        return hash(tuple((cmd, tuple(args)) for cmd, args in self.commands))

    def to_tuple(self): # For make_hashable
         return tuple((cmd, tuple(args)) for cmd, args in self.commands)


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