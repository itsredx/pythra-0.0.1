# main.py

import sys
from typing import Optional, Set, List, Dict, TYPE_CHECKING, Callable, Any, Union
from pythra import *

# --- Component 1: A Reusable STATELESS Widget ---
# This widget just displays a piece of data. It has no internal state.
class GreetingCard(StatelessWidget):
    def __init__(self, name: str, key: Optional[Key] = None):
        super().__init__(key=key)
        self.name = name

    def build(self) -> Widget:
        return Container(
            padding=EdgeInsets.all(16),
            decoration=BoxDecoration(
                color=Colors.surfaceVariant,
                borderRadius=BorderRadius.all(8)
            ),
            child=Text(f"Hello, {self.name}!", style=TextStyle(fontSize=20))
        )

# --- Component 2: A Reusable STATEFUL Widget ---
# This widget manages its own internal counter state.
class CounterWidget(StatefulWidget):
    def __init__(self, initial_value: int = 0, key: Optional[Key] = None):
        super().__init__(key=key)
        self.initial_value = initial_value

    def createState(self) -> "CounterWidgetState":
        return CounterWidgetState()

class CounterWidgetState(State[CounterWidget]):
    def __init__(self):
        super().__init__()
        self.count = 0

    def initState(self):
        # NEW: Lifecycle method. Set initial state from the widget's config.
        self.count = self.get_widget().initial_value

    def increment(self):
        self.count += 1
        print("count: ",self.count)
        self.setState()

    def build(self) -> Widget:
        return Row(
            mainAxisAlignment=MainAxisAlignment.SPACE_BETWEEN,
            children=[
                Text(f"Private Counter: {self.count}"),
                ElevatedButton(
                    child=Text("+"),
                    onPressed=self.increment
                )
            ]
        )

# --- The Main Application State ---
class MainAppState(State):
    def __init__(self):
        super().__init__()
        self.show_greeting = True

    def toggle_greeting(self):
        self.show_greeting = not self.show_greeting
        self.setState()

    def build(self) -> Widget:
        # The main build method now composes other custom components.
        return Container(
            padding=EdgeInsets.all(24),
            alignment=Alignment.top_center(),
            child=Column(
                # spacing=20,
                crossAxisAlignment=CrossAxisAlignment.CENTER,
                children=[
                    Text("Pythra Component Model", style=TextStyle(fontSize=32, fontWeight='bold')),
                    
                    # Nesting a STATELESS widget
                    GreetingCard(name="Developer") if self.show_greeting else SizedBox(height=20),
                    
                    # Nesting a STATEFUL widget
                    CounterWidget(key=Key("counter1"), initial_value=10),
                    
                    # Nesting another, independent STATEFUL widget
                    CounterWidget(key=Key("counter2"), initial_value=100),

                    ElevatedButton(
                        child=Text("Toggle GreetingCard"),
                        onPressed=self.toggle_greeting
                    )
                ]
            )
        )

# --- App Definition ---
class MyApp(StatefulWidget):
    def createState(self) -> MainAppState:
        return MainAppState()

# --- Run ---
if __name__ == "__main__":
    app = Framework.instance()
    app.set_root(MyApp())
    app.run(title="Pythra Composition Test")