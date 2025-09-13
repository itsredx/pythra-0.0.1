# =============================================================================
# PYTHRA EVENTS SYSTEM - The "User Interaction Tracker" for Touch and Mouse
# =============================================================================
"""
PyThra Events System - Handle User Interactions

This is PyThra's "interaction detective" that captures and describes what users
do with their fingers, mouse, or other input devices. When users tap, drag, swipe,
or gesture, this system creates detailed "event reports" that your app can respond to.

**What kinds of interactions does this handle?**
- Taps and clicks (single finger touches or mouse clicks)
- Pan gestures (dragging with finger or mouse)
- Swipes and drags across the screen
- Future: pinch-to-zoom, rotation, multi-touch gestures

**Real-world analogy:**
Like a security guard with a clipboard who writes detailed reports:
- "At 10:15 AM, person tapped the red button"
- "At 10:16 AM, person dragged their finger 50 pixels to the right"
- "At 10:17 AM, person swiped quickly upward"

**How it works:**
1. **User Acts**: User taps, drags, or gestures on the screen
2. **Event Created**: PyThra creates a detailed "event report" object
3. **Details Captured**: Position, movement, timing, and other data are recorded
4. **Handler Called**: Your app's event handler function receives the report
5. **App Responds**: Your code decides what to do based on the interaction

**Key event types:**
- **TapDetails**: Information about taps/clicks
- **PanUpdateDetails**: Information about drag/swipe gestures

**Usage in widgets:**
```python
def handle_tap(tap_details: TapDetails):
    print("User tapped something!")
    # React to the tap - maybe increment a counter, show a dialog, etc.

def handle_drag(pan_details: PanUpdateDetails):
    print(f"User dragged {pan_details.dx} pixels horizontally")
    # React to the drag - maybe move an object, scroll content, etc.

# Use in a widget
GestureDetector(
    child=Container(width=100, height=100, color="blue"),
    onTap=handle_tap,
    onPanUpdate=handle_drag
)
```
"""

from dataclasses import dataclass

# =============================================================================
# TAP DETAILS - Information About Single Taps/Clicks
# =============================================================================

@dataclass
class TapDetails:
    """
    The "tap report" - contains information about a single tap or click event.
    
    **What is TapDetails?**
    When a user taps the screen or clicks with their mouse, PyThra creates a
    TapDetails object to describe exactly what happened. Think of it like a
    "police report" for the tap event.
    
    **Real-world analogy:**
    Like a receipt from a store transaction:
    - "Customer tapped the 'Buy Now' button"
    - "Location: Button in top-right corner"
    - "Time: 2:34 PM"
    - "Device: Smartphone touchscreen"
    
    **What information does it contain?**
    Currently basic (can be expanded in the future):
    - Event occurred (the fact that a tap happened)
    - Future: tap position (x, y coordinates)
    - Future: tap pressure (how hard they pressed)
    - Future: device type (finger, mouse, stylus)
    
    **When is this used?**
    - Button clicks and interactions
    - Menu item selections
    - Image or card taps
    - Any single "press and release" action
    
    **Example usage:**
    ```python
    def on_button_tapped(tap_details: TapDetails):
        print("Button was tapped!")
        # Here you could check tap_details for more info if needed
        # For now it's just confirmation that the tap happened
        increment_counter()
        show_success_message()
    
    # Wire it up to a button
    TextButton(
        child=Text("Tap Me!"),
        onPressed=on_button_tapped  # Pass the TapDetails object
    )
    ```
    
    **Note:** This is a "dataclass" which means it's like a simple container
    for data. Currently it doesn't hold any specific fields, but it's set up
    to be extended with tap position, timing, and other details in the future.
    """
    # Currently no fields, but ready to be expanded with:
    # x: float = 0  # X coordinate of the tap
    # y: float = 0  # Y coordinate of the tap
    # timestamp: float = 0  # When the tap occurred
    # pressure: float = 0  # How hard they pressed (if supported)
    pass

# =============================================================================
# PAN UPDATE DETAILS - Information About Drag/Swipe Gestures
# =============================================================================

@dataclass
class PanUpdateDetails:
    """
    The "drag report" - contains information about drag, swipe, and pan gestures.
    
    **What is PanUpdateDetails?**
    When a user drags their finger or mouse across the screen, PyThra creates
    PanUpdateDetails to describe the movement. "Pan" means "move around" - like
    panning a camera to look at different parts of a scene.
    
    **Real-world analogy:**
    Like a GPS giving you directions:
    - "You've moved 25 feet east from your starting point"
    - "You've moved 10 feet north from your starting point"
    - Instead of feet, we measure in pixels on the screen
    
    **What information does it contain?**
    - **dx**: How far moved horizontally since the drag started (in pixels)
    - **dy**: How far moved vertically since the drag started (in pixels)
    - Positive dx = moved right, negative dx = moved left
    - Positive dy = moved down, negative dy = moved up
    
    **When is this used?**
    - Dragging objects around the screen
    - Scrolling content (swipe to scroll)
    - Drawing apps (following finger movement)
    - Sliders and range controls
    - Image pan/zoom interactions
    
    **Example usage:**
    ```python
    def on_user_drags(pan_details: PanUpdateDetails):
        print(f"User dragged {pan_details.dx} pixels right")
        print(f"User dragged {pan_details.dy} pixels down")
        
        # Move an object based on the drag
        object_x += pan_details.dx
        object_y += pan_details.dy
        
        # Or scroll content
        scroll_offset_x = pan_details.dx
        scroll_offset_y = pan_details.dy
        
        # Update the UI to show the new position
        setState()  # Trigger a UI rebuild
    
    # Wire it up to a draggable area
    GestureDetector(
        child=Container(width=200, height=200, color="green"),
        onPanUpdate=on_user_drags
    )
    ```
    
    **Key concepts:**
    - **dx/dy are cumulative**: They show total movement from the start of the drag
    - **Not velocity**: These show distance moved, not speed
    - **Pixel coordinates**: Measured in screen pixels
    - **Updates frequently**: You get many PanUpdateDetails as the user drags
    
    Args:
        dx: Total horizontal distance moved since drag started (pixels)
        dy: Total vertical distance moved since drag started (pixels)
    """
    dx: float  # Change in x since the pan started (positive = moved right)
    dy: float  # Change in y since the pan started (positive = moved down)
