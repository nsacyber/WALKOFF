
# Copyright (c) 2015 Tanium Inc
#
# Generated from console.wsdl version 0.0.1     
#
#

from .base import BaseType


class ParseResultGroupList(BaseType):

    _soap_tag = 'parse_result_groups'

    def __init__(self):
        BaseType.__init__(
            self,
            simple_properties={},
            complex_properties={},
            list_properties={'parse_result_group': ParseResultGroup},
        )
        
        
        self.parse_result_group = []

from parse_result_group import ParseResultGroup

