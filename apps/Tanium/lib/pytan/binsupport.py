#!/usr/bin/env python
# -*- mode: Python; tab-width: 4; indent-tabs-mode: nil; -*-
# ex: set tabstop=4
# Please do not change the two lines above. See PEP 8, PEP 263.
"""Collection of classes and methods used throughout :mod:`pytan` for command line support"""
import sys

# disable python from creating .pyc files everywhere
sys.dont_write_bytecode = True

import os
import logging
import code
import traceback
import pprint
import argparse
import getpass
import json
import string
import csv
import io
import platform
import datetime
import time
import copy
from argparse import ArgumentDefaultsHelpFormatter as A1 # noqa
from argparse import RawDescriptionHelpFormatter as A2 # noqa

my_file = os.path.abspath(__file__)
my_dir = os.path.dirname(my_file)
parent_dir = os.path.dirname(my_dir)
path_adds = [parent_dir]
[sys.path.insert(0, aa) for aa in path_adds if aa not in sys.path]

import pytan
import taniumpy

__version__ = pytan.__version__
pname = os.path.splitext(os.path.basename(sys.argv[0]))[0]
mylog = logging.getLogger("pytan.handler")


class HistoryConsole(code.InteractiveConsole):
    """Class that provides an interactive python console with full auto complete, history, and history file support.

    Examples
    --------
        >>> HistoryConsole()
    """
    def __init__(self, locals=None, filename="<console>",
                 histfile=os.path.expanduser("~/.console-history"), **kwargs):
        code.InteractiveConsole.__init__(self, locals, filename)

        self.debug = kwargs.get('debug', False)

        import atexit
        self.atexit = atexit
        self.readline = None

        if platform.system().lower() == 'windows':
            my_file = os.path.abspath(__file__)
            my_dir = os.path.dirname(my_file)
            parent_dir = os.path.dirname(my_dir)
            pytan_root = os.path.dirname(parent_dir)
            winlib_dir = os.path.join(pytan_root, 'winlib')
            path_adds = [winlib_dir]
            [sys.path.insert(0, aa) for aa in path_adds if aa not in sys.path]

        self.import_readline()
        self.setup_autocomplete()
        self.read_history(histfile)
        self.setup_atexit_write_history(histfile)

    def import_readline(self):
        try:
            import readline
            self.readline = readline
            if self.debug:
                print "imported readline: {}".format(readline.__file__)
        except:
            print (
                "No readline support in this Python build, auto-completetion will not be enabled!"
            )
        else:
            import rlcompleter  # noqa
            if self.debug:
                print "imported rlcompleter: {}".format(rlcompleter.__file__)

    def setup_autocomplete(self):
        readline = self.readline

        rlfile = getattr(readline, '__file__', '') or ''
        rldoc = getattr(readline, '__doc__', '') or ''

        if 'libedit' in rldoc:
            if self.debug:
                print "osx libedit readline style readline"
            readline.parse_and_bind("bind ^I rl_complete")
            readline.parse_and_bind("bind ^R em-inc-search-prev")
        if 'readline.py' in rlfile:
            if self.debug:
                print "pyreadline style readline"
            readline.parse_and_bind("tab: complete")
        elif rldoc:
            if self.debug:
                print "normal readline style readline"
            readline.parse_and_bind("tab: complete")
        elif self.debug:
            print "readline module {} is unknown, methods: {}".format(
                readline, dir(readline),
            )

    def setup_atexit_write_history(self, histfile):
        readline = self.readline
        rl_has_history = hasattr(readline, "write_history_file")
        if rl_has_history:
            atexit = self.atexit
            atexit.register(self.write_history, histfile)
        elif self.debug:
            print "readline module {} has no write_history_file(), methods: {}".format(
                readline, dir(readline),
            )

    def read_history(self, histfile):
        readline = self.readline
        rl_has_history = hasattr(readline, "read_history_file")
        if rl_has_history:
            try:
                readline.read_history_file(histfile)
            except IOError:
                # the file doesn't exist/can't be accessed
                pass
            except Exception as e:
                print "Unable to read history file '{}', exception: '{}'".format(histfile, e)
        elif self.debug:
            print "readline module {} has no read_history_file(), methods: {}".format(
                readline, dir(readline),
            )

    def write_history(self, histfile):
        readline = self.readline
        rl_has_history = hasattr(readline, "write_history_file")

        if rl_has_history:
            try:
                readline.write_history_file(histfile) # noqa
            except Exception as e:
                print "Unable to write history file '{}', exception: '{}'".format(histfile, e)
        elif self.debug:
            print "readline module {} has no write_history_file(), methods: {}".format(
                readline, dir(readline),
            )


class CustomArgFormat(A1, A2):
    """Multiple inheritance Formatter class for :class:`argparse.ArgumentParser`.

    If a :class:`argparse.ArgumentParser` class uses this as it's Formatter class, it will show the defaults for each argument in the `help` output
    """
    pass


class CustomArgParse(argparse.ArgumentParser):
    """Custom :class:`argparse.ArgumentParser` class which does a number of things:

        * Uses :class:`pytan.utils.CustomArgFormat` as it's Formatter class, if none was passed in
        * Prints help if there is an error
        * Prints the help for any subparsers that exist
    """
    def __init__(self, *args, **kwargs):
        if 'formatter_class' not in kwargs:
            kwargs['formatter_class'] = CustomArgFormat
        # print kwargs
        argparse.ArgumentParser.__init__(self, *args, **kwargs)

    def error(self, message):
        self.print_help()
        print('ERROR:{}:{}\n'.format(pname, message))
        sys.exit(2)

    def print_help(self, **kwargs):
        super(CustomArgParse, self).print_help(**kwargs)
        subparsers_actions = [
            action for action in self._actions
            if isinstance(action, argparse._SubParsersAction)
        ]
        for subparsers_action in subparsers_actions:
            print ""
            # get all subparsers and print help
            for choice, subparser in subparsers_action.choices.items():
                # print subparser
                # print(" ** {} '{}':".format(
                    # subparsers_action.dest, choice))
                print(subparser.format_help())


def setup_parser(desc, help=False):
    """Method to setup the base :class:`pytan.utils.CustomArgParse` class for command line scripts that use :mod:`pytan`. This establishes the basic arguments that are needed by all such scripts, such as:

        * --help
        * --username
        * --password
        * --host
        * --port
        * --loglevel
        * --debugformat
    """
    parser = CustomArgParse(description=desc, add_help=help, formatter_class=CustomArgFormat)
    arggroup_name = 'Handler Authentication'
    auth_group = parser.add_argument_group(arggroup_name)
    auth_group.add_argument(
        '-u',
        '--username',
        required=False,
        action='store',
        dest='username',
        default=None,
        help='Name of user',
    )
    auth_group.add_argument(
        '-p',
        '--password',
        required=False,
        action='store',
        default=None,
        dest='password',
        help='Password of user',
    )
    auth_group.add_argument(
        '--session_id',
        required=False,
        action='store',
        default=None,
        dest='session_id',
        help='Session ID to authenticate with instead of username/password',
    )
    auth_group.add_argument(
        '--host',
        required=False,
        action='store',
        default=None,
        dest='host',
        help='Hostname/ip of SOAP Server',
    )
    auth_group.add_argument(
        '--port',
        required=False,
        action='store',
        default="443",
        dest='port',
        help='Port to use when connecting to SOAP Server',
    )

    arggroup_name = 'Handler Options'
    opt_group = parser.add_argument_group(arggroup_name)
    opt_group.add_argument(
        '-l',
        '--loglevel',
        required=False,
        action='store',
        type=int,
        default=0,
        dest='loglevel',
        help='Logging level to use, increase for more verbosity',
    )
    opt_group.add_argument(
        '--debugformat',
        required=False,
        action='store_true',
        default=False,
        dest='debugformat',
        help="Enable debug format for logging",
    )
    opt_group.add_argument(
        '--debug_method_locals',
        required=False,
        action='store_true',
        default=False,
        dest='debug_method_locals',
        help="Enable debug logging for each methods local variables",
    )
    opt_group.add_argument(
        '--record_all_requests',
        required=False,
        action='store_true',
        default=False,
        dest='record_all_requests',
        help="Record all requests in handler.session.ALL_REQUESTS_RESPONSES",
    )
    opt_group.add_argument(
        '--stats_loop_enabled',
        required=False,
        action='store_true',
        default=False,
        dest='stats_loop_enabled',
        help="Enable the statistics loop",
    )
    opt_group.add_argument(
        '--http_auth_retry',
        required=False,
        action='store_false',
        default=True,
        dest='http_auth_retry',
        help="Disable retry on HTTP authentication failures",
    )
    opt_group.add_argument(
        '--http_retry_count',
        required=False,
        action='store',
        type=int,
        default=5,
        dest='http_retry_count',
        help="Retry count for HTTP failures/invalid responses",
    )
    opt_group.add_argument(
        '--pytan_user_config',
        required=False,
        action='store',
        default='',
        dest='pytan_user_config',
        help=(
            "PyTan User Config file to use for PyTan arguments (defaults to: {})"
        ).format(pytan.constants.PYTAN_USER_CONFIG),
    )
    opt_group.add_argument(
        '--force_server_version',
        required=False,
        action='store',
        default='',
        dest='force_server_version',
        help=(
            "Force PyTan to consider the server version as this, instead of relying on the "
            "server version derived from the server info page."
        ),
    )
    return parser


def setup_parent_parser(doc):
    """Method to setup the base :class:`pytan.utils.CustomArgParse` class for command line scripts using :func:`pytan.utils.setup_parser` and return a parser object for adding arguments to
    """
    parent_parser = setup_parser(desc=doc, help=False)
    parser = CustomArgParse(description=doc, parents=[parent_parser])
    return parser


def setup_write_pytan_user_config_argparser(doc):
    """Method to setup the base :class:`pytan.utils.CustomArgParse` class for command line scripts using :func:`pytan.utils.setup_parser`, then add specific arguments for scripts that use :mod:`pytan` to write a pytan user config file.
    """
    parser = setup_parent_parser(doc=doc)
    output_group = parser.add_argument_group('Write PyTan User Config Options')

    output_group.add_argument(
        '--file',
        required=False,
        default='',
        action='store',
        dest='file',
        help=(
            "PyTan User Config file to write for PyTan arguments (defaults to: {})"
        ).format(pytan.constants.PYTAN_USER_CONFIG),
    )
    return parser


