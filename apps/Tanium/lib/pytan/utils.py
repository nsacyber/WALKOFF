#!/usr/bin/env python
# -*- mode: Python; tab-width: 4; indent-tabs-mode: nil; -*-
# ex: set tabstop=4
# Please do not change the two lines above. See PEP 8, PEP 263.
"""Collection of classes and methods used throughout :mod:`pytan`"""
import sys

# disable python from creating .pyc files everywhere
sys.dont_write_bytecode = True

import os
import socket
import time
import logging
import json
import datetime
import re
import itertools
import base64
from collections import OrderedDict

my_file = os.path.abspath(__file__)
my_dir = os.path.dirname(my_file)
parent_dir = os.path.dirname(my_dir)
path_adds = [parent_dir]
[sys.path.insert(0, aa) for aa in path_adds if aa not in sys.path]

import taniumpy
import xmltodict
import pytan

__version__ = pytan.__version__

mylog = logging.getLogger("pytan.handler")
humanlog = logging.getLogger("pytan.handler.ask_manual_human")
manuallog = logging.getLogger("pytan.handler.ask_manual")
prettylog = logging.getLogger("pytan.handler.prettybody")
timinglog = logging.getLogger("pytan.handler.timing")

DEBUG_OUTPUT = False


class SplitStreamHandler(logging.Handler):
    """Custom :class:`logging.Handler` class that sends all messages that are logging.INFO and below to STDOUT, and all messages that are logging.WARNING and above to STDERR
    """

    def __init__(self):
        logging.Handler.__init__(self)

    def emit(self, record):
        try:
            msg = self.format(record)
            if record.levelno < logging.WARNING:
                stream = sys.stdout
            else:
                stream = sys.stderr
            fs = "%s\n"
            try:
                is_unicode = isinstance(msg, unicode)
                if is_unicode and getattr(stream, 'encoding', None):
                    ufs = u'%s\n'
                    try:
                        stream.write(ufs % msg)
                    except UnicodeEncodeError:
                        stream.write((ufs % msg).encode(stream.encoding))
                else:
                    stream.write(fs % msg)
            except UnicodeError:
                stream.write(fs % msg.encode("UTF-8"))
            self.flush()
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)


def is_list(l):
    """returns True if `l` is a list, False if not"""
    return type(l) in [list, tuple]


def is_str(l):
    """returns True if `l` is a string, False if not"""
    return type(l) in [unicode, str]


def is_dict(l):
    """returns True if `l` is a dictionary, False if not"""
    return type(l) in [dict, OrderedDict]


def is_num(l):
    """returns True if `l` is a number, False if not"""
    return type(l) in [float, int, long]


def jsonify(v, indent=2, sort_keys=True):
    """Turns python object `v` into a pretty printed JSON string

    Parameters
    ----------
    v : object
        * python object to convert to JSON

    indent : int, 2
        * number of spaces to indent JSON string when pretty printing

    sort_keys : bool, True
        * sort keys of JSON string when pretty printing

    Returns
    -------
    str :
        * JSON pretty printed string
    """
    return json.dumps(v, indent=indent, sort_keys=sort_keys)


def get_now():
    """Get current time in human friendly format

    Returns
    -------
    str :
        str of current time return from :func:`human_time`
    """
    return human_time(time.localtime())


def human_time(t, tformat='%Y_%m_%d-%H_%M_%S-%Z'):
    """Get time in human friendly format

    Parameters
    ----------
    t : int, float, time
        * either a unix epoch or struct_time object to convert to string
    tformat : str, optional
        * format of string to convert time to

    Returns
    -------
    str :
        * `t` converted to str
    """
    if is_num(t):
        t = time.localtime(t)
    return time.strftime(tformat, t)


def seconds_from_now(secs=0, tz='utc'):
    """Get time in Tanium SOAP API format `secs` from now

    Parameters
    ----------
    secs : int
        * seconds from now to get time str
    tz : str, optional
        * time zone to return string in, default is 'utc' - supplying anything else will supply local time

    Returns
    -------
    str :
        * time `secs` from now in Tanium SOAP API format
    """
    if secs is None:
        secs = 0

    if tz == 'utc':
        now = datetime.datetime.utcnow()
    else:
        now = datetime.datetime.now()
    from_now = now + datetime.timedelta(seconds=secs)
    # now.strftime('%Y-%m-%dT%H:%M:%S')
    return from_now.strftime('%Y-%m-%dT%H:%M:%S')


def timestr_to_datetime(timestr):
    """Get a datetime.datetime object for `timestr`

    Parameters
    ----------
    timestr : str
        * date & time in taniums format

    Returns
    -------
    datetime.datetime
        * the datetime object for the timestr
    """
    return datetime.datetime.strptime(timestr, pytan.constants.TIME_FORMAT)


def datetime_to_timestr(dt):
    """Get a timestr for `dt`

    Parameters
    ----------
    dt : datetime.datetime
        * datetime object

    Returns
    -------
    timestr: str
        * the timestr for `dt` in taniums format
    """
    return dt.strftime(pytan.constants.TIME_FORMAT)


def port_check(address, port, timeout=5):
    """Check if `address`:`port` can be reached within `timeout`

    Parameters
    ----------
    address : str
        * hostname/ip address to check `port` on
    port : int
        * port to check on `address`
    timeout : int, optional
        * timeout after N seconds of not being able to connect

    Returns
    -------
    :mod:`socket` or False :
        * if connection succeeds, the socket object is returned, else False is returned
    """
    try:
        return socket.create_connection((address, port), timeout)
    except socket.error:
        return False


def test_app_port(host, port):
    """Validates that `host`:`port` can be reached using :func:`port_check`

    Parameters
    ----------
    host : str
        * hostname/ip address to check `port` on
    port : int
        * port to check on `host`

    Raises
    ------
    pytan.exceptions.HandlerError : :exc:`pytan.exceptions.HandlerError`
        * if `host`:`port` can not be reached
    """
    chk_tpl = "Port test to {}:{} {}".format
    if port_check(host, port):
        mylog.debug(chk_tpl(host, port, "SUCCESS"))
    else:
        raise pytan.exceptions.HandlerError(chk_tpl(host, port, "FAILURE"))


def spew(t):
    """Prints a string based on DEBUG_OUTPUT bool

    Parameters
    ----------
    t : str
        * string to debug print
    """
    if DEBUG_OUTPUT:
        print "DEBUG::{}".format(t)


def remove_logging_handler(name='all'):
    """Removes a logging handler

    Parameters
    ----------
    name : str
        * name of logging handler to remove. if name == 'all' then all logging handlers are removed
    """
    for k, v in sorted(get_all_pytan_loggers().iteritems()):
        for handler in v.handlers:
            if name == 'all':
                spew("Removing logging handler: {0}/{0.name} due to 'all'".format(handler))
                v.removeHandler(handler)
            elif handler.name == name:
                spew("Removing logging handler: {0}/{0.name} due to match".format(handler))
                v.removeHandler(handler)


def setup_console_logging(gmt_tz=True):
    """Creates a console logging handler using logging.StreamHandler(sys.stdout)"""

    ch_name = 'console'
    remove_logging_handler('console')

    if gmt_tz:
        # change the default time zone to GM time
        logging.Formatter.converter = time.gmtime
    else:
        logging.Formatter.converter = time.localtime

    # add a console handler to all loggers that goes to STDOUT for INFO
    # and below, but STDERR for WARNING and above (old method)
    # ch = SplitStreamHandler()

    ch = logging.StreamHandler(sys.stdout)
    ch.set_name(ch_name)
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(logging.Formatter(pytan.constants.INFO_FORMAT))

    for k, v in sorted(get_all_pytan_loggers().iteritems()):
        spew("setup_console_logging(): add handler: {0}/{0.name} to logger {1}".format(ch, k))
        v.addHandler(ch)


