
# Copyright (c) 2015 Tanium Inc
#
# Generated from console.wsdl version 0.0.1     
#
#

from .base import BaseType


class PluginArgument(BaseType):

    _soap_tag = 'argument'

    def __init__(self):
        BaseType.__init__(
            self,
            simple_properties={'name': str,
                        'type': str,
                        'value': str},
            complex_properties={},
            list_properties={},
        )
        self.name = None
        self.type = None
        self.value = None
        
        



