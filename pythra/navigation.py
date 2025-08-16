# In a new file: pythra/navigation.py
from .state import StatefulWidget, State, StatelessWidget
from .widgets import Stack, Key
from .base import Widget
from typing import Callable, List, Dict, Any, Optional
import weakref

class PageRoute:
    # The builder now accepts the navigator state as an argument
    def __init__(self, builder: Callable[['NavigatorState'], Widget], name: str = None):
        self.builder = builder
        self.name = name
        self.widget_instance = None

    # The build method will pass the state to the builder
    def build(self, navigator_state: 'NavigatorState') -> Widget:
        if not self.widget_instance:
            self.widget_instance = self.builder(navigator_state)
        return self.widget_instance

class NavigatorState(State):
    def initState(self):
        self.history: List[PageRoute] = [self.get_widget().initialRoute]
        
    def push(self, route: PageRoute):
        self.history.append(route)
        self.setState()

    def pop(self):
        if len(self.history) > 1:
            self.history.pop()
            self.setState()
            
    def build(self) -> Widget:
        if not self.history:
            return Container(color=Colors.black, child=Text("Error: Navigation stack is empty."))

        active_route = self.history[-1]
        
        # Pass `self` (the NavigatorState instance) to the route's build method
        return active_route.build(self)

class Navigator(StatefulWidget):
    # We no longer need the static state reference here.

    # @staticmethod
    # def of(widget: Widget) -> Optional['NavigatorState']:
    #     """
    #     Finds the nearest NavigatorState ancestor in the widget's context.
    #     This now delegates the lookup to the framework.
    #     """
    #     if not widget.framework:
    #         raise Exception("Cannot find Navigator: Widget is not attached to the framework.")
        
    #     # Ask the framework to find the state for us
    #     return widget.framework.find_ancestor_state_of_type(widget, NavigatorState)

    def __init__(self, key: Key, initialRoute: PageRoute, routes: Dict[str, Callable[[], Widget]] = None):
        self.initialRoute = initialRoute
        self.routes = routes or {}
        super().__init__(key=key)

    def createState(self) -> NavigatorState:
        # The state is created normally. The framework will track its location.
        return NavigatorState()