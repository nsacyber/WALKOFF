
# Copyright (c) 2015 Tanium Inc
#
# Generated from console.wsdl version 0.0.1     
#
#

from .base import BaseType


class SavedQuestionList(BaseType):

    _soap_tag = 'saved_questions'

    def __init__(self):
        BaseType.__init__(
            self,
            simple_properties={},
            complex_properties={'cache_info': CacheInfo},
            list_properties={'saved_question': SavedQuestion},
        )
        
        self.cache_info = None
        self.saved_question = []

from saved_question import SavedQuestion
from cache_info import CacheInfo

