
# Copyright (c) 2015 Tanium Inc
#
# Generated from console.wsdl version 0.0.1     
#
#

from .base import BaseType


class ParseResult(BaseType):

    _soap_tag = 'parse_result'

    def __init__(self):
        BaseType.__init__(
            self,
            simple_properties={'id': int,
                        'parameter_definition': str},
            complex_properties={'parameters': ParameterList},
            list_properties={},
        )
        self.id = None
        self.parameter_definition = None
        self.parameters = None
        

from parameter_list import ParameterList

