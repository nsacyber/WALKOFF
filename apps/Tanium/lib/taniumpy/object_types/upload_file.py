
# Copyright (c) 2015 Tanium Inc
#
# Generated from console.wsdl version 0.0.1     
#
#

from .base import BaseType


class UploadFile(BaseType):

    _soap_tag = 'upload_file'

    def __init__(self):
        BaseType.__init__(
            self,
            simple_properties={'id': int,
                        'key': str,
                        'destination_file': str,
                        'hash': str,
                        'force_overwrite': int,
                        'file_size': int,
                        'start_pos': int,
                        'bytes': str,
                        'file_cached': int,
                        'part_size': int,
                        'percent_complete': int},
            complex_properties={},
            list_properties={},
        )
        self.id = None
        self.key = None
        self.destination_file = None
        self.hash = None
        self.force_overwrite = None
        self.file_size = None
        self.start_pos = None
        self.bytes = None
        self.file_cached = None
        self.part_size = None
        self.percent_complete = None
        
        