def setup_tsat_argparser(doc):
    """Method to setup the base :class:`pytan.utils.CustomArgParse` class for command line scripts using :func:`pytan.utils.setup_parser`, then add specific arguments for scripts that use :mod:`pytan` to get objects.
    """
    parser = setup_parent_parser(doc=doc)

    output_dir = os.path.join(os.getcwd(), 'TSAT_OUTPUT', pytan.utils.get_now())

    arggroup = parser.add_argument_group('TSAT General Options')
    arggroup.add_argument(
        '--platform',
        required=False,
        default=[],
        action='append',
        dest='platforms',
        help='Only ask questions for sensors on a given platform',
    )
    arggroup.add_argument(
        '--category',
        required=False,
        default=[],
        action='append',
        dest='categories',
        help='Only ask questions for sensors in a given category',
    )
    arggroup.add_argument(
        '--sensor',
        required=False,
        default=[],
        action='append',
        dest='sensors',
        help='Only run sensors that match these supplied names',
    )
    arggroup.add_argument(
        '--add_sensor',
        required=False,
        action='append',
        default=[],
        dest='add_sensor',
        help='Add sensor to every question that gets asked (i.e. "Computer Name")',
    )

    arggroup.add_argument(
        '--output_dir',
        required=False,
        action='store',
        default=output_dir,
        dest='report_dir',
        help='Directory to save output to',
    )
    arggroup.add_argument(
        '--sleep',
        required=False,
        type=int,
        action='store',
        default=1,
        dest='sleep',
        help='Number of seconds to wait between asking questions',
    )
    arggroup.add_argument(
        '--tsatdebug',
        required=False,
        action='store_true',
        default=False,
        dest='tsatdebug',
        help='Enable debug messages for just TSAT (not all of PyTan)',
    )

    group = arggroup.add_mutually_exclusive_group()
    group.add_argument(
        '--prompt_missing_params',
        action='store_true',
        dest='param_prompt',
        default=True,
        required=False,
        help='If a sensor has parameters and none are supplied, prompt for the value (default)'
    )
    group.add_argument(
        '--no_missing_params',
        action='store_false',
        dest='param_prompt',
        default=argparse.SUPPRESS,
        required=False,
        help='If a sensor has parameters and none are supplied, error out.'
    )
    group.add_argument(
        '--skip_missing_params',
        action='store_const',
        const=None,
        dest='param_prompt',
        default=argparse.SUPPRESS,
        required=False,
        help='If a sensor has parameters and none are supplied, skip it',
    )

    arggroup.add_argument(
        '--build_config_file',
        required=False,
        action='store',
        default=None,
        dest='build_config_file',
        help='Build a configuration file by finding all sensors that have parameters and prompting for the values, then saving the key/value pairs as a JSON file that can be used by --config_file',
    )
    arggroup.add_argument(
        '--config_file',
        required=False,
        action='store',
        default=None,
        dest='config_file',
        help='Use a parameter configuration file built by --build_config_file for sensor parameters'
    )
    arggroup.add_argument(
        '-gp',
        '--globalparam',
        required=False,
        action='append',
        nargs=2,
        dest='globalparams',
        default=[],
        help='Global parameters in the format of "KEY" "VALUE" -- if any sensor uses "KEY" as a parameter name, then "VALUE" will be used for that sensors parameter',
    )

    arggroup = parser.add_argument_group('Question Asking Options')

    arggroup.add_argument(
        '-f',
        '--filter',
        required=False,
        action='append',
        default=[],
        dest='question_filters',
        help='Whole question filter; pass --filters-help to get a full description',
    )
    arggroup.add_argument(
        '-o',
        '--option',
        required=False,
        action='append',
        default=[],
        dest='question_options',
        help='Whole question option; pass --options-help to get a full description',
    )

    arggroup = parser.add_argument_group('Answer Polling Options')

    arggroup.add_argument(
        '--complete_pct',
        required=False,
        type=float,
        action='store',
        default=pytan.pollers.QuestionPoller.COMPLETE_PCT_DEFAULT,
        dest='complete_pct',
        help='Percent to consider questions complete',
    )
    arggroup.add_argument(
        '--override_timeout_secs',
        required=False,
        type=int,
        action='store',
        default=0,
        dest='override_timeout_secs',
        help='If supplied and not 0, instead of using the question expiration timestamp as the timeout, timeout after N seconds',
    )
    arggroup.add_argument(
        '--polling_secs',
        required=False,
        type=int,
        action='store',
        default=pytan.pollers.QuestionPoller.POLLING_SECS_DEFAULT,
        dest='polling_secs',
        help='Number of seconds to wait in between GetResultInfo loops while polling for each question',
    )
    arggroup.add_argument(
        '--override_estimated_total',
        required=False,
        type=int,
        action='store',
        default=0,
        dest='override_estimated_total',
        help='If supplied and not 0, use this as the estimated total number of systems instead of what Tanium Platform reports',
    )
    arggroup.add_argument(
        '--force_passed_done_count',
        required=False,
        type=int,
        action='store',
        default=0,
        dest='force_passed_done_count',
        help='If supplied and not 0, when this number of systems have passed the right hand side of the question (the question filter), consider the question complete instead of relying the estimated total that Tanium Platform reports',
    )

    # TODO: LATER, flush out SSE OPTIONS

    # arggroup_name = 'Server Side Export Options'
    # arggroup = parser.add_argument_group(arggroup_name)

    # arggroup.add_argument(
    #     '--sse',
    #     action='store_true',
    #     dest='sse',
    #     default=False,
    #     required=False,
    #     help='Perform a server side export when getting data'
    # )

    # arggroup.add_argument(
    #     '--sse_format',
    #     required=False,
    #     action='store',
    #     default='csv',
    #     choices=['csv', 'xml', 'cef'],
    #     dest='sse_format',
    #     help='If --sse, perform server side export in this format',
    # )

    # arggroup.add_argument(
    #     '--leading',
    #     required=False,
    #     action='store',
    #     default='',
    #     dest='leading',
    #     help='If --sse, and --sse_format = "cef", prepend each row with this text',
    # )
    # arggroup.add_argument(
    #     '--trailing',
    #     required=False,
    #     action='store',
    #     default='',
    #     dest='trailing',
    #     help='If --sse, and --sse_format = "cef", append each row with this text',
    # )

    arggroup_name = 'Answer Export Options'
    arggroup = parser.add_argument_group(arggroup_name)

    arggroup.add_argument(
        '--export_format',
        action='store',
        default='csv',
        choices=['csv', 'xml', 'json'],
        dest='export_format',
        help='If --no_sse, export Format to create report file in',
    )

    group = arggroup.add_mutually_exclusive_group()
    group.add_argument(
        '--sort',
        default=[],
        action='append',
        dest='header_sort',
        required=False,
        help='If --no_sse and --export_format = csv, Sort headers by given names and then sort the rest alphabetically'
    )
    group.add_argument(
        '--no-sort',
        action='store_false',
        dest='header_sort',
        default=argparse.SUPPRESS,
        required=False,
        help='If --no_sse and --export_format = csv, Do not sort the headers at all'
    )
    group.add_argument(
        '--auto_sort',
        action='store_true',
        dest='header_sort',
        default=argparse.SUPPRESS,
        required=False,
        help='If --no_sse and --export_format = csv, Sort the headers with a basic alphanumeric sort'
    )

    group = arggroup.add_mutually_exclusive_group()
    group.add_argument(
        '--add-sensor',
        action='store_true',
        dest='header_add_sensor',
        default=argparse.SUPPRESS,
        required=False,
        help='If --no_sse and --export_format = csv, Add the sensor names to each header'
    )
    group.add_argument(
        '--no-add-sensor',
        action='store_false',
        dest='header_add_sensor',
        default=False,
        required=False,
        help='If --no_sse and --export_format = csv, Do not add the sensor names to each header'
    )

    group = arggroup.add_mutually_exclusive_group()
    group.add_argument(
        '--add-type',
        action='store_true',
        dest='header_add_type',
        default=argparse.SUPPRESS,
        required=False,
        help='If --no_sse and --export_format = csv, Add the result type to each header'
    )
    group.add_argument(
        '--no-add-type',
        action='store_false',
        dest='header_add_type',
        default=False,
        required=False,
        help='If --no_sse and --export_format = csv, Do not add the result type to each header'
    )

    group = arggroup.add_mutually_exclusive_group()
    group.add_argument(
        '--expand-columns',
        action='store_true',
        dest='expand_grouped_columns',
        default=argparse.SUPPRESS,
        required=False,
        help='If --no_sse and --export_format = csv, Expand multi-line cells into their own rows that have sensor correlated columns in the new rows'
    )
    group.add_argument(
        '--no-columns',
        action='store_false',
        dest='expand_grouped_columns',
        default=False,
        required=False,
        help='If --no_sse and --export_format = csv, Do not add expand multi-line cells into their own rows'
    )

    arggroup = parser.add_argument_group('PyTan Help Options')
    arggroup.add_argument(
        '--sensors-help',
        required=False,
        action='store_true',
        default=False,
        dest='sensors_help',
        help='Get the full help for sensor strings and exit',
    )
    arggroup.add_argument(
        '--filters-help',
        required=False,
        action='store_true',
        default=False,
        dest='filters_help',
        help='Get the full help for filters strings and exit',
    )
    arggroup.add_argument(
        '--options-help',
        required=False,
        action='store_true',
        default=False,
        dest='options_help',
        help='Get the full help for options strings and exit',
    )

    arggroup = parser.add_argument_group('TSAT Show Options')
    arggroup.add_argument(
        '--show_platforms',
        required=False,
        action='store_true',
        default=False,
        dest='show_platforms',
        help='Print a list of all valid platforms (does not run sensors)',
    )
    arggroup.add_argument(
        '--show_categories',
        required=False,
        action='store_true',
        default=False,
        dest='show_categories',
        help='Print a list of all valid categories (does not run sensors)',
    )
    arggroup.add_argument(
        '--show_sensors',
        required=False,
        action='store_true',
        default=False,
        dest='show_sensors',
        help='Print a list of all valid sensor names, their categories, their platforms, and their parameters (does not run sensors)',
    )
    return parser


def setup_get_object_argparser(obj, doc):
    """Method to setup the base :class:`pytan.utils.CustomArgParse` class for command line scripts using :func:`pytan.utils.setup_parser`, then add specific arguments for scripts that use :mod:`pytan` to get objects.
    """
    parser = setup_parent_parser(doc=doc)
    arggroup_name = 'Get {} Options'.format(obj.replace('_', ' ').capitalize())
    get_object_group = parser.add_argument_group(arggroup_name)

    get_object_group.add_argument(
        '--all',
        required=False,
        default=False,
        action='store_true',
        dest='all',
        help='Get all {}s'.format(obj),
    )

    obj_map = pytan.utils.get_obj_map(obj)
    search_keys = copy.copy(obj_map['search'])

    if 'id' not in search_keys:
        search_keys.append('id')

    if obj == 'whitelisted_url':
        search_keys.append('url_regex')
    elif obj == 'user':
        search_keys.append('name')

    for k in search_keys:
        get_object_group.add_argument(
            '--{}'.format(k),
            required=False,
            action='append',
            default=[],
            dest=k,
            help='{} of {} to get'.format(k, obj),
        )

    return parser


def setup_print_server_info_argparser(doc):
    """Method to setup the base :class:`pytan.utils.CustomArgParse` class for command line scripts using :func:`pytan.utils.setup_parser`, then add specific arguments for scripts that use :mod:`pytan` to print sensor info.
    """
    parser = setup_parent_parser(doc=doc)
    output_group = parser.add_argument_group('Output Options')

    output_group.add_argument(
        '--json',
        required=False,
        default=False,
        action='store_true',
        dest='json',
        help='Show a json dump of the server information',
    )
    return parser


def setup_print_sensors_argparser(doc):
    """Method to setup the base :class:`pytan.utils.CustomArgParse` class for command line scripts using :func:`pytan.utils.setup_parser`, then add specific arguments for scripts that use :mod:`pytan` to print server info.
    """
    parser = setup_get_object_argparser(obj='sensor', doc=__doc__)
    output_group = parser.add_argument_group('Output Options')
    output_group.add_argument(
        '--category',
        required=False,
        default=[],
        action='append',
        dest='categories',
        help='Only show sensors in given category',
    )
    output_group.add_argument(
        '--platform',
        required=False,
        default=[],
        action='append',
        dest='platforms',
        help='Only show sensors for given platform',
    )
    output_group.add_argument(
        '--hide_params',
        required=False,
        default=False,
        action='store_true',
        dest='hide_params',
        help='Do not show parameters in output',
    )
    output_group.add_argument(
        '--params_only',
        required=False,
        default=False,
        action='store_true',
        dest='params_only',
        help='Only show sensors with parameters',
    )
    output_group.add_argument(
        '--json',
        required=False,
        default=False,
        action='store_true',
        dest='json',
        help='Show a json dump of the server information',
    )
    return parser


def setup_create_sensor_argparser(doc):
    """Method to setup the base :class:`pytan.utils.CustomArgParse` class for command line scripts using :func:`pytan.utils.setup_parser`, then add specific arguments for scripts that use :mod:`pytan` to create a sensor.
    """
    parser = setup_parser(desc=doc, help=True)
    arggroup_name = 'Create Sensor Options'
    arggroup = parser.add_argument_group(arggroup_name)

    arggroup.add_argument(
        '--unsupported',
        required=False,
        action='store',
        dest='unsupported',
        default=None,
        help='Creating sensors using this method not yet supported, use create_sensor_from_json instead!',
    )
    return parser


def setup_create_group_argparser(doc):
    """Method to setup the base :class:`pytan.utils.CustomArgParse` class for command line scripts using :func:`pytan.utils.setup_parser`, then add specific arguments for scripts that use :mod:`pytan` to create a group.
    """
    parser = setup_parser(desc=doc, help=True)
    arggroup_name = 'Create Group Options'
    arggroup = parser.add_argument_group(arggroup_name)

    arggroup.add_argument(
        '-n',
        '--name',
        required=True,
        action='store',
        dest='groupname',
        default=None,
        help='Name of group to create',
    )

    arggroup.add_argument(
        '-f',
        '--filter',
        required=False,
        action='append',
        dest='filters',
        default=[],
        help='Filters to use for group, supply --filters-help to see filter help',
    )

    arggroup.add_argument(
        '-o',
        '--option',
        required=False,
        action='append',
        dest='filter_options',
        default=[],
        help='Filter options to use for group, supply --options-help to see options'
        ' help',
    )

    arggroup.add_argument(
        '--filters-help',
        required=False,
        action='store_true',
        default=False,
        dest='filters_help',
        help='Get the full help for filters strings',
    )

    arggroup.add_argument(
        '--options-help',
        required=False,
        action='store_true',
        default=False,
        dest='options_help',
        help='Get the full help for options strings',
    )
    return parser


def setup_create_whitelisted_url_argparser(doc):
    """Method to setup the base :class:`pytan.utils.CustomArgParse` class for command line scripts using :func:`pytan.utils.setup_parser`, then add specific arguments for scripts that use :mod:`pytan` to create a whitelisted_url.
    """
    parser = setup_parser(desc=doc, help=True)
    arggroup_name = 'Create Whitelisted URL Options'
    arggroup = parser.add_argument_group(arggroup_name)

    arggroup.add_argument(
        '--url',
        required=True,
        action='store',
        dest='url',
        default=None,
        help='Text of new Whitelisted URL',
    )

    arggroup.add_argument(
        '--regex',
        required=False,
        action='store_true',
        dest='regex',
        default=False,
        help='Whitelisted URL is a regex pattern',
    )

    arggroup.add_argument(
        '-d',
        '--download',
        required=False,
        action='store',
        dest='download_seconds',
        type=int,
        default=86400,
        help='Download Whitelisted URL every N seconds',
    )

    arggroup.add_argument(
        '-prop',
        '--property',
        required=False,
        action='append',
        dest='properties',
        nargs=2,
        default=[],
        help='Property name and value to assign to Whitelisted URL',
    )
    return parser


def setup_create_package_argparser(doc):
    """Method to setup the base :class:`pytan.utils.CustomArgParse` class for command line scripts using :func:`pytan.utils.setup_parser`, then add specific arguments for scripts that use :mod:`pytan` to create a package.
    """
    parser = setup_parser(desc=doc, help=True)
    arggroup_name = 'Create Package Options'
    arggroup = parser.add_argument_group(arggroup_name)

    arggroup.add_argument(
        '-n',
        '--name',
        required=True,
        action='store',
        dest='name',
        default=None,
        help='Name of package to create',
    )

    arggroup.add_argument(
        '-c',
        '--command',
        required=True,
        action='store',
        dest='command',
        default='',
        help='Command to execute with package',
    )

    arggroup.add_argument(
        '-d',
        '--display-name',
        required=False,
        action='store',
        dest='display_name',
        default='',
        help='Display name of package',
    )

    arggroup.add_argument(
        '--command-timeout',
        required=False,
        action='store',
        dest='command_timeout_seconds',
        type=int,
        default=600,
        help='Command for this package timeout in N seconds',
    )

    arggroup.add_argument(
        '--expire-seconds',
        required=False,
        action='store',
        dest='expire_seconds',
        type=int,
        default=600,
        help='Expire actions created for this package in N seconds',
    )

    arggroup.add_argument(
        '-f',
        '--file-url',
        required=False,
        action='store',
        dest='file_urls',
        default=[],
        help='URL of file to include with package, can specify any of the '
        'following: "$url", or "$download_seconds::$url", or "$filename||$url",'
        ' or "$filename||$download_seconds::$url"',
    )

    arggroup.add_argument(
        '--parameters-file',
        required=False,
        action='store',
        dest='parameters_json_file',
        default='',
        help='JSON file describing parameters for this package, see '
        'doc/example_of_all_package_parameters.json for an example',
    )
    arggroup.add_argument(
        '-vf',
        '--verify-filter',
        required=False,
        action='append',
        dest='verify_filters',
        default=[],
        help='Filters to use for verifying the package after it is deployed, '
        ', supply --filters-help to see filter help',
    )

    arggroup.add_argument(
        '-vo',
        '--verify-option',
        required=False,
        action='append',
        dest='verify_filter_options',
        default=[],
        help='Options to use for the verify filters, supply --options-help to see '
        'options help',
    )

    arggroup.add_argument(
        '--filters-help',
        required=False,
        action='store_true',
        default=False,
        dest='filters_help',
        help='Get the full help for filters strings',
    )

    arggroup.add_argument(
        '--options-help',
        required=False,
        action='store_true',
        default=False,
        dest='options_help',
        help='Get the full help for options strings',
    )

    arggroup.add_argument(
        '--verify-expire-seconds',
        required=False,
        action='store',
        dest='verify_expire_seconds',
        type=int,
        default=600,
        help='Expire the verify filters used by this package in N seconds',
    )
    return parser


