
# Copyright (c) 2015 Tanium Inc
#
# Generated from console.wsdl version 0.0.1     
#
#

from .base import BaseType


class SystemSettingList(BaseType):

    _soap_tag = 'system_settings'

    def __init__(self):
        BaseType.__init__(
            self,
            simple_properties={},
            complex_properties={'cache_info': CacheInfo},
            list_properties={'system_setting': SystemSetting},
        )
        
        self.cache_info = None
        self.system_setting = []

from system_setting import SystemSetting
from cache_info import CacheInfo

