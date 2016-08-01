
# Copyright (c) 2015 Tanium Inc
#
# Generated from console.wsdl version 0.0.1     
#
#

from .base import BaseType


class PackageFileStatus(BaseType):

    _soap_tag = 'status'

    def __init__(self):
        BaseType.__init__(
            self,
            simple_properties={'server_id': int,
                        'server_name': str,
                        'status': int,
                        'cache_status': str,
                        'cache_message': str,
                        'bytes_downloaded': int,
                        'bytes_total': int,
                        'download_start_time': str,
                        'last_download_progress_time': str},
            complex_properties={},
            list_properties={},
        )
        self.server_id = None
        self.server_name = None
        self.status = None
        self.cache_status = None
        self.cache_message = None
        self.bytes_downloaded = None
        self.bytes_total = None
        self.download_start_time = None
        self.last_download_progress_time = None
        
        



