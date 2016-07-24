
# Copyright (c) 2015 Tanium Inc
#
# Generated from console.wsdl version 0.0.1     
#
#

from .base import BaseType


class SavedActionRowIdList(BaseType):

    _soap_tag = 'row_ids'

    def __init__(self):
        BaseType.__init__(
            self,
            simple_properties={},
            complex_properties={},
            list_properties={'row_id': int},
        )
        
        
        self.row_id = []



