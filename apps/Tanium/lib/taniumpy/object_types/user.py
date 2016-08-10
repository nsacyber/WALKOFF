
# Copyright (c) 2015 Tanium Inc
#
# Generated from console.wsdl version 0.0.1     
#
#

from .base import BaseType


class User(BaseType):

    _soap_tag = 'user'

    def __init__(self):
        BaseType.__init__(
            self,
            simple_properties={'id': int,
                        'name': str,
                        'domain': str,
                        'group_id': int,
                        'deleted_flag': int,
                        'last_login': str,
                        'active_session_count': int,
                        'local_admin_flag': int},
            complex_properties={'permissions': PermissionList,
                        'roles': UserRoleList,
                        'metadata': MetadataList},
            list_properties={},
        )
        self.id = None
        self.name = None
        self.domain = None
        self.group_id = None
        self.deleted_flag = None
        self.last_login = None
        self.active_session_count = None
        self.local_admin_flag = None
        self.permissions = None
        self.roles = None
        self.metadata = None
        

from permission_list import PermissionList
from user_role_list import UserRoleList
from metadata_list import MetadataList

