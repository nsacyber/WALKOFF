
# Copyright (c) 2015 Tanium Inc
#
# Generated from console.wsdl version 0.0.1     
#
#

from .base import BaseType


class MetadataList(BaseType):

    _soap_tag = 'metadata'

    def __init__(self):
        BaseType.__init__(
            self,
            simple_properties={},
            complex_properties={},
            list_properties={'item': MetadataItem},
        )
        
        
        self.item = []

from metadata_item import MetadataItem

