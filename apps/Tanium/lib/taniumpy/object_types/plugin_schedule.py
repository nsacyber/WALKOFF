
# Copyright (c) 2015 Tanium Inc
#
# Generated from console.wsdl version 0.0.1     
#
#

from .base import BaseType


class PluginSchedule(BaseType):

    _soap_tag = 'plugin_schedule'

    def __init__(self):
        BaseType.__init__(
            self,
            simple_properties={'id': int,
                        'name': str,
                        'plugin_name': str,
                        'plugin_bundle': str,
                        'plugin_server': str,
                        'start_hour': int,
                        'end_hour': int,
                        'start_date': int,
                        'end_date': int,
                        'run_on_days': str,
                        'run_interval_seconds': int,
                        'enabled': int,
                        'deleted_flag': int,
                        'input': str,
                        'last_run_time': str,
                        'last_exit_code': int,
                        'last_run_text': str},
            complex_properties={'arguments': PluginArgumentList,
                        'user': User,
                        'last_run_sql': PluginSql},
            list_properties={},
        )
        self.id = None
        self.name = None
        self.plugin_name = None
        self.plugin_bundle = None
        self.plugin_server = None
        self.start_hour = None
        self.end_hour = None
        self.start_date = None
        self.end_date = None
        self.run_on_days = None
        self.run_interval_seconds = None
        self.enabled = None
        self.deleted_flag = None
        self.input = None
        self.last_run_time = None
        self.last_exit_code = None
        self.last_run_text = None
        self.arguments = None
        self.user = None
        self.last_run_sql = None
        

from plugin_argument_list import PluginArgumentList
from user import User
from plugin_sql import PluginSql

