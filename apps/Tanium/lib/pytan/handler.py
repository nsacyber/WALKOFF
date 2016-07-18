# -*- mode: Python; tab-width: 4; indent-tabs-mode: nil; -*-
# ex: set tabstop=4
# Please do not change the two lines above. See PEP 8, PEP 263.
"""The main :mod:`pytan` module that provides first level entities for programmatic use."""
import sys

# disable python from creating .pyc files everywhere
sys.dont_write_bytecode = True

import os
import logging
import io
import datetime
import pprint
import json

my_file = os.path.abspath(__file__)
my_dir = os.path.dirname(my_file)
parent_dir = os.path.dirname(my_dir)
path_adds = [parent_dir]
[sys.path.insert(0, aa) for aa in path_adds if aa not in sys.path]

import taniumpy
import pytan


class Handler(object):
    """Creates a connection to a Tanium SOAP Server on host:port

    Parameters
    ----------
    username : str
        * default: None
        * `username` to connect to `host` with
    password : str
        * default: None
        * `password` to connect to `host` with
    host : str
        * default: None
        * hostname or ip of Tanium SOAP Server
    port : int, optional
        * default: 443
        * port of Tanium SOAP Server on `host`
    loglevel : int, optional
        * default: 0
        * 0 do not print anything except warnings/errors
        * 1 and higher will print more
    debugformat : bool, optional
        * default: False
        * False: use one line logformat
        * True: use two lines
    gmt_log : bool, optional
        * default: True
        * True: use GMT timezone for log output
        * False: use local time for log output
    session_id : str, optional
        * default: None
        * session_id to use while authenticating instead of username/password
    pytan_user_config : str, optional
        * default: pytan.constants.PYTAN_USER_CONFIG
        * JSON file containing key/value pairs to override class variables

    Other Parameters
    ----------------
    http_debug : bool, optional
        * default: False
        * False: do not print requests package debug
        * True: do print requests package debug
        * This is passed through to :class:`pytan.sessions.Session`
    http_auth_retry: bool, optional
        * default: True
        * True: retry HTTP GET/POST's
        * False: do not retry HTTP GET/POST's
        * This is passed through to :class:`pytan.sessions.Session`
    http_retry_count: int, optional
        * default: 5
        * number of times to retry HTTP GET/POST's if the connection times out/fails
        * This is passed through to :class:`pytan.sessions.Session`
    soap_request_headers : dict, optional
        * default: {'Content-Type': 'text/xml; charset=utf-8', 'Accept-Encoding': 'gzip'}
        * dictionary of headers to add to every HTTP GET/POST
        * This is passed through to :class:`pytan.sessions.Session`
    auth_connect_timeout_sec : int, optional
        * default: 5
        * number of seconds before timing out for a connection while authenticating
        * This is passed through to :class:`pytan.sessions.Session`
    auth_response_timeout_sec : int, optional
        * default: 15
        * number of seconds before timing out for a response while authenticating
        * This is passed through to :class:`pytan.sessions.Session`
    info_connect_timeout_sec : int, optional
        * default: 5
        * number of seconds before timing out for a connection while getting /info.json
        * This is passed through to :class:`pytan.sessions.Session`
    info_response_timeout_sec : int, optional
        * default: 15
        * number of seconds before timing out for a response while getting /info.json
        * This is passed through to :class:`pytan.sessions.Session`
    soap_connect_timeout_sec : int, optional
        * default: 15
        * number of seconds before timing out for a connection for a SOAP request
        * This is passed through to :class:`pytan.sessions.Session`
    soap_response_timeout_sec : int, optional
        * default: 540
        * number of seconds before timing out for a response for a SOAP request
        * This is passed through to :class:`pytan.sessions.Session`
    stats_loop_enabled : bool, optional
        * default: False
        * False: do not enable the statistics loop thread
        * True: enable the statistics loop thread
        * This is passed through to :class:`pytan.sessions.Session`
    stats_loop_sleep_sec : int, optional
        * default: 5
        * number of seconds to sleep in between printing the statistics when stats_loop_enabled is True
        * This is passed through to :class:`pytan.sessions.Session`
    record_all_requests: bool, optional
        * default: False
        * False: do not add each requests response object to session.ALL_REQUESTS_RESPONSES
        * True: add each requests response object to session.ALL_REQUESTS_RESPONSES
        * This is passed through to :class:`pytan.sessions.Session`
    stats_loop_targets : list of dict, optional
        * default: [{'Version': 'Settings/Version'}, {'Active Questions': 'Active Question Cache/Active Question Estimate'}, {'Clients': 'Active Question Cache/Active Client Estimate'}, {'Strings': 'String Cache/Total String Count'}, {'Handles': 'System Performance Info/HandleCount'}, {'Processes': 'System Performance Info/ProcessCount'}, {'Memory Available': 'percentage(System Performance Info/PhysicalAvailable,System Performance Info/PhysicalTotal)'}]
        * list of dictionaries with the key being the section of info.json to print info from, and the value being the item with in that section to print the value
        * This is passed through to :class:`pytan.sessions.Session`
    persistent: bool, optional
        * default: False
        * False: do not request a persistent session
        * True: do request a persistent
        * This is passed through to :func:`pytan.sessions.Session.authenticate`
    force_server_version: str, optional
        * default: ''
        * use this to override the server_version detection

    Notes
    -----
      * for 6.2: port 444 is the default SOAP port, port 443 forwards /soap/ URLs to the SOAP port,
        Use port 444 if you have direct access to it. However, port 444 is the only port that
        exposes the /info page in 6.2
      * for 6.5: port 443 is the default SOAP port, there is no port 444

    See Also
    --------
    :data:`pytan.constants.LOG_LEVEL_MAPS` : maps a given `loglevel` to respective logger names and their logger levels
    :data:`pytan.constants.INFO_FORMAT` : debugformat=False
    :data:`pytan.constants.DEBUG_FORMAT` : debugformat=True
    :class:`taniumpy.session.Session` : Session object used by Handler

    Examples
    --------
    Setup a Handler() object::

        >>> import sys
        >>> sys.path.append('/path/to/pytan/')
        >>> import pytan
        >>> handler = pytan.Handler('username', 'password', 'host')
    """

    def __init__(self, username=None, password=None, host=None, port=443,
                 loglevel=0, debugformat=False, gmt_log=True, session_id=None, **kwargs):
        super(Handler, self).__init__()
        self.mylog = logging.getLogger("pytan.handler")
        self.methodlog = logging.getLogger("method_debug")

        # update self with all local variables that are not self/kwargs/k/v
        for k, v in locals().iteritems():
            if k in ['self', 'kwargs', 'k', 'v']:
                continue
            setattr(self, k, v)

        # setup the console logging handler
        pytan.utils.setup_console_logging(gmt_tz=self.gmt_log)

        # create all the loggers and set their levels based on loglevel
        pytan.utils.set_log_levels(loglevel=self.loglevel)

        # change the format of console logging handler if need be
        pytan.utils.change_console_format(debug=self.debugformat)

        # get the default pytan user config file
        puc_default = os.path.expanduser(pytan.constants.PYTAN_USER_CONFIG)

        # see if the pytan_user_config file location was overridden
        puc_kwarg = kwargs.get('pytan_user_config', '')

        self.puc = puc_kwarg or puc_default
        kwargs = self.read_pytan_user_config(kwargs)

        if gmt_log != self.gmt_log:
            pytan.utils.setup_console_logging(gmt_tz=self.gmt_log)

        if loglevel != self.loglevel:
            pytan.utils.set_log_levels(loglevel=self.loglevel)

        if debugformat != self.debugformat:
            pytan.utils.change_console_format(debug=self.debugformat)

        self.debug_method_locals = kwargs.get('debug_method_locals', False)

        self._debug_locals(sys._getframe().f_code.co_name, locals())

        if not self.session_id:

            if not self.username:
                raise pytan.exceptions.HandlerError("Must supply username!")

            if not self.password:
                raise pytan.exceptions.HandlerError("Must supply password!")

        if self.password:
            self.password = pytan.utils.vig_decode(pytan.constants.PYTAN_KEY, self.password)

        if not self.host:
            raise pytan.exceptions.HandlerError("Must supply host!")

        if not self.port:
            raise pytan.exceptions.HandlerError("Must supply port!")

        try:
            self.port = int(self.port)
        except ValueError:
            raise pytan.exceptions.HandlerError("port must be an integer!")

        pytan.utils.test_app_port(host=self.host, port=self.port)

        # establish our Session class
        self.session = pytan.sessions.Session(host=self.host, port=self.port, **kwargs)

        # authenticate using the Session class
        self.session.authenticate(
            username=self.username, password=self.password, session_id=self.session_id, **kwargs
        )

    def __str__(self):
        self._debug_locals(sys._getframe().f_code.co_name, locals())

        str_tpl = "PyTan v{} Handler for {}".format
        ret = str_tpl(pytan.__version__, self.session)
        return ret

    def read_pytan_user_config(self, kwargs):
        """Read a PyTan User Config and update the current class variables

        Returns
        -------
        kwargs : dict
            * kwargs with updated variables from PyTan User Config (if any)
        """
        if not os.path.isfile(self.puc):
            m = "Unable to find PyTan User config file at: {}".format
            self.mylog.debug(m(self.puc))
            return kwargs

        try:
            with open(self.puc) as fh:
                puc_dict = json.load(fh)
        except Exception as e:
            m = "PyTan User config file at: {} is invalid, exception: {}".format
            self.mylog.error(m(self.puc, e))
        else:
            m = "PyTan User config file successfully loaded: {} ".format
            self.mylog.info(m(self.puc))

            # handle class params
            for h_arg, arg_default in pytan.constants.HANDLER_ARG_DEFAULTS.iteritems():
                if h_arg not in puc_dict:
                    continue

                if h_arg == 'password':
                    puc_dict['password'] = pytan.utils.vig_decode(
                        pytan.constants.PYTAN_KEY, puc_dict['password'],
                    )

                class_val = getattr(self, h_arg, None)
                puc_val = puc_dict[h_arg]

                if class_val != arg_default:
                    m = "User supplied argument for {}, ignoring value from: {}".format
                    self.mylog.debug(m(h_arg, self.puc))
                    continue

                if arg_default is None or puc_val != class_val:
                    m = "Setting class variable {} with value from: {}".format
                    self.mylog.debug(m(h_arg, self.puc))
                    setattr(self, h_arg, puc_val)

            # handle kwargs params
            for k, v in puc_dict.iteritems():
                if k in ['self', 'kwargs', 'k', 'v']:
                    m = "Skipping kwargs variable {} from: {}".format
                    self.mylog.debug(m(k, self.puc))
                    continue

                if not hasattr(self, k) and k not in kwargs:
                    m = "Setting kwargs variable {} with value from: {}".format
                    self.mylog.debug(m(k, self.puc))
                    kwargs[k] = v
        return kwargs

    def write_pytan_user_config(self, **kwargs):
        """Write a PyTan User Config with the current class variables for use with pytan_user_config in instantiating Handler()

        Parameters
        ----------
        pytan_user_config : str, optional
            * default: self.puc
            * JSON file to wite with current class variables

        Returns
        -------
        puc : str
            * filename of PyTan User Config that was written to
        """
        puc_kwarg = kwargs.get('pytan_user_config', '')
        puc = puc_kwarg or self.puc
        puc = os.path.expanduser(puc)

        puc_dict = {}

        for k, v in vars(self).iteritems():
            if k in ['mylog', 'methodlog', 'session', 'puc']:
                m = "Skipping class variable {} from inclusion in: {}".format
                self.mylog.debug(m(k, puc))
                continue

            m = "Including class variable {} in: {}".format
            self.mylog.debug(m(k, puc))
            puc_dict[k] = v

        # obfuscate the password
        puc_dict['password'] = pytan.utils.vig_encode(pytan.constants.PYTAN_KEY, self.password)

        try:
            with open(puc, 'w+') as fh:
                json.dump(puc_dict, fh, skipkeys=True, indent=2)
        except Exception as e:
            m = "Failed to write PyTan User config: '{}', exception: {}".format
            raise pytan.exceptions.HandlerError(m(puc, e))
        else:
            m = "PyTan User config file successfully written: {} ".format
            self.mylog.info(m(puc))
        return puc

    def get_server_version(self, **kwargs):
        """Uses :func:`taniumpy.session.Session.get_server_version` to get the version of the Tanium Server

        Returns
        -------
        server_version: str
            * Version of Tanium Server in string format
        """
        self._debug_locals(sys._getframe().f_code.co_name, locals())

        server_version = self.session.get_server_version(**kwargs)
        return server_version

    # Questions
    def ask(self, **kwargs):
        """Ask a type of question and get the results back

        Parameters
        ----------
        qtype : str, optional
            * default: 'manual'
            * type of question to ask: {'saved', 'manual', '_manual'}

        Returns
        -------
        result : dict, containing:
            * `question_object` : one of the following depending on `qtype`: :class:`taniumpy.object_types.question.Question` or :class:`taniumpy.object_types.saved_question.SavedQuestion`
            * `question_results` : :class:`taniumpy.object_types.result_set.ResultSet`

        See Also
        --------
        :data:`pytan.constants.Q_OBJ_MAP` : maps qtype to a method in Handler()
        :func:`pytan.handler.Handler.ask_saved` : method used when qtype == 'saved'
        :func:`pytan.handler.Handler.ask_manual` : method used when qtype == 'manual'
        :func:`pytan.handler.Handler._ask_manual` : method used when qtype == '_manual'
        """
        self._debug_locals(sys._getframe().f_code.co_name, locals())

        qtype = kwargs.get('qtype', 'manual')

        clean_keys = ['qtype']
        clean_kwargs = pytan.utils.clean_kwargs(kwargs=kwargs, keys=clean_keys)

        q_obj_map = pytan.utils.get_q_obj_map(qtype=qtype)

        method = getattr(self, q_obj_map['handler'])
        result = method(**clean_kwargs)
        return result

    def ask_saved(self, refresh_data=False, **kwargs):
        """Ask a saved question and get the results back

        Parameters
        ----------
        id : int, list of int, optional
            * id of saved question to ask
        name : str, list of str
            * name of saved question
        refresh_data: bool, optional
            * default False
            * False: do not perform a getResultInfo before issuing a getResultData
            * True: perform a getResultInfo before issuing a getResultData
        sse : bool, optional
            * default: False
            * True: perform a server side export when getting result data
            * False: perform a normal get result data (default for 6.2)
            * Keeping False by default for now until the columnset's are properly identified in the server export
        sse_format : str, optional
            * default: 'xml_obj'
            * format to have server side export report in, one of: {'csv', 'xml', 'xml_obj', 'cef', 0, 1, 2}
        leading : str, optional
            * default: ''
            * used for sse_format 'cef' only, the string to prepend to each row
        trailing : str, optional
            * default: ''
            * used for sse_format 'cef' only, the string to append to each row
        polling_secs : int, optional
            * default: 5
            * Number of seconds to wait in between GetResultInfo loops
            * This is passed through to :class:`pytan.pollers.QuestionPoller`
        complete_pct : int/float, optional
            * default: 99
            * Percentage of mr_tested out of estimated_total to consider the question "done"
            * This is passed through to :class:`pytan.pollers.QuestionPoller`
        override_timeout_secs : int, optional
            * default: 0
            * If supplied and not 0, timeout in seconds instead of when object expires
            * This is passed through to :class:`pytan.pollers.QuestionPoller`
        callbacks : dict, optional
            * default: {}
            * can be a dict of functions to be run with the key names being the various state changes: 'ProgressChanged', 'AnswersChanged', 'AnswersComplete'
            * This is passed through to :func:`pytan.pollers.QuestionPoller.run`
        override_estimated_total : int, optional
            * instead of getting number of systems that should see this question from result_info.estimated_total, use this number
            * This is passed through to :func:`pytan.pollers.QuestionPoller`
        force_passed_done_count : int, optional
            * when this number of systems have passed the right hand side of the question, consider the question complete
            * This is passed through to :func:`pytan.pollers.QuestionPoller`

        Returns
        -------
        ret : dict, containing
            * `question_object` : :class:`taniumpy.object_types.saved_question.SavedQuestion`, the saved question object
            * `question_object` : :class:`taniumpy.object_types.question.Question`, the question asked by `saved_question_object`
            * `question_results` : :class:`taniumpy.object_types.result_set.ResultSet`, the results for `question_object`
            * `poller_object` : None if `refresh_data` == False, elsewise :class:`pytan.pollers.QuestionPoller`, poller object used to wait until all results are in before getting `question_results`,
            * `poller_success` : None if `refresh_data` == False, elsewise True or False

        Notes
        -----
        id or name must be supplied
        """
        self._debug_locals(sys._getframe().f_code.co_name, locals())

        clean_kwargs = pytan.utils.clean_kwargs(kwargs=kwargs)
        sse = kwargs.get('sse', False)
        clean_kwargs['sse_format'] = clean_kwargs.get('sse_format', 'xml_obj')

        # get the saved_question object the user passed in
        h = "Issue a GetObject to find saved question objects"
        sq_objs = self.get(objtype='saved_question', pytan_help=h, **clean_kwargs)

        if len(sq_objs) != 1:
            err = (
                "Multiple saved questions returned, can only ask one "
                "saved question!\nArgs: {}\nReturned saved questions:\n\t{}"
            ).format
            sq_obj_str = '\n\t'.join([str(x) for x in sq_objs])
            raise pytan.exceptions.HandlerError(err(kwargs, sq_obj_str))

        sq_obj = sq_objs[0]

        h = (
            "Issue a GetObject to get the full object of the last question asked by a saved "
            "question"
        )
        q_obj = self._find(obj=sq_obj.question, pytan_help=h, **clean_kwargs)

        poller = None
        poller_success = None

        if refresh_data:
            # if GetResultInfo is issued on a saved question, Tanium will issue a new question
            # to fetch new/updated results
            h = (
                "Issue a GetResultInfo for a saved question in order to issue a new question, "
                "which refreshes the data for that saved question"
            )
            self.get_result_info(obj=sq_obj, pytan_help=h, **clean_kwargs)

            # re-fetch the saved question object to get the newly asked question info
            h = (
                "Issue a GetObject for the saved question in order get the ID of the newly "
                "asked question"
            )
            shrunk_obj = pytan.utils.shrink_obj(obj=sq_obj)
            sq_obj = self._find(obj=shrunk_obj, pytan_help=h, **clean_kwargs)

            h = (
                "Issue a GetObject to get the full object of the last question asked by a saved "
                "question"
            )
            q_obj = self._find(obj=sq_obj.question, pytan_help=h, **clean_kwargs)

            m = "Question Added, ID: {}, query text: {!r}, expires: {}".format
            self.mylog.debug(m(q_obj.id, q_obj.query_text, q_obj.expiration))

            # poll the new question for this saved question to wait for results
            poller = pytan.pollers.QuestionPoller(handler=self, obj=q_obj, **clean_kwargs)
            poller_success = poller.run(**clean_kwargs)

        # get the results
        if sse and self.session.platform_is_6_5(**clean_kwargs):
            h = (
                "Issue a GetResultData for a server side export to get the answers for the last "
                "asked question of this saved question"
            )

            rd = self.get_result_data_sse(obj=q_obj, pytan_help=h, **clean_kwargs)
        else:
            h = (
                "Issue a GetResultData to get the answers for the last asked question of "
                "this saved question"
            )
            rd = self.get_result_data(obj=q_obj, pytan_help=h, **clean_kwargs)

        if isinstance(rd, taniumpy.object_types.result_set.ResultSet):
            # add the sensors from this question to the ResultSet object for reporting
            rd.sensors = [x.sensor for x in q_obj.selects]

        ret = {
            'saved_question_object': sq_obj,
            'poller_object': poller,
            'poller_success': poller_success,
            'question_object': q_obj,
            'question_results': rd,
        }

        return ret

    def ask_manual(self, **kwargs):
        """Ask a manual question using human strings and get the results back

        This method takes a string or list of strings and parses them into
        their corresponding definitions needed by :func:`_ask_manual`

        Parameters
        ----------
        sensors : str, list of str
            * default: []
            * sensors (columns) to include in question
        question_filters : str, list of str, optional
            * default: []
            * filters that apply to the whole question
        question_options : str, list of str, optional
            * default: []
            * options that apply to the whole question
        get_results : bool, optional
            * default: True
            * True: wait for result completion after asking question
            * False: just ask the question and return it in result
        sensors_help : bool, optional
            * default: False
            * False: do not print the help string for sensors
            * True: print the help string for sensors and exit
        filters_help : bool, optional
            * default: False
            * False: do not print the help string for filters
            * True: print the help string for filters and exit
        options_help : bool, optional
            * default: False
            * False: do not print the help string for options
            * True: print the help string for options and exit
        polling_secs : int, optional
            * default: 5
            * Number of seconds to wait in between GetResultInfo loops
            * This is passed through to :class:`pytan.pollers.QuestionPoller`
        complete_pct : int/float, optional
            * default: 99
            * Percentage of mr_tested out of estimated_total to consider the question "done"
            * This is passed through to :class:`pytan.pollers.QuestionPoller`
        override_timeout_secs : int, optional
            * default: 0
            * If supplied and not 0, timeout in seconds instead of when object expires
            * This is passed through to :class:`pytan.pollers.QuestionPoller`
        callbacks : dict, optional
            * default: {}
            * can be a dict of functions to be run with the key names being the various state changes: 'ProgressChanged', 'AnswersChanged', 'AnswersComplete'
            * This is passed through to :func:`pytan.pollers.QuestionPoller.run`
        override_estimated_total : int, optional
            * instead of getting number of systems that should see this question from result_info.estimated_total, use this number
            * This is passed through to :func:`pytan.pollers.QuestionPoller`
        force_passed_done_count : int, optional
            * when this number of systems have passed the right hand side of the question, consider the question complete
            * This is passed through to :func:`pytan.pollers.QuestionPoller`

        Returns
        -------
        result : dict, containing:
            * `question_object` : :class:`taniumpy.object_types.question.Question`, the actual question created and added by PyTan
            * `question_results` : :class:`taniumpy.object_types.result_set.ResultSet`, the Result Set for `question_object` if `get_results` == True
            * `poller_object` : :class:`pytan.pollers.QuestionPoller`, poller object used to wait until all results are in before getting `question_results`
            * `poller_success` : None if `get_results` == True, elsewise True or False

        Examples
        --------
        >>> # example of str for `sensors`
        >>> sensors = 'Sensor1'

        >>> # example of str for `sensors` with params
        >>> sensors = 'Sensor1{key:value}'

        >>> # example of str for `sensors` with params and filter
        >>> sensors = 'Sensor1{key:value}, that contains:example text'

        >>> # example of str for `sensors` with params and filter and options
        >>> sensors = (
        ...     'Sensor1{key:value}, that contains:example text,'
        ...     'opt:ignore_case, opt:max_data_age:60'
        ... )

        >>> # example of str for question_filters
        >>> question_filters = 'Sensor2, that contains:example test'

        >>> # example of list of str for question_options
        >>> question_options = ['max_data_age:3600', 'and']

        Notes
        -----

        When asking a question from the Tanium console, you construct a question like:

            Get Computer Name and IP Route Details from all machines with Is Windows containing "True"

        Asking the same question in PyTan has some similarities:

            >>> r = handler.ask_manual(sensors=['Computer Name', 'IP Route Details'], question_filters=['Is Windows, that contains:True'])

        There are two sensors in this question, after the "Get" and before the "from all machines": "Computer Name" and "IP Route Details". The sensors after the "Get" and before the "from all machines" can be referred to as any number of things:

            * sensors
            * left hand side
            * column selects

        The sensors that are defined after the "Get" and before the "from all machines" are best described as a column selection, and control what columns you want to show up in your results. These sensor names are the same ones that would need to be passed into ask_question() for the sensors arguments.

        You can filter your column selections by using a filter in the console like so:

            Get Computer Name starting with "finance" and IP Route Details from all machines with Is Windows containing "True"

        And in PyTan:

             >>> r = handler.ask_manual(sensors=['Computer Name, that starts with:finance', 'IP Route Details'], question_filters=['Is Windows, that contains:True'])

        This will cause the results to have the same number of columns, but for any machine that returns results that do not match the filter specified for a given sensor, the row for that column will contain "[no results]".

        There is also a sensor specified after the "from all machines with": "Is Windows". This sensor can be referred to as any number of things:

            * question filters
            * sensors (also)
            * right hand side
            * row selects

        Any system that does not match the conditions in the question filters will return no results at all.  These question filters are really just sensors all over again, but instead of controlling what columns are output in the results, they control what rows are output in the results.

        See Also
        --------
        :data:`pytan.constants.FILTER_MAPS` : valid filter dictionaries for filters
        :data:`pytan.constants.OPTION_MAPS` : valid option dictionaries for options
        :func:`pytan.handler.Handler._ask_manual` : private method with the actual workflow used to create and add the question object
        """
        self._debug_locals(sys._getframe().f_code.co_name, locals())

        pytan.utils.check_for_help(kwargs=kwargs)

        sensors = kwargs.get('sensors', [])
        q_filters = kwargs.get('question_filters', [])
        q_options = kwargs.get('question_options', [])

        sensor_defs = pytan.utils.dehumanize_sensors(sensors=sensors)
        q_filter_defs = pytan.utils.dehumanize_question_filters(question_filters=q_filters)
        q_option_defs = pytan.utils.dehumanize_question_options(question_options=q_options)

        clean_keys = ['sensor_defs', 'question_filter_defs', 'question_option_defs']
        clean_kwargs = pytan.utils.clean_kwargs(kwargs=kwargs, keys=clean_keys)

        result = self._ask_manual(
            sensor_defs=sensor_defs,
            question_filter_defs=q_filter_defs,
            question_option_defs=q_option_defs,
            **clean_kwargs
        )
        return result

    def parse_query(self, question_text, **kwargs):
        """Ask a parsed question as `question_text` and get a list of parsed results back

        Parameters
        ----------
        question_text : str
            * The question text you want the server to parse into a list of parsed results

        Returns
        -------
        parse_job_results : :class:`taniumpy.object_types.parse_result_group.ParseResultGroup`
        """
        self._debug_locals(sys._getframe().f_code.co_name, locals())

        if not self.session.platform_is_6_5(**kwargs):
            m = "ParseJob not supported in version: {}".format
            m = m(self.session.server_version)
            raise pytan.exceptions.UnsupportedVersionError(m)

        parse_job = taniumpy.ParseJob()
        parse_job.question_text = question_text
        parse_job.parser_version = 2

        clean_keys = ['obj']
        clean_kwargs = pytan.utils.clean_kwargs(kwargs=kwargs, keys=clean_keys)

        parse_job_results = self.session.add(obj=parse_job, **clean_kwargs)
        return parse_job_results

    def ask_parsed(self, question_text, picker=None, get_results=True, **kwargs):
        """Ask a parsed question as `question_text` and use the index of the parsed results from `picker`

        Parameters
        ----------
        question_text : str
            * The question text you want the server to parse into a list of parsed results
        picker : int
            * default: None
            * The index number of the parsed results that correlates to the actual question you wish to run
        get_results : bool, optional
            * default: True
            * True: wait for result completion after asking question
            * False: just ask the question and return it in `ret`
        sse : bool, optional
            * default: False
            * True: perform a server side export when getting result data
            * False: perform a normal get result data (default for 6.2)
            * Keeping False by default for now until the columnset's are properly identified in the server export
        sse_format : str, optional
            * default: 'xml_obj'
            * format to have server side export report in, one of: {'csv', 'xml', 'xml_obj', 'cef', 0, 1, 2}
        leading : str, optional
            * default: ''
            * used for sse_format 'cef' only, the string to prepend to each row
        trailing : str, optional
            * default: ''
            * used for sse_format 'cef' only, the string to append to each row
        polling_secs : int, optional
            * default: 5
            * Number of seconds to wait in between GetResultInfo loops
            * This is passed through to :class:`pytan.pollers.QuestionPoller`
        complete_pct : int/float, optional
            * default: 99
            * Percentage of mr_tested out of estimated_total to consider the question "done"
            * This is passed through to :class:`pytan.pollers.QuestionPoller`
        override_timeout_secs : int, optional
            * default: 0
            * If supplied and not 0, timeout in seconds instead of when object expires
            * This is passed through to :class:`pytan.pollers.QuestionPoller`
        callbacks : dict, optional
            * default: {}
            * can be a dict of functions to be run with the key names being the various state changes: 'ProgressChanged', 'AnswersChanged', 'AnswersComplete'
            * This is passed through to :func:`pytan.pollers.QuestionPoller.run`
        override_estimated_total : int, optional
            * instead of getting number of systems that should see this question from result_info.estimated_total, use this number
            * This is passed through to :func:`pytan.pollers.QuestionPoller`
        force_passed_done_count : int, optional
            * when this number of systems have passed the right hand side of the question, consider the question complete
            * This is passed through to :func:`pytan.pollers.QuestionPoller`

        Returns
        -------
        ret : dict, containing:
            * `question_object` : :class:`taniumpy.object_types.question.Question`, the actual question added by PyTan
            * `question_results` : :class:`taniumpy.object_types.result_set.ResultSet`, the Result Set for `question_object` if `get_results` == True
            * `poller_object` : :class:`pytan.pollers.QuestionPoller`, poller object used to wait until all results are in before getting `question_results`
            * `poller_success` : None if `get_results` == True, elsewise True or False
            * `parse_results` : :class:`taniumpy.object_types.parse_result_group_list.ParseResultGroupList`, the parse result group returned from Tanium after parsing `question_text`

        Examples
        --------

        Ask the server to parse 'computer name', but don't pick a choice (will print out a list of choices at critical logging level and then throw an exception):
            >>> v = handler.ask_parsed('computer name')

        Ask the server to parse 'computer name' and pick index 1 as the question you want to run:
            >>> v = handler.ask_parsed('computer name', picker=1)
        """
        self._debug_locals(sys._getframe().f_code.co_name, locals())

        if not self.session.platform_is_6_5(**kwargs):
            m = "ParseJob not supported in version: {}".format
            m = m(self.session.server_version)
            raise pytan.exceptions.UnsupportedVersionError(m)

        clean_keys = ['obj', 'question_text', 'handler']
        clean_kwargs = pytan.utils.clean_kwargs(kwargs=kwargs, keys=clean_keys)

        sse = kwargs.get('sse', False)
        clean_kwargs['sse_format'] = clean_kwargs.get('sse_format', 'xml_obj')

        h = "Issue an AddObject to add a ParseJob for question_text and get back ParseResultGroups"
        parse_job_results = self.parse_query(
            question_text=question_text, pytan_help=h, **clean_kwargs
        )

        if not parse_job_results:
            m = (
                "Question Text '{}' was unable to be parsed into a valid query text by the server"
            ).format
            raise pytan.exceptions.ServerParseError(m())

        pi = "Index {0}, Score: {1.score}, Query: {1.question_text!r}".format
        pw = (
            "You must supply an index as picker=$index to choose one of the parse "
            "responses -- re-run ask_parsed with picker set to one of these indexes!!"
        ).format

        if picker is None:
            self.mylog.critical(pw())
            for idx, x in enumerate(parse_job_results):
                self.mylog.critical(pi(idx + 1, x))
            raise pytan.exceptions.PickerError(pw())

        try:
            picked_parse_job = parse_job_results[picker - 1]
        except:
            invalid_pw = (
                "You supplied an invalid picker index {} - {}"
            ).format
            self.mylog.critical(invalid_pw(picker, pw))

            pi = "Index {0}, Score: {1.score}, Query: {1.question_text!r}"
            for idx, x in enumerate(parse_job_results):
                self.mylog.critical(pi(idx + 1, x))
            raise pytan.exceptions.PickerError(pw())

        add_obj = picked_parse_job.question

        # add our Question and get a Question ID back
        h = "Issue an AddObject to add the Question object from the chosen ParseResultGroup"
        added_obj = self._add(obj=add_obj, pytan_help=h, **clean_kwargs)

        m = "Question Added, ID: {}, query text: {!r}, expires: {}".format
        self.mylog.debug(m(added_obj.id, added_obj.query_text, added_obj.expiration))

        poller = pytan.pollers.QuestionPoller(handler=self, obj=added_obj, **clean_kwargs)

        ret = {
            'question_object': added_obj,
            'poller_object': poller,
            'question_results': None,
            'poller_success': None,
            'parse_results': parse_job_results,
        }

        if get_results:
            # poll the Question ID returned above to wait for results
            ret['poller_success'] = ret['poller_object'].run(**clean_kwargs)

            # get the results
            if sse:
                rd = self.get_result_data_sse(obj=added_obj, **clean_kwargs)
            else:
                rd = self.get_result_data(obj=added_obj, **clean_kwargs)

            if isinstance(rd, taniumpy.object_types.result_set.ResultSet):
                # add the sensors from this question to the ResultSet object for reporting
                rd.sensors = rd.sensors = [x.sensor for x in added_obj.selects]

            ret['question_results'] = rd
        return ret

    # Actions
    def deploy_action(self, **kwargs):
        """Deploy an action and get the results back

        This method takes a string or list of strings and parses them into
        their corresponding definitions needed by :func:`_deploy_action`

        Parameters
        ----------
        package : str
            * package to deploy with this action
        action_filters : str, list of str, optional
            * default: []
            * each string must describe a sensor and a filter which limits which computers the action will deploy `package` to
        action_options : str, list of str, optional
            * default: []
            * options to apply to `action_filters`
        start_seconds_from_now : int, optional
            * default: 0
            * start action N seconds from now
        distribute_seconds : int, optional
            * default: 0
            * distribute action evenly over clients over N seconds
        issue_seconds : int, optional
            * default: 0
            * have the server re-ask the action status question if performing a GetResultData over N seconds ago
        expire_seconds : int, optional
            * default: package.expire_seconds
            * expire action N seconds from now, will be derived from package if not supplied
        run : bool, optional
            * default: False
            * False: just ask the question that pertains to verify action, export the results to CSV, and raise pytan.exceptions.RunFalse -- does not deploy the action
            * True: actually deploy the action
        get_results : bool, optional
            * default: True
            * True: wait for result completion after deploying action
            * False: just deploy the action and return the object in `ret`
        action_name : str, optional
            * default: prepend package name with "API Deploy "
            * custom name for action
        action_comment : str, optional
            * default:
            * custom comment for action
        polling_secs : int, optional
            * default: 5
            * Number of seconds to wait in between GetResultInfo loops
            * This is passed through to :class:`pytan.pollers.ActionPoller`
        complete_pct : int/float, optional
            * default: 100
            * Percentage of passed_count out of successfully run actions to consider the action "done"
            * This is passed through to :class:`pytan.pollers.ActionPoller`
        override_timeout_secs : int, optional
            * default: 0
            * If supplied and not 0, timeout in seconds instead of when object expires
            * This is passed through to :class:`pytan.pollers.ActionPoller`
        override_passed_count : int, optional
            * instead of getting number of systems that should run this action by asking a question, use this number
            * This is passed through to :class:`pytan.pollers.ActionPoller`

        Returns
        -------
        ret : dict, containing:
            * `saved_action_object` : :class:`taniumpy.object_types.saved_action.SavedAction`, the saved_action added for this action (None if 6.2)
            * `action_object` : :class:`taniumpy.object_types.action.Action`, the action object that tanium created for `saved_action`
            * `package_object` : :class:`taniumpy.object_types.package_spec.PackageSPec`, the package object used in `saved_action`
            * `action_info` : :class:`taniumpy.object_types.result_info.ResultInfo`, the initial GetResultInfo call done before getting results
            * `poller_object` : :class:`pytan.pollers.ActionPoller`, poller object used to wait until all results are in before getting `action_results`
            * `poller_success` : None if `get_results` == False, elsewise True or False
            * `action_results` : None if `get_results` == False, elsewise :class:`taniumpy.object_types.result_set.ResultSet`, the results for `action_object`
            * `action_result_map` : None if `get_results` == False, elsewise progress map for `action_object` in dictionary form

        Examples
        --------
        >>> # example of str for `package`
        >>> package = 'Package1'

        >>> # example of str for `package` with params
        >>> package = 'Package1{key:value}'

        >>> # example of str for `action_filters` with params and filter for sensors
        >>> action_filters = 'Sensor1{key:value}, that contains:example text'

        >>> # example of list of str for `action_options`
        >>> action_options = ['max_data_age:3600', 'and']

        See Also
        --------
        :data:`pytan.constants.FILTER_MAPS` : valid filter dictionaries for filters
        :data:`pytan.constants.OPTION_MAPS` : valid option dictionaries for options
        :func:`pytan.handler.Handler._deploy_action` : private method with the actual workflow used to create and add the action object
        """
        self._debug_locals(sys._getframe().f_code.co_name, locals())

        pytan.utils.check_for_help(kwargs=kwargs)

        # the human string describing the sensors/filter that user wants
        # to deploy the action against
        action_filters = kwargs.get('action_filters', [])

        # the question options to use on the pre-action question and on the
        # group for the action filters
        action_options = kwargs.get('action_options', [])

        # name of package to deploy with params as {key=value1,key2=value2}
        package = kwargs.get('package', '')

        action_filter_defs = pytan.utils.dehumanize_sensors(action_filters, 'action_filters', True)
        action_option_defs = pytan.utils.dehumanize_question_options(action_options)
        package_def = pytan.utils.dehumanize_package(package)

        clean_keys = ['package_def', 'action_filter_defs', 'action_option_defs']
        clean_kwargs = pytan.utils.clean_kwargs(kwargs=kwargs, keys=clean_keys)

        deploy_result = self._deploy_action(
            action_filter_defs=action_filter_defs,
            action_option_defs=action_option_defs,
            package_def=package_def,
            **clean_kwargs
        )
        return deploy_result

    def approve_saved_action(self, id, **kwargs):
        """Approve a saved action

        Parameters
        ----------
        id : int
            * id of saved action to approve

        Returns
        -------
        saved_action_approve_obj : :class:`taniumpy.object_types.saved_action_approval.SavedActionApproval`
            * The object containing the return from SavedActionApproval
        """
        self._debug_locals(sys._getframe().f_code.co_name, locals())

        clean_keys = ['pytan_help', 'objtype', 'id', 'obj']
        clean_kwargs = pytan.utils.clean_kwargs(kwargs=kwargs, keys=clean_keys)

        h = "Issue a GetObject to find saved action objects"
        saved_action_obj = self.get(objtype='saved_action', id=id, pytan_help=h, **clean_kwargs)[0]

        add_sap_obj = taniumpy.SavedActionApproval()
        add_sap_obj.id = saved_action_obj.id
        add_sap_obj.approved_flag = 1

        # we dont want to re-fetch the object, so use sessions add instead of handlers add
        h = "Issue an AddObject to add a SavedActionApproval"
        sap_obj = self.session.add(obj=add_sap_obj, pytan_help=h, **clean_kwargs)

        m = 'Action approved successfully, ID of saved action : {}'.format
        self.mylog.debug(m(sap_obj.id))

        return sap_obj

    def stop_action(self, id, **kwargs):
        """Stop an action

        Parameters
        ----------
        id : int
            * id of action to stop

        Returns
        -------
        action_stop_obj : :class:`taniumpy.object_types.action_stop.ActionStop`
            The object containing the ID of the action stop job
        """
        self._debug_locals(sys._getframe().f_code.co_name, locals())

        clean_keys = ['pytan_help', 'objtype', 'id', 'obj']
        clean_kwargs = pytan.utils.clean_kwargs(kwargs=kwargs, keys=clean_keys)

        h = "Issue a GetObject to find the action object we want to stop"
        action_obj = self.get(objtype='action', id=id, pytan_help=h, **clean_kwargs)[0]

        add_action_stop_obj = taniumpy.ActionStop()
        add_action_stop_obj.action = action_obj

        h = "Issue an AddObject to add a StopAction"
        action_stop_obj = self.session.add(obj=add_action_stop_obj, pytan_help=h, **clean_kwargs)

        h = "Re-issue a GetObject to ensure the stopped_flag is 1"
        after_action_obj = self.get(objtype='action', id=id, pytan_help=h, **clean_kwargs)[0]

        if after_action_obj.stopped_flag:
            m = 'Action stopped successfully, ID of action stop: {}'.format
            self.mylog.debug(m(action_stop_obj.id))
        else:
            m = (
                "Action not stopped successfully, json of action after issuing StopAction: {}"
            ).format
            raise pytan.exceptions.HandlerError(m(self.export_obj(after_action_obj, 'json')))

        return action_stop_obj

    # Result Data / Result Info
    def get_result_data(self, obj, aggregate=False, shrink=True, **kwargs):
        """Get the result data for a python API object

        This method issues a GetResultData command to the SOAP api for `obj`. GetResultData returns the columns and rows that are currently available for `obj`.

        Parameters
        ----------
        obj : :class:`taniumpy.object_types.base.BaseType`
            * object to get result data for
        aggregate : bool, optional
            * default: False
            * False: get all the data
            * True: get just the aggregate data (row counts of matches)
        shrink : bool, optional
            * default: True
            * True: Shrink the object down to just id/name/hash attributes (for smaller request)
            * False: Use the full object as is

        Returns
        -------
        rd : :class:`taniumpy.object_types.result_set.ResultSet`
            The return of GetResultData for `obj`
        """

        """ note #1 from jwk:
        For Action GetResultData: You have to make a ResultInfo request at least once every 2 minutes. The server gathers the result data by asking a saved question. It won't re-issue the saved question unless you make a GetResultInfo request. When you make a GetResultInfo request, if there is no question that is less than 2 minutes old, the server will automatically reissue a new question instance to make sure fresh data is available.

        note #2 from jwk:
        To get the aggregate data (without computer names), set row_counts_only_flag = 1. To get the computer names, use row_counts_only_flag = 0 (default).
        """
        self._debug_locals(sys._getframe().f_code.co_name, locals())

        if shrink:
            shrunk_obj = pytan.utils.shrink_obj(obj=obj)
        else:
            shrunk_obj = obj

        kwargs['export_flag'] = pytan.utils.get_kwargs_int(key='export_flag', default=0, **kwargs)

        if kwargs['export_flag']:
            grd = self.session.get_result_data_sse
        else:
            grd = self.session.get_result_data

        h = "Issue a GetResultData to get answers for a question"
        kwargs['pytan_help'] = kwargs.get('pytan_help', h)
        kwargs['suppress_object_list'] = kwargs.get('suppress_object_list', 1)

        if aggregate:
            kwargs['row_counts_only_flag'] = 1

        clean_keys = ['obj']
        clean_kwargs = pytan.utils.clean_kwargs(kwargs=kwargs, keys=clean_keys)

        # do a getresultdata
        rd = grd(obj=shrunk_obj, **clean_kwargs)

        return rd

    def get_result_data_sse(self, obj, **kwargs):
        """Get the result data for a python API object using a server side export (sse)

        This method issues a GetResultData command to the SOAP api for `obj` with the option
        `export_flag` set to 1. This will cause the server to process all of the data for a given
        result set and save it as `export_format`. Then the user can use an authenticated GET
        request to get the status of the file via "/export/${export_id}.status". Once the status
        returns "Completed.", the actual report file can be retrieved by an authenticated GET
        request to "/export/${export_id}.gz". This workflow saves a lot of processing time and removes the need to paginate large result sets necessary in normal GetResultData calls.

        *Version support*
            * 6.5.314.4231: initial sse support (csv only)
            * 6.5.314.4300: export_format support (adds xml and cef)
            * 6.5.314.4300: fix core dump if multiple sse done on empty resultset
            * 6.5.314.4300: fix no status file if sse done on empty resultset
            * 6.5.314.4300: fix response if more than two sse done in same second

        Parameters
        ----------
        obj : :class:`taniumpy.object_types.base.BaseType`
            * object to get result data for
        sse_format : str, optional
            * default: 'csv'
            * format to have server create report in, one of: {'csv', 'xml', 'xml_obj', 'cef', 0, 1, 2}
        leading : str, optional
            * default: ''
            * used for sse_format 'cef' only, the string to prepend to each row
        trailing : str, optional
            * default: ''
            * used for sse_format 'cef' only, the string to append to each row

        See Also
        --------
        :data:`pytan.constants.SSE_FORMAT_MAP` : maps `sse_format` to an integer for use by the SOAP API
        :data:`pytan.constants.SSE_RESTRICT_MAP` : maps sse_format integers to supported platform versions
        :data:`pytan.constants.SSE_CRASH_MAP` : maps platform versions that can cause issues in various scenarios

        Returns
        -------
        export_data : either `str` or :class:`taniumpy.object_types.result_set.ResultSet`
            * If sse_format is one of csv, xml, or cef, export_data will be a `str` containing the contents of the ResultSet in said format
            * If sse_format is xml_obj, export_data will be a :class:`taniumpy.object_types.result_set.ResultSet`
        """
        self._debug_locals(sys._getframe().f_code.co_name, locals())

        self._check_sse_version()
        self._check_sse_crash_prevention(obj=obj)

        sse_format = kwargs.get('sse_format', 'csv')
        sse_format_int = self._resolve_sse_format(sse_format=sse_format)

        # add the export_flag = 1 to the kwargs for inclusion in options node
        kwargs['export_flag'] = 1

        # add the export_format to the kwargs for inclusion in options node
        kwargs['export_format'] = sse_format_int

        # add the export_leading_text to the kwargs for inclusion in options node
        leading = kwargs.get('leading', '')
        if leading:
            kwargs['export_leading_text'] = leading

        # add the export_trailing_text to the kwargs for inclusion in options node
        trailing = kwargs.get('trailing', '')
        if trailing:
            kwargs['export_trailing_text'] = trailing

        clean_keys = [
            'obj', 'pytan_help', 'handler', 'export_id', 'leading', 'trailing', 'sse_format',
        ]
        clean_kwargs = pytan.utils.clean_kwargs(kwargs=kwargs, keys=clean_keys)

        h = "Issue a GetResultData to start a Server Side Export and get an export_id"
        export_id = self.get_result_data(obj=obj, pytan_help=h, **clean_kwargs)

        m = "Server Side Export Started, id: '{}'".format
        self.mylog.debug(m(export_id))

        poller = pytan.pollers.SSEPoller(handler=self, export_id=export_id, **clean_kwargs)
        poller_success = poller.run(**clean_kwargs)

        if not poller_success:
            m = (
                "Server Side Export Poller failed while waiting for completion, last status: {}"
            ).format
            sse_status = getattr(poller, 'sse_status', 'Unknown')
            raise pytan.exceptions.ServerSideExportError(m(sse_status))

        export_data = poller.get_sse_data(**clean_kwargs)

        if sse_format.lower() == 'xml_obj':
            export_data = self.xml_to_result_set_obj(x=export_data)

        return export_data

    def xml_to_result_set_obj(self, x, **kwargs):
        """Wraps a Result Set XML from a server side export in the appropriate tags and returns a ResultSet object

        Parameters
        ----------
        x : str
            * str of XML to convert to a ResultSet object

        Returns
        -------
        rs : :class:`taniumpy.object_types.result_set.ResultSet`
            * x converted into a ResultSet object
        """
        self._debug_locals(sys._getframe().f_code.co_name, locals())

        rs_xml = '<result_sets><result_set>{}</result_set></result_sets>'.format
        rs_xml = rs_xml(x)
        rs_tree = pytan.sessions.ET.fromstring(rs_xml)
        rs = taniumpy.ResultSet.fromSOAPElement(rs_tree)
        rs._RAW_XML = rs_xml
        return rs

    def get_result_info(self, obj, shrink=True, **kwargs):
        """Get the result info for a python API object

        This method issues a GetResultInfo command to the SOAP api for `obj`. GetResultInfo returns information about how many servers have passed the `obj`, total number of servers, and so on.

        Parameters
        ----------
        obj : :class:`taniumpy.object_types.base.BaseType`
            * object to get result data for
        shrink : bool, optional
            * default: True
            * True: Shrink the object down to just id/name/hash attributes (for smaller request)
            * False: Use the full object as is

        Returns
        -------
        ri : :class:`taniumpy.object_types.result_info.ResultInfo`
            * The return of GetResultInfo for `obj`
        """
        self._debug_locals(sys._getframe().f_code.co_name, locals())

        if shrink:
            shrunk_obj = pytan.utils.shrink_obj(obj=obj)
        else:
            shrunk_obj = obj

        h = "Issue a GetResultData to get answers for a question"
        kwargs['pytan_help'] = kwargs.get('pytan_help', h)
        kwargs['suppress_object_list'] = kwargs.get('suppress_object_list', 1)

        clean_keys = ['obj']
        clean_kwargs = pytan.utils.clean_kwargs(kwargs=kwargs, keys=clean_keys)

        ri = self.session.get_result_info(obj=shrunk_obj, **clean_kwargs)
        return ri

    # Objects
    def create_from_json(self, objtype, json_file, **kwargs):
        """Creates a new object using the SOAP api from a json file

        Parameters
        ----------
        objtype : str
            * Type of object described in `json_file`
        json_file : str
            * path to JSON file that describes an API object

        Returns
        -------
        ret : :class:`taniumpy.object_types.base.BaseType`
            * TaniumPy object added to Tanium SOAP Server

        See Also
        --------
        :data:`pytan.constants.GET_OBJ_MAP` : maps objtype to supported 'create_json' types
        """
        self._debug_locals(sys._getframe().f_code.co_name, locals())

        obj_map = pytan.utils.get_obj_map(objtype=objtype)

        create_json_ok = obj_map['create_json']

        if not create_json_ok:
            json_createable = ', '.join([
                x for x, y in pytan.constants.GET_OBJ_MAP.items() if y['create_json']
            ])
            m = "{} is not a json createable object! Supported objects: {}".format
            raise pytan.exceptions.HandlerError(m(objtype, json_createable))

        add_obj = pytan.utils.load_taniumpy_from_json(json_file=json_file)

        if getattr(add_obj, '_list_properties', ''):
            obj_list = [x for x in add_obj]
        else:
            obj_list = [add_obj]

        del_keys = ['id', 'hash']
        [
            setattr(y, x, None)
            for y in obj_list for x in del_keys
            if hasattr(y, x)
        ]

        if obj_map.get('allfix'):
            all_type = obj_map['allfix']
        else:
            all_type = obj_map['all']

        ret = pytan.utils.get_taniumpy_obj(obj_map=all_type)()

        h = "Issue an AddObject to add an object"
        kwargs['pytan_help'] = kwargs.get('pytan_help', h)

        clean_keys = ['obj']
        clean_kwargs = pytan.utils.clean_kwargs(kwargs=kwargs, keys=clean_keys)

        for x in obj_list:
            try:
                list_obj = self._add(obj=x, **clean_kwargs)
            except Exception as e:
                m = (
                    "Failure while importing {}: {}\nJSON Dump of object: {}"
                ).format
                raise pytan.exceptions.HandlerError(m(x, e, x.to_json(x)))

            m = "New {} (ID: {}) created successfully!".format
            self.mylog.info(m(list_obj, getattr(list_obj, 'id', 'Unknown')))

            ret.append(list_obj)
        return ret

    def run_plugin(self, obj, **kwargs):
        """Wrapper around :func:`pytan.session.Session.run_plugin` to run the plugin and zip up the SQL results into a python dictionary

        Parameters
        ----------
        obj : :class:`taniumpy.object_types.plugin.Plugin`
            * Plugin object to run

        Returns
        -------
        plugin_result, sql_zipped : tuple
            * plugin_result will be the taniumpy object representation of the SOAP response from Tanium server
            * sql_zipped will be a dict with the SQL results embedded in the SOAP response
        """
        self._debug_locals(sys._getframe().f_code.co_name, locals())

        # run the plugin
        h = "Issue a RunPlugin run a plugin and get results back"
        kwargs['pytan_help'] = kwargs.get('pytan_help', h)

        clean_keys = ['obj', 'p']
        clean_kwargs = pytan.utils.clean_kwargs(kwargs=kwargs, keys=clean_keys)

        plugin_result = self.session.run_plugin(obj=obj, **clean_kwargs)

        # zip up the sql results into a list of python dictionaries
        sql_zipped = pytan.utils.plugin_zip(p=plugin_result)

        # return the plugin result and the python dictionary of results
        return plugin_result, sql_zipped

    def create_dashboard(self, name, text='', group='', public_flag=True, **kwargs):
        """Calls :func:`pytan.handler.Handler.run_plugin` to run the CreateDashboard plugin and parse the response

        Parameters
        ----------
        name : str
            * name of dashboard to create
        text : str, optional
            * default: ''
            * text for this dashboard
        group : str, optional
            * default: ''
            * group name for this dashboard
        public_flag : bool, optional
            * default: True
            * True: make this dashboard public
            * False: do not make this dashboard public

        Returns
        -------
        plugin_result, sql_zipped : tuple
            * plugin_result will be the taniumpy object representation of the SOAP response from Tanium server
            * sql_zipped will be a dict with the SQL results embedded in the SOAP response
        """
        self._debug_locals(sys._getframe().f_code.co_name, locals())

        clean_kwargs = pytan.utils.clean_kwargs(kwargs=kwargs)

        # get the ID for the group if a name was passed in
        if group:
            h = "Issue a GetObject to find the ID of a group name"
            group_id = self.get(objtype='group', name=group, pytan_help=h, **clean_kwargs)[0].id
        else:
            group_id = 0

        if public_flag:
            public_flag = 1
        else:
            public_flag = 0

        # create the plugin parent
        plugin = taniumpy.Plugin()
        plugin.name = 'CreateDashboard'
        plugin.bundle = 'Dashboards'

        # create the plugin arguments
        plugin.arguments = taniumpy.PluginArgumentList()

        arg1 = taniumpy.PluginArgument()
        arg1.name = 'dash_name'
        arg1.type = 'String'
        arg1.value = name
        plugin.arguments.append(arg1)

        arg2 = taniumpy.PluginArgument()
        arg2.name = 'dash_text'
        arg2.type = 'String'
        arg2.value = text
        plugin.arguments.append(arg2)

        arg3 = taniumpy.PluginArgument()
        arg3.name = 'group_id'
        arg3.type = 'Number'
        arg3.value = group_id
        plugin.arguments.append(arg3)

        arg4 = taniumpy.PluginArgument()
        arg4.name = 'public_flag'
        arg4.type = 'Number'
        arg4.value = public_flag
        plugin.arguments.append(arg4)

        arg5 = taniumpy.PluginArgument()
        arg5.name = 'sqid_xml'
        arg5.type = 'String'
        arg5.value = ''
        plugin.arguments.append(arg5)

        # run the plugin
        h = "Issue a RunPlugin for the CreateDashboard plugin to create a dashboard"
        plugin_result, sql_zipped = self.run_plugin(obj=plugin, pytan_help=h, **clean_kwargs)

        # return the plugin result and the python dictionary of results
        return plugin_result, sql_zipped

    def delete_dashboard(self, name, **kwargs):
        """Calls :func:`pytan.handler.Handler.run_plugin` to run the DeleteDashboards plugin and parse the response

        Parameters
        ----------
        name : str
            * name of dashboard to delete

        Returns
        -------
        plugin_result, sql_zipped : tuple
            * plugin_result will be the taniumpy object representation of the SOAP response from Tanium server
            * sql_zipped will be a dict with the SQL results embedded in the SOAP response
        """
        self._debug_locals(sys._getframe().f_code.co_name, locals())

        clean_keys = ['obj', 'name', 'pytan_help']
        clean_kwargs = pytan.utils.clean_kwargs(kwargs=kwargs, keys=clean_keys)

        dashboards_to_del = self.get_dashboards(name=name, **clean_kwargs)[1]

        # create the plugin parent
        plugin = taniumpy.Plugin()
        plugin.name = 'DeleteDashboards'
        plugin.bundle = 'Dashboards'

        # create the plugin arguments
        plugin.arguments = taniumpy.PluginArgumentList()

        arg1 = taniumpy.PluginArgument()
        arg1.name = 'dashboard_ids'
        arg1.type = 'Number_Set'
        arg1.value = ','.join([x['id'] for x in dashboards_to_del])
        plugin.arguments.append(arg1)

        # run the plugin
        h = "Issue a RunPlugin for the DeleteDashboards plugin to delete a dashboard"
        plugin_result, sql_zipped = self.run_plugin(obj=plugin, pytan_help=h, **clean_kwargs)

        # return the plugin result and the python dictionary of results
        return plugin_result, sql_zipped

    def get_dashboards(self, name='', **kwargs):
        """Calls :func:`pytan.handler.Handler.run_plugin` to run the GetDashboards plugin and parse the response

        Parameters
        ----------
        name : str, optional
            * default: ''
            * name of dashboard to get, if empty will return all dashboards

        Returns
        -------
        plugin_result, sql_zipped : tuple
            * plugin_result will be the taniumpy object representation of the SOAP response from Tanium server
            * sql_zipped will be a dict with the SQL results embedded in the SOAP response
        """
        self._debug_locals(sys._getframe().f_code.co_name, locals())

        clean_keys = ['obj', 'name', 'pytan_help']
        clean_kwargs = pytan.utils.clean_kwargs(kwargs=kwargs, keys=clean_keys)

        # create the plugin parent
        plugin = taniumpy.Plugin()
        plugin.name = 'GetDashboards'
        plugin.bundle = 'Dashboards'

        # run the plugin
        h = "Issue a RunPlugin for the GetDashboards plugin to get all dashboards"
        plugin_result, sql_zipped = self.run_plugin(obj=plugin, pytan_help=h, **clean_kwargs)

        # if name specified, filter the list of dicts for matching name
        if name:
            sql_zipped = [x for x in sql_zipped if x['name'] == name]
            if not sql_zipped:
                m = "No dashboards found that match name: {!r}".format
                raise pytan.exceptions.NotFoundError(m(name))

        # return the plugin result and the python dictionary of results
        return plugin_result, sql_zipped

    def create_sensor(self, **kwargs):
        """Create a sensor object

        Warnings
        --------
        Not currently supported, too complicated to add.
        Use :func:`create_from_json` instead for this object type!

        Raises
        ------
        pytan.exceptions.HandlerError : :exc:`pytan.utils.pytan.exceptions.HandlerError`
        """
        self._debug_locals(sys._getframe().f_code.co_name, locals())

        m = (
            "Sensor creation not supported via PyTan as of yet, too complex\n"
            "Use create_sensor_from_json() instead!"
        )
        raise pytan.exceptions.HandlerError(m)

    def create_package(self, name, command, display_name='', file_urls=[],
                       command_timeout_seconds=600, expire_seconds=600, parameters_json_file='',
                       verify_filters=[], verify_filter_options=[], verify_expire_seconds=600,
                       **kwargs):
        """Create a package object

        Parameters
        ----------
        name : str
            * name of package to create
        command : str
            * command to execute
        display_name : str, optional
            * display name of package
        file_urls : list of strings, optional
            * default: []
            * URL of file to add to package
            * can optionally define download_seconds by using SECONDS::URL
            * can optionally define file name by using FILENAME||URL
            * can combine optionals by using SECONDS::FILENAME||URL
            * FILENAME will be extracted from basename of URL if not provided
        command_timeout_seconds : int, optional
            * default: 600
            * timeout for command execution in seconds
        parameters_json_file : str, optional
            * default: ''
            * path to json file describing parameters for package
        expire_seconds : int, optional
            * default: 600
            * timeout for action expiry in seconds
        verify_filters : str or list of str, optional
            * default: []
            * each string must describe a filter to be used to verify the package
        verify_filter_options : str or list of str, optional
            * default: []
            * each string must describe an option for `verify_filters`
        verify_expire_seconds : int, optional
            * default: 600
            * timeout for verify action expiry in seconds
        filters_help : bool, optional
            * default: False
            * False: do not print the help string for filters
            * True: print the help string for filters and exit
        options_help : bool, optional
            * default: False
            * False: do not print the help string for options
            * True: print the help string for options and exit
        metadata: list of list of strs, optional
            * default: []
            * each list must be a 2 item list:
            * list item 1 property name
            * list item 2 property value

        Returns
        -------
        package_obj : :class:`taniumpy.object_types.package_spec.PackageSpec`
            * TaniumPy object added to Tanium SOAP Server

        See Also
        --------
        :data:`pytan.constants.FILTER_MAPS` : valid filters for verify_filters
        :data:`pytan.constants.OPTION_MAPS` : valid options for verify_filter_options
        """
        self._debug_locals(sys._getframe().f_code.co_name, locals())

        pytan.utils.check_for_help(kwargs=kwargs)

        clean_keys = ['obj', 'pytan_help', 'defs']
        clean_kwargs = pytan.utils.clean_kwargs(kwargs=kwargs, keys=clean_keys)

        metadata = kwargs.get('metadata', [])
        metadatalist_obj = pytan.utils.build_metadatalist_obj(properties=metadata)

        # bare minimum arguments for new package: name, command
        add_package_obj = taniumpy.PackageSpec()
        add_package_obj.name = name
        if display_name:
            add_package_obj.display_name = display_name
        add_package_obj.command = command
        add_package_obj.command_timeout = command_timeout_seconds
        add_package_obj.expire_seconds = expire_seconds
        add_package_obj.metadata = metadatalist_obj

        # VERIFY FILTERS
        if verify_filters:
            verify_filter_defs = pytan.utils.dehumanize_question_filters(
                question_filters=verify_filters
            )
            verify_option_defs = pytan.utils.dehumanize_question_options(
                question_options=verify_filter_options
            )
            verify_filter_defs = self._get_sensor_defs(defs=verify_filter_defs, **clean_kwargs)
            add_verify_group = pytan.utils.build_group_obj(
                q_filter_defs=verify_filter_defs, q_option_defs=verify_option_defs
            )
            h = "Issue an AddObject to add a Group object for this package"
            verify_group = self._add(obj=add_verify_group, pytan_help=h, **clean_kwargs)

            # this didn't work:
            # add_package_obj.verify_group = verify_group
            add_package_obj.verify_group_id = verify_group.id
            add_package_obj.verify_expire_seconds = verify_expire_seconds

        # PARAMETERS
        if parameters_json_file:
            add_package_obj.parameter_definition = pytan.utils.load_param_json_file(
                parameters_json_file=parameters_json_file
            )

        # FILES
        if file_urls:
            filelist_obj = taniumpy.PackageFileList()
            for file_url in file_urls:
                # if :: is in file_url, split on it and use 0 as
                # download_seconds
                if '::' in file_url:
                    download_seconds, file_url = file_url.split('::')
                else:
                    download_seconds = 0
                # if || is in file_url, split on it and use 0 as file name
                # else wise get file name from basename of URL
                if '||' in file_url:
                    filename, file_url = file_url.split('||')
                else:
                    filename = os.path.basename(file_url)
                file_obj = taniumpy.PackageFile()
                file_obj.name = filename
                file_obj.source = file_url
                file_obj.download_seconds = download_seconds
                filelist_obj.append(file_obj)
            add_package_obj.files = filelist_obj

        h = "Issue an AddObject to add a Group object for this package"
        package_obj = self._add(obj=add_package_obj, pytan_help=h, **clean_kwargs)

        m = "New package {!r} created with ID {!r}, command: {!r}".format
        self.mylog.info(m(package_obj.name, package_obj.id, package_obj.command))
        return package_obj

    def create_group(self, groupname, filters=[], filter_options=[], **kwargs):
        """Create a group object

        Parameters
        ----------
        groupname : str
            * name of group to create
        filters : str or list of str, optional
            * default: []
            * each string must describe a filter
        filter_options : str or list of str, optional
            * default: []
            * each string must describe an option for `filters`
        filters_help : bool, optional
            * default: False
            * False: do not print the help string for filters
            * True: print the help string for filters and exit
        options_help : bool, optional
            * default: False
            * False: do not print the help string for options
            * True: print the help string for options and exit

        Returns
        -------
        group_obj : :class:`taniumpy.object_types.group.Group`
            * TaniumPy object added to Tanium SOAP Server

        See Also
        --------
        :data:`pytan.constants.FILTER_MAPS` : valid filters for filters
        :data:`pytan.constants.OPTION_MAPS` : valid options for filter_options
        """
        self._debug_locals(sys._getframe().f_code.co_name, locals())

        pytan.utils.check_for_help(kwargs=kwargs)
        clean_kwargs = pytan.utils.clean_kwargs(kwargs=kwargs)

        filter_defs = pytan.utils.dehumanize_question_filters(question_filters=filters)
        option_defs = pytan.utils.dehumanize_question_options(question_options=filter_options)

        h = (
            "Issue a GetObject to get the full object of specified sensors for inclusion in a "
            "group"
        )
        filter_defs = self._get_sensor_defs(defs=filter_defs, pytan_help=h, **clean_kwargs)

        add_group_obj = pytan.utils.build_group_obj(
            q_filter_defs=filter_defs, q_option_defs=option_defs,
        )
        add_group_obj.name = groupname

        h = "Issue an AddObject to add a Group object"
        group_obj = self._add(obj=add_group_obj, pytan_help=h, **clean_kwargs)

        m = "New group {!r} created with ID {!r}, filter text: {!r}".format
        self.mylog.info(m(group_obj.name, group_obj.id, group_obj.text))
        return group_obj

    def create_user(self, name, rolename=[], roleid=[], properties=[], group='', **kwargs):
        """Create a user object

        Parameters
        ----------
        name : str
            * name of user to create
        rolename : str or list of str, optional
            * default: []
            * name(s) of roles to add to user
        roleid : int or list of int, optional
            * default: []
            * id(s) of roles to add to user
        properties: list of list of strs, optional
            * default: []
            * each list must be a 2 item list:
            * list item 1 property name
            * list item 2 property value
        group: str
            * default: ''
            * name of group to assign to user

        Returns
        -------
        user_obj : :class:`taniumpy.object_types.user.User`
            * TaniumPy object added to Tanium SOAP Server
        """
        self._debug_locals(sys._getframe().f_code.co_name, locals())

        clean_kwargs = pytan.utils.clean_kwargs(kwargs=kwargs)

        # get the ID for the group if a name was passed in
        if group:
            h = "Issue a GetObject to find the ID of a group name"
            group_id = self.get(objtype='group', name=group, pytan_help=h, **clean_kwargs)[0].id
        else:
            group_id = None

        if roleid or rolename:
            h = "Issue a GetObject to find a user role"
            rolelist_obj = self.get(objtype='userrole', id=roleid, name=rolename, pytan_help=h, **clean_kwargs)
        else:
            rolelist_obj = taniumpy.RoleList()

        metadatalist_obj = pytan.utils.build_metadatalist_obj(
            properties=properties, nameprefix='TConsole.User.Property',
        )
        add_user_obj = taniumpy.User()
        add_user_obj.name = name
        add_user_obj.roles = rolelist_obj
        add_user_obj.metadata = metadatalist_obj
        add_user_obj.group_id = group_id

        h = "Issue an AddObject to add a User object"
        user_obj = self._add(obj=add_user_obj, pytan_help=h, **clean_kwargs)

        m = "New user {!r} created with ID {!r}, roles: {!r}".format
        self.mylog.info(m(
            user_obj.name, user_obj.id, [x.name for x in rolelist_obj]
        ))
        return user_obj

    def create_whitelisted_url(self, url, regex=False, download_seconds=86400, properties=[],
                               **kwargs):
        """Create a whitelisted url object

        Parameters
        ----------
        url : str
            * text of new url
        regex : bool, optional
            * default: False
            * False: `url` is not a regex pattern
            * True: `url` is a regex pattern
        download_seconds : int, optional
            * default: 86400
            * how often to re-download `url`
        properties: list of list of strs, optional
            * default: []
            * each list must be a 2 item list:
            * list item 1 property name
            * list item 2 property value

        Returns
        -------
        url_obj : :class:`taniumpy.object_types.white_listed_url.WhiteListedUrl`
            * TaniumPy object added to Tanium SOAP Server
        """
        self._debug_locals(sys._getframe().f_code.co_name, locals())

        if regex:
            url = 'regex:' + url

        metadatalist_obj = pytan.utils.build_metadatalist_obj(
            properties=properties, nameprefix='TConsole.WhitelistedURL',
        )

        add_url_obj = taniumpy.WhiteListedUrl()
        add_url_obj.url_regex = url
        add_url_obj.download_seconds = download_seconds
        add_url_obj.metadata = metadatalist_obj

        clean_kwargs = pytan.utils.clean_kwargs(kwargs=kwargs)

        h = "Issue an AddObject to add a WhitelistedURL object"
        url_obj = self._add(obj=add_url_obj, pytan_help=h, **clean_kwargs)

        m = "New Whitelisted URL {!r} created with ID {!r}".format
        self.mylog.info(m(url_obj.url_regex, url_obj.id))
        return url_obj

    def delete(self, objtype, **kwargs):
        """Delete an object type

        Parameters
        ----------
        objtype : string
            * type of object to delete
        id/name/hash : int or string, list of int or string
            * search attributes of object to delete, must supply at least one valid search attr

        Returns
        -------
        ret : dict
            * dict containing deploy action object and results from deploy action

        See Also
        --------
        :data:`pytan.constants.GET_OBJ_MAP` : maps objtype to supported 'search' keys
        """
        self._debug_locals(sys._getframe().f_code.co_name, locals())

        obj_map = pytan.utils.get_obj_map(objtype=objtype)

        delete_ok = obj_map['delete']

        clean_kwargs = pytan.utils.clean_kwargs(kwargs=kwargs)

        if not delete_ok:
            deletable = ', '.join([
                x for x, y in pytan.constants.GET_OBJ_MAP.items() if y['delete']
            ])
            m = "{} is not a deletable object! Deletable objects: {}".format
            raise pytan.exceptions.HandlerError(m(objtype, deletable))

        h = "Issue a GetObject to find the object to be deleted"
        objs_to_del = self.get(objtype=objtype, pytan_help=h, **clean_kwargs)

        deleted_objects = []
        for obj_to_del in objs_to_del:
            h = "Issue a DeleteObject to delete an object"
            del_obj = self.session.delete(obj=obj_to_del, pytan_help=h, **clean_kwargs)

            deleted_objects.append(del_obj)

            m = "Deleted {!r}".format
            self.mylog.info(m(str(del_obj)))

        return deleted_objects

    def export_obj(self, obj, export_format='csv', **kwargs):
        """Exports a python API object to a given export format

        Parameters
        ----------
        obj : :class:`taniumpy.object_types.base.BaseType` or :class:`taniumpy.object_types.result_set.ResultSet`
            * TaniumPy object to export
        export_format : str, optional
            * default: 'csv'
            * the format to export `obj` to, one of: {'csv', 'xml', 'json'}
        header_sort : list of str, bool, optional
            * default: True
            * for `export_format` csv and `obj` types :class:`taniumpy.object_types.base.BaseType` or :class:`taniumpy.object_types.result_set.ResultSet`
            * True: sort the headers automatically
            * False: do not sort the headers at all
            * list of str: sort the headers returned by priority based on provided list
        header_add_sensor : bool, optional
            * default: False
            * for `export_format` csv and `obj` type :class:`taniumpy.object_types.result_set.ResultSet`
            * False: do not prefix the headers with the associated sensor name for each column
            * True: prefix the headers with the associated sensor name for each column
        header_add_type : bool, optional
            * default: False
            * for `export_format` csv and `obj` type :class:`taniumpy.object_types.result_set.ResultSet`
            * False: do not postfix the headers with the result type for each column
            * True: postfix the headers with the result type for each column
        expand_grouped_columns : bool, optional
            * default: False
            * for `export_format` csv and `obj` type :class:`taniumpy.object_types.result_set.ResultSet`
            * False: do not expand multiline row entries into their own rows
            * True: expand multiline row entries into their own rows
        explode_json_string_values : bool, optional
            * default: False
            * for `export_format` json or csv and `obj` type :class:`taniumpy.object_types.base.BaseType`
            * False: do not explode JSON strings in object attributes into their own object attributes
            * True: explode JSON strings in object attributes into their own object attributes
        minimal : bool, optional
            * default: False
            * for `export_format` xml and `obj` type :class:`taniumpy.object_types.base.BaseType`
            * False: include empty attributes in XML output
            * True: do not include empty attributes in XML output

        Returns
        -------
        result : str
            * the contents of exporting `export_format`

        Notes
        -----
        When performing a CSV export and importing that CSV into excel, keep in mind that Excel has a per cell character limit of 32,000. Any cell larger than that will be broken up into a whole new row, which can wreak havoc with data in Excel.

        See Also
        --------
        :data:`pytan.constants.EXPORT_MAPS` : maps the type `obj` to `export_format` and the optional args supported for each
        """
        self._debug_locals(sys._getframe().f_code.co_name, locals())

        objtype = type(obj)
        try:
            objclassname = objtype.__name__
        except:
            objclassname = 'Unknown'

        # see if supplied obj is a supported object type
        type_match = [
            x for x in pytan.constants.EXPORT_MAPS if isinstance(obj, getattr(taniumpy, x))
        ]

        if not type_match:
            err = (
                "{} not a supported object to export, must be one of: {}"
            ).format

            # build a list of supported object types
            supp_types = ', '.join(pytan.constants.EXPORT_MAPS.keys())
            raise pytan.exceptions.HandlerError(err(objtype, supp_types))

        # get the export formats for this obj type
        export_formats = pytan.constants.EXPORT_MAPS.get(type_match[0], '')

        if export_format not in export_formats:
            err = (
                "{!r} not a supported export format for {}, must be one of: {}"
            ).format(export_format, objclassname, ', '.join(export_formats))
            raise pytan.exceptions.HandlerError(err)

        # perform validation on optional kwargs, if they exist
        opt_keys = export_formats.get(export_format, [])

        for opt_key in opt_keys:
            check_args = dict(opt_key.items() + {'d': kwargs}.items())
            pytan.utils.check_dictkey(**check_args)

        # filter out the kwargs that are specific to this obj type and format type
        format_kwargs = {
            k: v for k, v in kwargs.iteritems()
            if k in [a['key'] for a in opt_keys]
        }

        # run the handler that is specific to this objtype, if it exists
        class_method_str = '_export_class_' + type_match[0]
        class_handler = getattr(self, class_method_str, '')

        if class_handler:
            result = class_handler(obj=obj, export_format=export_format, **format_kwargs)
        else:
            err = "{!r} not supported by Handler!".format
            raise pytan.exceptions.HandlerError(err(objclassname))

        return result

    def create_report_file(self, contents, report_file=None, **kwargs):
        """Exports a python API object to a file

        Parameters
        ----------
        contents : str
            * contents to write to `report_file`
        report_file : str, optional
            * filename to save report as
        report_dir : str, optional
            * default: None
            * directory to save report in, will use current working directory if not supplied
        prefix : str, optional
            * default: ''
            * prefix to add to `report_file`
        postfix : str, optional
            * default: ''
            * postfix to add to `report_file`

        Returns
        -------
        report_path : str
            * the full path to the file created with `contents`
        """
        self._debug_locals(sys._getframe().f_code.co_name, locals())

        if report_file is None:
            report_file = 'pytan_report_{}.txt'.format(pytan.utils.get_now())

        # try to get report_dir from the report_file
        report_dir = os.path.dirname(report_file)

        # try to get report_dir from kwargs
        if not report_dir:
            report_dir = kwargs.get('report_dir', None)

        # just use current working dir
        if not report_dir:
            report_dir = os.getcwd()

        # make report_dir if it doesnt exist
        if not os.path.isdir(report_dir):
            os.makedirs(report_dir)

        # remove any path from report_file
        report_file = os.path.basename(report_file)

        # if prefix/postfix, add to report_file
        prefix = kwargs.get('prefix', '')
        postfix = kwargs.get('postfix', '')
        report_file, report_ext = os.path.splitext(report_file)
        report_file = '{}{}{}{}'.format(prefix, report_file, postfix, report_ext)

        # join the report_dir and report_file to come up with report_path
        report_path = os.path.join(report_dir, report_file)

        with open(report_path, 'wb') as fd:
            fd.write(contents)

        m = "Report file {!r} written with {} bytes".format
        self.mylog.info(m(report_path, len(contents)))
        return report_path

    def export_to_report_file(self, obj, export_format='csv', **kwargs):
        """Exports a python API object to a file

        Parameters
        ----------
        obj : :class:`taniumpy.object_types.base.BaseType` or :class:`taniumpy.object_types.result_set.ResultSet`
            * TaniumPy object to export
        export_format : str, optional
            * default: 'csv'
            * the format to export `obj` to, one of: {'csv', 'xml', 'json'}
        header_sort : list of str, bool, optional
            * default: True
            * for `export_format` csv and `obj` types :class:`taniumpy.object_types.base.BaseType` or :class:`taniumpy.object_types.result_set.ResultSet`
            * True: sort the headers automatically
            * False: do not sort the headers at all
            * list of str: sort the headers returned by priority based on provided list
        header_add_sensor : bool, optional
            * default: False
            * for `export_format` csv and `obj` type :class:`taniumpy.object_types.result_set.ResultSet`
            * False: do not prefix the headers with the associated sensor name for each column
            * True: prefix the headers with the associated sensor name for each column
        header_add_type : bool, optional
            * default: False
            * for `export_format` csv and `obj` type :class:`taniumpy.object_types.result_set.ResultSet`
            * False: do not postfix the headers with the result type for each column
            * True: postfix the headers with the result type for each column
        expand_grouped_columns : bool, optional
            * default: False
            * for `export_format` csv and `obj` type :class:`taniumpy.object_types.result_set.ResultSet`
            * False: do not expand multiline row entries into their own rows
            * True: expand multiline row entries into their own rows
        explode_json_string_values : bool, optional
            * default: False
            * for `export_format` json or csv and `obj` type :class:`taniumpy.object_types.base.BaseType`
            * False: do not explode JSON strings in object attributes into their own object attributes
            * True: explode JSON strings in object attributes into their own object attributes
        minimal : bool, optional
            * default: False
            * for `export_format` xml and `obj` type :class:`taniumpy.object_types.base.BaseType`
            * False: include empty attributes in XML output
            * True: do not include empty attributes in XML output
        report_file: str, optional
            * default: None
            * filename to save report as, will be automatically generated if not supplied
        report_dir: str, optional
            * default: None
            * directory to save report in, will use current working directory if not supplied
        prefix: str, optional
            * default: ''
            * prefix to add to `report_file`
        postfix: str, optional
            * default: ''
            * postfix to add to `report_file`

        Returns
        -------
        report_path, result : tuple
            * report_path : str, the full path to the file created with contents of `result`
            * result : str, the contents written to report_path

        See Also
        --------
        :func:`pytan.handler.Handler.export_obj` : method that performs the actual work to do the exporting
        :func:`pytan.handler.Handler.create_report_file` : method that performs the actual work to write the report file

        Notes
        -----
        When performing a CSV export and importing that CSV into excel, keep in mind that Excel has a per cell character limit of 32,000. Any cell larger than that will be broken up into a whole new row, which can wreak havoc with data in Excel.
        """
        self._debug_locals(sys._getframe().f_code.co_name, locals())

        report_file = kwargs.get('report_file', None)

        if not report_file:
            report_file = "{}_{}.{}".format(
                type(obj).__name__, pytan.utils.get_now(), export_format,
            )
            m = "No report file name supplied, generated name: {!r}".format
            self.mylog.debug(m(report_file))

        clean_keys = ['obj', 'export_format', 'contents', 'report_file']
        clean_kwargs = pytan.utils.clean_kwargs(kwargs=kwargs, keys=clean_keys)

        # get the results of exporting the object
        contents = self.export_obj(obj=obj, export_format=export_format, **clean_kwargs)
        report_path = self.create_report_file(
            report_file=report_file, contents=contents, **clean_kwargs
        )
        return report_path, contents

    def get(self, objtype, **kwargs):
        """Get an object type

        Parameters
        ----------
        objtype : string
            * type of object to get
        id/name/hash : int or string, list of int or string
            * search attributes of object to get, must supply at least one valid search attr

        Returns
        -------
        obj_list : :class:`taniumpy.object_types.base.BaseType`
            * The object list of items found for `objtype`

        See Also
        --------
        :data:`pytan.constants.GET_OBJ_MAP` : maps objtype to supported 'search' keys
        :func:`pytan.handler.Handler._get_multi` : private method used to get multiple items
        :func:`pytan.handler.Handler._get_single` : private method used to get singular items
        """
        self._debug_locals(sys._getframe().f_code.co_name, locals())

        h = "Issue a GetObject to find an object"
        kwargs['pytan_help'] = kwargs.get('pytan_help', h)

        clean_keys = ['obj', 'objtype', 'obj_map']
        clean_kwargs = pytan.utils.clean_kwargs(kwargs=kwargs, keys=clean_keys)

        err_keys = ['pytan_help']
        err_args = pytan.utils.clean_kwargs(kwargs=kwargs, keys=err_keys)

        obj_map = pytan.utils.get_obj_map(objtype=objtype)

        manual_search = obj_map['manual']
        api_attrs = obj_map['search']

        api_kwattrs = [kwargs.get(x, '') for x in api_attrs]

        # if the api doesn't support filtering for this object,
        # or if the user didn't supply any api_kwattrs and manual_search
        # is true, get all objects of this type and manually filter
        if not api_attrs or (not any(api_kwattrs) and manual_search):
            all_objs = self.get_all(objtype=objtype, **clean_kwargs)

            return_objs = getattr(taniumpy, all_objs.__class__.__name__)()

            for k, v in kwargs.iteritems():
                if not v:
                    continue
                if not hasattr(all_objs[0], k):
                    continue
                if not pytan.utils.is_list(v):
                    v = [v]
                for aobj in all_objs:
                    aobj_val = getattr(aobj, k)
                    aobj_val_str = str(aobj_val)
                    if aobj_val not in v and aobj_val_str not in v:
                        continue
                    return_objs.append(aobj)

            if not return_objs:
                err = "No results found searching for {} with {}!!".format
                raise pytan.exceptions.HandlerError(err(objtype, err_args))

            return return_objs

        # if api supports filtering for this object,
        # but no filters supplied in kwargs, raise
        if not any(api_kwattrs):
            err = "Getting a {} requires at least one filter: {}".format
            raise pytan.exceptions.HandlerError(err(objtype, api_attrs))

        # if there is a multi in obj_map, that means we can pass a list
        # type to the taniumpy. the list will have an entry for each api_kw
        if obj_map['multi']:
            return self._get_multi(obj_map=obj_map, **clean_kwargs)

        # if there is a single in obj_map but not multi, that means
        # we have to find each object individually
        elif obj_map['single']:
            return self._get_single(obj_map=obj_map, **clean_kwargs)

        err = "No single or multi search defined for {}".format
        raise pytan.exceptions.HandlerError(err(objtype))

    def get_all(self, objtype, **kwargs):
        """Get all objects of a type

        Parameters
        ----------
        objtype : string
            * type of object to get

        Returns
        -------
        obj_list : :class:`taniumpy.object_types.base.BaseType`
            * The object list of items found for `objtype`

        See Also
        --------
        :data:`pytan.constants.GET_OBJ_MAP` : maps objtype to supported 'search' keys
        :func:`pytan.handler.Handler._find` : private method used to find items
        """
        self._debug_locals(sys._getframe().f_code.co_name, locals())

        h = "Issue a GetObject to find an object"
        kwargs['pytan_help'] = kwargs.get('pytan_help', h)

        clean_keys = ['obj', 'objtype', 'obj_map']
        clean_kwargs = pytan.utils.clean_kwargs(kwargs=kwargs, keys=clean_keys)

        obj_map = pytan.utils.get_obj_map(objtype=objtype)

        all_type = obj_map['all']
        api_obj_all = pytan.utils.get_taniumpy_obj(obj_map=all_type)()

        found = self._find(obj=api_obj_all, **clean_kwargs)
        return found

    # BEGIN PRIVATE METHODS
    def _add(self, obj, **kwargs):
        """Wrapper for interfacing with :func:`taniumpy.session.Session.add`

        Parameters
        ----------
        obj : :class:`taniumpy.object_types.base.BaseType`
            * object to add

        Returns
        -------
        added_obj : :class:`taniumpy.object_types.base.BaseType`
           * full object that was added
        """
        self._debug_locals(sys._getframe().f_code.co_name, locals())

        try:
            search_str = '; '.join([str(x) for x in obj])
        except:
            search_str = obj

        self.mylog.debug("Adding object {}".format(search_str))

        kwargs['suppress_object_list'] = kwargs.get('suppress_object_list', 1)

        clean_keys = ['obj', 'objtype', 'obj_map']
        clean_kwargs = pytan.utils.clean_kwargs(kwargs=kwargs, keys=clean_keys)

        h = "Issue an AddObject to add an object"
        clean_kwargs['pytan_help'] = clean_kwargs.get('pytan_help', h)

        try:
            added_obj = self.session.add(obj=obj, **clean_kwargs)
        except Exception as e:
            err = "Error while trying to add object '{}': {}!!".format
            raise pytan.exceptions.HandlerError(err(search_str, e))

        h = "Issue a GetObject on the recently added object in order to get the full object"
        clean_kwargs['pytan_help'] = h

        try:
            added_obj = self._find(obj=added_obj, **clean_kwargs)
        except Exception as e:
            self.mylog.error(e)
            err = "Error while trying to find recently added object {}!!".format
            raise pytan.exceptions.HandlerError(err(search_str))

        self.mylog.debug("Added object {}".format(added_obj))
        return added_obj

    def _find(self, obj, **kwargs):
        """Wrapper for interfacing with :func:`taniumpy.session.Session.find`

        Parameters
        ----------
        obj : :class:`taniumpy.object_types.base.BaseType`
            * object to find

        Returns
        -------
        found : :class:`taniumpy.object_types.base.BaseType`
           * full object that was found
        """
        self._debug_locals(sys._getframe().f_code.co_name, locals())

        try:
            search_str = '; '.join([str(x) for x in obj])
        except:
            search_str = obj

        self.mylog.debug("Searching for {}".format(search_str))

        kwargs['suppress_object_list'] = kwargs.get('suppress_object_list', 1)

        clean_keys = ['obj', 'objtype', 'obj_map']
        clean_kwargs = pytan.utils.clean_kwargs(kwargs=kwargs, keys=clean_keys)

        h = "Issue a GetObject to find an object"
        clean_kwargs['pytan_help'] = clean_kwargs.get('pytan_help', h)

        try:
            found = self.session.find(obj=obj, **clean_kwargs)
        except Exception as e:
            self.mylog.debug(e)
            err = "No results found searching for {} (error: {})!!".format
            raise pytan.exceptions.HandlerError(err(search_str, e))

        if pytan.utils.empty_obj(found):
            err = "No results found searching for {}!!".format
            raise pytan.exceptions.HandlerError(err(search_str))

        self.mylog.debug("Found {}".format(found))
        return found

    def _get_multi(self, obj_map, **kwargs):
        """Find multiple item wrapper using :func:`_find`

        Parameters
        ----------
        obj_map : dict
            * dict containing the map for a given object type

        Returns
        -------
        found : :class:`taniumpy.object_types.base.BaseType`
           * full object that was found
        """
        self._debug_locals(sys._getframe().f_code.co_name, locals())

        api_attrs = obj_map['search']
        api_kwattrs = [kwargs.get(x, '') for x in api_attrs]
        api_kw = {k: v for k, v in zip(api_attrs, api_kwattrs)}

        multi_type = obj_map['multi']
        single_type = obj_map['single']

        # create a list object to append our searches to
        api_obj_multi = pytan.utils.get_taniumpy_obj(obj_map=multi_type)()

        for k, v in api_kw.iteritems():
            if v and k not in obj_map['search']:
                continue  # if we can't search for k, skip

            if not v:
                continue  # if v empty, skip

            if pytan.utils.is_list(v):
                for i in v:
                    api_obj_single = pytan.utils.get_taniumpy_obj(obj_map=single_type)()
                    setattr(api_obj_single, k, i)
                    api_obj_multi.append(api_obj_single)
            else:
                api_obj_single = pytan.utils.get_taniumpy_obj(obj_map=single_type)()
                setattr(api_obj_single, k, v)
                api_obj_multi.append(api_obj_single)

        clean_keys = ['obj']
        clean_kwargs = pytan.utils.clean_kwargs(kwargs=kwargs, keys=clean_keys)

        # find the multi list object
        found = self._find(obj=api_obj_multi, **clean_kwargs)
        return found

    def _get_single(self, obj_map, **kwargs):
        """Find single item wrapper using :func:`_find`

        Parameters
        ----------
        obj_map : dict
            * dict containing the map for a given object type

        Returns
        -------
        found : :class:`taniumpy.object_types.base.BaseType`
           * full object that was found
        """
        self._debug_locals(sys._getframe().f_code.co_name, locals())

        api_attrs = obj_map['search']
        api_kwattrs = [kwargs.get(x, '') for x in api_attrs]
        api_kw = {k: v for k, v in zip(api_attrs, api_kwattrs)}

        # we create a list object to append our single item searches to
        if obj_map.get('allfix', ''):
            all_type = obj_map['allfix']
        else:
            all_type = obj_map['all']

        found = pytan.utils.get_taniumpy_obj(obj_map=all_type)()

        clean_keys = ['obj_map', 'k', 'v']
        clean_kwargs = pytan.utils.clean_kwargs(kwargs=kwargs, keys=clean_keys)

        for k, v in api_kw.iteritems():
            if v and k not in obj_map['search']:
                continue  # if we can't search for k, skip

            if not v:
                continue  # if v empty, skip

            if pytan.utils.is_list(v):
                for i in v:
                    for x in self._single_find(obj_map=obj_map, k=k, v=i, **clean_kwargs):
                        found.append(x)
            else:
                for x in self._single_find(obj_map=obj_map, k=k, v=v, **clean_kwargs):
                    found.append(x)

        return found

    def _single_find(self, obj_map, k, v, **kwargs):
        """Wrapper for single item searches interfacing with :func:`taniumpy.session.Session.find`

        Parameters
        ----------
        obj_map : dict
            * dict containing the map for a given object type
        k : str
            * attribute name to set to `v`
        v : str
            * attribute value to set on `k`

        Returns
        -------
        found : :class:`taniumpy.object_types.base.BaseType`
           * full object that was found
        """
        self._debug_locals(sys._getframe().f_code.co_name, locals())

        found = []

        single_type = obj_map['single']
        api_obj_single = pytan.utils.get_taniumpy_obj(obj_map=single_type)()

        setattr(api_obj_single, k, v)

        clean_keys = ['obj']
        clean_kwargs = pytan.utils.clean_kwargs(kwargs=kwargs, keys=clean_keys)

        obj_ret = self._find(obj=api_obj_single, **clean_kwargs)

        if getattr(obj_ret, '_list_properties', ''):
            for i in obj_ret:
                found.append(i)
        else:
            found.append(obj_ret)

        return found

    def _get_sensor_defs(self, defs, **kwargs):
        """Uses :func:`get` to update a definition with a sensor object

        Parameters
        ----------
        defs : list of dict
            * list of dicts containing sensor definitions

        Returns
        -------
        defs : list of dict
           * list of dicts containing sensor definitions with sensor object in 'sensor_obj'
        """
        self._debug_locals(sys._getframe().f_code.co_name, locals())

        s_obj_map = pytan.constants.GET_OBJ_MAP['sensor']
        search_keys = s_obj_map['search']

        kwargs['include_hidden_flag'] = kwargs.get('include_hidden_flag', 0)

        clean_keys = ['objtype']
        clean_kwargs = pytan.utils.clean_kwargs(kwargs=kwargs, keys=clean_keys)

        for d in defs:
            def_search = {s: d.get(s, '') for s in search_keys if d.get(s, '')}
            def_search.update(clean_kwargs)

            # get the sensor object
            if 'sensor_obj' not in d:
                h = (
                    "Issue a GetObject to get the full object of a sensor for inclusion in a "
                    "question or action"
                )
                def_search['pytan_help'] = def_search.get('pytan_help', h)
                d['sensor_obj'] = self.get(objtype='sensor', **def_search)[0]
        return defs

    def _get_package_def(self, d, **kwargs):
        """Uses :func:`get` to update a definition with a package object

        Parameters
        ----------
        d : dict
            * dict containing package definition

        Returns
        -------
        d : dict
           * dict containing package definitions with package object in 'package_obj'
        """
        self._debug_locals(sys._getframe().f_code.co_name, locals())

        s_obj_map = pytan.constants.GET_OBJ_MAP['package']
        search_keys = s_obj_map['search']

        kwargs['include_hidden_flag'] = kwargs.get('include_hidden_flag', 0)

        clean_keys = ['objtype']
        clean_kwargs = pytan.utils.clean_kwargs(kwargs=kwargs, keys=clean_keys)

        def_search = {s: d.get(s, '') for s in search_keys if d.get(s, '')}
        def_search.update(clean_kwargs)

        # get the package object
        if 'package_obj' not in d:
            h = (
                "Issue a GetObject to get the full object of a package for inclusion in an "
                "action"
            )
            def_search['pytan_help'] = def_search.get('pytan_help', h)
            d['package_obj'] = self.get(objtype='package', **def_search)[0]
        return d

    def _export_class_BaseType(self, obj, export_format, **kwargs): # noqa
        """Handles exporting :class:`taniumpy.object_types.base.BaseType`

        Parameters
        ----------
        obj : :class:`taniumpy.object_types.base.BaseType`
            * taniumpy object to export
        export_format : str
            * str of format to perform export in

        Returns
        -------
        result : str
           * results of exporting `obj` into format `export_format`
        """
        self._debug_locals(sys._getframe().f_code.co_name, locals())

        # run the handler that is specific to this export_format, if it exists
        format_method_str = '_export_format_' + export_format
        format_handler = getattr(self, format_method_str, '')

        clean_keys = ['obj']
        clean_kwargs = pytan.utils.clean_kwargs(kwargs=kwargs, keys=clean_keys)

        if format_handler:
            result = format_handler(obj=obj, **clean_kwargs)
        else:
            err = "{!r} not coded for in Handler!".format
            raise pytan.exceptions.HandlerError(err(export_format))

        return result

    def _export_class_ResultSet(self, obj, export_format, **kwargs): # noqa
        """Handles exporting :class:`taniumpy.object_types.result_set.ResultSet`

        Parameters
        ----------
        obj : :class:`taniumpy.object_types.result_set.ResultSet`
            * taniumpy object to export
        export_format : str
            * str of format to perform export in

        Returns
        -------
        result : str
           * results of exporting `obj` into format `export_format`
        """

        """
        ensure kwargs[sensors] has all the sensors that correlate
        to the what_hash of each column, but only if header_add_sensor=True
        needed for: ResultSet.write_csv(header_add_sensor=True)
        """
        self._debug_locals(sys._getframe().f_code.co_name, locals())

        header_add_sensor = kwargs.get('header_add_sensor', False)
        sensors = kwargs.get('sensors', []) or getattr(obj, 'sensors', [])

        clean_keys = ['objtype', 'hash', 'obj']
        clean_kwargs = pytan.utils.clean_kwargs(kwargs=kwargs, keys=clean_keys)

        if header_add_sensor and export_format == 'csv':
            clean_kwargs['sensors'] = sensors
            sensor_hashes = [x.hash for x in sensors]
            column_hashes = [x.what_hash for x in obj.columns]
            missing_hashes = [
                x for x in column_hashes if x not in sensor_hashes and x > 1
            ]
            if missing_hashes:
                missing_sensors = self.get(objtype='sensor', hash=missing_hashes, **clean_kwargs)
                clean_kwargs['sensors'] += list(missing_sensors)

        # run the handler that is specific to this export_format, if it exists
        format_method_str = '_export_format_' + export_format
        format_handler = getattr(self, format_method_str, '')

        if format_handler:
            result = format_handler(obj=obj, **clean_kwargs)
        else:
            err = "{!r} not coded for in Handler!".format
            raise pytan.exceptions.HandlerError(err(export_format))

        return result

    def _export_format_csv(self, obj, **kwargs):
        """Handles exporting format: CSV

        Parameters
        ----------
        obj : :class:`taniumpy.object_types.result_set.ResultSet` or :class:`taniumpy.object_types.base.BaseType`
            * taniumpy object to export

        Returns
        -------
        result : str
           * results of exporting `obj` into csv format
        """
        self._debug_locals(sys._getframe().f_code.co_name, locals())

        if not hasattr(obj, 'write_csv'):
            err = "{!r} has no write_csv() method!".format
            raise pytan.exceptions.HandlerError(err(obj))

        out = io.BytesIO()

        clean_keys = ['fd', 'val']
        clean_kwargs = pytan.utils.clean_kwargs(kwargs=kwargs, keys=clean_keys)

        if getattr(obj, '_list_properties', ''):
            result = obj.write_csv(fd=out, val=list(obj), **clean_kwargs)
        else:
            result = obj.write_csv(fd=out, val=obj, **clean_kwargs)

        result = out.getvalue()
        return result

    def _export_format_json(self, obj, **kwargs):
        """Handles exporting format: JSON

        Parameters
        ----------
        obj : :class:`taniumpy.object_types.result_set.ResultSet` or :class:`taniumpy.object_types.base.BaseType`
            * taniumpy object to export

        Returns
        -------
        result : str
           * results of exporting `obj` into json format
        """
        self._debug_locals(sys._getframe().f_code.co_name, locals())

        if not hasattr(obj, 'to_json'):
            err = "{!r} has no to_json() method!".format
            raise pytan.exceptions.HandlerError(err(obj))

        clean_keys = ['jsonable']
        clean_kwargs = pytan.utils.clean_kwargs(kwargs=kwargs, keys=clean_keys)

        result = obj.to_json(jsonable=obj, **clean_kwargs)
        return result

    def _export_format_xml(self, obj, **kwargs):
        """Handles exporting format: XML

        Parameters
        ----------
        obj : :class:`taniumpy.object_types.result_set.ResultSet` or :class:`taniumpy.object_types.base.BaseType`
            * taniumpy object to export

        Returns
        -------
        result : str
           * results of exporting `obj` into XML format
        """
        self._debug_locals(sys._getframe().f_code.co_name, locals())

        result = None

        if hasattr(obj, 'toSOAPBody'):
            raw_xml = obj.toSOAPBody(**kwargs)
        elif hasattr(obj, '_RAW_XML'):
            raw_xml = obj._RAW_XML
        else:
            err = "{!r} has no toSOAPBody() method or _RAW_XML attribute!".format
            raise pytan.exceptions.HandlerError(err(obj))

        clean_keys = ['x']
        clean_kwargs = pytan.utils.clean_kwargs(kwargs=kwargs, keys=clean_keys)

        result = pytan.utils.xml_pretty(x=raw_xml, **clean_kwargs)
        return result

    def _deploy_action(self, run=False, get_results=True, **kwargs):
        """Deploy an action and get the results back

        This method requires in-depth knowledge of how filters and options are created in the API, and as such is not meant for human consumption. Use :func:`deploy_action` instead.

        Parameters
        ----------
        package_def : dict
            * definition that describes a package
        action_filter_defs : str, dict, list of str or dict, optional
            * default: []
            * action filter definitions
        action_option_defs : dict, list of dict, optional
            * default: []
            * action filter option definitions
        start_seconds_from_now : int, optional
            * default: 0
            * start action N seconds from now
        distribute_seconds : int, optional
            * default: 0
            * distribute action evenly over clients over N seconds
        issue_seconds : int, optional
            * default: 0
            * have the server re-ask the action status question if performing a GetResultData over N seconds ago
        expire_seconds : int, optional
            * default: package.expire_seconds
            * expire action N seconds from now, will be derived from package if not supplied
        run : bool, optional
            * default: False
            * False: just ask the question that pertains to verify action, export the results to CSV, and raise pytan.exceptions.RunFalse -- does not deploy the action
            * True: actually deploy the action
        get_results : bool, optional
            * default: True
            * True: wait for result completion after deploying action
            * False: just deploy the action and return the object in `ret`
        action_name : str, optional
            * default: prepend package name with "API Deploy "
            * custom name for action
        action_comment : str, optional
            * default:
            * custom comment for action
        polling_secs : int, optional
            * default: 5
            * Number of seconds to wait in between GetResultInfo loops
            * This is passed through to :class:`pytan.pollers.ActionPoller`
        complete_pct : int/float, optional
            * default: 100
            * Percentage of passed_count out of successfully run actions to consider the action "done"
            * This is passed through to :class:`pytan.pollers.ActionPoller`
        override_timeout_secs : int, optional
            * default: 0
            * If supplied and not 0, timeout in seconds instead of when object expires
            * This is passed through to :class:`pytan.pollers.ActionPoller`
        override_passed_count : int, optional
            * instead of getting number of systems that should run this action by asking a question, use this number
            * This is passed through to :class:`pytan.pollers.ActionPoller`

        Returns
        -------
        ret : dict, containing:
            * `saved_action_object` : :class:`taniumpy.object_types.saved_action.SavedAction`, the saved_action added for this action (None if 6.2)
            * `action_object` : :class:`taniumpy.object_types.action.Action`, the action object that tanium created for `saved_action`
            * `package_object` : :class:`taniumpy.object_types.package_spec.PackageSPec`, the package object used in `saved_action`
            * `action_info` : :class:`taniumpy.object_types.result_info.ResultInfo`, the initial GetResultInfo call done before getting results
            * `poller_object` : :class:`pytan.pollers.ActionPoller`, poller object used to wait until all results are in before getting `action_results`
            * `poller_success` : None if `get_results` == False, elsewise True or False
            * `action_results` : None if `get_results` == False, elsewise :class:`taniumpy.object_types.result_set.ResultSet`, the results for `action_object`
            * `action_result_map` : None if `get_results` == False, elsewise progress map for `action_object` in dictionary form

        Examples
        --------
        >>> # example of dict for `package_def`
        >>> package_def = {'name': 'PackageName1', 'params':{'param1': 'value1'}}

        >>> # example of str for `action_filter_defs`
        >>> action_filter_defs = 'Sensor1'

        >>> # example of dict for `action_filter_defs`
        >>> action_filter_defs = {
        ... 'name': 'Sensor1',
        ...     'filter': {
        ...         'operator': 'RegexMatch',
        ...         'not_flag': 0,
        ...         'value': '.*'
        ...     },
        ...     'options': {'and_flag': 1}
        ... }

        See Also
        --------
        :data:`pytan.constants.FILTER_MAPS` : valid filter dictionaries for filters
        :data:`pytan.constants.OPTION_MAPS` : valid option dictionaries for options

        Notes
        -----
            * For 6.2:
                * We need to add an Action object
                * The Action object should not be in an ActionList
                * Action.start_time must be specified, if it is not specified the action shows up as expired immediately. We default to 1 second from current time if start_seconds_from_now is not passed in

            * For 6.5 / 6.6:
                * We need to add a SavedAction object, the server creates the Action object for us
                * To emulate what the console does, the SavedAction should be in a SavedActionList
                * Action.start_time does not need to be specified
        """
        self._debug_locals(sys._getframe().f_code.co_name, locals())

        pytan.utils.check_for_help(kwargs=kwargs)

        clean_keys = [
            'defs',
            'd',
            'obj',
            'objtype',
            'key',
            'default',
            'defname',
            'deftypes',
            'empty_ok',
            'id',
            'pytan_help',
            'handler',
        ]

        clean_kwargs = pytan.utils.clean_kwargs(kwargs=kwargs, keys=clean_keys)

        if not self.session.platform_is_6_5(**kwargs):
            objtype = taniumpy.Action
            objlisttype = None
            force_start_time = True
        else:
            objtype = taniumpy.SavedAction
            objlisttype = taniumpy.SavedActionList
            force_start_time = False

        package_def = pytan.utils.parse_defs(
            defname='package_def',
            deftypes=['dict()'],
            empty_ok=False,
            **clean_kwargs
        )
        action_filter_defs = pytan.utils.parse_defs(
            defname='action_filter_defs',
            deftypes=['list()', 'str()', 'dict()'],
            strconv='name',
            empty_ok=True,
            **clean_kwargs
        )
        action_option_defs = pytan.utils.parse_defs(
            defname='action_option_defs',
            deftypes=['dict()'],
            empty_ok=True,
            **clean_kwargs
        )

        pytan.utils.val_package_def(package_def=package_def)
        pytan.utils.val_sensor_defs(sensor_defs=action_filter_defs)

        package_def = self._get_package_def(d=package_def, **clean_kwargs)
        h = (
            "Issue a GetObject to get the full object of a sensor for inclusion in a "
            "Group for an Action"
        )
        action_filter_defs = self._get_sensor_defs(
            defs=action_filter_defs, pytan_help=h, **clean_kwargs
        )

        start_seconds_from_now = pytan.utils.get_kwargs_int(
            key='start_seconds_from_now', default=0, **clean_kwargs
        )

        expire_seconds = pytan.utils.get_kwargs_int(key='expire_seconds', **clean_kwargs)

        action_name_default = "API Deploy {0.name}".format(package_def['package_obj'])
        action_name = kwargs.get('action_name', action_name_default)

        action_comment_default = 'Created by PyTan v{}'.format(pytan.__version__)
        action_comment = kwargs.get('action_comment', action_comment_default)

        issue_seconds_default = 0
        issue_seconds = kwargs.get('issue_seconds', issue_seconds_default)

        distribute_seconds_default = 0
        distribute_seconds = kwargs.get('distribute_seconds', distribute_seconds_default)

        """
        ask the question that pertains to the action filter, save the result as CSV,
        and raise a RunFalse exception

        this will be used to get a count for how many servers should be seen
        in the deploy action resultdata as 'completed'

        We supply Computer Name and Online = True as the sensors if run is
        False, then exit out after asking the question to allow the user
        to verify the results by looking at the CSV file

        The action filter for the deploy action is used as the question
        filter

        note from jwk: passed_count == the number of machines that pass the filter and
        therefore the number that should take the action
        """
        if not run:
            pre_action_sensors = ['Computer Name', 'Online, that =:True']
            pre_action_sensor_defs = pytan.utils.dehumanize_sensors(sensors=pre_action_sensors)

            q_clean_keys = [
                'sensor_defs',
                'question_filter_defs',
                'question_option_defs',
                'hide_no_results_flag',
                'pytan_help',
                'get_results',
            ]
            q_clean_kwargs = pytan.utils.clean_kwargs(kwargs=kwargs, keys=q_clean_keys)

            h = (
                "Ask a question to determine the number of systems this action would affect if it "
                "was actually run"
            )
            q_clean_kwargs['sensor_defs'] = pre_action_sensor_defs
            q_clean_kwargs['question_filter_defs'] = action_filter_defs
            q_clean_kwargs['question_option_defs'] = action_option_defs
            q_clean_kwargs['hide_no_results_flag'] = 1

            pre_action_question = self._ask_manual(pytan_help=h, **q_clean_kwargs)

            passed_count = pre_action_question['question_results'].passed
            m = "Number of systems that match action filter (passed_count): {}".format
            self.mylog.debug(m(passed_count))

            if passed_count == 0:
                m = "Number of systems that match the action filters provided is zero!"
                raise pytan.exceptions.HandlerError(m)

            default_format = 'csv'
            export_format = kwargs.get('export_format', default_format)

            default_prefix = 'VERIFY_BEFORE_DEPLOY_ACTION_'
            export_prefix = kwargs.get('prefix', default_prefix)

            e_clean_keys = [
                'obj',
                'export_format',
                'prefix',
            ]
            e_clean_kwargs = pytan.utils.clean_kwargs(kwargs=kwargs, keys=e_clean_keys)
            e_clean_kwargs['obj'] = pre_action_question['question_results']
            e_clean_kwargs['export_format'] = export_format
            e_clean_kwargs['prefix'] = export_prefix
            report_path, result = self.export_to_report_file(**e_clean_kwargs)

            m = (
                "'Run' is not True!!\n"
                "View and verify the contents of {} (length: {} bytes)\n"
                "Re-run this deploy action with run=True after verifying"
            ).format
            raise pytan.exceptions.RunFalse(m(report_path, len(result)))

        # BUILD THE PACKAGE OBJECT TO BE ADDED TO THE ACTION
        add_package_obj = pytan.utils.copy_package_obj_for_action(obj=package_def['package_obj'])

        # if source_id is specified, a new package will be created with the parameters
        # for this action embedded into it - specifying hidden = 1 will ensure the new package
        # is hidden
        add_package_obj.hidden_flag = 1

        param_objlist = pytan.utils.build_param_objlist(
            obj=package_def['package_obj'],
            user_params=package_def['params'],
            delim='',
            derive_def=False,
            empty_ok=False,
        )

        if param_objlist:
            add_package_obj.source_id = package_def['package_obj'].id
            add_package_obj.parameters = param_objlist
        else:
            add_package_obj.id = package_def['package_obj'].id
            add_package_obj.name = package_def['package_obj'].name
            add_package_obj.source_id = None

        m = "DEPLOY_ACTION objtype: {}, objlisttype: {}, force_start_time: {}, version: {}".format
        self.mylog.debug(m(objtype, objlisttype, force_start_time, self.session.server_version))

        # BUILD THE ACTION OBJECT TO BE ADDED
        add_obj = objtype()
        add_obj.package_spec = add_package_obj
        add_obj.id = -1
        add_obj.name = action_name
        add_obj.issue_seconds = issue_seconds
        add_obj.distribute_seconds = distribute_seconds
        add_obj.comment = action_comment
        add_obj.status = 0
        add_obj.start_time = ''
        add_obj.end_time = ''
        add_obj.public_flag = 0
        add_obj.policy_flag = 0
        add_obj.approved_flag = 0
        add_obj.issue_count = 0

        if action_filter_defs or action_option_defs:
            targetgroup_obj = pytan.utils.build_group_obj(
                q_filter_defs=action_filter_defs, q_option_defs=action_option_defs,
            )
            add_obj.target_group = targetgroup_obj
        else:
            targetgroup_obj = None

        if start_seconds_from_now:
            add_obj.start_time = pytan.utils.seconds_from_now(secs=start_seconds_from_now)

        if force_start_time and not add_obj.start_time:
            if not start_seconds_from_now:
                start_seconds_from_now = 1
            add_obj.start_time = pytan.utils.seconds_from_now(secs=start_seconds_from_now)

        if package_def['package_obj'].expire_seconds:
            add_obj.expire_seconds = package_def['package_obj'].expire_seconds

        if expire_seconds:
            add_obj.expire_seconds = expire_seconds

        if objlisttype:
            add_objs = objlisttype()
            add_objs.append(add_obj)
            h = "Issue an AddObject to add a list of SavedActions (6.5 logic)"
            added_objs = self._add(obj=add_objs, pytan_help=h, **clean_kwargs)
            added_obj = added_objs[0]

            m = "DEPLOY_ACTION ADDED: {}, ID: {}".format
            self.mylog.debug(m(added_obj.__class__.__name__, added_obj.id))

            h = "Issue a GetObject to get the last action created for a SavedAction"
            action_obj = self._find(obj=added_obj.last_action, pytan_help=h, **clean_kwargs)
        else:
            added_obj = None
            h = "Issue an AddObject to add a single Action (6.2 logic)"
            action_obj = self._add(obj=add_obj, pytan_help=h, **clean_kwargs)

        h = "Issue a GetObject to get the package for an Action"
        action_package = self._find(obj=action_obj.package_spec, pytan_help=h, **clean_kwargs)

        m = "DEPLOY_ACTION ADDED: {}, ID: {}".format
        self.mylog.debug(m(action_package.__class__.__name__, action_package.id))

        m = "DEPLOY_ACTION ADDED: {}, ID: {}".format
        self.mylog.debug(m(action_obj.__class__.__name__, action_obj.id))

        h = (
            "Issue a GetResultInfo on an Action to have the Server create a question that "
            "tracks the results for a Deployed Action"
        )
        action_info = self.get_result_info(obj=action_obj, pytan_help=h, **clean_kwargs)

        m = "DEPLOY_ACTION ADDED: Question for Action Results, ID: {}".format
        self.mylog.debug(m(action_info.question_id))

        poller = pytan.pollers.ActionPoller(handler=self, obj=action_obj, **clean_kwargs)
        ret = {
            'saved_action_object': added_obj,
            'action_object': action_obj,
            'package_object': action_package,
            'group_object': targetgroup_obj,
            'action_info': action_info,
            'poller_object': poller,
            'action_results': None,
            'action_result_map': None,
            'poller_success': None,
        }

        if get_results:
            ret['poller_success'] = ret['poller_object'].run(**kwargs)
            ret['action_results'] = ret['poller_object'].result_data
            ret['action_result_map'] = ret['poller_object'].result_map

        return ret

    def _ask_manual(self, get_results=True, **kwargs):
        """Ask a manual question using definitions and get the results back

        This method requires in-depth knowledge of how filters and options are created in the API,
        and as such is not meant for human consumption. Use :func:`ask_manual` instead.

        Parameters
        ----------
        sensor_defs : str, dict, list of str or dict
            * default: []
            * sensor definitions
        question_filter_defs : dict, list of dict, optional
            * default: []
            * question filter definitions
        question_option_defs : dict, list of dict, optional
            * default: []
            * question option definitions
        get_results : bool, optional
            * default: True
            * True: wait for result completion after asking question
            * False: just ask the question and return it in `ret`
        sse : bool, optional
            * default: False
            * True: perform a server side export when getting result data
            * False: perform a normal get result data (default for 6.2)
            * Keeping False by default for now until the columnset's are properly identified in the server export
        sse_format : str, optional
            * default: 'xml_obj'
            * format to have server side export report in, one of: {'csv', 'xml', 'xml_obj', 'cef', 0, 1, 2}
        leading : str, optional
            * default: ''
            * used for sse_format 'cef' only, the string to prepend to each row
        trailing : str, optional
            * default: ''
            * used for sse_format 'cef' only, the string to append to each row
        polling_secs : int, optional
            * default: 5
            * Number of seconds to wait in between GetResultInfo loops
            * This is passed through to :class:`pytan.pollers.QuestionPoller`
        complete_pct : int/float, optional
            * default: 99
            * Percentage of mr_tested out of estimated_total to consider the question "done"
            * This is passed through to :class:`pytan.pollers.QuestionPoller`
        override_timeout_secs : int, optional
            * default: 0
            * If supplied and not 0, timeout in seconds instead of when object expires
            * This is passed through to :class:`pytan.pollers.QuestionPoller`
        callbacks : dict, optional
            * default: {}
            * can be a dict of functions to be run with the key names being the various state changes: 'ProgressChanged', 'AnswersChanged', 'AnswersComplete'
            * This is passed through to :func:`pytan.pollers.QuestionPoller.run`
        override_estimated_total : int, optional
            * instead of getting number of systems that should see this question from result_info.estimated_total, use this number
            * This is passed through to :func:`pytan.pollers.QuestionPoller`
        force_passed_done_count : int, optional
            * when this number of systems have passed the right hand side of the question, consider the question complete
            * This is passed through to :func:`pytan.pollers.QuestionPoller`

        Returns
        -------
        ret : dict, containing:
            * `question_object` : :class:`taniumpy.object_types.question.Question`, the actual question created and added by PyTan
            * `question_results` : :class:`taniumpy.object_types.result_set.ResultSet`, the Result Set for `question_object` if `get_results` == True
            * `poller_object` : :class:`pytan.pollers.QuestionPoller`, poller object used to wait until all results are in before getting `question_results`
            * `poller_success` : None if `get_results` == True, elsewise True or False

        Examples
        --------
        >>> # example of str for sensor_defs
        >>> sensor_defs = 'Sensor1'

        >>> # example of dict for sensor_defs
        >>> sensor_defs = {
        ... 'name': 'Sensor1',
        ...     'filter': {
        ...         'operator': 'RegexMatch',
        ...         'not_flag': 0,
        ...         'value': '.*'
        ...     },
        ...     'params': {'key': 'value'},
        ...     'options': {'and_flag': 1}
        ... }

        >>> # example of dict for question_filter_defs
        >>> question_filter_defs = {
        ...     'operator': 'RegexMatch',
        ...     'not_flag': 0,
        ...     'value': '.*'
        ... }

        See Also
        --------
        :data:`pytan.constants.FILTER_MAPS` : valid filter dictionaries for filters
        :data:`pytan.constants.OPTION_MAPS` : valid option dictionaries for options
        """
        self._debug_locals(sys._getframe().f_code.co_name, locals())

        pytan.utils.check_for_help(kwargs=kwargs)

        clean_keys = [
            'defs',
            'd',
            'obj',
            'objtype',
            'key',
            'default',
            'defname',
            'deftypes',
            'empty_ok',
            'id',
            'pytan_help',
            'handler',
            'sse',
        ]
        clean_kwargs = pytan.utils.clean_kwargs(kwargs=kwargs, keys=clean_keys)

        # get our defs from kwargs and churn them into what we want
        sensor_defs = pytan.utils.parse_defs(
            defname='sensor_defs',
            deftypes=['list()', 'str()', 'dict()'],
            strconv='name',
            empty_ok=True,
            **clean_kwargs
        )

        q_filter_defs = pytan.utils.parse_defs(
            defname='question_filter_defs',
            deftypes=['list()', 'dict()'],
            empty_ok=True,
            **clean_kwargs
        )

        q_option_defs = pytan.utils.parse_defs(
            defname='question_option_defs',
            deftypes=['dict()'],
            empty_ok=True,
            **clean_kwargs
        )

        sse = kwargs.get('sse', False)
        clean_kwargs['sse_format'] = clean_kwargs.get('sse_format', 'xml_obj')

        max_age_seconds = pytan.utils.get_kwargs_int(
            key='max_age_seconds', default=600, **clean_kwargs
        )

        # do basic validation of our defs
        pytan.utils.val_sensor_defs(sensor_defs=sensor_defs)
        pytan.utils.val_q_filter_defs(q_filter_defs=q_filter_defs)

        # get the sensor objects that are in our defs and add them as d['sensor_obj']
        h = (
            "Issue a GetObject to get the full object of a sensor for inclusion in a "
            "Select for a Question"
        )
        sensor_defs = self._get_sensor_defs(defs=sensor_defs, pytan_help=h, **clean_kwargs)
        h = (
            "Issue a GetObject to get the full object of a sensor for inclusion in a "
            "Group for a Question"
        )
        q_filter_defs = self._get_sensor_defs(defs=q_filter_defs, pytan_help=h, **clean_kwargs)

        # build a SelectList object from our sensor_defs
        selectlist_obj = pytan.utils.build_selectlist_obj(sensor_defs=sensor_defs)

        # build a Group object from our question filters/options
        group_obj = pytan.utils.build_group_obj(
            q_filter_defs=q_filter_defs, q_option_defs=q_option_defs,
        )

        # build a Question object from selectlist_obj and group_obj
        add_obj = pytan.utils.build_manual_q(selectlist_obj=selectlist_obj, group_obj=group_obj)

        add_obj.max_age_seconds = max_age_seconds

        # add our Question and get a Question ID back
        h = "Issue an AddObject to add a Question object"
        added_obj = self._add(obj=add_obj, pytan_help=h, **clean_kwargs)

        m = "Question Added, ID: {}, query text: {!r}, expires: {}".format
        self.mylog.debug(m(added_obj.id, added_obj.query_text, added_obj.expiration))

        poller = pytan.pollers.QuestionPoller(handler=self, obj=added_obj, **clean_kwargs)

        ret = {
            'question_object': added_obj,
            'poller_object': poller,
            'question_results': None,
            'poller_success': None,
        }

        if get_results:
            # poll the Question ID returned above to wait for results
            ret['poller_success'] = ret['poller_object'].run(**clean_kwargs)

            # get the results
            if sse and self.session.platform_is_6_5(**clean_kwargs):
                rd = self.get_result_data_sse(obj=added_obj, **clean_kwargs)
            else:
                rd = self.get_result_data(obj=added_obj, **clean_kwargs)

            if isinstance(rd, taniumpy.object_types.result_set.ResultSet):
                # add the sensors from this question to the ResultSet object for reporting
                rd.sensors = [x['sensor_obj'] for x in sensor_defs]

            ret['question_results'] = rd
        return ret

    def _version_support_check(self, v_maps, **kwargs):
        """Checks that each of the version maps in v_maps is greater than or equal to
        the current servers version

        Parameters
        ----------
        v_maps : list of str
            * each str should be a platform version
            * each str will be checked against self.session.server_version
            * if self.session.server_version is not greater than or equal to any str in v_maps, return will be False
            * if self.session.server_version is greater than all strs in v_maps, return will be True
            * if self.server_version is invalid/can't be determined, return will be False

        Returns
        -------
        bool
            * True if all values in all v_maps are greater than or equal to self.session.server_version
            * False otherwise
        """
        self._debug_locals(sys._getframe().f_code.co_name, locals())

        if self.session._invalid_server_version():
            # server version is not valid, force a refresh right now
            self.session.get_server_version(**kwargs)

        if self.session._invalid_server_version():
            # server version is STILL invalid, return False
            return False

        for v_map in v_maps:
            if not self.session.server_version >= v_map:
                return False
        return True

    def _check_sse_format_support(self, sse_format, sse_format_int, **kwargs):
        """Determines if the export format integer is supported in the server version

        Parameters
        ----------
        sse_format : str or int
            * user supplied export format
        sse_format_int : int
            * `sse_format` parsed into an int
        """
        self._debug_locals(sys._getframe().f_code.co_name, locals())

        if sse_format_int not in pytan.constants.SSE_RESTRICT_MAP:
            return

        restrict_maps = pytan.constants.SSE_RESTRICT_MAP[sse_format_int]

        if not self._version_support_check(v_maps=restrict_maps, **kwargs):
            restrict_maps_txt = '\n'.join([str(x) for x in restrict_maps])

            m = (
                "Server version {} does not support export format {!r}, "
                "server version must be equal to or greater than one of:\n{}"
            ).format

            m = m(self.session.server_version, sse_format, restrict_maps_txt)

            raise pytan.exceptions.UnsupportedVersionError(m)

    def _resolve_sse_format(self, sse_format, **kwargs):
        """Resolves the server side export format the user supplied to an integer for the API

        Parameters
        ----------
        sse_format : str or int
            * user supplied export format

        Returns
        -------
        sse_format_int : int
            * `sse_format` parsed into an int
        """
        self._debug_locals(sys._getframe().f_code.co_name, locals())

        sse_format_int = [x[-1] for x in pytan.constants.SSE_FORMAT_MAP if sse_format.lower() in x]

        if not sse_format_int:
            m = "Unsupport export format {!r}, must be one of:\n{}".format
            ef_map_txt = '\n'.join(
                [', '.join(['{!r}'.format(x) for x in y]) for y in pytan.constants.SSE_FORMAT_MAP]
            )
            raise pytan.exceptions.HandlerError(m(sse_format, ef_map_txt))

        sse_format_int = sse_format_int[0]

        m = "'sse_format resolved from '{}' to '{}'".format
        self.mylog.debug(m(sse_format, sse_format_int))

        self._check_sse_format_support(
            sse_format=sse_format, sse_format_int=sse_format_int, **kwargs
        )

        return sse_format_int

    def _check_sse_version(self, **kwargs):
        """Validates that the server version supports server side export"""
        self._debug_locals(sys._getframe().f_code.co_name, locals())

        if not self.session.platform_is_6_5(**kwargs):
            m = "Server side export not supported in version: {}".format
            m = m(self.session.server_version)
            raise pytan.exceptions.UnsupportedVersionError(m)

    def _check_sse_crash_prevention(self, obj, **kwargs):
        """Runs a number of methods used to prevent crashing the platform server when performing server side exports

        Parameters
        ----------
        obj : :class:`taniumpy.object_types.base.BaseType`
            * object to pass to self._check_sse_empty_rs
        """
        self._debug_locals(sys._getframe().f_code.co_name, locals())

        clean_keys = ['obj', 'v_maps', 'ok_version']
        clean_kwargs = pytan.utils.clean_kwargs(kwargs=kwargs, keys=clean_keys)

        restrict_maps = pytan.constants.SSE_CRASH_MAP

        ok_version = self._version_support_check(v_maps=restrict_maps, **clean_kwargs)

        self._check_sse_timing(ok_version=ok_version, **clean_kwargs)
        self._check_sse_empty_rs(obj=obj, ok_version=ok_version, **clean_kwargs)

    def _check_sse_timing(self, ok_version, **kwargs):
        """Checks that the last server side export was at least 1 second ago if server version is less than any versions in pytan.constants.SSE_CRASH_MAP

        Parameters
        ----------
        ok_version : bool
            * if the version currently running is an "ok" version
        """
        self._debug_locals(sys._getframe().f_code.co_name, locals())

        last_get_rd_sse = getattr(self, 'last_get_rd_sse', None)

        if last_get_rd_sse:
            last_elapsed = datetime.datetime.utcnow() - last_get_rd_sse
            if last_elapsed.seconds == 0 and not ok_version:
                m = "You must wait at least one second between server side export requests!".format
                raise pytan.exceptions.ServerSideExportError(m())

        self.last_get_rd_sse = datetime.datetime.utcnow()

    def _check_sse_empty_rs(self, obj, ok_version, **kwargs):
        """Checks if the server version is less than any versions in pytan.constants.SSE_CRASH_MAP, if so verifies that the result set is not empty

        Parameters
        ----------
        obj : :class:`taniumpy.object_types.base.BaseType`
            * object to get result info for to ensure non-empty answers
        ok_version : bool
            * if the version currently running is an "ok" version
        """
        self._debug_locals(sys._getframe().f_code.co_name, locals())

        clean_keys = ['obj']
        clean_kwargs = pytan.utils.clean_kwargs(kwargs=kwargs, keys=clean_keys)

        if not ok_version:
            ri = self.get_result_info(obj=obj, **clean_kwargs)
            if ri.row_count == 0:
                m = (
                    "No rows available to perform a server side export with, result info: {}"
                ).format
                raise pytan.exceptions.ServerSideExportError(m(ri))

    def _debug_locals(self, fname, flocals):
        """Method to print out locals for a function if self.debug_method_locals is True"""
        if getattr(self, 'debug_method_locals', False):
            m = "Local variables for {}.{}:\n{}".format
            self.methodlog.debug(m(self.__class__.__name__, fname, pprint.pformat(flocals)))