def setup_pytan_shell_argparser(doc):
    """Method to setup the base :class:`pytan.utils.CustomArgParse` class for command line scripts using :func:`pytan.utils.setup_parser`, then add specific arguments for scripts that use :mod:`pytan` to create a python shell.
    """
    parser = setup_parser(desc=doc, help=True)
    return parser


def setup_get_session_argparser(doc):
    """Method to setup the base :clas:`pytan.utils.CustomArgParse` class for command line scripts using :func:`pytan.utils.setup_parser`,then add specific
        arguments for scripts that use :mod:`pytan` to create a tanium session.
    """
    parser = setup_parser(desc=doc, help=True)
    arggroup_name = 'Get Session Options'
    arggroup = parser.add_argument_group(arggroup_name)

    arggroup.add_argument(
        '--persistent',
        required=False,
        action='store_true',
        dest='persistent',
        default=argparse.SUPPRESS,
        help='Persist session for 1 week after last use.',
    )

    return parser


def setup_close_session_argparser(doc):
    """Method to setup the base :class:`pytan.utils.CustomArgParse` class for command line scripts using :func:`pytan.utils.setup_parser`,then add specific
        arguments for scripts that use :mod:`pytan` to close open tanium sessions.
    """
    parser = setup_parser(desc=doc, help=True)
    arggroup_name = 'Close Session Optipons'
    arggroup = parser.add_argument_group(arggroup_name)

    arggroup.add_argument(
        '--all_session_ids',
        required=False,
        action='store_true',
        dest='all_session_ids',
        default=argparse.SUPPRESS,
        help='Closes all open tanium sessions.'
    )

    return parser


def setup_create_user_argparser(doc):
    """Method to setup the base :class:`pytan.utils.CustomArgParse` class for command line scripts using :func:`pytan.utils.setup_parser`, then add specific arguments for scripts that use :mod:`pytan` to create a user.
    """
    parser = setup_parser(desc=doc, help=True)
    arggroup_name = 'Create User Options'
    arggroup = parser.add_argument_group(arggroup_name)

    arggroup.add_argument(
        '-n',
        '--name',
        required=True,
        action='store',
        dest='name',
        default=None,
        help='Name of user to create',
    )

    arggroup.add_argument(
        '-rn',
        '--rolename',
        required=False,
        action='append',
        dest='rolename',
        default=[],
        help='Name of role to assign to new user',
    )

    arggroup.add_argument(
        '-ri',
        '--roleid',
        required=False,
        action='append',
        type=int,
        dest='roleid',
        default=[],
        help='ID of role to assign to new user',
    )
    arggroup.add_argument(
        '-g',
        '--group',
        required=False,
        action='store',
        dest='group',
        default='',
        help='Name of group to assign to user',
    )

    arggroup.add_argument(
        '-prop',
        '--property',
        required=False,
        action='append',
        dest='properties',
        nargs=2,
        default=[],
        help='Property name and value to assign to user',
    )
    return parser


def setup_create_json_object_argparser(obj, doc):
    """Method to setup the base :class:`pytan.utils.CustomArgParse` class for command line scripts using :func:`pytan.utils.setup_parser`, then add specific arguments for scripts that use :mod:`pytan` to create objects from json files.
    """
    parser = setup_parent_parser(doc=doc)
    arggroup_name = 'Create {} from JSON Options'.format(obj.replace('_', ' ').capitalize())
    arggroup = parser.add_argument_group(arggroup_name)
    arggroup.add_argument(
        '-j',
        '--json',
        required=True,
        action='store',
        default='',
        dest='json_file',
        help='JSON file to use for creating the object',
    )
    return parser


def setup_delete_object_argparser(obj, doc):
    """Method to setup the base :class:`pytan.utils.CustomArgParse` class for command line scripts using :func:`pytan.utils.setup_parser`, then add specific arguments for scripts that use :mod:`pytan` to delete objects.
    """
    parser = setup_parent_parser(doc=doc)
    arggroup_name = 'Delete {} Options'.format(obj.replace('_', ' ').capitalize())
    arggroup = parser.add_argument_group(arggroup_name)

    obj_map = pytan.utils.get_obj_map(obj)
    search_keys = copy.copy(obj_map['search'])

    if obj == 'whitelisted_url':
        search_keys.append('url_regex')
    elif obj == 'user':
        search_keys.append('name')

    for k in search_keys:
        arggroup.add_argument(
            '--{}'.format(k),
            required=False,
            action='append',
            default=[],
            dest=k,
            help='{} of {} to get'.format(k, obj),
        )

    return parser


def setup_ask_saved_argparser(doc):
    """Method to setup the base :class:`pytan.utils.CustomArgParse` class for command line scripts using :func:`pytan.utils.setup_parser`, then add specific arguments for scripts that use :mod:`pytan` to ask saved questions.
    """
    parser = setup_parent_parser(doc=doc)
    arggroup_name = 'Saved Question Options'
    arggroup = parser.add_argument_group(arggroup_name)

    arggroup_name = 'Saved Question Selectors'
    arggroup = parser.add_argument_group(arggroup_name)

    group = arggroup.add_mutually_exclusive_group()

    group.add_argument(
        '--no-refresh_data',
        action='store_false',
        dest='refresh_data',
        default=argparse.SUPPRESS,
        required=False,
        help='Do not refresh the data available for a saved question (default)'
    )

    group.add_argument(
        '--refresh_data',
        action='store_true',
        dest='refresh_data',
        default=argparse.SUPPRESS,
        required=False,
        help='Refresh the data available for a saved question',
    )

    group = arggroup.add_mutually_exclusive_group()

    obj = 'saved_question'
    obj_map = pytan.utils.get_obj_map(obj)
    search_keys = copy.copy(obj_map['search'])
    for k in search_keys:
        group.add_argument(
            '--{}'.format(k),
            required=False,
            action='store',
            dest=k,
            help='{} of {} to ask'.format(k, obj),
        )

    parser = add_ask_report_argparser(parser=parser)
    return parser


def setup_approve_saved_action_argparser(doc):
    """Method to setup the base :class:`pytan.utils.CustomArgParse` class for command line scripts using :func:`pytan.utils.setup_parser`, then add specific arguments for scripts that use :mod:`pytan` to approve saved actions.
    """
    parser = setup_parent_parser(doc=doc)
    arggroup_name = 'Approve Saved Action Options'
    arggroup = parser.add_argument_group(arggroup_name)

    arggroup.add_argument(
        '-i',
        '--id',
        required=True,
        type=int,
        action='store',
        dest='id',
        help='ID of Saved Action to approve',
    )

    return parser


def setup_stop_action_argparser(doc):
    """Method to setup the base :class:`pytan.utils.CustomArgParse` class for command line scripts using :func:`pytan.utils.setup_parser`, then add specific arguments for scripts that use :mod:`pytan` to stop actions.
    """
    parser = setup_parent_parser(doc=doc)
    arggroup_name = 'Stop Action Options'
    arggroup = parser.add_argument_group(arggroup_name)

    arggroup.add_argument(
        '-i',
        '--id',
        required=True,
        type=int,
        action='store',
        dest='id',
        help='ID of Deploy Action to stop',
    )

    return parser


def setup_deploy_action_argparser(doc):
    """Method to setup the base :class:`pytan.utils.CustomArgParse` class for command line scripts using :func:`pytan.utils.setup_parser`, then add specific arguments for scripts that use :mod:`pytan` to deploy actions.
    """
    parser = setup_parent_parser(doc=doc)
    arggroup_name = 'Deploy Action Options'
    arggroup = parser.add_argument_group(arggroup_name)

    arggroup.add_argument(
        '--run',
        required=False,
        action='store_true',
        default=False,
        dest='run',
        help='Run the deploy action, if not supplied the deploy action will '
        'only ask the question that matches --filter and save the results to '
        'csv file for verification',
    )

    group = arggroup.add_mutually_exclusive_group()

    group.add_argument(
        '--no-results',
        action='store_false',
        dest='get_results',
        default=argparse.SUPPRESS,
        required=False,
        help='Do not get the results after starting the deploy '
        'action'
    )
    group.add_argument(
        '--results',
        action='store_true',
        dest='get_results',
        default=True,
        required=False,
        help='Get the results after starting the deploy action '
        '(default)',
    )

    arggroup.add_argument(
        '-k',
        '--package',
        required=False,
        action='store',
        default='',
        dest='package',
        help='Package to deploy action with, optionally describe parameters, '
        'pass --package-help to get a full description',
    )

    arggroup.add_argument(
        '-f',
        '--filter',
        required=False,
        action='append',
        default=[],
        dest='action_filters',
        help='Filter to deploy action against; pass --filters-help'
        'to get a full description',
    )

    arggroup.add_argument(
        '-o',
        '--option',
        required=False,
        action='append',
        default=[],
        dest='action_options',
        help='Options for deploy action filter; pass --options-help to get a '
        'full description',
    )

    arggroup.add_argument(
        '--start_seconds_from_now',
        required=False,
        action='store',
        type=int,
        default=None,
        dest='start_seconds_from_now',
        help='Start the action N seconds from now',
    )

    arggroup.add_argument(
        '--expire_seconds',
        required=False,
        action='store',
        type=int,
        default=None,
        dest='expire_seconds',
        help='Expire the action N seconds after it starts, if not supplied '
        'the packages own expire_seconds will be used',
    )

    arggroup.add_argument(
        '--package-help',
        required=False,
        action='store_true',
        default=False,
        dest='package_help',
        help='Get the full help for package string',
    )

    arggroup.add_argument(
        '--filters-help',
        required=False,
        action='store_true',
        default=False,
        dest='filters_help',
        help='Get the full help for filters strings',
    )

    arggroup.add_argument(
        '--options-help',
        required=False,
        action='store_true',
        default=False,
        dest='options_help',
        help='Get the full help for options strings',
    )
    parser = add_report_file_options(parser=parser)
    return parser


def setup_get_results_argparser(doc):
    """Method to setup the base :class:`pytan.utils.CustomArgParse` class for command line scripts using :func:`pytan.utils.setup_parser`, then add specific arguments for scripts that use :mod:`pytan` to get results for questions or actions.
    """
    parser = setup_parent_parser(doc=doc)
    arggroup_name = 'Get Result Options'
    arggroup = parser.add_argument_group(arggroup_name)

    arggroup.add_argument(
        '-o',
        '--object',
        action='store',
        default='question',
        choices=['saved_question', 'question', 'action'],
        dest='objtype',
        help='Type of object to get results for',
    )

    arggroup.add_argument(
        '-i',
        '--id',
        required=False,
        action='store',
        type=int,
        dest='id',
        help='id of object to get results for',
    )

    arggroup.add_argument(
        '-n',
        '--name',
        required=False,
        action='store',
        default='',
        dest='name',
        help='name of object to get results for',
    )
    parser = add_ask_report_argparser(parser)
    return parser


def setup_ask_parsed_argparser(doc):
    """Method to setup the base :class:`pytan.utils.CustomArgParse` class for command line scripts using :func:`pytan.utils.setup_parser`, then add specific arguments for scripts that use :mod:`pytan` to ask parsed questions.
    """
    parser = setup_parent_parser(doc=doc)
    arggroup_name = 'Parsed Question Options'
    arggroup = parser.add_argument_group(arggroup_name)

    arggroup.add_argument(
        '-q',
        '--question_text',
        required=True,
        action='store',
        default='',
        dest='question_text',
        help='The question text you want the server to parse into a list of parsed results',
    )

    arggroup.add_argument(
        '--picker',
        required=False,
        action='store',
        type=int,
        dest='picker',
        help='The index number of the parsed results that correlates to the actual question you wish to run -- you can get this by running this once without it to print out a list of indexes',
    )

    group = arggroup.add_mutually_exclusive_group()

    group.add_argument(
        '--no-results',
        action='store_false',
        dest='get_results',
        default=argparse.SUPPRESS,
        required=False,
        help='Do not get the results after asking the quesiton '
        'action'
    )
    group.add_argument(
        '--results',
        action='store_true',
        dest='get_results',
        default=True,
        required=False,
        help='Get the results after asking the quesiton (default)',
    )
    parser = add_ask_report_argparser(parser=parser)
    return parser


