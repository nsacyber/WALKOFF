
# Copyright (c) 2015 Tanium Inc
#
# Generated from console.wsdl version 0.0.1     
#
#

from .base import BaseType


class ErrorList(BaseType):

    _soap_tag = 'errors'

    def __init__(self):
        BaseType.__init__(
            self,
            simple_properties={},
            complex_properties={},
            list_properties={'error': XmlError},
        )
        
        
        self.error = []

from xml_error import XmlError

