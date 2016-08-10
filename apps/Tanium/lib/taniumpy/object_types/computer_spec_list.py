
# Copyright (c) 2015 Tanium Inc
#
# Generated from console.wsdl version 0.0.1     
#
#

from .base import BaseType


class ComputerSpecList(BaseType):

    _soap_tag = 'computer_specs'

    def __init__(self):
        BaseType.__init__(
            self,
            simple_properties={},
            complex_properties={'cache_info': CacheInfo},
            list_properties={'computer_spec': ComputerGroupSpec},
        )
        
        self.cache_info = None
        self.computer_spec = []

from computer_group_spec import ComputerGroupSpec
from cache_info import CacheInfo

