# id_manager.py
class IDManager:
    """
    A class to manage and generate unique IDs for widgets.

    This class provides functionality to generate unique IDs in the format 'widget_<counter>',
    where the counter is incremented each time an ID is generated. It also provides the option to 
    reset the ID counter and clear the stored IDs.

    Attributes:
        ids (dict): A dictionary to track the generated IDs.
        counter (int): A counter to ensure unique ID generation.

    Methods:
        generate_id():
            Generates and returns a new unique ID in the format 'widget_<counter>'.
        
        reset():
            Resets the ID counter and clears the stored IDs.
    """
    def __init__(self):
        """
        Initializes an empty dictionary to store generated IDs and sets the counter to 0.
        """
        self.ids = {}
        self.counter = 0

    def generate_id(self):
        """
        Generates a unique ID in the format 'widget_<counter>' and stores it in the 'ids' dictionary.

        Returns:
            str: A unique widget ID.
        """
        self.counter += 1
        new_id = f"widget_{self.counter}"
        self.ids[new_id] = True
        return new_id

    def reset(self):
        """
        Resets the ID counter to 0 and clears the stored IDs.

        This method is useful when starting fresh or clearing all the generated IDs.
        """
        self.ids.clear()
        self.counter = 0
