
# Copyright (c) 2015 Tanium Inc
#
# Generated from console.wsdl version 0.0.1     
#
#

from .base import BaseType


class ActionStop(BaseType):

    _soap_tag = 'action_stop'

    def __init__(self):
        BaseType.__init__(
            self,
            simple_properties={'id': int},
            complex_properties={'action': Action},
            list_properties={},
        )
        self.id = None
        self.action = None
        

from action import Action

