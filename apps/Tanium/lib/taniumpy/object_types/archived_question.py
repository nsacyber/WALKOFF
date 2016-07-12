
# Copyright (c) 2015 Tanium Inc
#
# Generated from console.wsdl version 0.0.1     
#
#

from .base import BaseType


class ArchivedQuestion(BaseType):

    _soap_tag = 'archived_question'

    def __init__(self):
        BaseType.__init__(
            self,
            simple_properties={'id': int},
            complex_properties={},
            list_properties={},
        )
        self.id = None
        
        