def setup_ask_manual_argparser(doc):
    """Method to setup the base :class:`pytan.utils.CustomArgParse` class for command line scripts using :func:`pytan.utils.setup_parser`, then add specific arguments for scripts that use :mod:`pytan` to ask manual questions.
    """
    parser = setup_parent_parser(doc=doc)
    arggroup_name = 'Manual Question Options'
    arggroup = parser.add_argument_group(arggroup_name)

    arggroup.add_argument(
        '-s',
        '--sensor',
        required=False,
        action='append',
        default=[],
        dest='sensors',
        help='Sensor, optionally describe parameters, options, and a filter'
        '; pass --sensors-help to get a full description',
    )

    arggroup.add_argument(
        '-f',
        '--filter',
        required=False,
        action='append',
        default=[],
        dest='question_filters',
        help='Whole question filter; pass --filters-help to get a full description',
    )

    arggroup.add_argument(
        '-o',
        '--option',
        required=False,
        action='append',
        default=[],
        dest='question_options',
        help='Whole question option; pass --options-help to get a full description',
    )

    arggroup.add_argument(
        '--sensors-help',
        required=False,
        action='store_true',
        default=False,
        dest='sensors_help',
        help='Get the full help for sensor strings',
    )

    arggroup.add_argument(
        '--filters-help',
        required=False,
        action='store_true',
        default=False,
        dest='filters_help',
        help='Get the full help for filters strings',
    )

    arggroup.add_argument(
        '--options-help',
        required=False,
        action='store_true',
        default=False,
        dest='options_help',
        help='Get the full help for options strings',
    )
    group = arggroup.add_mutually_exclusive_group()

    group.add_argument(
        '--no-results',
        action='store_false',
        dest='get_results',
        default=argparse.SUPPRESS,
        required=False,
        help='Do not get the results after asking the quesiton '
        'action'
    )
    group.add_argument(
        '--results',
        action='store_true',
        dest='get_results',
        default=True,
        required=False,
        help='Get the results after asking the quesiton '
        '(default)',
    )
    group.add_argument(
        '--complete_pct',
        required=False,
        type=float,
        action='store',
        default=pytan.pollers.QuestionPoller.COMPLETE_PCT_DEFAULT,
        dest='complete_pct',
        help='Percent to consider questions complete',
    )
    parser = add_ask_report_argparser(parser=parser)
    return parser


def add_ask_report_argparser(parser):
    """Method to extend a :class:`pytan.utils.CustomArgParse` class for command line scripts with arguments for scripts that need to supply export format subparsers for asking questions.
    """
    parser = add_report_file_options(parser=parser)

    arggroup_name = 'Export Options'
    arggroup = parser.add_argument_group(arggroup_name)

    group = arggroup.add_mutually_exclusive_group()
    group.add_argument(
        '--enable_sse',
        action='store_true',
        dest='sse',
        default=True,
        required=False,
        help='Perform a server side export when getting data'
    )
    group.add_argument(
        '--disable_sse',
        action='store_false',
        dest='sse',
        required=False,
        help='Perform a normal get result data export when getting data'
    )

    arggroup.add_argument(
        '--sse_format',
        required=False,
        action='store',
        default='xml_obj',
        choices=['csv', 'xml', 'xml_obj', 'cef'],
        dest='sse_format',
        help='If sse = True, perform server side export in this format',
    )

    arggroup.add_argument(
        '--leading',
        required=False,
        action='store',
        default='',
        dest='leading',
        help='If sse = True, and sse_format = "cef", prepend each row with this text',
    )
    arggroup.add_argument(
        '--trailing',
        required=False,
        action='store',
        default='',
        dest='trailing',
        help='If sse = True, and sse_format = "cef", append each row with this text',
    )

    arggroup.add_argument(
        '--export_format',
        action='store',
        default='csv',
        choices=['csv', 'xml', 'json'],
        dest='export_format',
        help='Export Format to create report file in, only used if sse = False',
    )

    group = arggroup.add_mutually_exclusive_group()
    group.add_argument(
        '--sort',
        default=[],
        action='append',
        dest='header_sort',
        required=False,
        help='For export_format: csv, Sort headers by given names'
    )
    group.add_argument(
        '--no-sort',
        action='store_false',
        dest='header_sort',
        default=argparse.SUPPRESS,
        required=False,
        help='For export_format: csv, Do not sort the headers at all'
    )
    group.add_argument(
        '--auto_sort',
        action='store_true',
        dest='header_sort',
        default=argparse.SUPPRESS,
        required=False,
        help='For export_format: csv, Sort the headers with a basic alphanumeric sort (default)'
    )

    group = arggroup.add_mutually_exclusive_group()
    group.add_argument(
        '--add-sensor',
        action='store_true',
        dest='header_add_sensor',
        default=argparse.SUPPRESS,
        required=False,
        help='For export_format: csv, Add the sensor names to each header'
    )
    group.add_argument(
        '--no-add-sensor',
        action='store_false',
        dest='header_add_sensor',
        default=argparse.SUPPRESS,
        required=False,
        help='For export_format: csv, Do not add the sensor names to each header (default)'
    )

    group = arggroup.add_mutually_exclusive_group()
    group.add_argument(
        '--add-type',
        action='store_true',
        dest='header_add_type',
        default=argparse.SUPPRESS,
        required=False,
        help='For export_format: csv, Add the result type to each header'
    )
    group.add_argument(
        '--no-add-type',
        action='store_false',
        dest='header_add_type',
        default=argparse.SUPPRESS,
        required=False,
        help='For export_format: csv, Do not add the result type to each header (default)'
    )

    group = arggroup.add_mutually_exclusive_group()
    group.add_argument(
        '--expand-columns',
        action='store_true',
        dest='expand_grouped_columns',
        default=argparse.SUPPRESS,
        required=False,
        help='For export_format: csv, Expand multi-line cells into their own rows that have sensor correlated columns in the new rows'
    )
    group.add_argument(
        '--no-columns',
        action='store_false',
        dest='expand_grouped_columns',
        default=argparse.SUPPRESS,
        required=False,
        help='For export_format: csv, Do not add expand multi-line cells into their own rows (default)'
    )
    return parser


def add_report_file_options(parser):
    """Method to extend a :class:`pytan.utils.CustomArgParse` class for command line scripts with arguments for scripts that need to supply export file and directory options.
    """
    opt_group = parser.add_argument_group('Report File Options')
    opt_group.add_argument(
        '--file',
        required=False,
        action='store',
        default=None,
        dest='report_file',
        help='File to save report to (will be automatically generated if not '
        'supplied)',
    )
    opt_group.add_argument(
        '--dir',
        required=False,
        action='store',
        default=None,
        dest='report_dir',
        help='Directory to save report to (current directory will be used if '
        'not supplied)',
    )
    return parser


def add_get_object_report_argparser(parser):
    """Method to extend a :class:`pytan.utils.CustomArgParse` class for command line scripts with arguments for scripts that need to supply export format subparsers for getting objects.
    """
    parser = add_report_file_options(parser)
    arggroup_name = 'Export Options'
    arggroup = parser.add_argument_group(arggroup_name)

    arggroup.add_argument(
        '--export_format',
        action='store',
        default='csv',
        choices=['csv', 'xml', 'json'],
        dest='export_format',
        help='Export Format to create report file in, only used if sse = False',
    )

    group = arggroup.add_mutually_exclusive_group()
    group.add_argument(
        '--sort',
        default=[],
        action='append',
        dest='header_sort',
        required=False,
        help='Only for export_format csv, Sort headers by given names'
    )
    group.add_argument(
        '--no-sort',
        action='store_false',
        dest='header_sort',
        default=argparse.SUPPRESS,
        required=False,
        help='Only for export_format csv, Do not sort the headers at all'
    )
    group.add_argument(
        '--auto_sort',
        action='store_true',
        dest='header_sort',
        default=argparse.SUPPRESS,
        required=False,
        help='Only for export_format csv, Sort the headers with a basic alphanumeric sort (default)'
    )

    group = arggroup.add_mutually_exclusive_group()
    group.add_argument(
        '--no-explode-json',
        action='store_false',
        dest='explode_json_string_values',
        default=argparse.SUPPRESS,
        required=False,
        help='Only for export_format csv or json, Do not explode any embedded JSON into their own columns'
    )
    group.add_argument(
        '--explode-json',
        action='store_true',
        dest='explode_json_string_values',
        default=argparse.SUPPRESS,
        required=False,
        help='Only for export_format csv or json, Only for export_format csv, Explode any embedded JSON into their own columns (default)'
    )

    group = arggroup.add_mutually_exclusive_group()
    group.add_argument(
        '--no-include_type',
        action='store_false',
        dest='include_type',
        default=argparse.SUPPRESS,
        required=False,
        help='Only for export_format json, Do not include SOAP type in JSON output'
    )
    group.add_argument(
        '--include_type',
        action='store_true',
        dest='include_type',
        required=False,
        default=argparse.SUPPRESS,
        help='Only for export_format json, Include SOAP type in JSON output (default)'
    )

    group = arggroup.add_mutually_exclusive_group()
    group.add_argument(
        '--no-minimal',
        action='store_false',
        dest='minimal',
        default=argparse.SUPPRESS,
        required=False,
        help='Only for export_format xml, Produce the full XML representation, including empty attributes'
    )
    group.add_argument(
        '--minimal',
        action='store_true',
        dest='minimal',
        default=argparse.SUPPRESS,
        required=False,
        help='Only for export_format xml, Only include attributes that are not empty (default)'
    )

    return parser


def setup_get_saved_question_history_argparser(doc):
    """Method to setup the base :class:`pytan.utils.CustomArgParse` class for command line scripts using :func:`pytan.utils.setup_parser`, then add specific arguments for scripts that use :mod:`pytan` to get saved question history.
    """
    parser = setup_parent_parser(doc=doc)

    arggroup_name = 'Saved Question Options'
    arggroup = parser.add_argument_group(arggroup_name)

    group = arggroup.add_mutually_exclusive_group()

    group.add_argument(
        '--no-empty_results',
        action='store_false',
        dest='empty_results',
        default=argparse.SUPPRESS,
        required=False,
        help='Do not include details for questions with no data (default)'
    )

    group.add_argument(
        '--empty_results',
        action='store_true',
        dest='empty_results',
        default=argparse.SUPPRESS,
        required=False,
        help='Include details for questions with no data ',
    )

    group = arggroup.add_mutually_exclusive_group()

    group.add_argument(
        '--no-all_questions',
        action='store_false',
        dest='all_questions',
        default=argparse.SUPPRESS,
        required=False,
        help='Do not include details for ALL questions, only the ones associated with a given saved question via --name or --id (default)'
    )

    group.add_argument(
        '--all_questions',
        action='store_true',
        dest='all_questions',
        default=argparse.SUPPRESS,
        required=False,
        help='Include details for ALL questions',
    )

    opt_group = parser.add_argument_group('Report File Options')
    opt_group.add_argument(
        '--file',
        required=False,
        action='store',
        default='pytan_question_history_{}.csv'.format(pytan.utils.get_now()),
        dest='report_file',
        help='File to save report to',
    )
    opt_group.add_argument(
        '--dir',
        required=False,
        action='store',
        default=None,
        dest='report_dir',
        help='Directory to save report to (current directory will be used if not supplied)',
    )

    arggroup_name = 'Saved Question Selectors'
    arggroup = parser.add_argument_group(arggroup_name)

    group = arggroup.add_mutually_exclusive_group()

    obj = 'saved_question'
    obj_map = pytan.utils.get_obj_map(obj)
    search_keys = copy.copy(obj_map['search'])
    for k in search_keys:
        group.add_argument(
            '--{}'.format(k),
            required=False,
            action='store',
            dest=k,
            help='{} of {} to ask'.format(k, obj),
        )

    return parser


def process_get_saved_question_history_args(parser, handler, args):
    """Process command line args supplied by user for getting saved question history

    Parameters
    ----------
    parser : :class:`argparse.ArgParse`
        * ArgParse object used to parse `all_args`
    handler : :class:`pytan.handler.Handler`
        * Instance of Handler created from command line args
    args : args object
        * args parsed from `parser`

    Returns
    -------
    response : :class:`taniumpy.object_types.base.BaseType`
        * response from :func:`pytan.handler.Handler.create_user`
    """

    all_questions_bool = args.__dict__.get('all_questions', False)
    empty_results_bool = args.__dict__.get('empty_results', False)

    # if the user didn't specify ALL questions, lets find the saved question object so we can
    # filter all the questions down to just the ones for this saved question
    if not all_questions_bool:
        get_args = {'objtype': 'saved_question'}

        if args.id:
            get_args['id'] = args.id
        elif args.name:
            get_args['name'] = args.name
        else:
            parser.error("Must supply --id or --name of saved question if not using --all_questions")

        print "++ Finding saved question: {}".format(pytan.utils.jsonify(get_args))

        try:
            saved_question = handler.get(**get_args)[0]
        except Exception as e:
            traceback.print_exc()
            print "\n\nError occurred: {}".format(e)
            sys.exit(99)

        print "Found Saved Question: '{}'".format(saved_question)

    # get all questions
    try:
        all_questions = handler.get_all('question', include_hidden_flag=1)
    except Exception as e:
        traceback.print_exc()
        print "\n\nError occurred: {}".format(e)
        sys.exit(99)

    print "Found {} Total Questions".format(len(all_questions))

    if not all_questions_bool:
        all_questions = [
            x for x in all_questions
            if getattr(x.saved_question, 'id', '') == saved_question.id
        ]

        print (
            "Found {} Questions asked for Saved_question '{}'"
        ).format(len(all_questions), saved_question)

    print "Getting ResultInfo for {} Questions".format(len(all_questions))

    # store the ResultInfo for each question as x.result_info
    [
        setattr(x, 'result_info', handler.get_result_info(x))
        for x in all_questions
    ]

    if not empty_results_bool:
        all_questions = [
            x for x in all_questions
            if x.result_info.row_count
        ]
        print "Found {} Questions that actually have data".format(len(all_questions))

    # flatten out saved_question.id
    [
        setattr(x, 'saved_question_id', getattr(x.saved_question, 'id', '???'))
        for x in all_questions
    ]

    # derive start time from expiration and expire_seconds
    [
        setattr(x, 'start_time', pytan.utils.calculate_question_start_time(x)[0])
        for x in all_questions
    ]

    # flatten out result info attributes
    result_info_attrs = [
        'row_count',
        'estimated_total',
        'mr_tested',
        'passed',
    ]
    [
        setattr(x, y, getattr(x.result_info, y, '???'))
        for x in all_questions
        for y in result_info_attrs
    ]

    # dictify all questions for use with csv_dictwriter
    question_attrs = [
        'id',
        'query_text',
        'saved_question_id',
        'start_time',
        'expiration',
        'row_count',
        'estimated_total',
        'mr_tested',
        'passed',
    ]

    human_map = [
        'Question ID',
        'Question Text',
        'Spawned by Saved Question ID',
        'Question Started',
        'Question Expired',
        'Row Count',
        'Client Count Right Now',
        'Client Count that saw this question',
        'Client Count that passed this questions filters',
    ]

    all_question_dicts = [
        {human_map[question_attrs.index(k)]: str(getattr(x, k, '???')) for k in question_attrs}
        for x in all_questions
    ]

    # turn the list of dicts into a CSV string
    all_question_csv = csvdictwriter(
        rows_list=all_question_dicts,
        headers=human_map,
    )

    report_file = handler.create_report_file(
        contents=all_question_csv,
        report_file=args.report_file,
        report_dir=args.report_dir,
    )

    print "Wrote {} bytes to report file: '{}'".format(len(all_question_csv), report_file)
    return report_file