def change_console_format(debug=False):
    """Changes the logging format for console handler to :data:`pytan.constants.DEBUG_FORMAT` or :data:`pytan.constants.INFO_FORMAT`

    Parameters
    ----------
    debug : bool, optional
        * False : set logging format for console handler to :data:`pytan.constants.INFO_FORMAT`
        * True :  set logging format for console handler to :data:`pytan.constants.DEBUG_FORMAT`
    """
    for k, v in sorted(get_all_pytan_loggers().iteritems()):
        for handler in v.handlers:
            if handler.name == 'console':
                if debug:
                    handler.setFormatter(logging.Formatter(pytan.constants.DEBUG_FORMAT))
                else:
                    handler.setFormatter(logging.Formatter(pytan.constants.INFO_FORMAT))


def set_log_levels(loglevel=0):
    """Enables loggers based on loglevel and :data:`pytan.constants.LOG_LEVEL_MAPS`

    Parameters
    ----------
    loglevel : int, optional
        * loglevel to match against each item in :data:`pytan.constants.LOG_LEVEL_MAPS` - each item that is greater than or equal to loglevel will have the according loggers set to their respective levels identified there-in.
    """
    if loglevel >= 20:
        set_all_loglevels('DEBUG')
        return

    set_all_loglevels('WARN')

    for logmap in pytan.constants.LOG_LEVEL_MAPS:
        if loglevel >= logmap[0]:
            for lname, llevel in logmap[1].iteritems():
                spew('set_log_levels(): setting %s to %s' % (lname, llevel))
                logging.getLogger(lname).setLevel(getattr(logging, llevel))


def print_log_levels():
    """Prints info about each loglevel from :data:`pytan.constants.LOG_LEVEL_MAPS`"""
    for logmap in pytan.constants.LOG_LEVEL_MAPS:
        print "Logging level: {} - Description: {}".format(logmap[0], logmap[2])
        if logmap[0] == 0:
            for k, v in sorted(get_all_pytan_loggers().iteritems()):
                print "\tLogger {!r} will only show WARNING and above".format(k)
            continue
        for lname, llevel in logmap[1].iteritems():
            print "\tLogger {!r} will show {} and above".format(lname, llevel)


def set_all_loglevels(level='DEBUG'):
    """Sets all loggers that the logging system knows about to a given logger level"""

    for k, v in sorted(get_all_pytan_loggers().iteritems()):
        spew("set_all_loglevels(): setting pytan logger '{}' to {}".format(k, level))
        v.setLevel(getattr(logging, level))
        v.propagate = False


def get_all_pytan_loggers():
    """Gets all loggers currently known to pythons logging system that exist in :data:`pytan.constants.LOG_LEVEL_MAPS`

    Creates loggers for any pytan loggers that do not exist yet
    """
    pytan_log_strings = [x[1].keys() for x in pytan.constants.LOG_LEVEL_MAPS if x[1].keys()]
    pytan_log_strings = sorted(list(set(list(itertools.chain(*pytan_log_strings)))))

    pytan_loggers = {x: logging.getLogger(x) for x in pytan_log_strings}
    return pytan_loggers


def get_all_loggers():
    """Gets all loggers currently known to pythons logging system`"""
    logger_dict = logging.Logger.manager.loggerDict
    all_loggers = {k: v for k, v in logger_dict.iteritems() if isinstance(v, logging.Logger)}
    all_loggers['root'] = logging.getLogger()
    return all_loggers


def load_taniumpy_from_json(json_file):
    """Opens a json file and parses it into an taniumpy object

    Parameters
    ----------
    json_file : str
        * path to JSON file that describes an API object

    Returns
    -------
    obj : :class:`taniumpy.object_types.base.BaseType`
        * TaniumPy object converted from json file
    """
    try:
        fh = open(json_file)
    except Exception as e:
        m = "Unable to open json_file {!r}, {}".format
        raise pytan.exceptions.HandlerError(m(json_file, e))

    howto_m = (
        "Use get_${OBJECT_TYPE}.py with --include-type and "
        "--no-explode-json to export a valid JSON file that can be used "
        "for importing"
    )

    try:
        json_dict = json.load(fh)
    except Exception as e:
        m = "Unable to parse json_file {!r}, {}\n{}".format
        raise pytan.exceptions.HandlerError(m(json_file, e, howto_m))

    try:
        fh.close()
    except:
        pass

    if '_type' not in json_dict:
        m = "Missing '_type' key in JSON loaded dictionary!\n{}".format
        raise pytan.exceptions.HandlerError(m(howto_m))

    try:
        obj = taniumpy.BaseType.from_jsonable(json_dict)
    except Exception as e:
        m = (
            "Unable to parse json_file {!r} into an API {} object\n"
            "Exception from API.from_jsonable(): {}\n{}"
        ).format
        raise pytan.exceptions.HandlerError(m(json_file, json_dict['_type'], e, howto_m))
    return obj


def load_param_json_file(parameters_json_file):
    """Opens a json file and sanity checks it for use as a parameters element for a taniumpy object

    Parameters
    ----------
    parameters_json_file : str
        * path to JSON file that describes an API object

    Returns
    -------
    obj
        * contents of parameters_json_file de-serialized
    """
    try:
        pf = open(parameters_json_file)
    except Exception as e:
        m = (
            "Failed to load JSON parameter file {!r}, error {!r}!!\n"
            "Refer to doc/example_of_all_package_parameters.json "
            "file for examples of each parameter type"
        ).format
        raise pytan.exceptions.HandlerError(m(parameters_json_file, e))

    try:
        pd = json.load(pf)
    except Exception as e:
        m = (
            "Failed to load JSON parameter file {!r}, error {!r}!!\n"
            "Refer to doc/example_of_all_package_parameters.json "
            "file for examples of each parameter type"
        ).format
        raise pytan.exceptions.HandlerError(m(parameters_json_file, e))

    try:
        pf.close()
    except:
        pass

    try:
        pd_params = pd['parameters']
    except:
        m = (
            "JSON parameter file {!r} is missing a 'parameters' "
            "list!!\n"
            "Refer to doc/example_of_all_package_parameters.json "
            "file for examples of each parameter type"
        ).format
        raise pytan.exceptions.HandlerError(m(parameters_json_file))

    for pd_param in pd_params:
        if 'key' not in pd_param:
            m = (
                "JSON parameter file {!r} is missing a 'key' "
                "in the parameter {!r}!!\n"
                "Refer to doc/example_of_all_package_parameters.json "
                "file for examples of each parameter type"
            ).format
            raise pytan.exceptions.HandlerError(m(parameters_json_file, pd_param))

    return json.dumps(pd)


def dehumanize_sensors(sensors, key='sensors', empty_ok=True):
    """Turns a sensors str or list of str into a sensor definition

    Parameters
    ----------
    sensors : str, list of str
        * A str or list of str that describes a sensor(s) and optionally a selector, parameters, filter, and/or options
    key : str, optional
        * Name of key that user should have provided `sensors` as
    empty_ok : bool, optional
        * False: `sensors` is not allowed to be empty, throw :exc:`pytan.exceptions.HumanParserError` if it is empty
        * True: `sensors` is allowed to be empty

    Returns
    -------
    sensor_defs : list of dict
        * list of dict parsed from `sensors`
    """
    if not any([is_list(sensors), is_str(sensors)]):
        err = "A string or list of strings must be supplied as '{0}'!".format(key)
        raise pytan.exceptions.HumanParserError(err)

    if not sensors:
        if not empty_ok:
            err = "A string or list of strings must be supplied as '{0}'!".format(key)
            raise pytan.exceptions.HumanParserError(err)
        else:
            return []

    if not is_list(sensors):
        sensors = [sensors]

    sensor_defs = []
    for sensor in sensors:
        if not is_str(sensor):
            raise pytan.exceptions.HumanParserError("{!r} must be a string".format(sensor))
        s, parsed_selector = extract_selector(sensor)
        s, parsed_params = extract_params(s)
        s, parsed_options = extract_options(s)
        s, parsed_filter = extract_filter(s)
        sensor_def = {}
        sensor_def[parsed_selector] = s
        sensor_def['params'] = parsed_params
        sensor_def['options'] = parsed_options
        sensor_def['filter'] = parsed_filter

        dbg = 'parsed string {!r} into definition:\n {}'.format
        humanlog.debug(dbg(sensor, jsonify(sensor_def)))

        sensor_defs.append(sensor_def)

    return sensor_defs


