
# Copyright (c) 2015 Tanium Inc
#
# Generated from console.wsdl version 0.0.1     
#
#

from .base import BaseType


class XmlError(BaseType):

    _soap_tag = 'error'

    def __init__(self):
        BaseType.__init__(
            self,
            simple_properties={'type': str,
                        'exception': str,
                        'error_context': str},
            complex_properties={},
            list_properties={},
        )
        self.type = None
        self.exception = None
        self.error_context = None
        
        