def process_create_json_object_args(parser, handler, obj, args):
    """Process command line args supplied by user for create json object

    Parameters
    ----------
    parser : :class:`argparse.ArgParse`
        * ArgParse object used to parse `all_args`
    handler : :class:`pytan.handler.Handler`
        * Instance of Handler created from command line args
    obj : str
        * Object type for create json object
    args : args object
        * args parsed from `parser`

    Returns
    -------
    response : :class:`taniumpy.object_types.base.BaseType`
        * response from :func:`pytan.handler.Handler.create_from_json`
    """
    # put our query args into their own dict and remove them from all_args
    obj_grp_names = [
        'Create {} from JSON Options'.format(
            obj.replace('_', ' ').capitalize()
        )
    ]
    obj_grp_opts = get_grp_opts(parser=parser, grp_names=obj_grp_names)
    obj_grp_args = {k: getattr(args, k) for k in obj_grp_opts}
    try:
        response = handler.create_from_json(obj, **obj_grp_args)
    except Exception as e:
        traceback.print_exc()
        print "\n\nError occurred: {}".format(e)
        sys.exit(100)
    for i in response:
        obj_id = getattr(i, 'id', 'unknown')
        print "Created item: {}, ID: {}".format(i, obj_id)
    return response


class TsatWorker(object):
    '''no doc as of yet, push to re-write

    relies on functions in binsupport:
        * filter_filename
        * csvdictwriter
        * filter_sourced_sensors
        * filter_sensors

    '''
    DEBUG_FORMAT = (
        '[%(lineno)-5d - %(filename)20s:%(funcName)s()] %(asctime)s\n'
        '%(levelname)-8s %(name)s %(message)s'
    )
    """
    Logging format for debugformat=True
    """

    CON_INFO_FORMAT = (
        '%(levelname)-8s %(message)s'
    )
    """
    Console Logging format for debugformat=False
    """

    FILE_INFO_FORMAT = (
        '%(asctime)s %(levelname)-8s %(message)s'
    )
    """
    Console Logging format for debugformat=False
    """

    LOG_LEVEL = logging.DEBUG
    MY_NAME = "tsat"
    ARGS = None
    PARSER = None
    HANDLER = None
    MY_KWARGS = None
    CON_LOG_OUTPUT = sys.stdout
    SHOW_ARGS = False
    FINAL_REPORT_HEADERS = [
        'sensor',
        'msg',
        'failure_msg',
        'question',
        'question_id',
        'elapsed_seconds',
        'rows_returned',
        'report_file',
        'estimated_total_clients',
    ]

    PARAM_VALS = {'global': {}}

    def __init__(self, parser, args, handler, **kwargs):
        self.ARGS = args
        self.PARSER = parser
        self.HANDLER = handler
        self.MY_KWARGS = kwargs

    def start(self):
        self.check_help_args()
        self.check_log_format()
        self.set_log_level()
        self.set_mylog()
        show_opts = self.get_parser_args(['TSAT Show Options'])
        if any(show_opts.values()):
            self.handle_show_opts()
        else:
            self.check_report_dir()
            logfile_path = self.get_logfile_path(self.MY_NAME, self.ARGS.report_dir)
            self.add_file_log(logfile_path)
            self.set_sensors()
            self.check_config_file()
            if self.ARGS.build_config_file:
                self.build_config_file()
            else:
                self.add_cmdline_global_params()
                reports = self.run_sensors()
                self.write_final_results(reports)

    def handle_show_opts(self):
        self.sensors = self.HANDLER.get_all('sensor')
        if self.ARGS.show_platforms:
            self.show_platforms()
        if self.ARGS.show_categories:
            self.show_categories()
        if self.ARGS.show_sensors:
            self.show_sensors()

    def load_parameters(self, sensor):
        param_def = sensor.parameter_definition or {}
        if param_def:
            try:
                param_def = json.loads(param_def)
            except:
                m = "Error loading JSON parameter definition for sensor {}: {}".format
                self.mylog.error(m(sensor.name, param_def))
                param_def = {}
        params = param_def.get('parameters', [])
        return params

    def show_sensors(self):
        for x in sorted(self.sensors, key=lambda x: x.category):
            platforms = parse_sensor_platforms(x)
            params = self.load_parameters(x)
            desc = (x.description or '').replace('\n', ' ').strip()

            out = [
                "* Sensor Name: '{sensor.name}'",
                "  * Platforms: {platforms}",
                "  * Category: {sensor.category}",
                "  * Description: {description}",
            ]

            skip_attrs = [
                'model',
                'parameterType',
                'snapInterval',
                'validationExpressions',
                'key',
            ]

            for param in params:
                for k, v in sorted(param.iteritems()):
                    if k in skip_attrs:
                        continue
                    out.append("  * Parameter '{}' - '{}': {}".format(param['key'], k, v))

            linesep = '__________________________________________\n'
            out = (linesep + '\n'.join(out)).format
            self.mylog.info(out(sensor=x, platforms=', '.join(platforms), description=desc))

    def show_categories(self):
        cats = sorted(list(set([x.category for x in self.sensors if x.category])))
        cats = '\n\t'.join(cats)
        self.mylog.info("List of valid categories:\n\t{}".format(cats))

    def show_platforms(self):
        all_plats = []
        for x in self.sensors:
            platforms = parse_sensor_platforms(x)
            if not platforms:
                continue
            for p in platforms:
                if p in all_plats:
                    continue
                all_plats.append(p)
        all_plats = '\n\t'.join(sorted(all_plats))
        self.mylog.info("List of valid platforms:\n\t{}".format(all_plats))

    def check_help_args(self):
        help_args = self.get_parser_args(['Help Options'])
        if any(help_args.values()):
            self.HANDLER.ask_manual(**help_args)
            raise Exception("Help option supplied!")

    def check_log_format(self):
        if self.ARGS.debugformat:
            self.CON_INFO_FORMAT = self.DEBUG_FORMAT
            self.FILE_INFO_FORMAT = self.DEBUG_FORMAT

    def set_log_level(self):
        if self.ARGS.tsatdebug or self.ARGS.loglevel >= 4:
            log_level = logging.DEBUG
        else:
            log_level = logging.INFO
        self.LOG_LEVEL = log_level

    def remove_file_log(self, logfile):
        """Utility to remove a log file from python's logging module"""
        self.mylog.debug('Removing file logging to: {}'.format(logfile))
        basename = os.path.basename(logfile)
        root_logger = logging.getLogger()
        all_loggers = pytan.utils.get_all_loggers()
        for k, v in all_loggers.items():
            for x in v.handlers:
                if x.name == basename:
                    root_logger.removeHandler(x)

    def add_file_log(self, logfile):
        """Utility to add a log file from python's logging module"""
        self.remove_file_log(logfile)
        self.mylog.debug('Adding file logging to: {}'.format(logfile))
        all_loggers = pytan.utils.get_all_loggers()
        basename = os.path.basename(logfile)
        file_handler = logging.FileHandler(logfile)
        file_handler.set_name(basename)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(logging.Formatter(self.FILE_INFO_FORMAT))
        for k, v in all_loggers.items():
            v.addHandler(file_handler)
            v.propagate = False

    def set_mylog(self):
        logging.Formatter.converter = time.gmtime

        ch = logging.StreamHandler(self.CON_LOG_OUTPUT)
        ch.setLevel(self.LOG_LEVEL)
        ch.setFormatter(logging.Formatter(self.CON_INFO_FORMAT))

        mylog = logging.getLogger(self.MY_NAME)
        mylog.setLevel(logging.DEBUG)

        for handler in mylog.handlers:
            mylog.removeHandler(handler)

        mylog.addHandler(ch)
        self.mylog = mylog

    def check_report_dir(self):
        if not os.path.exists(self.ARGS.report_dir):
            os.makedirs(self.ARGS.report_dir)
            self.mylog.debug("Created report_dir: {}".format(self.ARGS.report_dir))

        self.mylog.info("Using report_dir: {}".format(self.ARGS.report_dir))

    def set_sensors(self):
        sensors = self.HANDLER.get_all('sensor')
        self.mylog.info("Found {} total sensors".format(len(sensors)))

        # filter out all sensors that have a source_id
        # (i.e. are created as temp sensors for params)
        real_sensors = filter_sourced_sensors(sensors=sensors)
        self.mylog.info("Filtered out sourced sensors: {}".format(len(real_sensors)))

        if not real_sensors:
            m = "No sensors found!"
            self.mylog.error(m)
            raise Exception(m)

        filtered_sensors = filter_sensors(
            sensors=real_sensors,
            filter_platforms=self.ARGS.platforms,
            filter_categories=self.ARGS.categories,
        )
        m = "Filtered out sensors based on platform/category filters: {}".format
        self.mylog.info(m(len(filtered_sensors)))

        # only include sensors with params
        # filtered_sensors = [x for x in filtered_sensors if self.load_parameters(x)]

        if self.ARGS.sensors:
            filtered_sensors = [
                x for x in filtered_sensors
                if x.name.lower() in [y.lower() for y in self.ARGS.sensors]
            ]
        m = "Filtered out sensors based on sensor names: {}".format
        self.mylog.info(m(len(filtered_sensors)))

        if not filtered_sensors:
            m = (
                "Platform/Category/Sensor name filters too restrictive, no sensors match! "
                "Try --show_platforms and/or --show_categories"
            )
            self.mylog.error(m)
            raise Exception(m)

        self.sensors = filtered_sensors

    def build_config_file(self):
        for sensor in self.sensors:
            sensor_param_defs = self.load_parameters(sensor)

            if not sensor_param_defs:
                m = "Skipping sensor {!r}, no parameters defined".format
                self.mylog.debug(m(sensor.name))
                continue

            for sp in sensor_param_defs:
                key = str(sp['key'])
                sp['sensor_value'] = self.PARAM_VALS.get(sensor.name, {}).get(key, None)
                sp['global_value'] = self.PARAM_VALS.get('global', {}).get(key, None)
                if not any([sp['sensor_value'], sp['global_value']]):
                    self.param_value_prompt(sensor, sp)
                    m = "parameter values updated to: {}".format
                    self.mylog.debug(m(self.PARAM_VALS))

        config = {}
        config['parameters'] = self.PARAM_VALS
        config_json = pytan.utils.jsonify(config)
        try:
            fh = open(self.ARGS.build_config_file, 'wb')
            fh.write(config_json)
            fh.close()
            m = "Configuration file written to: {}".format
            self.mylog.info(m(self.ARGS.build_config_file))
        except:
            m = "Unable to write configuration to: {}".format
            self.mylog.error(m(self.ARGS.build_config_file))
            raise

    def check_config_file(self):
        cfile = self.ARGS.config_file

        if not cfile:
            return

        if not os.path.isfile(cfile):
            m = "Configuration file does not exist: {}".format
            raise Exception(m(cfile))

        try:
            fh = open(cfile)
            config = json.load(fh)
            fh.close()
            m = "Configuration file read from: {}".format
            self.mylog.info(m(cfile))
        except:
            m = "Configuration file unable to be read from: {}".format
            self.mylog.error(m(cfile))
            raise

        if 'parameters' not in config:
            m = "No 'parameters' section in configuration file, not loading parameter values"
            self.mylog.error(m)
            return

        self.PARAM_VALS.update(config['parameters'])
        m = "Loaded 'parameters' section from configuration file"
        self.mylog.info(m)
        return

    def add_cmdline_global_params(self):
        if self.ARGS.globalparams:
            cgp = dict(self.ARGS.globalparams)
            self.PARAM_VALS['global'].update(cgp)
            self.mylog.debug("Updated global parameters to: {}".format(self.PARAM_VALS['global']))

    def run_sensors(self):
        if self.ARGS.build_config_file:
            m = "Not running sensors, --build_config_file was specified!".format
            self.mylog.info(m())
            return

        self.all_start_time = datetime.datetime.now()

        reports = []
        for idx, sensor in enumerate(self.sensors):
            sensor_dir = self.get_sensor_dir(sensor.name)
            logfile_path = self.get_logfile_path(sensor.name, sensor_dir)
            self.add_file_log(logfile_path)

            start_time = datetime.datetime.now()
            report_info = self.run_sensor(idx, sensor)
            end_time = datetime.datetime.now()
            elapsed_time = end_time - start_time
            report_info['elapsed_seconds'] = elapsed_time.seconds

            if report_info['status']:
                loglvl = self.mylog.info
                report_info['prefix'] = '++'
            else:
                loglvl = self.mylog.error
                report_info['prefix'] = '!!'

            m = '{prefix} {msg} for question {question!r} in {elapsed_seconds} seconds'.format
            loglvl(m(**report_info))

            if report_info['failure_msg']:
                self.mylog.error("!! {}".format(report_info['failure_msg']))

            # m = 'report_info:\n{}'.format
            # self.mylog.debug(m(pprint.pformat(report_info)))
            self.remove_file_log(logfile_path)

            reports.append(report_info)
            time.sleep(self.ARGS.sleep)

        self.all_end_time = datetime.datetime.now()
        self.all_elapsed_time = self.all_end_time - self.all_start_time
        return reports

    def get_parser_args(self, grps):
        parser_opts = get_grp_opts(parser=self.PARSER, grp_names=grps)
        p_args = {k: getattr(self.ARGS, k) for k in parser_opts}
        return p_args

    def param_type_prompt(self, sensor, param_def):
        key = param_def['key']
        typeprompt = (
            "\n"
            "Choose from the following type for parameter '{}' in sensor '{}':\n"
            "\n"
            "   (1) Global sensor value (default)\n"
            "   (2) Sensor specific value\n"
            "\n"
            "Global sensor values will be used for all sensors with the same parameter name "
            "unless they have their own sensor specific value specified\n"
            "\n"
            "Enter Choice: "
        ).format(key, sensor.name)

        typemap = {
            "": 'global',
            "1": 'global',
            "2": sensor.name,
        }

        param_section = None

        while True:
            ptype = raw_input(typeprompt)
            if ptype not in typemap:
                m = "\n!! Invalid choice '{}', must be one of: {}\n".format
                print m(ptype, ', '.join(typemap.keys()))
                continue

            if param_section == 'global':
                ptxt = 'global sensor'
            else:
                ptxt = 'sensor specific'

            print "\n~~ Will store value as {}".format(ptxt)
            param_section = typemap[ptype]
            break
        return param_section

    def param_value_prompt(self, sensor, param_def, param_section=None):
        key = param_def['key']
        ptxt = {
            'ptype': 'sensor specific',
            'key': key,
            'sname': sensor.name,
            'help_str': "No help defined",
        }

        if param_section is None:
            param_section = self.param_type_prompt(sensor, param_def)

        if param_section == 'global':
            ptxt['ptype'] = 'global sensor'

        valueprompt = [
            "",
            "Supply the {ptype} value for parameter '{key}' in sensor '{sname}'"
            "",
            "",
        ]

        defval = str(param_def.get('defaultValue', ''))
        if defval:
            ptxt['defval'] = defval
            valueprompt.append("  * Default Defined Value: {defval}")

        label = param_def.get('label', '')
        if label:
            ptxt['label'] = label
            valueprompt.append("  * Label: {label}")

        valid_values = param_def.get('values', [])
        if valid_values:
            ptxt['valid_values'] = ', '.join(valid_values)
            valueprompt.append("  * Valid Values: {valid_values}")

        help_str = param_def.get('helpString', '')
        if help_str:
            ptxt['help_str'] = help_str
            valueprompt.append("  * Help string: {help_str}")

        prompt_str = param_def.get('promptText', '')
        if prompt_str:
            ptxt['prompt_str'] = prompt_str
            valueprompt.append("  * Prompt string: {prompt_str}")

        maxchars = param_def.get('maxChars', None)
        if maxchars is not None:
            ptxt['maxchars'] = maxchars
            valueprompt.append("  * Maximum Characters: {maxchars}")

        minval = param_def.get('minimum', None)
        if minval is not None:
            ptxt['minval'] = minval
            valueprompt.append("  * Minimum Value: {minval}")

        maxval = param_def.get('maximum', None)
        if maxval is not None:
            ptxt['maxval'] = maxval
            valueprompt.append("  * Maximum Value: {maxval}")

        valueprompt.append("\nEnter value: ")
        valueprompt = '\n'.join(valueprompt).format(**ptxt)

        param_value = None
        while True:
            param_value = raw_input(valueprompt)
            if not param_value:
                if defval:
                    print "\n~~ Using default value of: '{}'".format(defval)
                    param_value = defval
                    break

                if valid_values:
                    print "\n~~ Using first valid value of: '{}'".format(valid_values[0])
                    param_value = valid_values[0]
                    break

            if valid_values and param_value not in valid_values:
                m = "\n!! Invalid choice '{}', must be one of: {}\n".format
                print m(param_value, valid_values)
                continue

            if not param_value:
                m = "\n!! No default value defined, must supply a value!\n".format
                print m()
                continue

            if param_value:
                break

        if param_section not in self.PARAM_VALS:
            self.PARAM_VALS[param_section] = {}

        self.PARAM_VALS[param_section][key] = param_value

        return param_value

    def run_sensor(self, idx, sensor):
        handler = self.HANDLER
        report_info = {
            'sensor': sensor.name,
            'msg': 'Not yet run question for {}'.format(sensor.name),
            'report_file': '',
            'elapsed_seconds': -1,
            'question': '',
            'failure_msg': '',
            'status': False,
            'estimated_total_clients': -1,
            'rows_returned': -1,
        }

        current_count = "({}/{})".format(idx + 1, len(self.sensors))

        param_dict = {}
        sensor_param_defs = self.load_parameters(sensor)

        if sensor_param_defs:
            m = "-- Parsing parameters for sensor: {} {}".format
            self.mylog.info(m(sensor.name, current_count))

        fetch_map = [
            {'section': sensor.name, 'name': 'Sensor specific param'},
            {'section': 'global', 'name': 'Global param'},
        ]

        for sp in sensor_param_defs:
            key = str(sp['key'])

            for x in fetch_map:
                value = self.PARAM_VALS.get(x['section'], {}).get(key, None)
                if value is None:
                    m = "{} not found for key '{}', checking global".format
                    self.mylog.debug(m(x['name'], key))
                else:
                    m = "{} found for key '{}', value '{}'".format
                    self.mylog.debug(m(x['name'], key, value))
                    break

            if value is None:
                if self.ARGS.param_prompt is None:
                    m = "Skipped sensor {!r}, no parameter value supplied for '{}'".format
                    report_info['failure_msg'] = m(sensor.name, key)
                    return report_info

                elif self.ARGS.param_prompt is False:
                    m = "Stopped at sensor {!r}, no parameter value supplied for '{}'".format
                    raise Exception(m(sensor.name, key))

                elif self.ARGS.param_prompt is True:
                    value = self.param_value_prompt(sensor, sp)

            if value is None:
                m = "Stopped at sensor {!r}, still no parameter value supplied for '{}'".format
                raise Exception(m(sensor.name, key))
            else:
                param_dict[key] = value
                continue

        if param_dict:
            for k, v in param_dict.iteritems():
                if v.startswith('eval:'):
                    orig_v = v.replace('eval:', '')
                    try:
                        v = eval(orig_v)
                        param_dict[k] = v
                        m = "Evaluated key '{}' value '{}' into value '{}' for sensor: '{}'".format
                        self.mylog.info(m(k, orig_v, v, sensor.name))
                    except:
                        m = "Failed to evaluate key '{}' using value '{}' for sensor: '{}'".format
                        self.mylog.error(m(k, v, sensor.name))
                        raise

                m = "@@ Parameter key '{}' using value '{}' for sensor: '{}'".format
                self.mylog.info(m(k, v, sensor.name))

        m = "-- Asking question for sensor: '{}' {}".format
        self.mylog.info(m(sensor.name, current_count))

        sensor_defs = []
        sensor_def = {'filter': {}, 'params': param_dict, 'name': sensor.name, 'options': {}}
        sensor_defs.append(sensor_def)

        if self.ARGS.add_sensor:
            add_sensor_defs = pytan.utils.dehumanize_sensors(sensors=self.ARGS.add_sensor)
            sensor_defs += add_sensor_defs

        q_filter_defs = pytan.utils.dehumanize_question_filters(
            question_filters=self.ARGS.question_filters
        )
        q_option_defs = pytan.utils.dehumanize_question_options(
            question_options=self.ARGS.question_options
        )

        q_args = {}
        q_args['sensor_defs'] = sensor_defs
        q_args['question_filter_defs'] = q_filter_defs
        q_args['question_option_defs'] = q_option_defs
        q_args['get_results'] = False

        if self.SHOW_ARGS:
            self.mylog.debug("_ask_manual args:\n{}".format(pprint.pformat(q_args)))

        try:
            ret = handler._ask_manual(**q_args)
            report_info['msg'] = "Successfully asked"
            report_info['question'] = ret['question_object'].query_text
            report_info['question_id'] = ret['question_object'].id
        except Exception as e:
            m = "Question failed to be asked: {}".format(e)
            report_info['failure_msg'] = m
            return report_info

        m = "-- Polling question for sensor: '{}' {}".format
        self.mylog.info(m(sensor.name, current_count))

        p_args = self.get_parser_args(['Answer Polling Options'])
        p_args['handler'] = handler
        p_args['obj'] = ret['question_object']

        if self.SHOW_ARGS:
            self.mylog.debug("QuestionPoller args:\n{}".format(pprint.pformat(p_args)))

        try:
            poller = pytan.pollers.QuestionPoller(**p_args)
            poller_result = poller.run()
            report_info['msg'] = "Successfully asked and polled"
            report_info['estimated_total_clients'] = poller.result_info.estimated_total
        except Exception as e:
            m = "Question failed to be polled for answers: {}".format(e)
            report_info['failure_msg'] = m
            return report_info

        m = "-- Getting answers for sensor: '{}' {}".format
        self.mylog.info(m(sensor.name, current_count))

        # TODO: LATER, flush out SSE OPTIONS
        # if self.ARGS.sse and handler.session.platform_is_6_5():
        #     grd = handler.get_result_data_sse
        #     grd_args = self.get_parser_args(['Server Side Export Options'])
        # else:
        grd = handler.get_result_data
        grd_args = {}
        grd_args['obj'] = ret['question_object']

        if self.SHOW_ARGS:
            self.mylog.debug("{} args:\n{}".format(grd.__name__, pprint.pformat(grd_args)))

        try:
            rd = grd(**grd_args)
            rows_returned = len(getattr(rd, 'rows', []))
            report_info['rows_returned'] = rows_returned
            m = "Successfully asked, polled, and retrieved answers ({} rows)".format
            report_info['msg'] = m(rows_returned)
        except Exception as e:
            m = "Failed to retrieve answers: {}".format(e)
            report_info['failure_msg'] = m
            return report_info

        if not rd:
            m = "Unable to export question results to report file, no answers returned!"
            report_info['failure_msg'] = m
            return report_info

        if not rows_returned:
            m = "Unable to export question results to report file, no rows returned!"
            report_info['failure_msg'] = m
            return report_info

        m = "-- Exporting answers ({} rows) for sensor: '{}' {}".format
        self.mylog.info(m(rows_returned, sensor.name, current_count))

        e_args = self.get_parser_args(['Answer Export Options'])
        e_args['obj'] = rd
        e_args['report_dir'] = self.get_sensor_dir(sensor.name)

        if self.SHOW_ARGS:
            self.mylog.debug("export_to_report_file args:\n{}".format(pprint.pformat(p_args)))

        try:
            report_file, result = handler.export_to_report_file(**e_args)
            report_info['report_file'] = report_file
            m = "Successfully asked, polled, retrieved, and exported answers ({} rows)".format
            report_info['msg'] = m(rows_returned)
        except Exception as e:
            m = "Unable to export answers to report file, error: {}".format(e)
            report_info['failure_msg'] = m
            return report_info

        report_info['status'] = poller_result
        return report_info

    def get_sensor_dir(self, sensor_name):
        sensor_dir = os.path.join(self.ARGS.report_dir, filter_filename(sensor_name))
        if not os.path.exists(sensor_dir):
            os.makedirs(sensor_dir)
        return sensor_dir

    def get_logfile_path(self, logname, logdir):
        logfile = '{}_{}.log'.format(logname, pytan.utils.get_now())
        logfile = filter_filename(logfile)
        logfile_path = os.path.join(logdir, logfile)
        return logfile_path

    def write_final_results(self, reports):
        csv_str = csvdictwriter(reports, headers=self.FINAL_REPORT_HEADERS)
        csv_file = '{}_{}.csv'.format(self.MY_NAME, pytan.utils.get_now())
        csv_file = filter_filename(csv_file)
        csv_file_path = os.path.join(self.ARGS.report_dir, csv_file)

        csv_fh = open(csv_file_path, 'wb')
        csv_fh.write(csv_str)
        csv_fh.close()

        m = "Final CSV results of from all questions run written to: {}".format
        self.mylog.info(m(csv_file_path))
        m = "TSAT started: {}".format
        self.mylog.info(m(self.all_start_time))
        m = "TSAT ended: {}".format
        self.mylog.info(m(self.all_end_time))
        m = "TSAT elapsed time: {}".format
        self.mylog.info(m(self.all_elapsed_time))


