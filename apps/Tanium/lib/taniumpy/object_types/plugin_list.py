
# Copyright (c) 2015 Tanium Inc
#
# Generated from console.wsdl version 0.0.1     
#
#

from .base import BaseType


class PluginList(BaseType):

    _soap_tag = 'plugins'

    def __init__(self):
        BaseType.__init__(
            self,
            simple_properties={},
            complex_properties={'cache_info': CacheInfo},
            list_properties={'plugin': Plugin},
        )
        
        self.cache_info = None
        self.plugin = []

from plugin import Plugin
from cache_info import CacheInfo

