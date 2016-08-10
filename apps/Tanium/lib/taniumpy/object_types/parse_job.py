
# Copyright (c) 2015 Tanium Inc
#
# Generated from console.wsdl version 0.0.1     
#
#

from .base import BaseType


class ParseJob(BaseType):

    _soap_tag = 'parse_job'

    def __init__(self):
        BaseType.__init__(
            self,
            simple_properties={'question_text': str,
                        'parser_version': int},
            complex_properties={},
            list_properties={},
        )
        self.question_text = None
        self.parser_version = None
        
        