def process_tsat_args(parser, handler, args):
    """Process command line args supplied by user for tsat

    Parameters
    ----------
    parser : :class:`argparse.ArgParse`
        * ArgParse object used to parse `all_args`
    handler : :class:`pytan.handler.Handler`
        * Instance of Handler created from command line args
    args : args object
        * args parsed from `parser`
    """
    try:
        tsatworker = TsatWorker(parser=parser, handler=handler, args=args)
        tsatworker.start()
    except Exception as e:
        traceback.print_exc()
        print "\nError occurred: {}".format(e)
        sys.exit(100)


def process_delete_object_args(parser, handler, obj, args):
    """Process command line args supplied by user for delete object

    Parameters
    ----------
    parser : :class:`argparse.ArgParse`
        * ArgParse object used to parse `all_args`
    handler : :class:`pytan.handler.Handler`
        * Instance of Handler created from command line args
    obj : str
        * Object type for delete object
    args : args object
        * args parsed from `parser`

    Returns
    -------
    response : :class:`taniumpy.object_types.base.BaseType`
        * response from :func:`pytan.handler.Handler.delete`
    """
    # put our query args into their own dict and remove them from all_args
    obj_grp_names = [
        'Delete {} Options'.format(obj.replace('_', ' ').capitalize())
    ]
    obj_grp_opts = get_grp_opts(parser=parser, grp_names=obj_grp_names)
    obj_grp_args = {k: getattr(args, k) for k in obj_grp_opts}
    obj_grp_args['objtype'] = obj
    try:
        response = handler.delete(**obj_grp_args)
    except Exception as e:
        traceback.print_exc()
        print "\n\nError occurred: {}".format(e)
        sys.exit(100)
    for i in response:
        print "Deleted item: ", i
    return response


def process_approve_saved_action_args(parser, handler, args):
    """Process command line args supplied by user for approving a saved action

    Parameters
    ----------
    parser : :class:`argparse.ArgParse`
        * ArgParse object used to parse `all_args`
    handler : :class:`pytan.handler.Handler`
        * Instance of Handler created from command line args
    args : args
        * args object from parsing `parser`

    Returns
    -------
    approve_action
    """
    q_args = {'id': args.id}

    try:
        approve_action = handler.approve_saved_action(**q_args)
    except Exception as e:
        traceback.print_exc()
        print "\n\nError occurred: {}".format(e)
        sys.exit(99)

    print "++ Saved Action ID approved successfully: {0.id!r}".format(approve_action)
    return approve_action


