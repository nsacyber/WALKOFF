
# Copyright (c) 2015 Tanium Inc
#
# Generated from console.wsdl version 0.0.1     
#
#

from .base import BaseType


class SensorList(BaseType):

    _soap_tag = 'sensors'

    def __init__(self):
        BaseType.__init__(
            self,
            simple_properties={},
            complex_properties={'cache_info': CacheInfo},
            list_properties={'sensor': Sensor},
        )
        
        self.cache_info = None
        self.sensor = []

from sensor import Sensor
from cache_info import CacheInfo