def dehumanize_package(package):
    """Turns a package str into a package definition

    Parameters
    ----------
    package : str
        * A str that describes a package and optionally a selector and/or parameters

    Returns
    -------
    package_def : dict
        * dict parsed from `sensors`
    """
    if not is_str(package) or not package:
        err = "{!r} must be a string supplied as 'package'".format
        raise pytan.exceptions.HumanParserError(err(package))
    p, parsed_selector = extract_selector(package)
    p, parsed_params = extract_params(p)
    package_def = {}
    package_def[parsed_selector] = p
    package_def['params'] = parsed_params

    dbg = 'parsed string {!r} into definition:\n {}'.format
    humanlog.debug(dbg(package, jsonify(package_def)))

    return package_def


def dehumanize_question_filters(question_filters):
    """Turns a question_filters str or list of str into a question filter definition

    Parameters
    ----------
    question_filters : str, list of str
        * A str or list of str that describes a sensor for a question filter(s) and optionally a selector and/or filter

    Returns
    -------
    question_filter_defs : list of dict
        * list of dict parsed from `question_filters`
    """
    if not question_filters:
        return []

    if not is_list(question_filters):
        question_filters = [question_filters]

    question_filter_defs = []
    for question_filter in question_filters:
        s, parsed_selector = extract_selector(question_filter)
        s, parsed_filter = extract_filter(s)
        if not parsed_filter:
            err = "Filter {!r} is not a valid filter!".format
            raise pytan.exceptions.HumanParserError(err(question_filter))

        question_filter_def = {}
        question_filter_def[parsed_selector] = s
        question_filter_def['filter'] = parsed_filter

        dbg = (
            'parsed string {!r} into filter definition:\n {}'
        ).format
        dbg = dbg(question_filter, jsonify(question_filter_def))
        humanlog.debug(dbg)

        question_filter_defs.append(question_filter_def)

    return question_filter_defs


def dehumanize_question_options(question_options):
    """Turns a question_options str or list of str into a question option definition

    Parameters
    ----------
    question_options : str, list of str
        * A str or list of str that describes question options

    Returns
    -------
    question_option_defs : list of dict
        * list of dict parsed from `question_options`
    """
    if not question_options:
        return {}

    if not is_list(question_options):
        question_options = [question_options]

    dest = ['filter', 'group']
    question_option_defs = map_options(question_options, dest)
    dbg = (
        'parsed string {!r} into option definition:\n {}'
    ).format
    dbg = dbg(question_options, jsonify(question_option_defs))
    humanlog.debug(dbg)

    return question_option_defs


def extract_selector(s):
    """Extracts a selector from str `s`

    Parameters
    ----------
    s : str
        * A str that may or may not have a selector in the beginning in the form of id:, name:, or :hash -- if no selector found, name will be assumed as the default selector

    Returns
    -------
    s : str
        * str `s` without the parsed_selector included
    parsed_selector : str
        * selector extracted from `s`, or 'name' if none found
    """
    parsed_selector = 'name'
    for selector in pytan.constants.SELECTORS:
        if s.startswith(selector + ':'):
            parsed_selector = selector
            s = s.replace(selector + ':', '').strip()

    dbg = 'parsed new string to {!r} and selector to:\n{}'.format
    humanlog.debug(dbg(s, jsonify(parsed_selector)))

    return s, parsed_selector


def extract_params(s):
    """Extracts parameters from str `s`

    Parameters
    ----------
    s : str
        * A str that may or may not have parameters identified by {key=value}

    Returns
    -------
    s : str
        * str `s` without the parsed_params included
    parsed_params : list
        * parameters extracted from `s` if any found
    """
    # extract params from s

    # given example (note escaped comma in params):
    # 'Folder Name Search with RegEx Match{dirname=Program Files,regex=\,*}' \
    # ', that is .*, opt:max_data_age:3600, opt:ignore_case'

    params = re.findall(pytan.constants.PARAM_RE, s)
    # params=['dirname=Program Files,regex=\\,*']

    if len(params) > 1:
        err = "More than one parameter ({{}}) passed in {!r}".format
        raise pytan.exceptions.HumanParserError(err(s))
    elif len(params) == 1:
        param = params[0]
    else:
        param = ''
    # param='dirname=Program Files,regex=\\,*'

    if param:
        split_param = re.split(pytan.constants.PARAM_SPLIT_RE, param)
    else:
        split_param = []
    # split_param=['dirname=Program Files', 'regex=\\,*']

    parsed_params = {}
    for sp in split_param:
        # sp = 'dirname=Program Files'
        if pytan.constants.PARAM_KEY_SPLIT not in sp:
            err = "Parameter {} missing key/value seperator ({})".format
            raise pytan.exceptions.HumanParserError(err(sp, pytan.constants.PARAM_KEY_SPLIT))
        sp_key, sp_value = sp.split(pytan.constants.PARAM_KEY_SPLIT, 1)
        # remove any escapes for {}'s
        if '\\}' in sp_value:
            sp_value = sp_value.replace('\\}', '}')
        if '\\{' in sp_value:
            sp_value = sp_value.replace('\\{', '{')

        # sp_key = dirname
        # sp_value = Program Files
        parsed_params[sp_key] = sp_value

    # remove params from the s string
    s = re.sub(pytan.constants.PARAM_RE, '', s)
    # s='Folder Name Search with RegEx Match, that is .*, ' \
    # 'opt:max_data_age:3600, opt:ignore_case'

    dbg = 'parsed new string to {!r} and parameters to:\n{}'.format
    humanlog.debug(dbg(s, jsonify(parsed_params)))

    return s, parsed_params


def extract_options(s):
    """Extracts options from str `s`

    Parameters
    ----------
    s : str
        * A str that may or may not have options identified by ', opt:name[:value]'

    Returns
    -------
    s : str
        * str `s` without the parsed_options included
    parsed_options : list
        * options extracted from `s` if any found
    """
    # parse options out of s

    split_option = re.split(pytan.constants.OPTION_RE, s, 0, re.IGNORECASE)
    # split_option = ['Folder Name Search with RegEx Match, that is .*', \
    # 'max_data_age:3600', 'ignore_case']

    parsed_options = {}

    # if options parsed out from s
    if len(split_option) > 1:

        # get new s from index 0
        s = split_option[0].strip()
        # s='Folder Name Search with RegEx Match, that is .*'

        # get the option strings from index 1 and on
        parsed_options = [x.strip() for x in split_option[1:]]
        # parsed_options=['max_data_age:3600', 'ignore_case']

        parsed_options = map_options(parsed_options, ['filter'])

    dbg = 'parsed new string to {!r} and options to:\n{}'.format
    humanlog.debug(dbg(s, jsonify(parsed_options)))

    return s, parsed_options


def map_options(options, dest):
    """Maps a list of options using :func:`map_option`

    Parameters
    ----------
    options : list of str
        * list of str that should be validated
    dest : list of str
        * list of valid destinations (i.e. `filter` or `group`)

    Returns
    -------
    mapped_options : dict
        * dict of all mapped_options
    """
    mapped_options = {}
    for option in options:
        mapped_option = map_option(option, dest)
        if mapped_option:
            mapped_options.update(mapped_option)
        else:
            err = "Option {!r} is not a valid option!".format
            raise pytan.exceptions.HumanParserError(err(option))

    return mapped_options


