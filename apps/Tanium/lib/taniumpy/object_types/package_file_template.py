
# Copyright (c) 2015 Tanium Inc
#
# Generated from console.wsdl version 0.0.1     
#
#

from .base import BaseType


class PackageFileTemplate(BaseType):

    _soap_tag = 'file_template'

    def __init__(self):
        BaseType.__init__(
            self,
            simple_properties={'hash': str,
                        'name': str,
                        'source': str,
                        'download_seconds': int},
            complex_properties={},
            list_properties={},
        )
        self.hash = None
        self.name = None
        self.source = None
        self.download_seconds = None
        
        



