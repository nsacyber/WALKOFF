
# Copyright (c) 2015 Tanium Inc
#
# Generated from console.wsdl version 0.0.1     
#
#

from .base import BaseType


class SelectList(BaseType):

    _soap_tag = 'selects'

    def __init__(self):
        BaseType.__init__(
            self,
            simple_properties={},
            complex_properties={},
            list_properties={'select': Select},
        )
        
        
        self.select = []

from select import Select

