
# Copyright (c) 2015 Tanium Inc
#
# Generated from console.wsdl version 0.0.1     
#
#

from .base import BaseType


class Sensor(BaseType):

    _soap_tag = 'sensor'

    def __init__(self):
        BaseType.__init__(
            self,
            simple_properties={'id': int,
                        'name': str,
                        'hash': int,
                        'string_count': int,
                        'category': str,
                        'description': str,
                        'source_id': int,
                        'source_hash': int,
                        'parameter_definition': str,
                        'value_type': str,
                        'max_age_seconds': int,
                        'ignore_case_flag': int,
                        'exclude_from_parse_flag': int,
                        'delimiter': str,
                        'creation_time': str,
                        'modification_time': str,
                        'last_modified_by': str,
                        'preview_sensor_flag': int,
                        'hidden_flag': int,
                        'deleted_flag': int,
                        'cache_row_id': int},
            complex_properties={'queries': SensorQueryList,
                        'parameters': ParameterList,
                        'subcolumns': SensorSubcolumnList,
                        'string_hints': StringHintList,
                        'metadata': MetadataList},
            list_properties={},
        )
        self.id = None
        self.name = None
        self.hash = None
        self.string_count = None
        self.category = None
        self.description = None
        self.source_id = None
        self.source_hash = None
        self.parameter_definition = None
        self.value_type = None
        self.max_age_seconds = None
        self.ignore_case_flag = None
        self.exclude_from_parse_flag = None
        self.delimiter = None
        self.creation_time = None
        self.modification_time = None
        self.last_modified_by = None
        self.preview_sensor_flag = None
        self.hidden_flag = None
        self.deleted_flag = None
        self.cache_row_id = None
        self.queries = None
        self.parameters = None
        self.subcolumns = None
        self.string_hints = None
        self.metadata = None
        

from sensor_query_list import SensorQueryList
from parameter_list import ParameterList
from sensor_subcolumn_list import SensorSubcolumnList
from string_hint_list import StringHintList
from metadata_list import MetadataList

