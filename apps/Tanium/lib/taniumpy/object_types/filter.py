
# Copyright (c) 2015 Tanium Inc
#
# Generated from console.wsdl version 0.0.1     
#
#

from .base import BaseType


class Filter(BaseType):

    _soap_tag = 'filter'

    def __init__(self):
        BaseType.__init__(
            self,
            simple_properties={'id': int,
                        'operator': str,
                        'value_type': str,
                        'value': str,
                        'not_flag': int,
                        'max_age_seconds': int,
                        'ignore_case_flag': int,
                        'all_values_flag': int,
                        'substring_flag': int,
                        'substring_start': int,
                        'substring_length': int,
                        'delimiter': str,
                        'delimiter_index': int,
                        'utf8_flag': int,
                        'aggregation': str,
                        'all_times_flag': int,
                        'start_time': str,
                        'end_time': str},
            complex_properties={'sensor': Sensor},
            list_properties={},
        )
        self.id = None
        self.operator = None
        self.value_type = None
        self.value = None
        self.not_flag = None
        self.max_age_seconds = None
        self.ignore_case_flag = None
        self.all_values_flag = None
        self.substring_flag = None
        self.substring_start = None
        self.substring_length = None
        self.delimiter = None
        self.delimiter_index = None
        self.utf8_flag = None
        self.aggregation = None
        self.all_times_flag = None
        self.start_time = None
        self.end_time = None
        self.sensor = None
        

from sensor import Sensor