def process_stop_action_args(parser, handler, args):
    """Process command line args supplied by user for stopping an action

    Parameters
    ----------
    parser : :class:`argparse.ArgParse`
        * ArgParse object used to parse `all_args`
    handler : :class:`pytan.handler.Handler`
        * Instance of Handler created from command line args
    args : args
        * args object from parsing `parser`

    Returns
    -------
    stop_action
    """
    q_args = {'id': args.id}

    try:
        action_stop = handler.stop_action(**q_args)
    except Exception as e:
        traceback.print_exc()
        print "\n\nError occurred: {}".format(e)
        sys.exit(99)

    print "++ Action ID stopped successfully: {0.id!r}".format(action_stop)
    return action_stop


def process_get_results_args(parser, handler, args):
    """Process command line args supplied by user for getting results

    Parameters
    ----------
    parser : :class:`argparse.ArgParse`
        * ArgParse object used to parse `all_args`
    handler : :class:`pytan.handler.Handler`
        * Instance of Handler created from command line args
    args : args
        * args object from parsing `parser`

    Returns
    -------
    report_path, report_contents : tuple
        * results from :func:`pytan.handler.Handler.export_to_report_file` on the return of :func:`pytan.handler.Handler.get_result_data`
    """
    try:
        obj = handler.get(**args.__dict__)[0]
    except Exception as e:
        traceback.print_exc()
        print "\n\nError occurred: {}".format(e)
        sys.exit(99)

    m = "++ Found object: {}".format
    print(m(obj))

    if args.sse:
        try:
            results_obj = handler.get_result_data_sse(obj=obj, **args.__dict__)
        except Exception as e:
            print "\n\nError occurred: {}".format(e)
            sys.exit(99)

    else:
        try:
            results_obj = handler.get_result_data(obj=obj, **args.__dict__)
        except Exception as e:
            print "\n\nError occurred: {}".format(e)
            sys.exit(99)

    if isinstance(results_obj, taniumpy.object_types.result_set.ResultSet):
        if results_obj.rows:
            m = "++ Found results for object: {}".format
            print(m(results_obj))

            try:
                report_path, report_contents = handler.export_to_report_file(
                    obj=results_obj, **args.__dict__
                )
            except Exception as e:
                traceback.print_exc()
                print "\n\nError occurred: {}".format(e)
                sys.exit(99)

            m = "++ Report file {!r} written with {} bytes".format
            print(m(report_path, len(report_contents)))

        else:
            report_contents = results_obj
            report_path = ''
            m = "++ No rows returned for results: {}".format
            print(m(results_obj))

    else:
        report_contents = results_obj
        report_path = handler.create_report_file(contents=report_contents, **args.__dict__)
        m = "++ Report file {!r} written with {} bytes".format
        print(m(report_path, len(report_contents)))

    return report_path, report_contents


def process_create_user_args(parser, handler, args):
    """Process command line args supplied by user for create user object

    Parameters
    ----------
    parser : :class:`argparse.ArgParse`
        * ArgParse object used to parse `all_args`
    handler : :class:`pytan.handler.Handler`
        * Instance of Handler created from command line args
    args : args object
        * args parsed from `parser`

    Returns
    -------
    response : :class:`taniumpy.object_types.base.BaseType`
        * response from :func:`pytan.handler.Handler.create_user`
    """
    obj_grp_names = ['Create User Options']
    obj_grp_opts = get_grp_opts(parser=parser, grp_names=obj_grp_names)
    obj_grp_args = {k: getattr(args, k) for k in obj_grp_opts}

    try:
        response = handler.create_user(**obj_grp_args)
    except Exception as e:
        traceback.print_exc()
        print "\n\nError occurred: {}".format(e)
        sys.exit(99)

    roles_txt = ', '.join([x.name for x in response.roles])

    m = (
        "New user {0.name!r} created with ID {0.id!r}, roles: {1!r}, "
        "group id: {0.group_id!r}"
    ).format
    print(m(response, roles_txt))
    return response


def process_create_package_args(parser, handler, args):
    """Process command line args supplied by user for create package object

    Parameters
    ----------
    parser : :class:`argparse.ArgParse`
        * ArgParse object used to parse `all_args`
    handler : :class:`pytan.handler.Handler`
        * Instance of Handler created from command line args
    args : args object
        * args parsed from `parser`

    Returns
    -------
    response : :class:`taniumpy.object_types.base.BaseType`
        * response from :func:`pytan.handler.Handler.create_package`
    """
    obj_grp_names = ['Create Package Options']
    obj_grp_opts = get_grp_opts(parser=parser, grp_names=obj_grp_names)
    obj_grp_args = {k: getattr(args, k) for k in obj_grp_opts}

    try:
        response = handler.create_package(**obj_grp_args)
    except Exception as e:
        traceback.print_exc()
        print "\n\nError occurred: {}".format(e)
        sys.exit(99)

    m = "New package {0.name!r} created with ID {0.id!r}, command: {0.command!r}".format
    print(m(response))
    return response


def process_create_sensor_args(parser, handler, args):
    """Process command line args supplied by user for create sensor object

    Parameters
    ----------
    parser : :class:`argparse.ArgParse`
        * ArgParse object used to parse `all_args`
    handler : :class:`pytan.handler.Handler`
        * Instance of Handler created from command line args
    args : args object
        * args parsed from `parser`

    Returns
    -------
    response : :class:`taniumpy.object_types.base.BaseType`
        * response from :func:`pytan.handler.Handler.create_sensor`
    """
    obj_grp_names = ['Create Sensor Options']
    obj_grp_opts = get_grp_opts(parser=parser, grp_names=obj_grp_names)
    obj_grp_args = {k: getattr(args, k) for k in obj_grp_opts}

    try:
        response = handler.create_sensor(**obj_grp_args)
    except Exception as e:
        traceback.print_exc()
        print "\n\nError occurred: {}".format(e)
        sys.exit(99)

    m = "New sensor {0.name!r} created with ID {0.id!r}".format
    print(m(response))
    return response


def process_create_whitelisted_url_args(parser, handler, args):
    """Process command line args supplied by user for create group object

    Parameters
    ----------
    parser : :class:`argparse.ArgParse`
        * ArgParse object used to parse `all_args`
    handler : :class:`pytan.handler.Handler`
        * Instance of Handler created from command line args
    args : args object
        * args parsed from `parser`

    Returns
    -------
    response : :class:`taniumpy.object_types.base.BaseType`
        * response from :func:`pytan.handler.Handler.create_group`
    """
    obj_grp_names = ['Create Whitelisted URL Options']
    obj_grp_opts = get_grp_opts(parser=parser, grp_names=obj_grp_names)
    obj_grp_args = {k: getattr(args, k) for k in obj_grp_opts}

    try:
        response = handler.create_whitelisted_url(**obj_grp_args)
    except Exception as e:
        traceback.print_exc()
        print "\n\nError occurred: {}".format(e)
        sys.exit(99)

    m = "New Whitelisted URL {0.url_regex!r} created with ID {0.id!r}".format
    print(m(response))
    return response


def process_create_group_args(parser, handler, args):
    """Process command line args supplied by user for create group object

    Parameters
    ----------
    parser : :class:`argparse.ArgParse`
        * ArgParse object used to parse `all_args`
    handler : :class:`pytan.handler.Handler`
        * Instance of Handler created from command line args
    args : args object
        * args parsed from `parser`

    Returns
    -------
    response : :class:`taniumpy.object_types.base.BaseType`
        * response from :func:`pytan.handler.Handler.create_group`
    """
    obj_grp_names = ['Create Group Options']
    obj_grp_opts = get_grp_opts(parser=parser, grp_names=obj_grp_names)
    obj_grp_args = {k: getattr(args, k) for k in obj_grp_opts}

    try:
        response = handler.create_group(**obj_grp_args)
    except Exception as e:
        traceback.print_exc()
        print "\n\nError occurred: {}".format(e)
        sys.exit(99)

    m = (
        "New group {0.name!r} created with ID {0.id!r}, filter text: {0.text!r}"
    ).format
    print(m(response))
    return response


def process_write_pytan_user_config_args(parser, handler, args):
    """Process command line args supplied by user for writing pytan user config

    Parameters
    ----------
    parser : :class:`argparse.ArgParse`
        * ArgParse object used to parse `all_args`
    handler : :class:`pytan.handler.Handler`
        * Instance of Handler created from command line args
    args : args object
        * args parsed from `parser`
    """
    puc = handler.write_pytan_user_config(pytan_user_config=args.file)
    m = "PyTan User config file successfully written: {} ".format
    print m(puc)


def process_print_server_info_args(parser, handler, args):
    """Process command line args supplied by user for printing server info

    Parameters
    ----------
    parser : :class:`argparse.ArgParse`
        * ArgParse object used to parse `all_args`
    handler : :class:`pytan.handler.Handler`
        * Instance of Handler created from command line args
    args : args object
        * args parsed from `parser`
    """
    si = handler.session.get_server_info()

    if args.json:
        print pytan.utils.jsonify(si['diags_flat'])
    else:
        print str(handler)
        print_obj(si['diags_flat'])


def process_print_sensors_args(parser, handler, args):
    """Process command line args supplied by user for printing sensors

    Parameters
    ----------
    parser : :class:`argparse.ArgParse`
        * ArgParse object used to parse `all_args`
    handler : :class:`pytan.handler.Handler`
        * Instance of Handler created from command line args
    args : args object
        * args parsed from `parser`
    """
    all_sensors = process_get_object_args(
        parser=parser, handler=handler, obj='sensor', args=args, report=False
    )

    real_sensors = filter_sourced_sensors(all_sensors)
    print "Filtered out sourced sensors: {}".format(len(real_sensors))

    filtered_sensors = filter_sensors(
        sensors=real_sensors, filter_platforms=args.platforms, filter_categories=args.categories,
    )
    print "Filtered out sensors based on user filters: {}".format(len(filtered_sensors))

    if args.json:
        for x in filtered_sensors:
            result = handler.export_obj(obj=x, export_format='json')
            print "{}:\n{}".format(x, result)
        sys.exit()

    for x in sorted(filtered_sensors, key=lambda x: x.category):
        platforms = parse_sensor_platforms(x)

        param_def = x.parameter_definition or {}
        if param_def:
            try:
                param_def = json.loads(param_def)
            except:
                print "Error loading JSON parameter definition {}".format(param_def)
                param_def = {}

        params = param_def.get('parameters', [])
        if args.params_only and not params:
            continue

        desc = (x.description or '').replace('\n', ' ').strip()
        print (
            "\n  * Sensor Name: '{0.name}', Platforms: {1}, Category: {0.category}"
        ).format(x, ', '.join(platforms))
        print "  * Description: {}".format(desc)

        if args.hide_params:
            continue

        skip_attrs = [
            'model',
            'parameterType',
            'snapInterval',
            'validationExpressions',
            'key',
        ]

        for param in params:
            print "  * Parameter '{}':".format(param['key'])
            for k, v in sorted(param.iteritems()):
                if k in skip_attrs:
                    continue
                if not v:
                    continue
                print "    - '{}': {}".format(k, v)


def process_get_object_args(parser, handler, obj, args, report=True):
    """Process command line args supplied by user for get object

    Parameters
    ----------
    parser : :class:`argparse.ArgParse`
        * ArgParse object used to parse `all_args`
    handler : :class:`pytan.handler.Handler`
        * Instance of Handler created from command line args
    obj : str
        * Object type for get object
    args : args object
        * args parsed from `parser`

    Returns
    -------
    response : :class:`taniumpy.object_types.base.BaseType`
        * response from :func:`pytan.handler.Handler.get`
    """
    # put our query args into their own dict and remove them from all_args
    obj_grp_names = [
        'Get {} Options'.format(obj.replace('_', ' ').capitalize())
    ]
    obj_grp_opts = get_grp_opts(parser=parser, grp_names=obj_grp_names)
    obj_grp_args = {k: getattr(args, k) for k in obj_grp_opts}
    get_all = obj_grp_args.pop('all')
    o_dict = {'objtype': obj}
    obj_grp_args.update(o_dict)

    if get_all:
        try:
            response = handler.get_all(**o_dict)
        except Exception as e:
            traceback.print_exc()
            print "\n\nError occurred: {}".format(e)
            sys.exit(100)
    else:
        try:
            response = handler.get(**obj_grp_args)
        except Exception as e:
            traceback.print_exc()
            print "\n\nError occurred: {}".format(e)
            sys.exit(100)

    print "Found items: ", response

    if report:
        report_file, result = handler.export_to_report_file(obj=response, **args.__dict__)

        m = "Report file {!r} written with {} bytes".format
        print(m(report_file, len(result)))

    return response


def process_ask_parsed_args(parser, handler, args):
    """Process command line args supplied by user for ask parsed

    Parameters
    ----------
    parser : :class:`argparse.ArgParse`
        * ArgParse object used to parse `all_args`
    handler : :class:`pytan.handler.Handler`
        * Instance of Handler created from command line args
    args : args object
        * args parsed from `parser`

    Returns
    -------
    response
        * response from :func:`pytan.handler.Handler.ask_parsed`
    """
    # TODO: SSE FORMAT NOT BEING RECOGNIZED?
    # put our query args into their own dict and remove them from all_args
    obj_grp_names = ['Parsed Question Options', 'Export Options']
    obj_grp_opts = get_grp_opts(parser=parser, grp_names=obj_grp_names)
    obj_grp_args = {k: getattr(args, k) for k in obj_grp_opts if getattr(args, k, None)}

    print "++ Asking parsed question:\n{}".format(pytan.utils.jsonify(obj_grp_args))

    try:
        response = handler.ask(qtype='parsed', **obj_grp_args)
    except Exception as e:
        traceback.print_exc()
        print "\n\nError occurred: {}".format(e)
        sys.exit(99)

    question = response['question_object']
    results = response['question_results']
    print "++ Asked Question {0.query_text!r} ID: {0.id!r}".format(question)

    if results:
        try:
            report_file, report_contents = handler.export_to_report_file(
                obj=results, **args.__dict__
            )
        except Exception as e:
            print "\n\nError occurred: {}".format(e)
            sys.exit(99)

        m = "++ Report file {!r} written with {} bytes".format
        print(m(report_file, len(report_contents)))
    else:
        print "++ No action results returned, run get_results.py to get the results"

    return response


