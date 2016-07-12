
# Copyright (c) 2015 Tanium Inc
#
# Generated from console.wsdl version 0.0.1     
#
#

from .base import BaseType


class PluginArgumentList(BaseType):

    _soap_tag = 'arguments'

    def __init__(self):
        BaseType.__init__(
            self,
            simple_properties={},
            complex_properties={},
            list_properties={'argument': PluginArgument},
        )
        
        
        self.argument = []

from plugin_argument import PluginArgument

