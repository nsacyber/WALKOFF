
# Copyright (c) 2015 Tanium Inc
#
# Generated from console.wsdl version 0.0.1     
#
#

from .base import BaseType


class UserRole(BaseType):

    _soap_tag = 'role'

    def __init__(self):
        BaseType.__init__(
            self,
            simple_properties={'id': int,
                        'name': str,
                        'description': str},
            complex_properties={'permissions': PermissionList},
            list_properties={},
        )
        self.id = None
        self.name = None
        self.description = None
        self.permissions = None
        

from permission_list import PermissionList

