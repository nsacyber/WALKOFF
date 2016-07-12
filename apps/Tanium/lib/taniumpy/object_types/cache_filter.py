
# Copyright (c) 2015 Tanium Inc
#
# Generated from console.wsdl version 0.0.1     
#
#

from .base import BaseType


class CacheFilter(BaseType):

    _soap_tag = 'filter'

    def __init__(self):
        BaseType.__init__(
            self,
            simple_properties={'field': str,
                        'value': str,
                        'type': str,
                        'operator': str,
                        'not_flag': int},
            complex_properties={},
            list_properties={},
        )
        self.field = None
        self.value = None
        self.type = None
        self.operator = None
        self.not_flag = None
        
        



