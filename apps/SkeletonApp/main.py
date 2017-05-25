import logging
from apps import App


logger = logging.getLogger(__name__)

class Main(App):
    """
       Skeleton example app to build other apps off of
    
       Args:
           name (str): Name of the app
           device (list[str]): List of associated device names
           
    """
    def __init__(self, name=None, device=None):
        App.__init__(self, name, device)    #Required to call superconstructor

    def test_function(self):
        """
           Basic self contained function
        """
        return {}

    def test_function_with_param(self, args={}):
        """
           Basic function that takes in a parameter

           Args:
               test_param (str): String that will be returned
        """
        return args["test_param"]

    def test_function_with_object_reference(self):
        """
           Basic function that calls an instance variable.  In this case, a device name. 
        """
        return self.get_device().username
