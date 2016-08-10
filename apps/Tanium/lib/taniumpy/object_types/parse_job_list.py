
# Copyright (c) 2015 Tanium Inc
#
# Generated from console.wsdl version 0.0.1     
#
#

from .base import BaseType


class ParseJobList(BaseType):

    _soap_tag = 'parse_jobs'

    def __init__(self):
        BaseType.__init__(
            self,
            simple_properties={},
            complex_properties={},
            list_properties={'parse_job': ParseJob},
        )
        
        
        self.parse_job = []

from parse_job import ParseJob

