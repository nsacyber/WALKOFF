# -*- mode: Python; tab-width: 4; indent-tabs-mode: nil; -*-
# ex: set tabstop=4
# Please do not change the two lines above. See PEP 8, PEP 263.
'''A python package that makes using the Tanium Server SOAP API easy.'''

__title__ = 'PyTan'
__version__ = '2.1.8'
"""
Version of PyTan
"""

__author__ = 'Jim Olsen <jim.olsen@tanium.com>'
"""
Author of Pytan
"""

__license__ = 'MIT'
"""
License for PyTan
"""

__copyright__ = 'Copyright 2015 Tanium'
"""
Copyright for PyTan
"""

import sys
import os

# disable python from creating .pyc files everywhere
sys.dont_write_bytecode = True

my_file = os.path.abspath(__file__)
my_dir = os.path.dirname(my_file)
parent_dir = os.path.dirname(my_dir)
path_adds = [parent_dir]
[sys.path.insert(0, aa) for aa in path_adds]

import taniumpy  # noqa

import pytan  # noqa
import pytan.xml_clean  # noqa
import pytan.utils  # noqa
import pytan.handler  # noqa
import pytan.sessions  # noqa
import pytan.constants  # noqa
import pytan.help  # noqa
import pytan.exceptions  # noqa

from pytan import exceptions  # noqa
from pytan import utils  # noqa
from pytan import constants  # noqa
from pytan import pollers  # noqa
from pytan import sessions  # noqa
from pytan import help  # noqa
from pytan.handler import Handler  # noqa


# Set default logging handler to avoid "No handler found" warnings.
import logging
try:  # Python 2.7+
    from logging import NullHandler
except ImportError:
    class NullHandler(logging.Handler):
        def emit(self, record):
            pass

logging.getLogger(__name__).addHandler(NullHandler())
