
# Copyright (c) 2015 Tanium Inc
#
# Generated from console.wsdl version 0.0.1     
#
#

from .base import BaseType


class PackageFileList(BaseType):

    _soap_tag = 'package_files'

    def __init__(self):
        BaseType.__init__(
            self,
            simple_properties={},
            complex_properties={},
            list_properties={'file': PackageFile},
        )
        
        
        self.file = []

from package_file import PackageFile

