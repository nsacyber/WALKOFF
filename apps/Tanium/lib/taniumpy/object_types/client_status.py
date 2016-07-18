
# Copyright (c) 2015 Tanium Inc
#
# Generated from console.wsdl version 0.0.1     
#
#

from .base import BaseType


class ClientStatus(BaseType):

    _soap_tag = 'client_status'

    def __init__(self):
        BaseType.__init__(
            self,
            simple_properties={'host_name': str,
                        'computer_id': str,
                        'ipaddress_client': str,
                        'ipaddress_server': str,
                        'protocol_version': int,
                        'full_version': str,
                        'last_registration': str,
                        'send_state': str,
                        'receive_state': str,
                        'status': str,
                        'port_number': int,
                        'public_key_valid': int,
                        'cache_row_id': int},
            complex_properties={},
            list_properties={},
        )
        self.host_name = None
        self.computer_id = None
        self.ipaddress_client = None
        self.ipaddress_server = None
        self.protocol_version = None
        self.full_version = None
        self.last_registration = None
        self.send_state = None
        self.receive_state = None
        self.status = None
        self.port_number = None
        self.public_key_valid = None
        self.cache_row_id = None
        
        



