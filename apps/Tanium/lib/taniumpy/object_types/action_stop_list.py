
# Copyright (c) 2015 Tanium Inc
#
# Generated from console.wsdl version 0.0.1     
#
#

from .base import BaseType


class ActionStopList(BaseType):

    _soap_tag = 'action_stops'

    def __init__(self):
        BaseType.__init__(
            self,
            simple_properties={},
            complex_properties={},
            list_properties={'action_stop': ActionStop},
        )
        
        
        self.action_stop = []

from action_stop import ActionStop

