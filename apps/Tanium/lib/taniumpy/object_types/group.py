
# Copyright (c) 2015 Tanium Inc
#
# Generated from console.wsdl version 0.0.1     
#
#

from .base import BaseType


class Group(BaseType):

    _soap_tag = 'group'

    def __init__(self):
        BaseType.__init__(
            self,
            simple_properties={'id': int,
                        'name': str,
                        'text': str,
                        'and_flag': int,
                        'not_flag': int,
                        'type': int,
                        'source_id': int,
                        'deleted_flag': int},
            complex_properties={'sub_groups': GroupList,
                        'filters': FilterList,
                        'parameters': ParameterList},
            list_properties={},
        )
        self.id = None
        self.name = None
        self.text = None
        self.and_flag = None
        self.not_flag = None
        self.type = None
        self.source_id = None
        self.deleted_flag = None
        self.sub_groups = None
        self.filters = None
        self.parameters = None
        

from group_list import GroupList
from filter_list import FilterList
from parameter_list import ParameterList

