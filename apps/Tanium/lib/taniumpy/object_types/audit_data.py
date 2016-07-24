
# Copyright (c) 2015 Tanium Inc
#
# Generated from console.wsdl version 0.0.1     
#
#

from .base import BaseType


class AuditData(BaseType):

    _soap_tag = 'audit_data'

    def __init__(self):
        BaseType.__init__(
            self,
            simple_properties={'creation_time': str,
                        'modification_time': str,
                        'last_modified_by': str},
            complex_properties={},
            list_properties={},
        )
        self.creation_time = None
        self.modification_time = None
        self.last_modified_by = None
        
        



