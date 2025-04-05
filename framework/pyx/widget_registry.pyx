cdef class WidgetRegistry:
    cdef dict _registry  # Internal dictionary to store widgets

    def __init__(self):
        self._registry = {}

    # Allow widget_data to be any Python object (e.g., function, class instance)
    def add_widget(self, str widget_id, object widget_data):
        """Add a widget to the registry."""
        self._registry[widget_id] = widget_data

    def update_widget(self, str widget_id, object widget_data):
        """Update a widget in the registry."""
        self._registry[widget_id] = widget_data

    def get_widget(self, str widget_id):
        """Retrieve a widget from the registry."""
        return self._registry.get(widget_id)

    def delete_widget(self, str widget_id):
        """Delete a widget from the registry."""
        if widget_id in self._registry:
            del self._registry[widget_id]

    def get_size(self):
        """Return the size of the registry."""
        return len(self._registry)

    def get_all_widgets(self):
        """Return all widgets in the registry."""
        return {widget_id: widget_object for widget_id, widget_object in self._registry.items()}
