
# Copyright (c) 2015 Tanium Inc
#
# Generated from console.wsdl version 0.0.1     
#
#

from .base import BaseType


class PackageFileTemplateList(BaseType):

    _soap_tag = 'file_templates'

    def __init__(self):
        BaseType.__init__(
            self,
            simple_properties={},
            complex_properties={},
            list_properties={'file_template': PackageFileTemplate},
        )
        
        
        self.file_template = []

from package_file_template import PackageFileTemplate