def map_option(opt, dest):
    """Maps an opt str against :data:`constants.OPTION_MAPS`

    Parameters
    ----------
    opt : str
        * option str that should be validated
    dest : list of str
        * list of valid destinations (i.e. `filter` or `group`)

    Returns
    -------
    opt_attrs : dict
        * dict containing mapped option attributes for SOAP API
    """
    opt_attrs = {}

    for om in pytan.constants.OPTION_MAPS:
        if opt_attrs:
            break

        if om['destination'] not in dest:
            continue

        # if what the user supplied for an option doesnt match the
        # string in om['human'], go to next string
        if not opt.lower().startswith(om['human']):
            continue

        dbg = "option {!r} mapped to: {!r}".format
        humanlog.debug(dbg(opt, om))

        opt_attrs = om.get('attrs', {})

        human_type = om.get('human_type', '')
        valid_type = om.get('valid_type', str)
        # if human_type we expect the option string
        # to be name:value
        if human_type:
            opt_split = opt.split(':')

            if len(opt_split) != 2:
                format_str = "Format should be '{}:${}'".format
                format_str = format_str(om['human'], human_type.upper())

                err = "Option {!r} is missing a {} value of {}\n{}".format
                err = err(opt, valid_type, human_type, format_str)
                raise pytan.exceptions.HumanParserError(err)

            opt_name, opt_value = opt_split

            opt_attrs = {om['attr']: opt_value}

    return opt_attrs


def extract_filter(s):
    """Extracts a filter from str `s`

    Parameters
    ----------
    s : str
        * A str that may or may not have a filter identified by ', that HUMAN VALUE'

    Returns
    -------
    s : str
        * str `s` without the parsed_filter included
    parsed_filter : dict
        * filter attributes mapped from filter from `s` if any found
    """
    split_filter = re.split(pytan.constants.FILTER_RE, s, re.IGNORECASE)
    # split_filter = ['Folder Name Search with RegEx Match', ' is:.*']

    parsed_filter = {}

    # if filter parsed out from s
    if len(split_filter) > 1:

        # get new s from index 0
        s = split_filter[0].strip()
        # s='Folder Name Search with RegEx Match'

        # get the filter string from index 1
        parsed_filter = split_filter[1].strip()
        # parsed_filter='is:.*'

        parsed_filter = map_filter(parsed_filter)
        if not parsed_filter:
            err = "Filter {!r} is not a valid filter!".format
            raise pytan.exceptions.HumanParserError(err(split_filter[1]))

    dbg = 'parsed new string to {!r} and filters to:\n{}'.format
    humanlog.debug(dbg(s, jsonify(parsed_filter)))

    return s, parsed_filter


def map_filter(filter_str):
    """Maps a filter str against :data:`constants.FILTER_MAPS`

    Parameters
    ----------
    filter_str : str
        * filter_str str that should be validated

    Returns
    -------
    filter_attrs : dict
        * dict containing mapped filter attributes for SOAP API
    """
    filter_attrs = {}

    filter_split = filter_str.split(':')
    if len(filter_split) != 2:
        err = "Invalid filter in {!r}, missing ':' to seperate filter from value?" .format
        raise pytan.exceptions.HumanParserError(err(filter_str))

    filter_name, filter_value = filter_split
    filter_name = filter_name.strip().lower()

    if not filter_value:
        err = "Invalid filter value in {!r}".format
        raise pytan.exceptions.HumanParserError(err(filter_str))

    for fm in pytan.constants.FILTER_MAPS:
        for fh in fm['human']:
            if filter_name == fh:
                filter_attrs = fm
                break

    if filter_attrs:

        pre_value = filter_attrs.get('pre_value', '')
        post_value = filter_attrs.get('post_value', '')

        if pre_value:
            filter_value = '{}{}'.format(pre_value, filter_value)

        if post_value:
            filter_value = '{}{}'.format(filter_value, post_value)

        filter_attrs = {
            'operator': filter_attrs['operator'],
            'not_flag': filter_attrs['not_flag'],
            'value': filter_value,
        }
    return filter_attrs


def get_kwargs_int(key, default=None, **kwargs):
    """Gets key from kwargs and validates it is an int

    Parameters
    ----------
    key : str
        * key to get from kwargs
    default : int, optional
        * default value to use if key not found in kwargs
    kwargs : dict
        * kwargs to get key from

    Returns
    -------
    val : int
        value from key, or default if supplied
    """

    val = kwargs.get(key, default)
    if val is None:
        return val
    try:
        val = int(val)
    except ValueError:
        err = "'{}' must be an int, you supplied: {}"
        raise pytan.exceptions.HandlerError(err(key, val))
    return val


def parse_defs(defname, deftypes, strconv=None, empty_ok=True, defs=None, **kwargs):
    """Parses and validates defs into new_defs

    Parameters
    ----------
    defname : str
        * Name of definition
    deftypes : list of str
        * list of valid types that defs can be
    strconv : str
        * if supplied, and defs is a str, turn defs into a dict with key = strconv, value = defs
    empty_ok : bool
        * True: defs is allowed to be empty
        * False: defs is not allowed to be empty

    Returns
    -------
    new_defs : list of dict
        * parsed and validated defs
    """
    if defs is None:
        defs = kwargs.get(defname, eval(deftypes[0]))

    type_msg = "{0!r} requires a non-empty value of type: {1}".format
    type_msg = type_msg(defname, ' or '.join(deftypes))

    if not defs:
        if not empty_ok:
            err = "Argument {0!r} is empty!\n{1}".format
            raise pytan.exceptions.DefinitionParserError(err(defname, type_msg))
        else:
            return defs

    err = (
        "Argument {0!r} has an invalid type {1}\n{2}"
    ).format(defname, type(defs), type_msg)

    if deftypes == ['dict()']:
        if not is_dict(defs):
            raise pytan.exceptions.DefinitionParserError(err)
        else:
            return defs

    new_defs = []
    if is_str(defs):
        if 'str()' in deftypes:
            conv = defs
            if strconv is not None:
                conv = {strconv: defs}
            new_defs.append(conv)
        else:
            raise pytan.exceptions.DefinitionParserError(err)
    elif is_dict(defs):
        if 'dict()' in deftypes:
            new_defs.append(defs)
        else:
            raise pytan.exceptions.DefinitionParserError(err)
    elif is_list(defs):
        if 'list()' in deftypes:
            for k in defs:
                new_defs += parse_defs(
                    defname, deftypes, strconv, empty_ok, k, **kwargs
                )
        else:
            raise pytan.exceptions.DefinitionParserError(err)
    else:
        raise pytan.exceptions.DefinitionParserError(err)

    return new_defs


def val_sensor_defs(sensor_defs):
    """Validates sensor definitions

    Ensures each sensor definition has a selector, and if a sensor definition has a params, options, or filter key, that each key is valid

    Parameters
    ----------
    sensor_defs : list of dict
        * list of sensor definitions
    """
    s_obj_map = pytan.constants.GET_OBJ_MAP['sensor']
    search_keys = s_obj_map['search']

    for d in sensor_defs:
        # value checking for required keys
        def_search = {s: d.get(s, '') for s in search_keys if d.get(s, '')}

        if len(def_search) == 0:
            err = "Sensor definition {} missing one of {}!".format
            raise pytan.exceptions.DefinitionParserError(err(d, ', '.join(search_keys)))

        elif len(def_search) > 1:
            err = "Sensor definition {} has more than one of {}!".format
            raise pytan.exceptions.DefinitionParserError(err(d, ', '.join(search_keys)))

        # type checking for optional keys
        chk_def_key(d, 'params', [dict])
        chk_def_key(d, 'options', [dict])
        chk_def_key(d, 'filter', [dict])


