
# Copyright (c) 2015 Tanium Inc
#
# Generated from console.wsdl version 0.0.1     
#
#

from .base import BaseType


class Select(BaseType):

    _soap_tag = 'select'

    def __init__(self):
        BaseType.__init__(
            self,
            simple_properties={},
            complex_properties={'sensor': Sensor,
                        'filter': Filter,
                        'group': Group},
            list_properties={},
        )
        
        self.sensor = None
        self.filter = None
        self.group = None
        

from sensor import Sensor
from filter import Filter
from group import Group

