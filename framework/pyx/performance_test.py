import time
from widget_registry import WidgetRegistry

class MyWidget:
    def __init__(self, name):
        self.name = name

    def render(self):
        return f"<div>{self.name}</div>"

def some_function():
    return "I am a callable function!"

def test_widget_registry_performance(num_widgets=10):
    registry = WidgetRegistry()

    # Start timing for adding widgets
    start_time = time.time()

    # Add widgets to the registry
    for i in range(num_widgets):
        widget_object = MyWidget(name=f"My First Widget{i}")
        registry.add_widget(f"id_i", widget_object)

    # Time taken to add widgets
    add_time = time.time() - start_time
    print(f"Time to add {num_widgets} widgets: {add_time:.4f} seconds")
    print("Added Widgets:")
    #print(registry.get_all_widgets())

    # Start timing for updates
    start_time = time.time()

    # Update widgets in the registry
    for i in range(num_widgets):
        updated_widget_object = some_function
        registry.update_widget(f"id_i", updated_widget_object)

    # Time taken to update widgets
    update_time = time.time() - start_time
    print(f"Time to update {num_widgets} widgets: {update_time:.4f} seconds")
    print("Updated Widgets:")
    #print(registry.get_all_widgets())

    # Start timing for retrieval
    start_time = time.time()

    # Retrieve all widgets from the registry
    for i in range(num_widgets):
        widget_html = registry.get_widget(f"id_i")
        #print(widget_html)

    # Time taken to retrieve widgets
    retrieval_time = time.time() - start_time
    print(f"Time to retrieve {num_widgets} widgets: {retrieval_time:.4f} seconds")

    # Start timing for deletions
    start_time = time.time()

    # Delete all widgets from the registry
    for i in range(num_widgets):
        registry.delete_widget(f"id_i")

    # Time taken to delete widgets
    delete_time = time.time() - start_time
    print(f"Time to delete {num_widgets} widgets: {delete_time:.4f} seconds")
    print("Deleted Widgets:")
    #print(registry.get_all_widgets())  # Should show an empty registry

if __name__ == "__main__":
    test_widget_registry_performance(num_widgets=1000)