def val_package_def(package_def):
    """Validates package definitions

    Ensures package definition has a selector, and if a package definition has a params key, that key is valid

    Parameters
    ----------
    package_def : dict
        * package definition
    """
    s_obj_map = pytan.constants.GET_OBJ_MAP['package']
    search_keys = s_obj_map['search']

    # value checking for required keys
    def_search = {
        s: package_def.get(s, '')
        for s in search_keys if package_def.get(s, '')
    }

    if len(def_search) == 0:
        err = "Package definition {} missing one of {}!".format
        raise pytan.exceptions.DefinitionParserError(err(package_def, ', '.join(search_keys)))

    elif len(def_search) > 1:
        err = "Package definition {} has more than one of {}!".format
        raise pytan.exceptions.DefinitionParserError(err(package_def, ', '.join(search_keys)))

    # type checking for optional keys
    chk_def_key(package_def, 'params', [dict])


def val_q_filter_defs(q_filter_defs):
    """Validates question filter definitions

    Ensures each question filter definition has a selector, and if a question filter definition has a filter key, that key is valid

    Parameters
    ----------
    q_filter_defs : list of dict
        * list of question filter definitions
    """
    s_obj_map = pytan.constants.GET_OBJ_MAP['sensor']
    search_keys = s_obj_map['search']

    for d in q_filter_defs:
        # value checking for required keys
        def_search = {s: d.get(s, '') for s in search_keys if d.get(s, '')}

        if len(def_search) == 0:
            err = "Question Filter {} missing one of {}!".format
            raise pytan.exceptions.DefinitionParserError(err(d, ', '.join(search_keys)))

        elif len(def_search) > 1:
            err = "Question Filter {} has more than one of {}!".format
            raise pytan.exceptions.DefinitionParserError(err(d, ', '.join(search_keys)))

        # type checking for required filter key
        chk_def_key(d, 'filter', [dict], req=True)


def build_selectlist_obj(sensor_defs):
    """Creates a SelectList object from sensor_defs

    Parameters
    ----------
    sensor_defs : list of dict
        * List of dict that are sensor definitions

    Returns
    -------
    select_objlist : :class:`taniumpy.object_types.select_list.SelectList`
        * SelectList object with list of :class:`taniumpy.object_types.select.Select` built from `sensor_defs`
    """
    select_objlist = taniumpy.SelectList()

    for d in sensor_defs:

        # validate/map sensor params into a ParameterList()
        sensor_obj = d['sensor_obj']
        user_params = d.get('params', {})
        param_objlist = build_param_objlist(
            obj=sensor_obj,
            user_params=user_params,
            delim='||',
            derive_def=True,
            empty_ok=True
        )

        # validate/map sensor filter into a Filter()
        filter_obj = get_filter_obj(d)

        # get the options the user supplied
        options = d.get('options', {})

        # update filter_obj with any options the user supplied
        filter_obj = apply_options_obj(options, filter_obj, 'filter')

        # create a select object for this sensor
        select_obj = taniumpy.Select()
        select_obj.sensor = taniumpy.Sensor()
        select_obj.filter = filter_obj

        # if there are parameters, we need to set the following to
        # sensor_obj.id:
        #  - select_obj.sensor_obj.source_id
        #  - select_obj.filter.sensor.id
        if param_objlist:
            select_obj.sensor.source_id = d['sensor_obj'].id
            select_obj.sensor.parameters = param_objlist
            select_obj.filter.sensor.id = d['sensor_obj'].id
        else:
            select_obj.sensor.hash = d['sensor_obj'].hash

        select_objlist.select.append(select_obj)
    return select_objlist


def build_group_obj(q_filter_defs, q_option_defs):
    """Creates a Group object from q_filter_defs and q_option_defs

    Parameters
    ----------
    q_filter_defs : list of dict
        * List of dict that are question filter definitions
    q_option_defs : dict
        * dict of question filter options

    Returns
    -------
    group_obj : :class:`taniumpy.object_types.group.Group`
        * Group object with list of :class:`taniumpy.object_types.filter.Filter` built from `q_filter_defs` and `q_option_defs`
    """
    filter_objlist = taniumpy.FilterList()

    for d in q_filter_defs:
        # validate/map question filter into a Filter()
        filter_obj = get_filter_obj(d)

        # update filter_obj with any options
        filter_obj = apply_options_obj(q_option_defs, filter_obj, 'filter')
        filter_objlist.filter.append(filter_obj)

    group_obj = taniumpy.Group()
    group_obj.filters = filter_objlist
    group_obj = apply_options_obj(q_option_defs, group_obj, 'group')

    return group_obj


def build_manual_q(selectlist_obj, group_obj):
    """Creates a Question object from selectlist_obj and group_obj

    Parameters
    ----------
    selectlist_obj : :class:`taniumpy.object_types.select_list.SelectList`
        * SelectList object to add to Question object
    group_obj : :class:`taniumpy.object_types.group.Group`
        * Group object to add to Question object

    Returns
    -------
    add_q_obj : :class:`taniumpy.object_types.question.Question`
        * Question object built from selectlist_obj and group_obj
    """
    add_q_obj = taniumpy.Question()
    add_q_obj.selects = selectlist_obj
    add_q_obj.group = group_obj
    return add_q_obj


def get_obj_params(obj):
    """Get the parameters from a TaniumPy object and JSON load them

    obj : :class:`taniumpy.object_types.base.BaseType`
        * TaniumPy object to get parameters from

    Returns
    -------
    params : dict
        * JSON loaded dict of parameters from `obj`

    """
    # get the parameter definitions
    param_def = getattr(obj, 'parameter_definition', {}) or {}

    # json load the parameter definitions if they exist
    if param_def:
        param_def = json.loads(param_def)

    # get the list of parameters from the parameter definitions
    params = param_def.get('parameters', [])
    return params


def build_param_obj(key, val, delim=''):
    """Creates a Parameter object from key and value, surrounding key with delim

    Parameters
    ----------
    key : str
        * key to use for parameter
    value : str
        * value to use for parameter
    delim : str
        * str to surround key with when adding to parameter object

    Returns
    -------
    param_obj : :class:`taniumpy.object_types.parameter.Parameter`
        * Parameter object built from key and val
    """
    # create a parameter object
    param_obj = taniumpy.Parameter()
    param_obj.key = '{0}{1}{0}'.format(delim, key)
    param_obj.value = val
    return param_obj


def derive_param_default(obj_param):
    """Derive a parameter default

    Parameters
    ----------
    obj_param : dict
        * parameter dict from TaniumPy object

    Returns
    -------
    def_val : str
        * default value derived from obj_param
    """
    # get the default value for this param if it exists
    def_val = obj_param.get('defaultValue', '')

    # get requireSelection for this param if it exists (pulldown menus)
    req_sel = obj_param.get('requireSelection', False)

    # get values for this param if it exists (pulldown menus)
    values = obj_param.get('values', [])

    # if this param requires a selection and it has a list of values
    # and there is no default value, use the first value as the
    # default value
    if req_sel and values and not def_val:
        def_val = values[0]
    return def_val


