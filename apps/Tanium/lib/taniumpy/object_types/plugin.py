
# Copyright (c) 2015 Tanium Inc
#
# Generated from console.wsdl version 0.0.1     
#
#

from .base import BaseType


class Plugin(BaseType):

    _soap_tag = 'plugin'

    def __init__(self):
        BaseType.__init__(
            self,
            simple_properties={'name': str,
                        'bundle': str,
                        'plugin_server': str,
                        'input': str,
                        'script_response': str,
                        'exit_code': int,
                        'type': str,
                        'path': str,
                        'filename': str,
                        'plugin_url': str,
                        'run_detached_flag': int,
                        'execution_id': int,
                        'timeout_seconds': int,
                        'cache_row_id': int,
                        'local_admin_flag': int,
                        'allow_rest': int,
                        'raw_http_response': int,
                        'raw_http_request': int,
                        'use_json_flag': int,
                        'status': str,
                        'status_file_content': str},
            complex_properties={'arguments': PluginArgumentList,
                        'sql_response': PluginSql,
                        'metadata': MetadataList,
                        'commands': PluginCommandList,
                        'permissions': PermissionList},
            list_properties={},
        )
        self.name = None
        self.bundle = None
        self.plugin_server = None
        self.input = None
        self.script_response = None
        self.exit_code = None
        self.type = None
        self.path = None
        self.filename = None
        self.plugin_url = None
        self.run_detached_flag = None
        self.execution_id = None
        self.timeout_seconds = None
        self.cache_row_id = None
        self.local_admin_flag = None
        self.allow_rest = None
        self.raw_http_response = None
        self.raw_http_request = None
        self.use_json_flag = None
        self.status = None
        self.status_file_content = None
        self.arguments = None
        self.sql_response = None
        self.metadata = None
        self.commands = None
        self.permissions = None
        

from plugin_argument_list import PluginArgumentList
from plugin_sql import PluginSql
from metadata_list import MetadataList
from plugin_command_list import PluginCommandList
from permission_list import PermissionList

