
# Copyright (c) 2015 Tanium Inc
#
# Generated from console.wsdl version 0.0.1     
#
#

from .base import BaseType


class SystemStatusAggregate(BaseType):

    _soap_tag = 'aggregate'

    def __init__(self):
        BaseType.__init__(
            self,
            simple_properties={'send_forward_count': int,
                        'send_backward_count': int,
                        'send_none_count': int,
                        'send_ok_count': int,
                        'receive_forward_count': int,
                        'receive_backward_count': int,
                        'receive_none_count': int,
                        'receive_ok_count': int,
                        'slowlink_count': int,
                        'blocked_count': int,
                        'leader_count': int,
                        'normal_count': int},
            complex_properties={'versions': VersionAggregateList},
            list_properties={},
        )
        self.send_forward_count = None
        self.send_backward_count = None
        self.send_none_count = None
        self.send_ok_count = None
        self.receive_forward_count = None
        self.receive_backward_count = None
        self.receive_none_count = None
        self.receive_ok_count = None
        self.slowlink_count = None
        self.blocked_count = None
        self.leader_count = None
        self.normal_count = None
        self.versions = None
        

from version_aggregate_list import VersionAggregateList

