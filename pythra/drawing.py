# =============================================================================
# PYTHRA DRAWING SYSTEM - The "Digital Artist" for Creating Custom Shapes
# =============================================================================
"""
PyThra Drawing System - Create Custom Shapes and Graphics

This is PyThra's "digital art studio" for creating custom shapes, lines, curves,
and complex graphics that go beyond simple rectangles and circles. Think of it
as having a professional drawing tool built right into your UI framework.

**What can you create?**
- Custom icons and symbols
- Complex geometric shapes
- Smooth curves and organic forms  
- Interactive diagrams and charts
- Custom button shapes and decorations
- Logos and branding elements

**Real-world analogy:**
Like using Adobe Illustrator or drawing with a vector graphics program:
- You give precise instructions ("move here", "draw line to there", "curve this way")
- The computer follows those instructions to create smooth, scalable graphics
- You can combine simple commands to create complex artwork

**How it works:**
1. **Path Commands**: Individual drawing instructions (MoveTo, LineTo, etc.)
2. **SVG Output**: Commands get converted to web-standard SVG graphics
3. **Widget Integration**: Your custom shapes become regular PyThra widgets
4. **Scalability**: Graphics scale perfectly at any size (vector-based)

**Key drawing concepts:**
- **Path**: A series of connected points and curves forming a shape
- **Commands**: Individual instructions like "move to point X,Y" or "draw line to X,Y"
- **Current Position**: The "pen location" that moves as you draw
- **SVG**: The web standard for scalable vector graphics
"""

import math
from .base import Widget

# =============================================================================
# PATH COMMAND WIDGET - The "Drawing Instruction" Base Class
# =============================================================================

class PathCommandWidget(Widget):
    """
    The base class for all drawing commands - like individual "drawing instructions".
    
    **What is a PathCommandWidget?**
    Think of this like a single instruction you'd give to an artist:
    - "Move your pencil to point (10, 20)"
    - "Draw a straight line to point (50, 60)"
    - "Draw a curved line through these control points"
    
    **Real-world analogy:**
    Like dance choreography instructions:
    - Each PathCommandWidget is one move in the dance
    - Combine many moves to create a complete dance routine
    - The "dancer" (SVG renderer) follows each instruction in sequence
    
    **All drawing commands inherit from this and implement:**
    - to_svg_command(): Converts the instruction to SVG format
    
    **You typically don't use this directly** - instead use the specific
    command types like MoveTo, LineTo, ArcTo, etc.
    """
    def to_svg_command(self, current_pos):
        raise NotImplementedError()

# =============================================================================
# BASIC DRAWING COMMANDS - The "Fundamental Drawing Moves"
# =============================================================================

class MoveTo(PathCommandWidget):
    """
    The "lift pen and move" command - moves to a point without drawing a line.
    
    **What does MoveTo do?**
    Like lifting your pen off paper and moving it to a new starting position.
    This is usually the first command in any drawing - it sets where you begin.
    
    **Real-world analogy:**
    - Like moving your finger to a new position on a touch screen before drawing
    - Like lifting a pencil and placing it at a new spot on paper
    - Like telling someone "start drawing from this corner of the page"
    
    **When to use MoveTo:**
    - Beginning a new shape or line
    - Creating disconnected shapes in the same path
    - Moving to start a new part of a complex drawing
    
    **Example:**
    ```python
    # Start drawing a triangle at point (10, 10)
    MoveTo(10, 10),  # "Lift pen, move to top corner"
    LineTo(50, 50),  # "Draw line to bottom right"
    LineTo(10, 50),  # "Draw line to bottom left"  
    ClosePath()      # "Draw line back to start (close triangle)"
    ```
    
    Args:
        x: The X coordinate to move to
        y: The Y coordinate to move to
    """
    def __init__(self, x: float, y: float):
        super().__init__()
        self.x, self.y = x, y
    
    def to_svg_command(self, current_pos):
        """Converts to SVG 'M' command and updates the current pen position."""
        current_pos['x'], current_pos['y'] = self.x, self.y
        return f"M {self.x} {self.y}"

