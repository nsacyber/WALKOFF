
# Copyright (c) 2015 Tanium Inc
#
# Generated from console.wsdl version 0.0.1     
#
#

from .base import BaseType


class Question(BaseType):

    _soap_tag = 'question'

    def __init__(self):
        BaseType.__init__(
            self,
            simple_properties={'id': int,
                        'expire_seconds': int,
                        'skip_lock_flag': int,
                        'expiration': str,
                        'name': str,
                        'query_text': str,
                        'hidden_flag': int,
                        'action_tracking_flag': int,
                        'force_computer_id_flag': int,
                        'cache_row_id': int,
                        'index': int},
            complex_properties={'selects': SelectList,
                        'context_group': Group,
                        'group': Group,
                        'user': User,
                        'management_rights_group': Group,
                        'saved_question': SavedQuestion},
            list_properties={},
        )
        self.id = None
        self.expire_seconds = None
        self.skip_lock_flag = None
        self.expiration = None
        self.name = None
        self.query_text = None
        self.hidden_flag = None
        self.action_tracking_flag = None
        self.force_computer_id_flag = None
        self.cache_row_id = None
        self.index = None
        self.selects = None
        self.context_group = None
        self.group = None
        self.user = None
        self.management_rights_group = None
        self.saved_question = None
        

from select_list import SelectList
from group import Group
from group import Group
from user import User
from group import Group
from saved_question import SavedQuestion