def build_param_objlist(obj, user_params, delim='', derive_def=False, empty_ok=False):
    """Creates a ParameterList object from user_params

    Parameters
    ----------
    obj : :class:`taniumpy.object_types.base.BaseType`
        * TaniumPy object to verify parameters against
    user_params : dict
        * dict describing key and value of user supplied params
    delim : str
        * str to surround key with when adding to parameter object
    derive_def : bool, optional
        * False: Do not derive default values, and throw a :exc:`pytan.exceptions.HandlerError` if user did not supply a value for a given parameter
        * True: Try to derive a default value for each parameter if user did not supply one
    empty_ok : bool, optional
        * False: If user did not supply a value for a given parameter, throw a :exc:`pytan.exceptions.HandlerError`
        * True: If user did not supply a value for a given parameter, do not add the parameter to the ParameterList object

    Returns
    -------
    param_objlist : :class:`taniumpy.object_types.parameter_list.ParameterList`
        ParameterList object with list of :class:`taniumpy.object_types.parameter.Parameter` built from user_params
    """
    # extract the params from the object
    obj_params = get_obj_params(obj)
    obj_name = str(obj)
    param_objlist = taniumpy.ParameterList()

    processed = []

    for obj_param in obj_params:
        # get the key for this param
        p_key = obj_param["key"]
        processed.append(p_key)
        user_val = user_params.get(p_key, '')

        if not user_val and derive_def:
            user_val = derive_param_default(obj_param)

        if not user_val and not empty_ok:
            err = (
                "{} parameter key '{}' requires a value, "
                "parameter definition:\n{}"
            ).format
            raise pytan.exceptions.HandlerError(err(obj_name, p_key, jsonify(obj_param)))
        param_obj = build_param_obj(p_key, user_val, delim)
        param_objlist.append(param_obj)

        dbg = "Parameter {} for {} mapped to: {}".format
        manuallog.debug(dbg(p_key, obj_name, param_obj))

    # ADD SUPPORT FOR PARAMS THAT ARE NOT IN OBJECT
    for k, v in user_params.iteritems():
        if k in processed:
            continue
        processed.append(k)
        param_obj = build_param_obj(k, v, delim)
        param_objlist.append(param_obj)

        dbg = "Undefined Parameter {} for {} mapped to: {}".format
        manuallog.debug(dbg(k, obj_name, param_obj))

    return param_objlist


def shrink_obj(obj, attrs=None):
    """Returns a new class of obj with only id/name/hash defined

    Parameters
    ----------
    obj : :class:`taniumpy.object_types.base.BaseType`
        * Object to shrink
    attrs : list of str
        * default: None
        * list of attribute str's to copy over to new object, will default to ['name', 'id', 'hash'] if None

    Returns
    -------
    new_obj : :class:`taniumpy.object_types.base.BaseType`
        * Shrunken object
    """
    if attrs is None:
        attrs = ['name', 'id', 'hash']

    new_obj = obj.__class__()
    [setattr(new_obj, a, getattr(obj, a)) for a in attrs if getattr(obj, a, '')]
    return new_obj


def copy_obj(obj, skip_attrs=None):
    """Returns a new class of obj with with out any attributes in skip_attrs specified

    Parameters
    ----------
    obj : :class:`taniumpy.object_types.base.BaseType`
        * Object to copy
    skip_attrs : list of str
        * default: None
        * list of attribute str's to skip copying over to new object, will default to [] if None

    Returns
    -------
    new_obj : :class:`taniumpy.object_types.base.BaseType`
        * Copied object with attributes in skip_attrs skipped
    """
    if not skip_attrs:
        skip_attrs = []

    new_obj = obj.__class__()
    [
        setattr(new_obj, a, getattr(obj, a))
        for a in vars(obj)
        if getattr(obj, a, None) is not None
        and a not in skip_attrs
    ]
    return new_obj


def copy_package_obj_for_action(obj, skip_attrs=None):
    """Returns a new class of package obj with with out any attributes in skip_attrs specified

    Parameters
    ----------
    obj : :class:`taniumpy.object_types.base.BaseType`
        * Object to copy
    skip_attrs : list of str
        * default: None
        * list of attribute str's to skip copying over to new object, default if None: ['id', 'deleted_flag', 'available_time', 'creation_time', 'modification_time', 'source_id']

    Returns
    -------
    new_obj : :class:`taniumpy.object_types.base.BaseType`
        * Copied object with attributes in skip_attrs skipped
    """
    if skip_attrs is None:
        # names of attributes to skip copying over from source package
        skip_attrs = [
            'id',
            'deleted_flag',
            'available_time',
            'creation_time',
            'modification_time',
            'source_id',
            'files',
        ]

    new_obj = copy_obj(obj, skip_attrs)
    return new_obj


def get_filter_obj(sensor_def):
    """Creates a Filter object from sensor_def

    Parameters
    ----------
    sensor_def : dict
        * dict containing sensor definition

    Returns
    -------
    filter_obj : :class:`taniumpy.object_types.filter.Filter`
        * Filter object created from `sensor_def`
    """
    sensor_obj = sensor_def['sensor_obj']

    # create our basic filter that is needed no matter what
    filter_obj = taniumpy.Filter()
    filter_obj.sensor = taniumpy.Sensor()
    filter_obj.sensor.hash = sensor_obj.hash

    # get the filter the user supplied
    filter_def = sensor_def.get('filter', {})

    # if no user supplied filter, return the basic filter object
    if not filter_def:
        return filter_obj

    # operator required
    def_op = filter_def.get('operator', None)
    if not def_op:
        err = "Filter {!r} requires an 'operator' key!".format
        raise pytan.exceptions.DefinitionParserError(err(filter_def))

    # not_flag optional
    def_not_flag = filter_def.get('not_flag', None)

    # value required
    def_value = filter_def.get('value', None)
    if not def_value:
        err = "Filter {!r} requires a 'value' key!".format
        raise pytan.exceptions.DefinitionParserError(err(filter_def))

    found_match = False
    for fm in pytan.constants.FILTER_MAPS:
        # if user supplied operator does not match this operator, next
        if not def_op.lower() == fm['operator'].lower():
            continue

        found_match = True

        filter_obj.value = def_value

        filter_obj.operator = fm['operator']
        if def_not_flag is not None:
            filter_obj.not_flag = def_not_flag

        dbg = "Filter {!r} mapped to: {}".format
        manuallog.debug(dbg(filter_def, str(filter_obj)))
        break

    if not found_match:
        err = "Invalid filter {!r}".format
        raise pytan.exceptions.DefinitionParserError(err(filter_def))

    return filter_obj


def apply_options_obj(options, obj, dest):
    """Updates an object with options

    Parameters
    ----------
    options : dict
        * dict containing options definition
    obj : :class:`taniumpy.object_types.base.BaseType`
        * TaniumPy object to apply `options` to
    dest : list of str
        * list of valid destinations (i.e. `filter` or `group`)

    Returns
    -------
    obj : :class:`taniumpy.object_types.base.BaseType`
        * TaniumPy object updated with attributes from `options`
    """
    # if no user supplied options, return the filter object unchanged
    if not options:
        return obj

    for k, v in options.iteritems():
        for om in pytan.constants.OPTION_MAPS:

            if om['destination'] != dest:
                continue

            om_attrs = om.get('attrs', {}).keys()
            om_attr = om.get('attr', '')

            if om_attr:
                om_attrs.append(om_attr)

            if k.lower() not in om_attrs:
                continue

            dbg = "option {!r} value {!r} mapped to: {!r}".format
            manuallog.debug(dbg(k, v, om))

            valid_values = om.get('valid_values', [])
            valid_type = om.get('valid_type', str)

            if valid_values:
                valid_values = eval(valid_values)
                valid_values_str = " -- valid values: "
                valid_values_str += ', '.join(valid_values)
            else:
                valid_values = []
                valid_values_str = ""

            if len(str(v)) == 0:
                err = (
                    "Option {!r} requires a {} value{}"
                ).format
                raise pytan.exceptions.DefinitionParserError(err(k, valid_type, valid_values_str))

            if valid_type == int:
                try:
                    v = int(v)
                except:
                    err = (
                        "Option {!r} value {!r} is not an integer"
                    ).format
                    raise pytan.exceptions.DefinitionParserError(err(k, v))

            if valid_type == str:
                if not is_str(v):
                    err = (
                        "Option {!r} value {!r} is not a string"
                    ).format
                    raise pytan.exceptions.DefinitionParserError(err(k, v))

            value_match = None
            if valid_values:
                for x in valid_values:
                    if v.lower() == x.lower():
                        value_match = x
                        break

                if value_match is None:
                    err = (
                        "Option {!r} value {!r} does not match one of {}"
                    ).format
                    raise pytan.exceptions.DefinitionParserError(err(k, v, valid_values))
                else:
                    v = value_match

            # update obj with k = v
            setattr(obj, k, v)

            break

    dbg = "Options {!r} updated to: {}".format
    manuallog.debug(dbg(options, str(obj)))
    return obj


