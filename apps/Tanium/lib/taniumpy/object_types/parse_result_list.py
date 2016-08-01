
# Copyright (c) 2015 Tanium Inc
#
# Generated from console.wsdl version 0.0.1     
#
#

from .base import BaseType


class ParseResultList(BaseType):

    _soap_tag = 'parse_results'

    def __init__(self):
        BaseType.__init__(
            self,
            simple_properties={},
            complex_properties={},
            list_properties={'parse_result': ParseResult},
        )
        
        
        self.parse_result = []

from parse_result import ParseResult

