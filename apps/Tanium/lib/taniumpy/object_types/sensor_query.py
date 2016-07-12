
# Copyright (c) 2015 Tanium Inc
#
# Generated from console.wsdl version 0.0.1     
#
#

from .base import BaseType


class SensorQuery(BaseType):

    _soap_tag = 'query'

    def __init__(self):
        BaseType.__init__(
            self,
            simple_properties={'platform': str,
                        'script': str,
                        'script_type': str,
                        'signature': str},
            complex_properties={},
            list_properties={},
        )
        self.platform = None
        self.script = None
        self.script_type = None
        self.signature = None
        
        



