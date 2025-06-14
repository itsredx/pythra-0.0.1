# main.py (or a separate custom_clippers.py)
import math # Add this at the top of the file with MyStarClipper
import sys
import math # For MyStarClipper
from PySide6.QtCore import QTimer, QCoreApplication
from typing import List, Tuple, Union, Any, Optional


# Framework Imports
from pythra import (
    Framework, State, StatefulWidget, Key, Widget, Column,
    Container, Text, ElevatedButton, ClipPath, # Add ClipPath
    Colors, EdgeInsets, MainAxisAlignment, Center, CrossAxisAlignment
)
# Import custom clippers and Path (adjust path if in separate file)
from pythra.drawing import Path, PathClipper, Size # Or wherever Path types are

class MyOvalClipper(PathClipper):
    def __init__(self, key: Optional[Key] = None): # Clippers can have keys if their state matters
        super().__init__()
        self.key = key

    def getClip(self, size: Size) -> Path:
        """Creates an oval path that fits within the given size."""
        width, height = size
        path = Path()
        # Path.addOval expects left, top, width, height
        path.addOval(0, 0, width, height)
        return path

    def shouldReclip(self, oldClipper: 'MyOvalClipper') -> bool:
        # Reclip if the clipper instance itself changes (e.g., different key or type)
        # If MyOvalClipper had properties (e.g., corner_radius), compare them here.
        return self != oldClipper # Default comparison

    def __eq__(self, other): # For shouldReclip and use in style_key for widget if needed
        return isinstance(other, MyOvalClipper) and self.key == other.key

    def __hash__(self):
        return hash((self.__class__, self.key))

    def to_tuple(self): # For make_hashable if clipper instance is part of a style_key
        return (self.__class__, self.key)


class MyStarClipper(PathClipper):
    def __init__(self, points=5, inner_radius_factor=0.4, key: Optional[Key] = None):
        super().__init__()
        self.points = points
        self.inner_radius_factor = inner_radius_factor
        self.key = key

    def getClip(self, size: Size) -> Path:
        path = Path()
        width, height = size
        centerX = width / 2
        centerY = height / 2
        outerRadius = min(width, height) / 2
        innerRadius = outerRadius * self.inner_radius_factor

        # Angle for each of the "outer" points of the star
        angle_step = (2 * math.pi) / self.points
        # Angle for the "inner" points, offset from outer
        inner_angle_offset = angle_step / 2
        
        start_angle = -math.pi / 2 # Start at the top point

        for i in range(self.points):
            # Outer point
            outer_x = centerX + outerRadius * math.cos(start_angle + i * angle_step)
            outer_y = centerY + outerRadius * math.sin(start_angle + i * angle_step)
            if i == 0:
                path.moveTo(outer_x, outer_y)
            else:
                path.lineTo(outer_x, outer_y)

            # Inner point
            inner_x = centerX + innerRadius * math.cos(start_angle + i * angle_step + inner_angle_offset)
            inner_y = centerY + innerRadius * math.sin(start_angle + i * angle_step + inner_angle_offset)
            path.lineTo(inner_x, inner_y)
            
        path.close()
        return path

    def shouldReclip(self, oldClipper: 'MyStarClipper') -> bool:
        return self != oldClipper or \
               self.points != oldClipper.points or \
               self.inner_radius_factor != oldClipper.inner_radius_factor

    def __eq__(self, other):
        return isinstance(other, MyStarClipper) and \
               self.points == other.points and \
               self.inner_radius_factor == other.inner_radius_factor and \
               self.key == other.key

    def __hash__(self):
        return hash((self.__class__, self.points, self.inner_radius_factor, self.key))

    def to_tuple(self):
        return (self.__class__, self.points, self.inner_radius_factor, self.key)



