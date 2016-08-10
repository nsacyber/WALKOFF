
# Copyright (c) 2015 Tanium Inc
#
# Generated from console.wsdl version 0.0.1     
#
#

from .base import BaseType


class SystemStatusList(BaseType):

    _soap_tag = 'system_status'

    def __init__(self):
        BaseType.__init__(
            self,
            simple_properties={},
            complex_properties={'aggregate': SystemStatusAggregate,
                        'cache_info': CacheInfo},
            list_properties={'client_status': ClientStatus},
        )
        
        self.aggregate = None
        self.cache_info = None
        self.client_status = []

from client_status import ClientStatus
from system_status_aggregate import SystemStatusAggregate
from cache_info import CacheInfo

