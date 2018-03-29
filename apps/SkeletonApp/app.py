import logging

from apps import App, action

logger = logging.getLogger(__name__)


@action
def test_global_action(data):
    return data


class SkeletonApp(App):
    """
       Skeleton example app to build other apps off of
    
       Args:
           name (str): Name of the app
           device (list[str]): List of associated device names
           
    """

    def __init__(self, name=None, device=None):
        App.__init__(self, name, device)  # Required to call superconstructor

    @action
    def test_function(self):
        """
           Basic self contained function
        """
        return {}

    @action
    def test_function_with_param(self, test_param):
        """
           Basic function that takes in a parameter

           Args:
               test_param (str): String that will be returned
        """
        return test_param

    @action
    def test_function_with_device_reference(self):
        """
           Basic function that calls an instance variable.  In this case, a device name. 
        """
        # password = self.get_device().get_encrypted_field('password'); do not store this variable in cache
        return self.device_fields['username']