# --- Test State ---
class ClipPathTestState(State):
    def __init__(self):
        super().__init__()
        self.use_star_clipper = False
        self.star_points = 5
        self.clipper_instance = MyOvalClipper(key=Key("oval_clipper"))
        print("ClipPathTestState Initialized")

    def toggle_clipper(self):
        print("ACTION: Toggle Clipper")
        self.use_star_clipper = not self.use_star_clipper
        if self.use_star_clipper:
            self.clipper_instance = MyStarClipper(points=self.star_points, key=Key(f"star_{self.star_points}"))
        else:
            self.clipper_instance = MyOvalClipper(key=Key("oval_clipper"))
        self.setState()

    def change_star_points(self):
        print("ACTION: Change Star Points")
        if self.use_star_clipper: # Only change if star is active
            self.star_points = 7 if self.star_points == 5 else 5
            self.clipper_instance = MyStarClipper(points=self.star_points, key=Key(f"star_{self.star_points}"))
            self.setState()
        else:
            print("  Star clipper not active, toggle first.")


    def build(self) -> Widget:
        print(f"\n--- Building ClipPathTest UI (UseStar: {self.use_star_clipper}, StarPoints: {self.star_points}) ---")

        clipped_content = Container(
            key=Key("clipped_container"),
            width=200, # Fixed size for predictable clipping
            height=150,
            color=Colors.secondaryContainer,
            child=Center( # Assuming Center is refactored
                child=Text(
                    "Clipped!" if not self.use_star_clipper else f"{self.star_points}-Point Star!",
                    key=Key("clipped_text"),
                    style={'fontSize': 20, 'color': Colors.onSecondaryContainer} # Basic style
                )
            )
        )

        return Container(
            key=Key("main_app_container"),
            padding=EdgeInsets.all(20),
            child=Column( # Assuming Column is refactored
                key=Key("main_layout_column"),
                mainAxisAlignment=MainAxisAlignment.START,
                crossAxisAlignment=CrossAxisAlignment.CENTER,
                children=[
                    Text("ClipPath Test", key=Key("header_text"), style={'fontSize': 24}),
                    Container(height=20), # Spacer

                    ClipPath(
                        key=Key("my_clip_path"),
                        clipper=self.clipper_instance, # Pass the current clipper
                        child=clipped_content
                    ),
                    Container(height=20),

                    ElevatedButton(
                        key=Key("toggle_clipper_btn"),
                        child=Text("Toggle Clipper (Oval/Star)"),
                        onPressed=self.toggle_clipper,
                        onPressedName="toggle_clipper_callback"
                    ),
                    Container(height=10),
                    ElevatedButton(
                        key=Key("change_star_btn"),
                        child=Text("Change Star Points (5/7)"),
                        onPressed=self.change_star_points,
                        onPressedName="change_star_points_callback"
                    )
                ]
            )
        )

# --- App Definition ---
class ClipApp(StatefulWidget):
    def createState(self) -> ClipPathTestState:
        return ClipPathTestState()

# --- Application Runner ---
class Application:
    def __init__(self):
        self.framework = Framework()
        self.my_app = ClipApp(key=Key("clip_test_app"))
        self.state_instance: Optional[ClipPathTestState] = None

    def schedule_tests(self):
        if not self.state_instance: return

        print("\n>>> Scheduling ClipPath Test Sequence <<<")
        QTimer.singleShot(2000, lambda: print("\n--- Initial State (Oval Clip) ---"))
        QTimer.singleShot(4000, self.state_instance.toggle_clipper) # Oval -> Star (5 points)
        QTimer.singleShot(7000, self.state_instance.change_star_points) # Star (5 points) -> Star (7 points)
        QTimer.singleShot(10000, self.state_instance.toggle_clipper) # Star (7 points) -> Oval
        QTimer.singleShot(12000, lambda: print("\n>>> ClipPath Test Sequence Complete <<<"))

    def run(self):
        self.framework.set_root(self.my_app)
        if isinstance(self.my_app, StatefulWidget): self.state_instance = self.my_app.get_state()
        QTimer.singleShot(0, self.schedule_tests)
        self.framework.run(title='ClipPath Test')

# --- Main Execution ---
if __name__ == "__main__":
    app_runner = Application()
    app_runner.run()