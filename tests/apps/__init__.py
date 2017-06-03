from apps import *


@classmethod
def modified_get_app_name(cls):
    try:
        return cls.__module__.split('.')[2]
    except IndexError:
        return None

# Patch the metaclass to accept different directory structure
App._get_app_name = modified_get_app_name
