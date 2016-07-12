
# Copyright (c) 2015 Tanium Inc
#
# Generated from console.wsdl version 0.0.1     
#
#

from .base import BaseType


class ComputerGroupSpec(BaseType):

    _soap_tag = 'computer_spec'

    def __init__(self):
        BaseType.__init__(
            self,
            simple_properties={'id': int,
                        'computer_name': str,
                        'ip_address': str},
            complex_properties={},
            list_properties={},
        )
        self.id = None
        self.computer_name = None
        self.ip_address = None
        
        



