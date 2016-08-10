
# Copyright (c) 2015 Tanium Inc
#
# Generated from console.wsdl version 0.0.1     
#
#

from .base import BaseType


class CacheInfo(BaseType):

    _soap_tag = 'cache_info'

    def __init__(self):
        BaseType.__init__(
            self,
            simple_properties={'cache_id': int,
                        'page_row_count': int,
                        'filtered_row_count': int,
                        'cache_row_count': int,
                        'expiration': str},
            complex_properties={'errors': ErrorList},
            list_properties={},
        )
        self.cache_id = None
        self.page_row_count = None
        self.filtered_row_count = None
        self.cache_row_count = None
        self.expiration = None
        self.errors = None
        

from error_list import ErrorList

