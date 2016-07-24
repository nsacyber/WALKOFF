
# Copyright (c) 2015 Tanium Inc
#
# Generated from console.wsdl version 0.0.1     
#
#

from .base import BaseType


class ParameterList(BaseType):

    _soap_tag = 'parameters'

    def __init__(self):
        BaseType.__init__(
            self,
            simple_properties={},
            complex_properties={},
            list_properties={'parameter': Parameter},
        )
        
        
        self.parameter = []

from parameter import Parameter

