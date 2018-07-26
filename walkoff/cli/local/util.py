import os
from walkoff import config


def load_config(config_path):
    if not config_path:
        config_path = os.getcwd()
    if os.path.isdir(config_path):
        config_path = os.path.join(config_path, "data", "walkoff.config")
    config.Config.load_config(config_path)


def clean_pycache(directory, verbosity):
    for root, dirnames, filenames in os.walk(directory):
        for filename in filenames:
            if filename.endswith((".pyc", ".pyo")):
                if verbosity > 2:
                    print("Removing: " + os.path.join(root, filename))
                os.remove(os.path.join(root, filename))