class LineTo(PathCommandWidget):
    """
    The "draw a straight line" command - draws from current position to a new point.
    
    **What does LineTo do?**
    Draws a perfectly straight line from wherever the "pen" currently is to the
    new coordinates you specify. This is the most basic drawing command.
    
    **Real-world analogy:**
    - Like drawing a straight line with a ruler
    - Like connecting two dots with the shortest path
    - Like telling someone "from where you are now, draw straight to this point"
    
    **When to use LineTo:**
    - Creating straight edges of shapes (rectangles, triangles, polygons)
    - Drawing geometric patterns and grids
    - Creating angular/sharp designs
    - Building the outline of any shape with straight sides
    
    **Example:**
    ```python
    # Draw a simple house outline
    MoveTo(100, 200),   # Start at bottom left corner
    LineTo(200, 200),   # Draw bottom edge (roof base)
    LineTo(200, 100),   # Draw right wall up
    LineTo(150, 50),    # Draw right roof edge
    LineTo(100, 100),   # Draw left roof edge  
    ClosePath()         # Draw left wall down to start
    ```
    
    Args:
        x: The X coordinate to draw the line to
        y: The Y coordinate to draw the line to
    """
    def __init__(self, x: float, y: float):
        super().__init__()
        self.x, self.y = x, y
    
    def to_svg_command(self, current_pos):
        """Converts to SVG 'L' command and updates the current pen position."""
        current_pos['x'], current_pos['y'] = self.x, self.y
        return f"L {self.x} {self.y}"

class ClosePath(PathCommandWidget):
    """
    The "connect back to start" command - draws a line back to where you started.
    
    **What does ClosePath do?**
    Automatically draws a straight line from the current position back to wherever
    your path started (the last MoveTo point). This "closes" your shape.
    
    **Real-world analogy:**
    - Like completing a circle by connecting the end back to the beginning
    - Like closing a fence by connecting the last post to the first
    - Like telling someone "now draw back to where you started"
    
    **When to use ClosePath:**
    - Finishing any closed shape (triangles, rectangles, polygons, etc.)
    - Creating filled shapes that need to be completely enclosed
    - Ensuring no gaps in your shape outline
    
    **Why is this useful?**
    Without ClosePath, your shape would have a small gap between the end and start.
    ClosePath ensures perfect closure and is required for filled shapes.
    
    **Example:**
    ```python
    # Draw a triangle that's properly closed
    MoveTo(50, 20),     # Start at top point
    LineTo(20, 80),     # Draw to bottom left
    LineTo(80, 80),     # Draw to bottom right
    ClosePath()         # Automatically draw back to top point
    # Result: Perfect triangle with no gaps
    ```
    
    **Note:** ClosePath takes no coordinates - it automatically knows where to go!
    """
    def to_svg_command(self, current_pos):
        """Converts to SVG 'Z' command. Doesn't change current position."""
        # Close doesn't change the current position tracker
        return "Z"

# You can add more complex commands like ArcTo, QuadraticCurveTo, etc.
# with properties for radius, flags, etc.
class ArcTo(PathCommandWidget):
    def __init__(self, x, y, rx, ry, large_arc=0, sweep=1, rotation=0):
        super().__init__()
        self.x, self.y, self.rx, self.ry = x, y, rx, ry
        self.large_arc, self.sweep, self.rotation = large_arc, sweep, rotation
    def to_svg_command(self, current_pos):
        current_pos['x'], current_pos['y'] = self.x, self.y
        return f"A {self.rx} {self.ry} {self.rotation} {self.large_arc} {self.sweep} {self.x} {self.y}"

