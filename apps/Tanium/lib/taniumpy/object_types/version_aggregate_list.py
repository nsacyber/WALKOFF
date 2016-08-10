
# Copyright (c) 2015 Tanium Inc
#
# Generated from console.wsdl version 0.0.1     
#
#

from .base import BaseType


class VersionAggregateList(BaseType):

    _soap_tag = 'versions'

    def __init__(self):
        BaseType.__init__(
            self,
            simple_properties={},
            complex_properties={},
            list_properties={'version': VersionAggregate},
        )
        
        
        self.version = []

from version_aggregate import VersionAggregate

