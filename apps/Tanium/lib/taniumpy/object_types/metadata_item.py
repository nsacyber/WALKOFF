
# Copyright (c) 2015 Tanium Inc
#
# Generated from console.wsdl version 0.0.1     
#
#

from .base import BaseType


class MetadataItem(BaseType):

    _soap_tag = 'item'

    def __init__(self):
        BaseType.__init__(
            self,
            simple_properties={'name': str,
                        'value': str,
                        'admin_flag': int},
            complex_properties={},
            list_properties={},
        )
        self.name = None
        self.value = None
        self.admin_flag = None
        
        



