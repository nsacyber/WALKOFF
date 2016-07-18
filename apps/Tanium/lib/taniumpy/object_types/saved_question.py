
# Copyright (c) 2015 Tanium Inc
#
# Generated from console.wsdl version 0.0.1     
#
#

from .base import BaseType


class SavedQuestion(BaseType):

    _soap_tag = 'saved_question'

    def __init__(self):
        BaseType.__init__(
            self,
            simple_properties={'id': int,
                        'name': str,
                        'public_flag': int,
                        'hidden_flag': int,
                        'issue_seconds': int,
                        'issue_seconds_never_flag': int,
                        'expire_seconds': int,
                        'sort_column': int,
                        'query_text': str,
                        'row_count_flag': int,
                        'keep_seconds': int,
                        'archive_enabled_flag': int,
                        'most_recent_question_id': int,
                        'action_tracking_flag': int,
                        'mod_time': str,
                        'index': int,
                        'cache_row_id': int},
            complex_properties={'question': Question,
                        'packages': PackageSpecList,
                        'user': User,
                        'archive_owner': User,
                        'mod_user': User,
                        'metadata': MetadataList},
            list_properties={},
        )
        self.id = None
        self.name = None
        self.public_flag = None
        self.hidden_flag = None
        self.issue_seconds = None
        self.issue_seconds_never_flag = None
        self.expire_seconds = None
        self.sort_column = None
        self.query_text = None
        self.row_count_flag = None
        self.keep_seconds = None
        self.archive_enabled_flag = None
        self.most_recent_question_id = None
        self.action_tracking_flag = None
        self.mod_time = None
        self.index = None
        self.cache_row_id = None
        self.question = None
        self.packages = None
        self.user = None
        self.archive_owner = None
        self.mod_user = None
        self.metadata = None
        

from question import Question
from package_spec_list import PackageSpecList
from user import User
from user import User
from user import User
from metadata_list import MetadataList