def chk_def_key(def_dict, key, keytypes, keysubtypes=None, req=False):
    """Checks that def_dict has key

    Parameters
    ----------
    def_dict : dict
        * Definition dictionary
    key : str
        * key to check for in def_dict
    keytypes : list of str
        * list of str of valid types for key
    keysubtypes : list of str
        * if key is a dict or list, validate that all values of dict or list are in keysubtypes
    req : bool
        * False: key does not have to be in def_dict
        * True: key must be in def_dict, throw :exc:`pytan.exceptions.DefinitionParserError` if not
    """
    if key not in def_dict:
        if req:
            err = "Definition {} missing 'filter' key!".format
            raise pytan.exceptions.DefinitionParserError(err(def_dict))
        return

    val = def_dict.get(key)
    if type(val) not in keytypes:
        err = (
            "'{}' key in definition dictionary must be a {}, you supplied "
            "a {}!"
        ).format
        raise pytan.exceptions.DefinitionParserError(err(key, keytypes, type(val)))

    if not keysubtypes or not val:
        return

    if is_dict(val):
        subtypes = [type(x) for x in val.values()]
    else:
        subtypes = [type(x) for x in val]

    if not all([x in keysubtypes for x in subtypes]):
        err = (
            "'{}' key in definition dictionary must be a {} of {}s, "
            "you supplied {}!"
        ).format
        raise pytan.exceptions.DefinitionParserError(err(key, keytypes, keysubtypes, subtypes))


def empty_obj(taniumpy_object):
    """Validate that a given TaniumPy object is not empty

    Parameters
    ----------
    taniumpy_object : :class:`taniumpy.object_types.base.BaseType`
        * object to check if empty

    Returns
    -------
    bool
        * True if `taniumpy_object` is considered empty, False otherwise
    """
    v = [getattr(taniumpy_object, '_list_properties', {}), is_str(taniumpy_object)]
    if any(v) and not taniumpy_object:
        return True
    else:
        return False


def get_q_obj_map(qtype):
    """Gets an object map for `qtype`

    Parameters
    ----------
    qtype : str
        * question type to get object map from in :data:`pytan.constants.Q_OBJ_MAP`

    Returns
    -------
    obj_map : dict
        * matching object map for `qtype` from :data:`pytan.constants.Q_OBJ_MAP`
    """
    try:
        obj_map = pytan.constants.Q_OBJ_MAP[qtype.lower()]
    except KeyError:
        err = "{} not a valid question type, must be one of {!r}".format
        raise pytan.exceptions.HandlerError(err(qtype, pytan.constants.Q_OBJ_MAP.keys()))
    return obj_map


def get_obj_map(objtype):
    """Gets an object map for `objtype`

    Parameters
    ----------
    objtype : str
        * object type to get object map from in :data:`pytan.constants.GET_OBJ_MAP`

    Returns
    -------
    obj_map : dict
        * matching object map for `objtype` from :data:`pytan.constants.GET_OBJ_MAP`
    """
    try:
        obj_map = pytan.constants.GET_OBJ_MAP[objtype.lower()]
    except KeyError:
        err = "{} not a valid object to get, must be one of {!r}".format
        raise pytan.exceptions.HandlerError(err(objtype, pytan.constants.GET_OBJ_MAP.keys()))
    return obj_map


def get_taniumpy_obj(obj_map):
    """Gets a taniumpy object from `obj_map`

    Parameters
    ----------
    obj_map : str
        * str of taniumpy object to fetch

    Returns
    -------
    obj : :class:`taniumpy.object_types.base.BaseType`
        * matching taniumpy object for `obj_map`
    """
    try:
        obj = getattr(taniumpy, obj_map)
    except Exception as e:
        err = "Could not find taniumpy object {}: {}".format
        raise pytan.exceptions.HandlerError(err(obj_map, e))

    return obj


def check_dictkey(d, key, valid_types, valid_list_types):
    """Yet another method to check a dictionary for a key

    Parameters
    ----------
    d : dict
        * dictionary to check for key
    key : str
        * key to check for in d
    valid_types : list of str
        * list of str of valid types for key
    valid_list_types : list of str
        * if key is a list, validate that all values of list are in valid_list_types
    """
    if key in d:
        k_val = d[key]
        k_type = type(k_val)
        if k_type not in valid_types:
            err = "{!r} must be one of {}, you supplied {}!".format
            raise pytan.exceptions.HandlerError(err(key, valid_types, k_type))
        if is_list(k_val) and valid_list_types:
            valid_list_types = [eval(x) for x in valid_list_types]
            list_types = [type(x) for x in k_val]
            list_types_match = [x in valid_list_types for x in list_types]
            if not all(list_types_match):
                err = "{!r} must be a list of {}, you supplied {}!".format
                raise pytan.exceptions.HandlerError(err(key, valid_list_types, list_types))


def func_timing(f):
    """Decorator to add timing information around a function """
    def wrap(*args, **kwargs):
        time1 = datetime.datetime.utcnow()
        ret = f(*args, **kwargs)
        time2 = datetime.datetime.utcnow()
        elapsed = time2 - time1
        m = '{}() TIMING start: {}, end: {}, elapsed: {}'.format
        timinglog.debug(m(f.func_name, time1, time2, elapsed))
        return ret
    return wrap


def eval_timing(c):
    """Yet another method to time things -- c will be evaluated and timing information will be printed out
    """
    t_start = datetime.now()
    r = eval(c)
    t_end = datetime.now()
    t_elapsed = t_end - t_start

    m = "Timing info for {} -- START: {}, END: {}, ELAPSED: {}, RESPONSE LEN: {}".format
    mylog.warn(m(c, t_start, t_end, t_elapsed, len(r)))
    return (c, r, t_start, t_end, t_elapsed)


def xml_pretty(x, pretty=True, indent='  ', **kwargs):
    """Uses :mod:`xmltodict` to pretty print an XML str `x`

    Parameters
    ----------
    x : str
        * XML string to pretty print

    Returns
    -------
    str :
        * The pretty printed string of `x`
    """

    x_parsed = xmltodict.parse(x)
    x_unparsed = xmltodict.unparse(x_parsed, pretty=pretty, indent=indent)
    return x_unparsed


def log_session_communication(h):
    """Uses :func:`xml_pretty` to pretty print the last request and response bodies from the
    session object in h to the logging system

    Parameters
    ----------
    h : Handler object
        * Handler object with session object containing last request and response body
    """
    response_obj = h.session.LAST_REQUESTS_RESPONSE
    request_body = response_obj.request.body
    response_body = response_obj.text

    try:
        req = xml_pretty(request_body)
    except Exception as e:
        req = "Failed to prettify xml: {}, raw xml:\n{}".format(e, request_body)

    prettylog.debug("Last HTTP request:\n{}".format(req))

    try:
        resp = xml_pretty(response_body)
    except Exception as e:
        resp = "Failed to prettify xml: {}, raw xml:\n{}".format(e, response_body)

    prettylog.debug("Last HTTP response:\n{}".format(xml_pretty(resp)))


