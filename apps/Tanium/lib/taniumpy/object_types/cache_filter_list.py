
# Copyright (c) 2015 Tanium Inc
#
# Generated from console.wsdl version 0.0.1     
#
#

from .base import BaseType


class CacheFilterList(BaseType):

    _soap_tag = 'cache_filters'

    def __init__(self):
        BaseType.__init__(
            self,
            simple_properties={},
            complex_properties={},
            list_properties={'filter': CacheFilter},
        )
        
        
        self.filter = []

from cache_filter import CacheFilter

