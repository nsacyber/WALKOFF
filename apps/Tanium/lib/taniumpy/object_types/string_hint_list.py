
# Copyright (c) 2015 Tanium Inc
#
# Generated from console.wsdl version 0.0.1     
#
#

from .base import BaseType


class StringHintList(BaseType):

    _soap_tag = 'string_hints'

    def __init__(self):
        BaseType.__init__(
            self,
            simple_properties={},
            complex_properties={},
            list_properties={'string_hint': str},
        )
        
        
        self.string_hint = []



