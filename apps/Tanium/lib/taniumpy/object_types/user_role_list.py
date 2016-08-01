
# Copyright (c) 2015 Tanium Inc
#
# Generated from console.wsdl version 0.0.1     
#
#

from .base import BaseType


class UserRoleList(BaseType):

    _soap_tag = 'roles'

    def __init__(self):
        BaseType.__init__(
            self,
            simple_properties={},
            complex_properties={},
            list_properties={'role': UserRole},
        )
        
        
        self.role = []

from user_role import UserRole

