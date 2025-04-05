import yaml

class Config:
    """
    A Singleton class for managing configuration settings loaded from a YAML file.

    Attributes:
        _instance (Config): The single instance of the Config class.
        initialized (bool): Indicates if the instance has been initialized.
        config (dict): A dictionary holding the configuration settings.
    """

    _instance = None  # Class-level attribute to store the single instance

    def __new__(cls, *args, **kwargs):
        """
        Create or return the single instance of the Config class.

        Returns:
            Config: The singleton instance of the Config class.
        """
        if cls._instance is None:
            # If an instance doesn't exist, create one
            cls._instance = super(Config, cls).__new__(cls)
        return cls._instance  # Return the singleton instance

    def __init__(self, config_file='config.yaml'):
        """
        Initialize the Config instance by loading settings from a YAML file.

        Args:
            config_file (str): Path to the YAML configuration file. Defaults to 'config.yaml'.
        """
        # Only initialize the instance once
        if not hasattr(self, 'initialized'):
            self.initialized = True  # Mark the instance as initialized
            with open(config_file, 'r') as file:
                self.config = yaml.safe_load(file)

    def get(self, key, default=None):
        """
        Retrieve a configuration value by its key.

        Args:
            key (str): The key for the desired configuration value.
            default (any, optional): The default value to return if the key is not found. Defaults to None.

        Returns:
            any: The value associated with the key, or the default value if the key is not found.
        """
        return self.config.get(key, default)

