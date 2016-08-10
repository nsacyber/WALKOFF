
# Copyright (c) 2015 Tanium Inc
#
# Generated from console.wsdl version 0.0.1     
#
#

from .base import BaseType


class UploadFileList(BaseType):

    _soap_tag = 'file_parts'

    def __init__(self):
        BaseType.__init__(
            self,
            simple_properties={},
            complex_properties={},
            list_properties={'upload_file': UploadFile},
        )
        
        
        self.upload_file = []

from upload_file import UploadFile

