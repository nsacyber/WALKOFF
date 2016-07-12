
# Copyright (c) 2015 Tanium Inc
#
# Generated from console.wsdl version 0.0.1     
#
#

from .base import BaseType


class PackageSpec(BaseType):

    _soap_tag = 'package_spec'

    def __init__(self):
        BaseType.__init__(
            self,
            simple_properties={'id': int,
                        'name': str,
                        'display_name': str,
                        'command': str,
                        'command_timeout': int,
                        'expire_seconds': int,
                        'hidden_flag': int,
                        'signature': str,
                        'source_id': int,
                        'verify_group_id': int,
                        'verify_expire_seconds': int,
                        'skip_lock_flag': int,
                        'parameter_definition': str,
                        'creation_time': str,
                        'modification_time': str,
                        'last_modified_by': str,
                        'available_time': str,
                        'deleted_flag': int,
                        'last_update': str,
                        'cache_row_id': int},
            complex_properties={'files': PackageFileList,
                        'file_templates': PackageFileTemplateList,
                        'verify_group': Group,
                        'parameters': ParameterList,
                        'sensors': SensorList,
                        'metadata': MetadataList},
            list_properties={},
        )
        self.id = None
        self.name = None
        self.display_name = None
        self.command = None
        self.command_timeout = None
        self.expire_seconds = None
        self.hidden_flag = None
        self.signature = None
        self.source_id = None
        self.verify_group_id = None
        self.verify_expire_seconds = None
        self.skip_lock_flag = None
        self.parameter_definition = None
        self.creation_time = None
        self.modification_time = None
        self.last_modified_by = None
        self.available_time = None
        self.deleted_flag = None
        self.last_update = None
        self.cache_row_id = None
        self.files = None
        self.file_templates = None
        self.verify_group = None
        self.parameters = None
        self.sensors = None
        self.metadata = None
        

from package_file_list import PackageFileList
from package_file_template_list import PackageFileTemplateList
from group import Group
from parameter_list import ParameterList
from sensor_list import SensorList
from metadata_list import MetadataList

