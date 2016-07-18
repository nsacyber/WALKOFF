
# Copyright (c) 2015 Tanium Inc
#
# Generated from console.wsdl version 0.0.1     
#
#

from .base import BaseType


class SystemSetting(BaseType):

    _soap_tag = 'system_setting'

    def __init__(self):
        BaseType.__init__(
            self,
            simple_properties={'id': int,
                        'name': str,
                        'value': str,
                        'default_value': str,
                        'value_type': str,
                        'setting_type': str,
                        'hidden_flag': int,
                        'read_only_flag': int,
                        'cache_row_id': int},
            complex_properties={'audit_data': AuditData,
                        'metadata': MetadataList},
            list_properties={},
        )
        self.id = None
        self.name = None
        self.value = None
        self.default_value = None
        self.value_type = None
        self.setting_type = None
        self.hidden_flag = None
        self.read_only_flag = None
        self.cache_row_id = None
        self.audit_data = None
        self.metadata = None
        

from audit_data import AuditData
from metadata_list import MetadataList

