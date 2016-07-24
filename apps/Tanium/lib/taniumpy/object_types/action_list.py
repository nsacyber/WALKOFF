
# Copyright (c) 2015 Tanium Inc
#
# Generated from console.wsdl version 0.0.1     
#
#

from .base import BaseType


class ActionList(BaseType):

    _soap_tag = 'actions'

    def __init__(self):
        BaseType.__init__(
            self,
            simple_properties={},
            complex_properties={'info': ActionListInfo,
                        'cache_info': CacheInfo},
            list_properties={'action': Action},
        )
        
        self.info = None
        self.cache_info = None
        self.action = []

from action_list_info import ActionListInfo
from action import Action
from cache_info import CacheInfo

