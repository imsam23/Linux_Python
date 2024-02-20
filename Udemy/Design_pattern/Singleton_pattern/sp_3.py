#  singleton class for Configuration settings
import json


class SingletonMeta(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


class Configuration(metaclass=SingletonMeta):
    def __init__(self, filename="config.json"):
        try:
            with open(filename, "r") as f:
                self._settings = json.load(f)
        except FileNotFoundError:
            print("Configuration file not found. Using defaults.")
            self._settings = {}

    def get_setting(self, key, default=None):
        return self._settings.get(key, default)

    def set_setting(self, key, value):
        self._settings[key] = value

    def save_settings(self, filename="config.json"):
        with open(filename, "w") as f:
            json.dump(self._settings, f, indent=4)

# Access the singleton instance
config = Configuration()  # Load settings from "config.json"

# Get a setting
api_key = config.get_setting("api_key")

# Set a setting
config.set_setting("timeout", 30)

# Save settings back to the file (optional)
config.save_settings()

