
# Copyright (c) 2015 Tanium Inc
#
# Generated from console.wsdl version 0.0.1     
#
#

from .base import BaseType


class WhiteListedUrlList(BaseType):

    _soap_tag = 'white_listed_urls'

    def __init__(self):
        BaseType.__init__(
            self,
            simple_properties={},
            complex_properties={},
            list_properties={'white_listed_url': WhiteListedUrl},
        )
        
        
        self.white_listed_url = []

from white_listed_url import WhiteListedUrl

