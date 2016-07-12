
# Copyright (c) 2015 Tanium Inc
#
# Generated from console.wsdl version 0.0.1     
#
#

from .base import BaseType


class PackageSpecList(BaseType):

    _soap_tag = 'package_specs'

    def __init__(self):
        BaseType.__init__(
            self,
            simple_properties={},
            complex_properties={'cache_info': CacheInfo},
            list_properties={'package_spec': PackageSpec},
        )
        
        self.cache_info = None
        self.package_spec = []

from package_spec import PackageSpec
from cache_info import CacheInfo