def xml_pretty_resultxml(x):
    """Uses :mod:`xmltodict` to pretty print an the ResultXML element in XML str `x`

    Parameters
    ----------
    x : str
        * XML string to pretty print

    Returns
    -------
    str :
        * The pretty printed string of ResultXML in `x`
    """

    x_parsed = xmltodict.parse(x)
    x_find = x_parsed["soap:Envelope"]["soap:Body"]["t:return"]["ResultXML"]
    x_unparsed = xml_pretty(x_find)
    return x_unparsed


def xml_pretty_resultobj(x):
    """Uses :mod:`xmltodict` to pretty print an the result-object element in XML str `x`

    Parameters
    ----------
    x : str
        * XML string to pretty print

    Returns
    -------
    str :
        * The pretty printed string of result-object in `x`
    """

    x_parsed = xmltodict.parse(x)
    x_find = x_parsed["soap:Envelope"]["soap:Body"]["t:return"]
    x_find = x_parsed["result-object"]
    x_unparsed = xmltodict.unparse(x_find, pretty=True, indent='  ')
    return x_unparsed


def get_dict_list_len(d, keys=[], negate=False):
    """Gets the sum of each list in dict `d`

    Parameters
    ----------
    d : dict of str : list
        * dict to sums of
    keys : list of str
        * list of keys to get sums of, if empty gets a sum of all keys
    negate : bool
        * only used if keys supplied
        * False : get the sums of `d` that do match keys
        * True : get the sums of `d` that do not match keys

    Returns
    -------
    list_len : int
        * sum of lists in `d` that match keys
    """
    if keys:
        if negate:
            list_len = sum([len(d[k]) for k in d if k not in keys])
        else:
            list_len = sum([len(d[k]) for k in d if k in keys])
    else:
        list_len = sum([len(d[k]) for k in d])
    return list_len


def build_metadatalist_obj(properties, nameprefix=""):
    """Creates a MetadataList object from properties

    Parameters
    ----------
    properties : list of list of strs
        * list of lists, each list having two strs - str 1: property key, str2: property value
    nameprefix : str
        * prefix to insert in front of property key when creating MetadataItem

    Returns
    -------
    metadatalist_obj : :class:`taniumpy.object_types.metadata_list.MetadataList`
        * MetadataList object with list of :class:`taniumpy.object_types.metadata_item.MetadataItem` built from `properties`
    """
    metadatalist_obj = taniumpy.MetadataList()
    for prop in properties:
        name = prop[0]
        value = prop[1]

        if nameprefix:
            name = "{}.{}".format(nameprefix, name)

        metadata_obj = taniumpy.MetadataItem()
        metadata_obj.name = name
        metadata_obj.value = value
        metadatalist_obj.append(metadata_obj)
    return metadatalist_obj


def get_percentage(part, whole):
    """Utility method for getting percentage of part out of whole

    Parameters
    ----------
    part: int, float
    whole: int, float

    Returns
    -------
    int : the percentage of part out of whole
    """
    if 0 in [part, whole]:
        return float(0)
    return 100 * (float(part) / float(whole))


def calc_percent(percent, whole):
    """Utility method for getting percentage of whole

    Parameters
    ----------
    percent: int, float
    whole: int, float

    Returns
    -------
    int : the percentage of whole
    """
    return int((percent * whole) / 100.0)


def plugin_zip(p):
    """Maps columns to values for each row in a plugins sql_response and returns a list of dicts

    Parameters
    ----------
    p : :class:`taniumpy.object_types.plugin.Plugin`
        * plugin object

    Returns
    -------
    dict
        * the columns and result_rows of the sql_response in Plugin object zipped up into a dictionary
    """
    return [
        dict(zip(p.sql_response.columns, x)) for x in p.sql_response.result_row
    ]


def clean_kwargs(kwargs, keys=None):
    """Removes each key from kwargs dict if found

    Parameters
    ----------
    kwargs : dict
        * dict of keyword args
    keys : list of str, optional
        * default: ['obj', 'pytan_help', 'objtype']
        * list of strs of keys to remove from kwargs

    Returns
    -------
    clean_kwargs : dict
        * the new dict of kwargs with keys removed
    """
    if keys is None:
        keys = ['obj', 'pytan_help', 'objtype']

    clean_kwargs = dict(kwargs)
    [clean_kwargs.pop(x) for x in keys if x in kwargs]
    return clean_kwargs


def check_for_help(kwargs):
    """Utility method to check for any help arguments and raise a PytanHelp exception with the appropriate help

    Parameters
    ----------
    kwargs : dict
        * dict of keyword args
    """
    help_keys = [x for x in dir(pytan.help) if x.endswith('_help')]
    for x in help_keys:
        if kwargs.get(x, False):
            help_out = getattr(pytan.help, x)()
            raise pytan.exceptions.PytanHelp(help_out)


def parse_versioning(server_version):
    """Parses server_version into a dictionary

    Parameters
    ----------
    server_version : str
        * str of server version

    Returns
    -------
    dict
        * dict of parsed tanium server version containing keys: major, minor, revision, and build
    """
    v_keys = ['major', 'minor', 'revision', 'build']
    # fallback_ints = [-1, -1, -1, -1]
    try:
        v_parts = server_version.split('.')
        v_ints = [int(x) for x in v_parts]
        v_dict = dict(zip(v_keys, v_ints))
    except:
        m = (
            "Unable to parse major, minor, revision, and build from server "
            "version string: {}"
        ).format
        raise pytan.exceptions.VersionParseError(m(server_version))
    return v_dict


def calculate_question_start_time(q):
    """Caclulates the start time of a question by doing q.expiration - q.expire_seconds

    Parameters
    ----------
    q : :class:`taniumpy.object_types.question.Question`
        * Question object to calculate start time for

    Returns
    -------
    tuple : str, datetime
        * a tuple containing the start time first in str format for Tanium Server API, second in datetime object format
    """
    expire_dt = pytan.utils.timestr_to_datetime(q.expiration)
    expire_seconds_delta = datetime.timedelta(seconds=q.expire_seconds)
    start_time_dt = expire_dt - expire_seconds_delta
    start_time = pytan.utils.datetime_to_timestr(start_time_dt)
    return start_time, start_time_dt


def vig_encode(key, string):
    """Obfuscates a string with a key using Vigenere cipher.

    Only useful for obfuscation, not real security!!

    Parameters
    ----------
    key : str
        * key to scrambled string with
    string : str
        * string to scramble with key

    Returns
    -------
    encoded_string : str
        * encoded string
    """
    string = str(string)
    encoded_chars = []
    for i in xrange(len(string)):
        key_c = key[i % len(key)]
        encoded_c = chr(ord(string[i]) + ord(key_c) % 256)
        encoded_chars.append(encoded_c)
    v_string = "".join(encoded_chars)
    encoded_string = base64.urlsafe_b64encode(v_string)
    encoded_string = '::{}::'.format(encoded_string)
    return encoded_string


def vig_decode(key, string):
    """De-obfuscates a string with a key using Vigenere cipher.

    Only useful for obfuscation, not real security!!

    Notes
    -----
    This will only work with strings that have been encoded with vig_encode(). "normal" strings will be returned as-is.

    Parameters
    ----------
    key : str
        * key that string is scrambled with
    string : str
        * string to unscramble with key

    Returns
    -------
    decoded_string : str
        * decoded string
    """
    if string.startswith('::') and string.endswith('::'):
        string = str(string[2:-2])
    else:
        return string

    v_string = base64.urlsafe_b64decode(string)

    decoded_chars = []
    for i in xrange(len(v_string)):
        key_c = key[i % len(key)]
        encoded_c = chr(abs(ord(v_string[i]) - ord(key_c) % 256))
        decoded_chars.append(encoded_c)
    decoded_string = "".join(decoded_chars)
    return decoded_string
