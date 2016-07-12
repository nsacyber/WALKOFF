
# Copyright (c) 2015 Tanium Inc
#
# Generated from console.wsdl version 0.0.1     
#
#

from .base import BaseType


class UploadFileStatus(BaseType):

    _soap_tag = 'upload_file_status'

    def __init__(self):
        BaseType.__init__(
            self,
            simple_properties={'hash': str,
                        'percent_complete': int,
                        'file_cached': int},
            complex_properties={'file_parts': UploadFileList},
            list_properties={},
        )
        self.hash = None
        self.percent_complete = None
        self.file_cached = None
        self.file_parts = None
        

from upload_file_list import UploadFileList

