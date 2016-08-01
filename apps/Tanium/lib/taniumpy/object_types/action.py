
# Copyright (c) 2015 Tanium Inc
#
# Generated from console.wsdl version 0.0.1     
#
#

from .base import BaseType


class Action(BaseType):

    _soap_tag = 'action'

    def __init__(self):
        BaseType.__init__(
            self,
            simple_properties={'id': int,
                        'name': str,
                        'comment': str,
                        'start_time': str,
                        'expiration_time': str,
                        'status': str,
                        'skip_lock_flag': int,
                        'expire_seconds': int,
                        'distribute_seconds': int,
                        'creation_time': str,
                        'stopped_flag': int,
                        'cache_row_id': int},
            complex_properties={'target_group': Group,
                        'action_group': Group,
                        'package_spec': PackageSpec,
                        'user': User,
                        'approver': User,
                        'history_saved_question': SavedQuestion,
                        'saved_action': SavedAction,
                        'metadata': MetadataList},
            list_properties={},
        )
        self.id = None
        self.name = None
        self.comment = None
        self.start_time = None
        self.expiration_time = None
        self.status = None
        self.skip_lock_flag = None
        self.expire_seconds = None
        self.distribute_seconds = None
        self.creation_time = None
        self.stopped_flag = None
        self.cache_row_id = None
        self.target_group = None
        self.action_group = None
        self.package_spec = None
        self.user = None
        self.approver = None
        self.history_saved_question = None
        self.saved_action = None
        self.metadata = None
        

from group import Group
from group import Group
from package_spec import PackageSpec
from user import User
from user import User
from saved_question import SavedQuestion
from saved_action import SavedAction
from metadata_list import MetadataList

