# In a new file pythra/events.py or at the top of pythra/styles.py

from dataclasses import dataclass

@dataclass
class TapDetails:
    """Details for a tap event."""
    # Could be expanded with position if needed later
    pass

@dataclass
class PanUpdateDetails:
    """Details for a pan (drag) update event."""
    dx: float  # Change in x since the pan started
    dy: float  # Change in y since the pan started