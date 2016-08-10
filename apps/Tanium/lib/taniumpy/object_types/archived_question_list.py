
# Copyright (c) 2015 Tanium Inc
#
# Generated from console.wsdl version 0.0.1     
#
#

from .base import BaseType


class ArchivedQuestionList(BaseType):

    _soap_tag = 'archived_questions'

    def __init__(self):
        BaseType.__init__(
            self,
            simple_properties={},
            complex_properties={},
            list_properties={'archived_question': ArchivedQuestion},
        )
        
        
        self.archived_question = []

from archived_question import ArchivedQuestion

