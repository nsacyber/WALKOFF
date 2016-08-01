from action import Action
from action_stop import ActionStop
from action_stop_list import ActionStopList
from action_list import ActionList
from system_status_aggregate import SystemStatusAggregate
from archived_question import ArchivedQuestion
from archived_question_list import ArchivedQuestionList
from plugin_argument import PluginArgument
from plugin_argument_list import PluginArgumentList
from audit_data import AuditData
from cache_filter_list import CacheFilterList
from cache_info import CacheInfo
from client_count import ClientCount
from client_status import ClientStatus
from plugin_sql_column import PluginSqlColumn
from plugin_command_list import PluginCommandList
from computer_group import ComputerGroup
from computer_group_list import ComputerGroupList
from computer_group_spec import ComputerGroupSpec
from computer_spec_list import ComputerSpecList
from xml_error import XmlError
from error_list import ErrorList
from package_file import PackageFile
from upload_file_list import UploadFileList
from package_file_status_list import PackageFileStatusList
from package_file_template import PackageFileTemplate
from package_file_template_list import PackageFileTemplateList
from filter import Filter
from filter_list import FilterList
from group import Group
from group_list import GroupList
from question_list_info import QuestionListInfo
from metadata_item import MetadataItem
from metadata_list import MetadataList
from object_list import ObjectList
from options import Options
from package_file_list import PackageFileList
from package_spec import PackageSpec
from package_spec_list import PackageSpecList
from parameter import Parameter
from parameter_list import ParameterList
from parse_job import ParseJob
from parse_job_list import ParseJobList
from parse_result import ParseResult
from parse_result_group import ParseResultGroup
from parse_result_group_list import ParseResultGroupList
from parse_result_list import ParseResultList
from permission_list import PermissionList
from plugin import Plugin
from plugin_schedule import PluginSchedule
from plugin_schedule_list import PluginScheduleList
from plugin_list import PluginList
from saved_action_policy import SavedActionPolicy
from sensor_query_list import SensorQueryList
from sensor_query import SensorQuery
from question import Question
from question_list import QuestionList
from plugin_sql_result import PluginSqlResult
from user_role import UserRole
from user_role_list import UserRoleList
from saved_action_row_id_list import SavedActionRowIdList
from saved_action import SavedAction
from saved_action_approval import SavedActionApproval
from saved_action_list import SavedActionList
from saved_question import SavedQuestion
from saved_question_list import SavedQuestionList
from select import Select
from select_list import SelectList
from sensor import Sensor
from sensor_list import SensorList
from soap_error import SoapError
from plugin_sql import PluginSql
from package_file_status import PackageFileStatus
from string_hint_list import StringHintList
from sensor_subcolumn import SensorSubcolumn
from sensor_subcolumn_list import SensorSubcolumnList
from system_setting import SystemSetting
from system_setting_list import SystemSettingList
from system_status_list import SystemStatusList
from upload_file import UploadFile
from upload_file_status import UploadFileStatus
from user import User
from user_list import UserList
from version_aggregate import VersionAggregate
from version_aggregate_list import VersionAggregateList
from white_listed_url import WhiteListedUrl
from white_listed_url_list import WhiteListedUrlList


OBJECT_LIST_TYPES = {
	'action': Action,
	'action_stop': ActionStop,
	'action_stops': ActionStopList,
	'actions': ActionList,
	'aggregate': SystemStatusAggregate,
	'archived_question': ArchivedQuestion,
	'archived_questions': ArchivedQuestionList,
	'argument': PluginArgument,
	'arguments': PluginArgumentList,
	'audit_data': AuditData,
	'cache_filters': CacheFilterList,
	'cache_info': CacheInfo,
	'client_count': ClientCount,
	'client_status': ClientStatus,
	'columns': PluginSqlColumn,
	'commands': PluginCommandList,
	'computer_group': ComputerGroup,
	'computer_groups': ComputerGroupList,
	'computer_spec': ComputerGroupSpec,
	'computer_specs': ComputerSpecList,
	'error': XmlError,
	'errors': ErrorList,
	'file': PackageFile,
	'file_parts': UploadFileList,
	'file_status': PackageFileStatusList,
	'file_template': PackageFileTemplate,
	'file_templates': PackageFileTemplateList,
	'filter': Filter,
	'filters': FilterList,
	'group': Group,
	'groups': GroupList,
	'info': QuestionListInfo,
	'item': MetadataItem,
	'metadata': MetadataList,
	'object_list': ObjectList,
	'options': Options,
	'package_files': PackageFileList,
	'package_spec': PackageSpec,
	'package_specs': PackageSpecList,
	'parameter': Parameter,
	'parameters': ParameterList,
	'parse_job': ParseJob,
	'parse_jobs': ParseJobList,
	'parse_result': ParseResult,
	'parse_result_group': ParseResultGroup,
	'parse_result_groups': ParseResultGroupList,
	'parse_results': ParseResultList,
	'permissions': PermissionList,
	'plugin': Plugin,
	'plugin_schedule': PluginSchedule,
	'plugin_schedules': PluginScheduleList,
	'plugins': PluginList,
	'policy': SavedActionPolicy,
	'queries': SensorQueryList,
	'query': SensorQuery,
	'question': Question,
	'questions': QuestionList,
	'result_row': PluginSqlResult,
	'role': UserRole,
	'roles': UserRoleList,
	'row_ids': SavedActionRowIdList,
	'saved_action': SavedAction,
	'saved_action_approval': SavedActionApproval,
	'saved_actions': SavedActionList,
	'saved_question': SavedQuestion,
	'saved_questions': SavedQuestionList,
	'select': Select,
	'selects': SelectList,
	'sensor': Sensor,
	'sensors': SensorList,
	'soap_error': SoapError,
	'sql_response': PluginSql,
	'status': PackageFileStatus,
	'string_hints': StringHintList,
	'subcolumn': SensorSubcolumn,
	'subcolumns': SensorSubcolumnList,
	'system_setting': SystemSetting,
	'system_settings': SystemSettingList,
	'system_status': SystemStatusList,
	'upload_file': UploadFile,
	'upload_file_status': UploadFileStatus,
	'user': User,
	'users': UserList,
	'version': VersionAggregate,
	'versions': VersionAggregateList,
	'white_listed_url': WhiteListedUrl,
	'white_listed_urls': WhiteListedUrlList,
}