
# Copyright (c) 2015 Tanium Inc
#
# Generated from console.wsdl version 0.0.1     
#
#

from .base import BaseType


class SoapError(BaseType):

    _soap_tag = 'soap_error'

    def __init__(self):
        BaseType.__init__(
            self,
            simple_properties={'object_name': str,
                        'exception_name': str,
                        'context': str,
                        'object_request': str},
            complex_properties={},
            list_properties={},
        )
        self.object_name = None
        self.exception_name = None
        self.context = None
        self.object_request = None
        
        



