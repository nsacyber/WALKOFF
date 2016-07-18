
# Copyright (c) 2015 Tanium Inc
#
# Generated from console.wsdl version 0.0.1     
#
#

from .base import BaseType


class VersionAggregate(BaseType):

    _soap_tag = 'version'

    def __init__(self):
        BaseType.__init__(
            self,
            simple_properties={'version_string': str,
                        'count': int,
                        'filtered': int},
            complex_properties={},
            list_properties={},
        )
        self.version_string = None
        self.count = None
        self.filtered = None
        
        



