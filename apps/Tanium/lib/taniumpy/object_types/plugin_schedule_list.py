
# Copyright (c) 2015 Tanium Inc
#
# Generated from console.wsdl version 0.0.1     
#
#

from .base import BaseType


class PluginScheduleList(BaseType):

    _soap_tag = 'plugin_schedules'

    def __init__(self):
        BaseType.__init__(
            self,
            simple_properties={},
            complex_properties={'cache_info': CacheInfo},
            list_properties={'plugin_schedule': PluginSchedule},
        )
        
        self.cache_info = None
        self.plugin_schedule = []

from plugin_schedule import PluginSchedule
from cache_info import CacheInfo