class QuadraticCurveTo(PathCommandWidget):
    """Represents an SVG 'Q' command for a quadratic Bézier curve."""
    def __init__(self, x1: float, y1: float, x: float, y: float):
        """
        Args:
            x1 (float): The x-coordinate of the control point.
            y1 (float): The y-coordinate of the control point.
            x (float): The x-coordinate of the end point.
            y (float): The y-coordinate of the end point.
        """
        super().__init__()
        self.x1, self.y1 = x1, y1
        self.x, self.y = x, y
    
    def to_svg_command(self, current_pos):
        current_pos['x'], current_pos['y'] = self.x, self.y
        return f"Q {self.x1} {self.y1} {self.x} {self.y}"




# ... (after all the PathCommandWidget classes) ...

def create_rounded_polygon_path(vertices: list[tuple[float, float]], radius: float) -> list[PathCommandWidget]:
    """
    Creates a list of path commands for a closed polygon with rounded corners.

    Args:
        vertices (list[tuple[float, float]]): A list of (x, y) tuples representing the polygon's vertices.
        radius (float): The radius to apply to each corner.

    Returns:
        list[PathCommandWidget]: A list of path commands to be used with ClipPath.
    """
    if not vertices or len(vertices) < 3 or radius <= 0:
        # Not enough points or no radius, return a simple sharp-cornered polygon
        commands = [MoveTo(vertices[0][0], vertices[0][1])]
        for i in range(1, len(vertices)):
            commands.append(LineTo(vertices[i][0], vertices[i][1]))
        commands.append(ClosePath())
        return commands

    commands = []
    num_vertices = len(vertices)

    for i in range(num_vertices):
        # Get the current, previous, and next vertices
        p1 = vertices[i]
        p0 = vertices[i - 1] # Wraps around to the last element for the first vertex
        p2 = vertices[(i + 1) % num_vertices]

        # Calculate vectors from the corner point (p1) to the adjacent points
        v1 = (p0[0] - p1[0], p0[1] - p1[1])
        v2 = (p2[0] - p1[0], p2[1] - p1[1])

        # Calculate the length of the adjacent edges
        len_v1 = math.sqrt(v1[0]**2 + v1[1]**2)
        len_v2 = math.sqrt(v2[0]**2 + v2[1]**2)
        
        # Clamp the radius to be at most half the length of the shorter edge
        # This prevents the rounded corner from overlapping with the next one
        clamped_radius = min(radius, len_v1 / 2, len_v2 / 2)

        # Calculate the start point of the curve (on the edge from p0 to p1)
        arc_start_x = p1[0] + (v1[0] / len_v1) * clamped_radius
        arc_start_y = p1[1] + (v1[1] / len_v1) * clamped_radius

        # Calculate the end point of the curve (on the edge from p1 to p2)
        arc_end_x = p1[0] + (v2[0] / len_v2) * clamped_radius
        arc_end_y = p1[1] + (v2[1] / len_v2) * clamped_radius

        if i == 0:
            # For the very first point, we start with a MoveTo command
            commands.append(MoveTo(arc_start_x, arc_start_y))
        else:
            # For subsequent points, we draw a line to the start of the arc
            commands.append(LineTo(arc_start_x, arc_start_y))
        
        # Now, create the rounded corner using a quadratic Bézier curve.
        # The corner point (p1) acts as the control point.
        commands.append(QuadraticCurveTo(
            x1=p1[0], y1=p1[1], # Control point is the sharp corner
            x=arc_end_x, y=arc_end_y  # End point of the curve
        ))

    commands.append(ClosePath())
    return commands





