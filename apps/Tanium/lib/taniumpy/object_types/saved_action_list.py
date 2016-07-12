
# Copyright (c) 2015 Tanium Inc
#
# Generated from console.wsdl version 0.0.1     
#
#

from .base import BaseType


class SavedActionList(BaseType):

    _soap_tag = 'saved_actions'

    def __init__(self):
        BaseType.__init__(
            self,
            simple_properties={},
            complex_properties={'cache_info': CacheInfo},
            list_properties={'saved_action': SavedAction},
        )
        
        self.cache_info = None
        self.saved_action = []

from saved_action import SavedAction
from cache_info import CacheInfo

