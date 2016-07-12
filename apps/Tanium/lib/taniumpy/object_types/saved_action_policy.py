
# Copyright (c) 2015 Tanium Inc
#
# Generated from console.wsdl version 0.0.1     
#
#

from .base import BaseType


class SavedActionPolicy(BaseType):

    _soap_tag = 'policy'

    def __init__(self):
        BaseType.__init__(
            self,
            simple_properties={'saved_question_id': int,
                        'saved_question_group_id': int,
                        'row_filter_group_id': int,
                        'max_age': int,
                        'min_count': int},
            complex_properties={'saved_question_group': Group,
                        'row_filter_group': Group},
            list_properties={},
        )
        self.saved_question_id = None
        self.saved_question_group_id = None
        self.row_filter_group_id = None
        self.max_age = None
        self.min_count = None
        self.saved_question_group = None
        self.row_filter_group = None
        

from group import Group
from group import Group

