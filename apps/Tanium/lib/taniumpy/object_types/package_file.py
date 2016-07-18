
# Copyright (c) 2015 Tanium Inc
#
# Generated from console.wsdl version 0.0.1     
#
#

from .base import BaseType


class PackageFile(BaseType):

    _soap_tag = 'file'

    def __init__(self):
        BaseType.__init__(
            self,
            simple_properties={'id': int,
                        'hash': str,
                        'name': str,
                        'size': int,
                        'source': str,
                        'download_seconds': int,
                        'trigger_download': int,
                        'cache_status': str,
                        'status': int,
                        'bytes_downloaded': int,
                        'bytes_total': int,
                        'download_start_time': str,
                        'last_download_progress_time': str,
                        'deleted_flag': int},
            complex_properties={'file_status': PackageFileStatusList},
            list_properties={},
        )
        self.id = None
        self.hash = None
        self.name = None
        self.size = None
        self.source = None
        self.download_seconds = None
        self.trigger_download = None
        self.cache_status = None
        self.status = None
        self.bytes_downloaded = None
        self.bytes_total = None
        self.download_start_time = None
        self.last_download_progress_time = None
        self.deleted_flag = None
        self.file_status = None
        

from package_file_status_list import PackageFileStatusList

