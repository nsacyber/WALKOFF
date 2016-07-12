
# Copyright (c) 2015 Tanium Inc
#
# Generated from console.wsdl version 0.0.1     
#
#

from .base import BaseType


class QuestionList(BaseType):

    _soap_tag = 'questions'

    def __init__(self):
        BaseType.__init__(
            self,
            simple_properties={},
            complex_properties={'info': QuestionListInfo,
                        'cache_info': CacheInfo},
            list_properties={'question': Question},
        )
        
        self.info = None
        self.cache_info = None
        self.question = []

from question_list_info import QuestionListInfo
from question import Question
from cache_info import CacheInfo

