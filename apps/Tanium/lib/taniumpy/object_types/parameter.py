
# Copyright (c) 2015 Tanium Inc
#
# Generated from console.wsdl version 0.0.1     
#
#

from .base import BaseType


class Parameter(BaseType):

    _soap_tag = 'parameter'

    def __init__(self):
        BaseType.__init__(
            self,
            simple_properties={'key': str,
                        'value': str,
                        'type': int},
            complex_properties={},
            list_properties={},
        )
        self.key = None
        self.value = None
        self.type = None
        
        



