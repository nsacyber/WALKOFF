
# Copyright (c) 2015 Tanium Inc
#
# Generated from console.wsdl version 0.0.1     
#
#

from .base import BaseType


class QuestionListInfo(BaseType):

    _soap_tag = 'info'

    def __init__(self):
        BaseType.__init__(
            self,
            simple_properties={'highest_id': int,
                        'total_count': int},
            complex_properties={},
            list_properties={},
        )
        self.highest_id = None
        self.total_count = None
        
        