def process_ask_manual_args(parser, handler, args):
    """Process command line args supplied by user for ask manual

    Parameters
    ----------
    parser : :class:`argparse.ArgParse`
        * ArgParse object used to parse `all_args`
    handler : :class:`pytan.handler.Handler`
        * Instance of Handler created from command line args
    args : args object
        * args parsed from `parser`

    Returns
    -------
    response
        * response from :func:`pytan.handler.Handler.ask_manual`
    """
    # put our query args into their own dict and remove them from all_args
    obj_grp_names = ['Manual Question Options']
    obj_grp_opts = get_grp_opts(parser=parser, grp_names=obj_grp_names)
    obj_grp_args = {k: getattr(args, k) for k in obj_grp_opts}
    other_args = {a: b for a, b in args.__dict__.iteritems() if a not in obj_grp_args}

    print "++ Asking manual question:\n{}".format(pytan.utils.jsonify(obj_grp_args))

    try:
        response = handler.ask(qtype='manual', **obj_grp_args)
    except Exception as e:
        traceback.print_exc()
        print "\n\nError occurred: {}".format(e)
        sys.exit(99)

    question = response['question_object']
    results = response['question_results']
    print "++ Asked Question {0.query_text!r} ID: {0.id!r}".format(question)

    if results:
        try:
            report_file, report_contents = handler.export_to_report_file(obj=results, **other_args)
        except Exception as e:
            traceback.print_exc()
            print "\n\nError occurred: {}".format(e)
            sys.exit(99)

        m = "++ Report file {!r} written with {} bytes".format
        print(m(report_file, len(report_contents)))
    else:
        print "++ No action results returned, run get_results.py to get the results"

    return response


def process_deploy_action_args(parser, handler, args):
    """Process command line args supplied by user for deploy action

    Parameters
    ----------
    parser : :class:`argparse.ArgParse`
        * ArgParse object used to parse `all_args`
    handler : :class:`pytan.handler.Handler`
        * Instance of Handler created from command line args
    args : args object
        * args parsed from `parser`

    Returns
    -------
    response
        * response from :func:`pytan.handler.Handler.deploy_action`
    """
    # put our query args into their own dict and remove them from all_args
    obj_grp_names = ['Deploy Action Options', 'Report File Options']
    obj_grp_opts = get_grp_opts(parser=parser, grp_names=obj_grp_names)
    obj_grp_args = {k: getattr(args, k) for k in obj_grp_opts}

    print "++ Deploying action:\n{}".format(pytan.utils.jsonify(obj_grp_args))

    try:
        response = handler.deploy_action(**obj_grp_args)
    except Exception as e:
        traceback.print_exc()
        print "\n\nError occurred: {}".format(e)
        sys.exit(99)

    action = response['action_object']
    print "++ Deployed Action {0.name!r} ID: {0.id!r}".format(action)
    print "++ Command used in Action: {0.package_spec.command!r}".format(action)

    if response['action_result_map']:
        print "++ Deploy action progress results:"
        for k, v in sorted(response['action_result_map'].iteritems()):
            print "Total {}: {}".format(k, v['total'])

    results = response['action_results']
    if results:
        if not obj_grp_args.get('report_file'):
            obj_grp_args['prefix'] = obj_grp_args.get('prefix', 'deploy_action_')

        try:
            report_file, report_contents = handler.export_to_report_file(
                obj=results, **obj_grp_args
            )
        except Exception as e:
            print "\n\nError occurred: {}".format(e)
            sys.exit(99)

        response['report_file'] = report_file
        response['report_contents'] = report_contents

        m = "++ Deploy results written to {!r} with {} bytes".format
        print(m(report_file, len(report_contents)))

    else:
        print (
            "++ No action results returned, run get_results.py to get the results"
        )

    return response


def process_pytan_shell_args(parser, handler, args):
    """Process command line args supplied by user for a python shell

    Parameters
    ----------
    parser : :class:`argparse.ArgParse`
        * ArgParse object used to parse `all_args`
    handler : :class:`pytan.handler.Handler`
        * Instance of Handler created from command line args
    args : args object
        * args parsed from `parser`
    """
    HistoryConsole()


def process_get_session_args(parser, handler, args):
    """Process command line args supplied by user for getting a session

    Parameters
    ----------
    parser : :class:`argparse.ArgParse`
        * ArgParse object used to parse `all_args`
    handler : :class:`pytan.handler.Handler`
        * Instance of handler created from command line args
    args : args object
        * args parsed from `parser`
    """
    print handler.session._session_id


def process_close_session_args(parser, handler, args):
    """Process command line args supplied by user for getting a session

    Parameters
    ----------
    Parser : :class:`argparse.ArgParse`
        * ArgParse object used to parse `all_args`
    handler : :class:`pytan.handler.Handler`
        * Instance of handler created for command line args
    args : args object
        * args parsed from `parser`
    """
    handler.session.logout(args)


def process_ask_saved_args(parser, handler, args):
    """Process command line args supplied by user for ask saved

    Parameters
    ----------
    parser : :class:`argparse.ArgParse`
        * ArgParse object used to parse `all_args`
    handler : :class:`pytan.handler.Handler`
        * Instance of Handler created from command line args
    args : args object
        * args parsed from `parser`

    Returns
    -------
    response
        * response from :func:`pytan.handler.Handler.ask_saved`
    """
    id_arg = args.id
    name_arg = args.name
    refresh_arg = args.__dict__.get('refresh_data', False)

    q_args = {}

    if id_arg:
        q_args['id'] = id_arg
    elif name_arg:
        q_args['name'] = name_arg
    else:
        parser.error("Must supply --id or --name")

    q_args['refresh_data'] = refresh_arg

    print "++ Asking saved question: {}".format(pytan.utils.jsonify(q_args))

    try:
        response = handler.ask(qtype='saved', **q_args)
    except Exception as e:
        traceback.print_exc()
        print "\n\nError occurred: {}".format(e)
        sys.exit(99)

    question = response['question_object']
    results = response['question_results']
    print "++ Saved Question {0.query_text!r} ID: {0.id!r}".format(question)

    try:
        report_file, report_contents = handler.export_to_report_file(obj=results, **args.__dict__)
    except Exception as e:
        traceback.print_exc()
        print "\n\nError occurred: {}".format(e)
        sys.exit(99)

    response['report_file'] = report_file
    response['report_contents'] = report_contents

    m = "Report file {!r} written with {} bytes".format
    print(m(report_file, len(report_contents)))
    return response


def process_handler_args(parser, args):
    """Process command line args supplied by user for handler

    Parameters
    ----------
    parser : :class:`argparse.ArgParse`
        * ArgParse object used to parse `all_args`
    args : args
        * args parsed from `parser`

    Returns
    -------
    h : :class:`pytan.handler.Handler`
        * Handler object
    """
    input_prompts(args)
    handler_grp_names = ['Handler Authentication', 'Handler Options']
    handler_opts = get_grp_opts(parser=parser, grp_names=handler_grp_names)
    handler_args = {k: getattr(args, k) for k in handler_opts}
    # print handler_args
    try:
        h = pytan.Handler(**handler_args)
    except Exception as e:
        traceback.print_exc()
        print "\n\nError occurred: {}".format(e)
        sys.exit(99)

    print str(h)
    return h


def get_grp_opts(parser, grp_names):
    """Used to get arguments in `parser` that match argument group names in `grp_names`

    Parameters
    ----------
    parser : :class:`argparse.ArgParse`
        * ArgParse object
    grp_names : list of str
        * list of str of argument group names to get arguments for

    Returns
    -------
    grp_opts : list of str
        * list of arguments gathered from argument group names in `grp_names`
    """
    action_grps = [a for a in parser._action_groups if a.title in grp_names]
    grp_opts = [a.dest for b in action_grps for a in b._group_actions]
    return grp_opts


def version_check(reqver):
    """Allows scripts using :mod:`pytan` to validate the version of the script
    aginst the version of :mod:`pytan`

    Parameters
    ----------
    reqver : str
        * string containing version number to check against :exc:`Exception`

    Raises
    ------
    VersionMismatchError : :exc:`Exception`
        * if :data:`pytan.__version__` is not greater or equal to `reqver`
    """
    log_tpl = (
        "{}: {} version {}, required {}").format
    if not __version__ >= reqver:
        s = "Script and API Version mismatch!"
        raise pytan.exceptions.VersionMismatchError(log_tpl(s, sys.argv[0], __version__, reqver))

    s = "Script and API Version match"
    mylog.debug(log_tpl(s, sys.argv[0], __version__, reqver))
    return True


def debug_list(debuglist):
    """Utility function to print the variables for a list of objects"""
    for x in debuglist:
        debug_obj(x)


def debug_obj(debugobj):
    """Utility function to print the variables for an object"""
    pprint.pprint(vars(debugobj))


def introspect(obj, depth=0):
    """Utility function to dump all info about an object"""
    import types
    print "%s%s: %s\n" % (depth * "\t", obj, [
        x for x in dir(obj) if x[:2] != "__"])
    depth += 1
    for x in dir(obj):
        if x[:2] == "__":
            continue
        subobj = getattr(obj, x)
        print "%s%s: %s" % (depth * "\t", x, subobj)
        if isinstance(subobj, types.InstanceType) and dir(subobj) != []:
            introspect(subobj, depth=depth + 1)
            print


def input_prompts(args):
    """Utility function to prompt for username, `, and host if empty"""
    puc_default = os.path.expanduser(pytan.constants.PYTAN_USER_CONFIG)
    puc_kwarg = args.__dict__.get('pytan_user_config', '')
    puc = puc_kwarg or puc_default
    puc_dict = {}

    if os.path.isfile(puc):
        try:
            with open(puc) as fh:
                puc_dict = json.load(fh)
        except Exception as e:
            m = "PyTan User Config file exists at '{}' but is not valid, Exception: {}".format
            print m(puc, e)

    if not args.session_id:
        if not args.username and not puc_dict.get('username', ''):
            username = raw_input('Tanium Username: ')
            args.username = username.strip()

        if not args.password and not puc_dict.get('password', ''):
            password = getpass.getpass('Tanium Password: ')
            args.password = password.strip()

    if not args.host and not puc_dict.get('host', ''):
        host = raw_input('Tanium Host: ')
        args.host = host.strip()
    return args


def print_obj(d, indent=0):
    """Pretty print a dictionary"""
    for k, v in d.iteritems():
        if pytan.utils.is_dict(v):
            print "{}{}: \n".format('  ' * indent, k),
            print_obj(v, indent + 1)
        elif pytan.utils.is_list(v):
            print "{}{}: ".format('  ' * indent, k)
            for a in v:
                print_obj(a, indent + 1)
        else:
            print "{}{}: {}".format('  ' * indent, k, v)


def filter_filename(filename):
    """Utility to filter a string into a valid filename"""
    valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
    filename = ''.join(c for c in filename if c in valid_chars)
    return filename


def remove_file_log(logfile):
    """Utility to remove a log file from python's logging module"""
    basename = os.path.basename(logfile)
    root_logger = logging.getLogger()
    try:
        for x in root_logger.handlers:
            if x.name == basename:
                mylog.info(('Stopped file logging to: {}').format(logfile))
                root_logger.removeHandler(x)
    except:
        pass


def add_file_log(logfile, debug=False):
    """Utility to add a log file from python's logging module"""
    remove_file_log(logfile)
    root_logger = logging.getLogger()
    basename = os.path.basename(logfile)
    try:
        file_handler = logging.FileHandler(logfile)
        file_handler.set_name(basename)
        if debug:
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(logging.Formatter(pytan.constants.DEBUG_FORMAT))
        else:
            file_handler.setLevel(logging.INFO)
            file_handler.setFormatter(logging.Formatter(pytan.constants.INFO_FORMAT))
        root_logger.addHandler(file_handler)
        mylog.info(('Added file logging to: {}').format(logfile))
    except Exception as e:
        mylog.error((
            'Problem setting up file logging to {}: {}'
        ).format(logfile, e))


def parse_sensor_platforms(sensor):
    """Utility to create a list of platforms for a given sensor"""
    platforms = [
        q.platform for q in sensor.queries
        if q.script
        and 'THIS IS A STUB' not in q.script
        and 'echo Windows Only' not in q.script
        and 'Not a Windows Sensor' not in q.script
    ]
    return platforms


def filter_sourced_sensors(sensors):
    """Utility to filter out all sensors that have a source_id specified (i.e. they are temp sensors created by the API)"""
    sensors = [x for x in sensors if not x.source_id]
    return sensors


def filter_sensors(sensors, filter_platforms=[], filter_categories=[]):
    """Utility to filter a list of sensors for specific platforms and/or categories"""
    if not filter_platforms and not filter_categories:
        return sorted(sensors, key=lambda x: x.category)

    new_sensors = []
    for x in sorted(sensors, key=lambda x: x.category):
        if filter_categories:
            # print "Filter cats: ", [y.lower() for y in filter_categories]
            # print "Sensor cat: ", str(x.category).lower()
            if str(x.category).lower() not in [y.lower() for y in filter_categories]:
                # print "no cat match!"
                continue

        platforms = parse_sensor_platforms(x)
        if filter_platforms:
            match = [
                p for p in platforms
                if p.lower() in [y.lower() for y in filter_platforms]
            ]
            if not match:
                # print "no platform match!"
                continue

        new_sensors.append(x)

    return new_sensors


def get_all_headers(rows_list):
    """Utility to get all the keys for a list of dicts"""
    headers = []
    for row_dict in rows_list:
        [headers.append(h) for h in row_dict.keys() if h not in headers]
    return headers


def csvdictwriter(rows_list, **kwargs):
    """returns the rows_list (list of dicts) as a CSV string"""
    csv_io = io.BytesIO()
    headers = kwargs.get('headers', []) or get_all_headers(rows_list)
    writer = csv.DictWriter(
        csv_io,
        fieldnames=headers,
        quoting=csv.QUOTE_NONNUMERIC,
        extrasaction='ignore',
    )
    writer.writerow(dict((h, h) for h in headers))
    writer.writerows(rows_list)
    csv_str = csv_io.getvalue()
    return csv_str
