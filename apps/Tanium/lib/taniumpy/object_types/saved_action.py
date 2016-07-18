
# Copyright (c) 2015 Tanium Inc
#
# Generated from console.wsdl version 0.0.1     
#
#

from .base import BaseType


class SavedAction(BaseType):

    _soap_tag = 'saved_action'

    def __init__(self):
        BaseType.__init__(
            self,
            simple_properties={'id': int,
                        'name': str,
                        'comment': str,
                        'status': int,
                        'issue_seconds': int,
                        'distribute_seconds': int,
                        'start_time': str,
                        'end_time': str,
                        'action_group_id': int,
                        'public_flag': int,
                        'policy_flag': int,
                        'expire_seconds': int,
                        'approved_flag': int,
                        'issue_count': int,
                        'creation_time': str,
                        'next_start_time': str,
                        'last_start_time': str,
                        'user_start_time': str,
                        'cache_row_id': int},
            complex_properties={'package_spec': PackageSpec,
                        'action_group': Group,
                        'target_group': Group,
                        'policy': SavedActionPolicy,
                        'metadata': MetadataList,
                        'row_ids': SavedActionRowIdList,
                        'user': User,
                        'approver': User,
                        'last_action': Action},
            list_properties={},
        )
        self.id = None
        self.name = None
        self.comment = None
        self.status = None
        self.issue_seconds = None
        self.distribute_seconds = None
        self.start_time = None
        self.end_time = None
        self.action_group_id = None
        self.public_flag = None
        self.policy_flag = None
        self.expire_seconds = None
        self.approved_flag = None
        self.issue_count = None
        self.creation_time = None
        self.next_start_time = None
        self.last_start_time = None
        self.user_start_time = None
        self.cache_row_id = None
        self.package_spec = None
        self.action_group = None
        self.target_group = None
        self.policy = None
        self.metadata = None
        self.row_ids = None
        self.user = None
        self.approver = None
        self.last_action = None
        

from package_spec import PackageSpec
from group import Group
from group import Group
from saved_action_policy import SavedActionPolicy
from metadata_list import MetadataList
from saved_action_row_id_list import SavedActionRowIdList
from user import User
from user import User
from action import Action