# --- NEW HIGH-LEVEL WIDGET ---
class RoundedPolygon(PathCommandWidget):
    """
    A high-level "super-command" that takes a list of simple path commands
    (MoveTo, LineTo) as children and generates a single, complete SVG path 
    string for a polygon with rounded corners.
    """
    def __init__(self, children: list[PathCommandWidget], radius: float, key=None):
        """
        Args:
            children (list[PathCommandWidget]): A list of MoveTo and LineTo commands
                                               defining the vertices of the polygon.
            radius (float): The radius to apply to the corners.
            key: Optional Key for the widget.
        """
        super().__init__(key=key, children=children)
        self.radius = radius

    def to_svg_command(self, current_pos) -> str:
        """
        Processes its children to generate a full, rounded path string.
        This method overrides the base class to return a complete path,
        not just a single command segment.
        """
        # 1. Extract vertices from the declarative child commands
        vertices = []
        for command in self._children:
            if isinstance(command, (MoveTo, LineTo)):
                vertices.append((command.x, command.y))

        # 2. Handle edge cases (if not enough vertices or no radius)
        if not vertices or len(vertices) < 3 or self.radius <= 0:
            if not vertices: return ""
            # Fallback to a sharp-cornered path
            sharp_path_parts = [MoveTo(vertices[0][0], vertices[0][1]).to_svg_command(current_pos)]
            for i in range(1, len(vertices)):
                sharp_path_parts.append(LineTo(vertices[i][0], vertices[i][1]).to_svg_command(current_pos))
            sharp_path_parts.append(ClosePath().to_svg_command(current_pos))
            return " ".join(sharp_path_parts)

        # 3. Use the rounding geometry logic to create the new path commands
        rounded_commands = []
        num_vertices = len(vertices)

        for i in range(num_vertices):
            p1 = vertices[i]
            p0 = vertices[i - 1]
            p2 = vertices[(i + 1) % num_vertices]

            v1 = (p0[0] - p1[0], p0[1] - p1[1])
            v2 = (p2[0] - p1[0], p2[1] - p1[1])

            len_v1 = math.sqrt(v1[0]**2 + v1[1]**2)
            len_v2 = math.sqrt(v2[0]**2 + v2[1]**2)
            
            clamped_radius = min(self.radius, len_v1 / 2, len_v2 / 2)

            arc_start_x = p1[0] + (v1[0] / len_v1) * clamped_radius
            arc_start_y = p1[1] + (v1[1] / len_v1) * clamped_radius

            arc_end_x = p1[0] + (v2[0] / len_v2) * clamped_radius
            arc_end_y = p1[1] + (v2[1] / len_v2) * clamped_radius

            if i == 0:
                rounded_commands.append(MoveTo(arc_start_x, arc_start_y))
            else:
                rounded_commands.append(LineTo(arc_start_x, arc_start_y))
            
            rounded_commands.append(QuadraticCurveTo(p1[0], p1[1], arc_end_x, arc_end_y))
        
        rounded_commands.append(ClosePath())

        # 4. Convert the new list of commands into a single SVG string
        final_path_parts = []
        # Use a local pos tracker as this widget generates a self-contained path
        internal_pos = {'x': 0, 'y': 0} 
        for cmd in rounded_commands:
            final_path_parts.append(cmd.to_svg_command(internal_pos))
        
        # Update the outer current_pos to the last point of our path
        current_pos.update(internal_pos)

        return " ".join(final_path_parts)

# in pythra/drawing.py

# ... (keep all existing classes) ...

class PolygonClipper(PathCommandWidget):
    """
    A high-level command that generates a responsive `clip-path: polygon(...)`
    using percentage-based vertices.
    """
    def __init__(self, points: list[tuple[float, float]], key=None):
        """
        Args:
            points (list[tuple[float, float]]): A list of (x, y) tuples where
                                                each value is a percentage (0-100).
            key: Optional Key for the widget.
        """
        # We don't have traditional children, but we pass an empty list
        # to the super constructor for consistency.
        super().__init__(key=key, children=[])
        self.points = points

    def to_svg_command(self, current_pos) -> str:
        """
        This method is a bit of a misnomer in this case, as we are not
        generating an SVG command but a full CSS `polygon()` function string.
        The Reconciler will treat the output as the final value.
        """
        if not self.points:
            return ""

        # Convert the list of tuples into the CSS polygon format
        # e.g., "polygon(50% 0%, 61% 35%, ...)"
        point_strings = [f"{p[0]}% {p[1]}%" for p in self.points]
        return f"polygon({', '.join(point_strings)})"