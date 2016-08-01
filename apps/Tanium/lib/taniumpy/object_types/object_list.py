
# Copyright (c) 2015 Tanium Inc
#
# Generated from console.wsdl version 0.0.1     
#
#

from .base import BaseType


class ObjectList(BaseType):

    _soap_tag = 'object_list'

    def __init__(self):
        BaseType.__init__(
            self,
            simple_properties={'export_id': str},
            complex_properties={'questions': QuestionList,
                        'actions': ActionList,
                        'saved_actions': SavedActionList,
                        'roles': UserRoleList,
                        'system_status': SystemStatusList,
                        'system_settings': SystemSettingList,
                        'client_count': ClientCount,
                        'white_listed_urls': WhiteListedUrlList,
                        'computer_groups': ComputerGroupList},
            list_properties={'question': Question,
                        'group': Group,
                        'groups': GroupList,
                        'saved_question': SavedQuestion,
                        'saved_questions': SavedQuestionList,
                        'archived_question': ArchivedQuestion,
                        'archived_questions': ArchivedQuestionList,
                        'parse_job': ParseJob,
                        'parse_jobs': ParseJobList,
                        'parse_result_group': ParseResultGroup,
                        'parse_result_groups': ParseResultGroupList,
                        'action': Action,
                        'saved_action': SavedAction,
                        'action_stop': ActionStop,
                        'action_stops': ActionStopList,
                        'package_spec': PackageSpec,
                        'package_specs': PackageSpecList,
                        'package_file': PackageFile,
                        'package_files': PackageFileList,
                        'sensor': Sensor,
                        'sensors': SensorList,
                        'user': User,
                        'users': UserList,
                        'client_status': ClientStatus,
                        'system_setting': SystemSetting,
                        'saved_action_approval': SavedActionApproval,
                        'plugin': Plugin,
                        'plugins': PluginList,
                        'plugin_schedule': PluginSchedule,
                        'plugin_schedules': PluginScheduleList,
                        'white_listed_url': WhiteListedUrl,
                        'upload_file': UploadFile,
                        'upload_file_status': UploadFileStatus,
                        'soap_error': SoapError,
                        'computer_group': ComputerGroup},
        )
        self.export_id = None
        self.questions = None
        self.actions = None
        self.saved_actions = None
        self.roles = None
        self.system_status = None
        self.system_settings = None
        self.client_count = None
        self.white_listed_urls = None
        self.computer_groups = None
        self.question = []
        self.group = []
        self.groups = []
        self.saved_question = []
        self.saved_questions = []
        self.archived_question = []
        self.archived_questions = []
        self.parse_job = []
        self.parse_jobs = []
        self.parse_result_group = []
        self.parse_result_groups = []
        self.action = []
        self.saved_action = []
        self.action_stop = []
        self.action_stops = []
        self.package_spec = []
        self.package_specs = []
        self.package_file = []
        self.package_files = []
        self.sensor = []
        self.sensors = []
        self.user = []
        self.users = []
        self.client_status = []
        self.system_setting = []
        self.saved_action_approval = []
        self.plugin = []
        self.plugins = []
        self.plugin_schedule = []
        self.plugin_schedules = []
        self.white_listed_url = []
        self.upload_file = []
        self.upload_file_status = []
        self.soap_error = []
        self.computer_group = []

from question import Question
from question_list import QuestionList
from group import Group
from group_list import GroupList
from saved_question import SavedQuestion
from saved_question_list import SavedQuestionList
from archived_question import ArchivedQuestion
from archived_question_list import ArchivedQuestionList
from parse_job import ParseJob
from parse_job_list import ParseJobList
from parse_result_group import ParseResultGroup
from parse_result_group_list import ParseResultGroupList
from action import Action
from action_list import ActionList
from saved_action import SavedAction
from saved_action_list import SavedActionList
from action_stop import ActionStop
from action_stop_list import ActionStopList
from package_spec import PackageSpec
from package_spec_list import PackageSpecList
from package_file import PackageFile
from package_file_list import PackageFileList
from sensor import Sensor
from sensor_list import SensorList
from user import User
from user_list import UserList
from user_role_list import UserRoleList
from client_status import ClientStatus
from system_setting import SystemSetting
from saved_action_approval import SavedActionApproval
from system_status_list import SystemStatusList
from system_setting_list import SystemSettingList
from client_count import ClientCount
from plugin import Plugin
from plugin_list import PluginList
from plugin_schedule import PluginSchedule
from plugin_schedule_list import PluginScheduleList
from white_listed_url import WhiteListedUrl
from white_listed_url_list import WhiteListedUrlList
from upload_file import UploadFile
from upload_file_status import UploadFileStatus
from soap_error import SoapError
from computer_group_list import ComputerGroupList
from computer_group import ComputerGroup

