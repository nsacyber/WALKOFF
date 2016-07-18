# -*- mode: Python; tab-width: 4; indent-tabs-mode: nil; -*-
# ex: set tabstop=4
# Please do not change the two lines above. See PEP 8, PEP 263.
"""Session classes for the :mod:`pytan` module."""
import sys

# disable python from creating .pyc files everywhere
sys.dont_write_bytecode = True

import os
import string
import logging
import json
import re
import threading
import time
import pprint

from datetime import datetime
from base64 import b64encode

try:
    import xml.etree.cElementTree as ET
except:
    import xml.etree.ElementTree as ET

my_file = os.path.abspath(__file__)
my_dir = os.path.dirname(my_file)
parent_dir = os.path.dirname(my_dir)
path_adds = [parent_dir]
[sys.path.insert(0, aa) for aa in path_adds if aa not in sys.path]

import pytan
from pytan.xml_clean import xml_cleaner
import requests
import taniumpy
requests.packages.urllib3.disable_warnings()

import sys
reload(sys)
sys.setdefaultencoding('utf-8')


class Session(object):
    """
    This session object uses the :mod:`requests` package instead of the built in httplib library.

    This provides support for keep alive, gzip, cookies, forwarding, and a host of other features
    automatically.


    Examples
    --------

    Setup a Session() object::

        >>> import sys
        >>> sys.path.append('/path/to/pytan/')
        >>> import pytan
        >>> session = pytan.sessions.Session('host')


    Authenticate with the Session() object::

        >>> session.authenticate('username', 'password')
    """
    XMLNS = {
        'SOAP-ENV': 'xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/"',
        'xsd': 'xmlns:xsd="http://www.w3.org/2001/XMLSchema"',
        'xsi': 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"',
        'typens': 'xmlns:typens="urn:TaniumSOAP"',
    }
    """The namespace mappings for use in XML Request bodies"""

    REQUEST_BODY_BASE = ("""<SOAP-ENV:Envelope {SOAP-ENV} {xsd} {xsi}>
<SOAP-ENV:Body>
  <typens:tanium_soap_request {typens}>
    <command>$command</command>
    <object_list>$object_list</object_list>
    $options
  </typens:tanium_soap_request>
</SOAP-ENV:Body>
</SOAP-ENV:Envelope>""").format(**XMLNS)
    """The XML template used for all SOAP Requests in string form"""

    AUTH_RES = 'auth'
    """The URL to use for authentication requests"""

    SOAP_RES = 'soap'
    """The URL to use for SOAP requests"""

    INFO_RES = 'info.json'
    """The URL to use for server info requests"""

    AUTH_CONNECT_TIMEOUT_SEC = 5
    """number of seconds before timing out for a connection while authenticating"""

    AUTH_RESPONSE_TIMEOUT_SEC = 15
    """number of seconds before timing out for a response while authenticating"""

    INFO_CONNECT_TIMEOUT_SEC = 5
    """number of seconds before timing out for a connection while getting server info"""

    INFO_RESPONSE_TIMEOUT_SEC = 15
    """number of seconds before timing out for a response while getting server info"""

    SOAP_CONNECT_TIMEOUT_SEC = 15
    """number of seconds before timing out for a connection while sending a SOAP Request"""

    SOAP_RESPONSE_TIMEOUT_SEC = 540
    """number of seconds before timing out for a response while sending a SOAP request"""

    SOAP_REQUEST_HEADERS = {'Content-Type': 'text/xml; charset=utf-8', 'Accept-Encoding': 'gzip'}
    """dictionary of headers to add to every HTTP GET/POST"""

    ELEMENT_RE_TXT = r'<{0}>(.*?)</{0}>'
    """regex string to search for an element in XML bodies"""

    HTTP_DEBUG = False
    """print requests package debug or not"""

    HTTP_RETRY_COUNT = 5
    """number of times to retry HTTP GET/POST's if the connection times out/fails"""

    HTTP_AUTH_RETRY = True
    """retry HTTP GET/POST's with username/password if session_id fails or not"""

    STATS_LOOP_ENABLED = False
    """enable the statistics loop thread or not"""

    STATS_LOOP_SLEEP_SEC = 5
    """number of seconds to sleep in between printing the statistics when stats_loop_enabled is True"""

    STATS_LOOP_TARGETS = [
        {'Version': 'Settings/Version'},
        {'Active Questions': 'Active Question Cache/Active Question Estimate'},
        {'Clients': 'Active Question Cache/Active Client Estimate'},
        {'Strings': 'String Cache/Total String Count'},
        {'Handles': 'System Performance Info/HandleCount'},
        {'Processes': 'System Performance Info/ProcessCount'},
        {'Memory Available': 'percentage(System Performance Info/PhysicalAvailable,System Performance Info/PhysicalTotal)'},
    ]
    """list of dictionaries with the key being the section of info.json to print info from, and the value being the item with in that section to print the value"""

    RECORD_ALL_REQUESTS = False
    """Controls whether each requests response object is appended to the self.ALL_REQUESTS_RESPONSES list"""

    BAD_RESPONSE_CMD_PRUNES = [
        '\n',
        'XML Parse Error: ',
        'SOAPProcessing Exception: class ',
        'ERROR: 400 Bad Request'
    ]
    """List of strings to remove from commands in responses that do not match the response in the request"""

    AUTH_FAIL_CODES = [401, 403]
    """List of HTTP response codes that equate to authorization failures"""

    BAD_SERVER_VERSIONS = [None, '', 'Unable to determine', 'Not yet determined']
    """List of server versions that are not valid"""

    # TRACKING VARIABLES -- THESE GET UPDATED BY SESSION
    ALL_REQUESTS_RESPONSES = []
    """This list will be updated with each requests response object that was received"""

    LAST_REQUESTS_RESPONSE = None
    """This variable will be updated with the last requests response object that was received"""

    LAST_RESPONSE_INFO = {}
    """This variable will be updated with the information from the most recent call to _get_response()"""

    host = None
    """host to connect to"""

    port = None
    """port to connect to"""

    server_version = "Not yet determined"
    """version string of server, will be updated when get_server_version() is called"""

    force_server_version = ''
    """In the case where the user wants to have pytan act as if the server is a specific version, regardless of what server_version is."""

    def __init__(self, host, port=443, **kwargs):
        self.methodlog = logging.getLogger("method_debug")
        self.DEBUG_METHOD_LOCALS = kwargs.get('debug_method_locals', False)

        self._debug_locals(sys._getframe().f_code.co_name, locals())

        self.setup_logging()

        self.REQUESTS_SESSION = requests.Session()
        """
        The Requests session allows you to persist certain parameters across requests. It also
        persists cookies across all requests made from the Session instance. Any requests that you
        make within a session will automatically reuse the appropriate connection
        """

        # disable SSL cert verification for all requests made in this session
        self.REQUESTS_SESSION.verify = False

        server = kwargs.get('server', '')
        self.host = server or host
        self.server = self.host
        self.port = port
        self._session_id = ''
        self._username = ''
        self._password = ''

        # kwargs overrides for object properties
        self.SOAP_REQUEST_HEADERS = kwargs.get(
            'soap_request_headers', self.SOAP_REQUEST_HEADERS)
        self.HTTP_DEBUG = kwargs.get('http_debug', False)
        self.HTTP_AUTH_RETRY = kwargs.get('http_auth_retry', self.HTTP_AUTH_RETRY)
        self.HTTP_RETRY_COUNT = kwargs.get('http_retry_count', self.HTTP_RETRY_COUNT)
        self.AUTH_CONNECT_TIMEOUT_SEC = kwargs.get(
            'auth_connect_timeout_sec', self.AUTH_CONNECT_TIMEOUT_SEC)
        self.AUTH_RESPONSE_TIMEOUT_SEC = kwargs.get(
            'auth_response_timeout_sec', self.AUTH_RESPONSE_TIMEOUT_SEC)
        self.INFO_CONNECT_TIMEOUT_SEC = kwargs.get(
            'info_connect_timeout_sec', self.INFO_CONNECT_TIMEOUT_SEC)
        self.INFO_RESPONSE_TIMEOUT_SEC = kwargs.get(
            'info_response_timeout_sec', self.INFO_RESPONSE_TIMEOUT_SEC)
        self.SOAP_CONNECT_TIMEOUT_SEC = kwargs.get(
            'soap_connect_timeout_sec', self.SOAP_CONNECT_TIMEOUT_SEC)
        self.SOAP_RESPONSE_TIMEOUT_SEC = kwargs.get(
            'soap_response_timeout_sec', self.SOAP_RESPONSE_TIMEOUT_SEC)
        self.STATS_LOOP_ENABLED = kwargs.get('stats_loop_enabled', self.STATS_LOOP_ENABLED)
        self.STATS_LOOP_SLEEP_SEC = kwargs.get('stats_loop_sleep_sec', self.STATS_LOOP_SLEEP_SEC)
        self.STATS_LOOP_TARGETS = kwargs.get('stats_loop_targets', self.STATS_LOOP_TARGETS)
        self.RECORD_ALL_REQUESTS = kwargs.get('record_all_requests', self.RECORD_ALL_REQUESTS)

        # re-enforce empty variables for init of session
        self.ALL_REQUESTS_RESPONSES = []
        self.LAST_RESPONSE_INFO = {}
        self.LAST_REQUESTS_RESPONSE = None
        self.server_version = "Not yet determined"

        self.force_server_version = kwargs.get('force_server_version', self.force_server_version)

    def setup_logging(self):
        self._debug_locals(sys._getframe().f_code.co_name, locals())

        self.qualname = "pytan.sessions.{}".format(self.__class__.__name__)
        self.mylog = logging.getLogger(self.qualname)
        self.authlog = logging.getLogger(self.qualname + ".auth")
        self.httplog = logging.getLogger(self.qualname + ".http")
        self.bodyhttplog = logging.getLogger(self.qualname + ".http.body")
        self.statslog = logging.getLogger("stats")

    def __str__(self):
        class_name = self.__class__.__name__
        server_version = self.get_server_version()
        str_tpl = "{} to {}:{}, Authenticated: {}, Platform Version: {}".format
        ret = str_tpl(class_name, self.host, self.port, self.is_auth, server_version)
        return ret

    @property
    def session_id(self):
        """Property to fetch the session_id for this object

        Returns
        -------
        self._session_id : str
        """
        return self._session_id

    @session_id.setter
    def session_id(self, value):
        """Setter to update the session_id for this object"""
        if self.session_id != value:
            self._session_id = value
            self.authlog.debug("Session ID updated to: {}".format(value))

    @property
    def is_auth(self):
        """Property to determine if there is a valid session_id or username and password stored in this object

        Returns
        -------
        bool
            * True: if self._session_id or self._username and _self.password are set
            * False: if not
        """
        auth = False
        if self._session_id:
            auth = True
        elif self._username and self._password:
            auth = True
        return auth

    def logout(self, all_session_ids=False, **kwargs):
        """Logout a given session_id from Tanium. If not session_id currently set, it will authenticate to get one.

        Parameters
        ----------
        all_session_ids : bool, optional
            * default: False
            * False: only log out the current session id for the current user
            * True: log out ALL session id's associated for the current user
        pytan_help : str, optional
            * default: ''
            * help string to add to self.LAST_REQUESTS_RESPONSE.pytan_help

        """
        self._debug_locals(sys._getframe().f_code.co_name, locals())

        self._check_auth()

        if not self.session_id:
            self.authenticate()

        if all_session_ids:
            logout = 1
        else:
            logout = 0

        headers = {}
        headers['session'] = self.session_id
        headers['logout'] = logout

        req_args = {}
        req_args['url'] = self.AUTH_RES
        req_args['headers'] = headers
        req_args['retry_count'] = False
        req_args['pytan_help'] = kwargs.get('pytan_help', '')

        try:
            self.http_get(**req_args)
        except Exception as e:
            m = "logout exception: {}".format
            self.authlog.debug(m(e))

        if all_session_ids:
            self.authlog.debug("Successfully logged out all session ids for current user")
        else:
            self.authlog.debug("Successfully logged out current session id for current user")

        self.session_id = ''

    def authenticate(self, username=None, password=None, session_id=None, **kwargs):
        """Authenticate against a Tanium Server using a username/password or a session ID

        Parameters
        ----------
        username : str, optional
            * default: None
            * username to authenticate as
        password : str, optional
            * default: None
            * password for `username`
        session_id : str, optional
            * default: None
            * session_id to authenticate with, this will be used in favor of username/password if all 3 are supplied.
        persistent: bool, optional
            * default: False
            * False: do not request a persistent session (returns a session_id that expires 5 minutes after last use)
            * True: do request a persistent (returns a session_id that expires 1 week after last use)
        pytan_help : str, optional
            * default: ''
            * help string to add to self.LAST_REQUESTS_RESPONSE.pytan_help

        Notes
        -----
        Can request a persistent session that will last up to 1 week when authenticating
        with username and password.

        New persistent sessions may be handed out by the Tanium server when the session handed
        by this auth call is used to login with that week. The new session must be used to login,
        as no matter what persistent sessions will expire 1 week after issuance (or when logout is
        called with that session, or when logout with all_sessions=True is called for any session
        for this user)

        the way sessions get issued:

         - a GET request to /auth is issued
         - username/password supplied in headers as base64 encoded, or session is supplied in
           headers as string
         - session is returned upon successful auth
         - if there is a header "persistent=1" in the headers, a session that expires after 1 week
           will be issued if username/password was used to auth. persistent is ignored if session
           is used to auth.
         - if there is not a header "persistent=1" in the headers, a session that expires after 5
           minutes will be issued
         - if session is used before it expires, it's expiry will be extended by 5 minutes or 1
           week, depending on the type of persistence
         - while using the SOAP api, new session ID's may be returned as part of the response.
           these new session ID's should be used in lieu of the old session ID

        /auth URL
        This url is used for validating a server user's credentials. It supports a few different
        ways to authenticate and returns a SOAP session ID on success.  These sessions expire
        after 5 minutes by default if they aren't used in SOAP requests.  This expiration is
        configured with the server setting 'session_expiration_seconds'.

        Supported Authentication Methods:
         - HTTP Basic Auth (Clear Text/BASE64)
         - Username/Password/Domain Headers (Clear Text)
         - Negotiate (NTLM Only)

        NTLM is enabled by default in 6.3 or greater and requires a persistent connection until a
        session is generated.
        """
        self._debug_locals(sys._getframe().f_code.co_name, locals())

        persistent = kwargs.get('persistent', False)
        auth_type = 'unknown'

        if session_id:
            auth_type = 'session ID'
            if persistent:
                m = (
                    "Unable to establish a persistent session when authenticating with a session!"
                ).format
                raise pytan.exceptions.AuthorizationError(m())
            self._session_id = session_id
        else:
            auth_type = 'username/password'
            if username:
                self._username = username
            if password:
                self._password = password

        if not session_id:
            if not self._username:
                raise pytan.exceptions.AuthorizationError("Must supply username")

            if not self._password:
                raise pytan.exceptions.AuthorizationError("Must supply password")

        auth_headers = {}

        if persistent:
            auth_headers['persistent'] = 1

        h = "Authenticate to the SOAP API via /auth"
        pytan_help = kwargs.get('pytan_help', h)

        req_args = {}
        req_args['url'] = self.AUTH_RES
        req_args['headers'] = auth_headers
        req_args['retry_count'] = kwargs.get('retry_count', 0)
        req_args['connect_timeout'] = kwargs.get('connect_timeout', self.AUTH_CONNECT_TIMEOUT_SEC)
        req_args['response_timeout'] = kwargs.get(
            'response_timeout', self.AUTH_RESPONSE_TIMEOUT_SEC
        )
        req_args['pytan_help'] = pytan_help

        try:
            body = self.http_get(**req_args)
        except Exception as e:
            m = "Error while trying to authenticate: {}".format
            raise pytan.exceptions.AuthorizationError(m(e))

        self.session_id = body
        if persistent:
            m = (
                "Successfully authenticated and received a persistent (up to 1 week)"
                "session id using {}"
            ).format
            self.authlog.debug(m(auth_type))
        else:
            m = (
                "Successfully authenticated and received a non-persistent (up to 5 minutes) "
                "session id using {}"
            ).format
            self.authlog.debug(m(auth_type))

        # start the stats thread loop in a background thread
        self._start_stats_thread(**kwargs)

    def find(self, obj, **kwargs):
        """Creates and sends a GetObject XML Request body from `object_type` and parses the response into an appropriate :mod:`taniumpy` object

        Parameters
        ----------
        obj : :class:`taniumpy.object_types.base.BaseType`
            * object to find

        Returns
        -------
        obj : :class:`taniumpy.object_types.base.BaseType`
            * found objects
        """
        self._debug_locals(sys._getframe().f_code.co_name, locals())

        clean_keys = ['obj', 'request_body']
        clean_kwargs = pytan.utils.clean_kwargs(kwargs=kwargs, keys=clean_keys)

        request_body = self._create_get_object_body(obj=obj, **clean_kwargs)
        response_body = self._get_response(request_body=request_body, **clean_kwargs)
        obj = taniumpy.BaseType.fromSOAPBody(body=response_body)
        return obj

    def save(self, obj, **kwargs):
        """Creates and sends a UpdateObject XML Request body from `obj` and parses the response into an appropriate :mod:`taniumpy` object

        Parameters
        ----------
        obj : :class:`taniumpy.object_types.base.BaseType`
            * object to save

        Returns
        -------
        obj : :class:`taniumpy.object_types.base.BaseType`
            * saved object
        """
        self._debug_locals(sys._getframe().f_code.co_name, locals())

        clean_keys = ['obj', 'request_body']
        clean_kwargs = pytan.utils.clean_kwargs(kwargs=kwargs, keys=clean_keys)

        request_body = self._create_update_object_body(obj=obj, **clean_kwargs)
        response_body = self._get_response(request_body=request_body, **clean_kwargs)
        obj = taniumpy.BaseType.fromSOAPBody(body=response_body)
        return obj

    def add(self, obj, **kwargs):
        """Creates and sends a AddObject XML Request body from `obj` and parses the response into an appropriate :mod:`taniumpy` object

        Parameters
        ----------
        obj : :class:`taniumpy.object_types.base.BaseType`
            * object to add

        Returns
        -------
        obj : :class:`taniumpy.object_types.base.BaseType`
            * added object
        """
        self._debug_locals(sys._getframe().f_code.co_name, locals())

        clean_keys = ['obj', 'request_body']
        clean_kwargs = pytan.utils.clean_kwargs(kwargs=kwargs, keys=clean_keys)

        request_body = self._create_add_object_body(obj=obj, **clean_kwargs)
        response_body = self._get_response(request_body=request_body, **clean_kwargs)
        obj = taniumpy.BaseType.fromSOAPBody(body=response_body)
        return obj

    def delete(self, obj, **kwargs):
        """Creates and sends a DeleteObject XML Request body from `obj` and parses the response into an appropriate :mod:`taniumpy` object

        Parameters
        ----------
        obj : :class:`taniumpy.object_types.base.BaseType`
            * object to delete

        Returns
        -------
        obj : :class:`taniumpy.object_types.base.BaseType`
            * deleted object
        """
        self._debug_locals(sys._getframe().f_code.co_name, locals())

        clean_keys = ['obj', 'request_body']
        clean_kwargs = pytan.utils.clean_kwargs(kwargs=kwargs, keys=clean_keys)

        request_body = self._create_delete_object_body(obj=obj, **clean_kwargs)
        response_body = self._get_response(request_body=request_body, **clean_kwargs)
        obj = taniumpy.BaseType.fromSOAPBody(body=response_body)
        return obj

    def run_plugin(self, obj, **kwargs):
        """Creates and sends a RunPlugin XML Request body from `obj` and parses the response into an appropriate :mod:`taniumpy` object

        Parameters
        ----------
        obj : :class:`taniumpy.object_types.base.BaseType`
            * object to run

        Returns
        -------
        obj : :class:`taniumpy.object_types.base.BaseType`
            * results from running object
        """
        self._debug_locals(sys._getframe().f_code.co_name, locals())

        clean_keys = ['obj', 'request_body']
        clean_kwargs = pytan.utils.clean_kwargs(kwargs=kwargs, keys=clean_keys)

        request_body = self._create_run_plugin_object_body(obj=obj, **clean_kwargs)
        response_body = self._get_response(request_body=request_body, **clean_kwargs)
        obj = taniumpy.BaseType.fromSOAPBody(body=response_body)
        return obj

    def get_result_info(self, obj, **kwargs):
        """Creates and sends a GetResultInfo XML Request body from `obj` and parses the response into an appropriate :mod:`taniumpy` object

        Parameters
        ----------
        obj : :class:`taniumpy.object_types.base.BaseType`
            * object to get result info for

        Returns
        -------
        obj : :class:`taniumpy.object_types.result_info.ResultInfo`
            * ResultInfo for `obj`
        """
        self._debug_locals(sys._getframe().f_code.co_name, locals())

        clean_keys = ['obj', 'request_body']
        clean_kwargs = pytan.utils.clean_kwargs(kwargs=kwargs, keys=clean_keys)

        request_body = self._create_get_result_info_body(obj=obj, **clean_kwargs)
        response_body = self._get_response(request_body=request_body, **clean_kwargs)

        # parse the ResultXML node into it's own element
        resultxml_text = self._extract_resultxml(response_body=response_body)

        cdata_el = ET.fromstring(resultxml_text)
        obj = taniumpy.ResultInfo.fromSOAPElement(cdata_el)
        obj._RAW_XML = resultxml_text
        return obj

    def get_result_data(self, obj, **kwargs):
        """Creates and sends a GetResultData XML Request body from `obj` and parses the response into an appropriate :mod:`taniumpy` object

        Parameters
        ----------
        obj : :class:`taniumpy.object_types.base.BaseType`
            * object to get result set for

        Returns
        -------
        obj : :class:`taniumpy.object_types.result_set.ResultSet`
            * otherwise, `obj` will be the ResultSet for `obj`
        """
        self._debug_locals(sys._getframe().f_code.co_name, locals())

        clean_keys = ['obj', 'request_body']
        clean_kwargs = pytan.utils.clean_kwargs(kwargs=kwargs, keys=clean_keys)

        request_body = self._create_get_result_data_body(obj=obj, **clean_kwargs)
        response_body = self._get_response(request_body=request_body, **clean_kwargs)

        # parse the ResultXML node into it's own element
        resultxml_text = self._extract_resultxml(response_body=response_body)

        cdata_el = ET.fromstring(resultxml_text)
        obj = taniumpy.ResultSet.fromSOAPElement(cdata_el)
        obj._RAW_XML = resultxml_text
        return obj

    def get_result_data_sse(self, obj, **kwargs):
        """Creates and sends a GetResultData XML Request body that starts a server side export from `obj` and parses the response for an export_id.

        Parameters
        ----------
        obj : :class:`taniumpy.object_types.base.BaseType`
            * object to start server side export

        Returns
        -------
        export_id : str
            * value of export_id element found in response
        """
        self._debug_locals(sys._getframe().f_code.co_name, locals())

        clean_keys = ['obj', 'request_body']
        clean_kwargs = pytan.utils.clean_kwargs(kwargs=kwargs, keys=clean_keys)

        request_body = self._create_get_result_data_body(obj=obj, **clean_kwargs)
        response_body = self._get_response(request_body=request_body, **clean_kwargs)

        # if there is an export_id node, return the contents of that
        export_id = self._regex_body_for_element(
            body=response_body, element='export_id', fail=True,
        )
        return export_id

    def get_server_info(self, port=None, fallback_port=444, **kwargs):
        """Gets the /info.json

        Parameters
        ----------
        port : int, optional
            * default: None
            * port to attempt getting /info.json from, if not specified will use self.port
        fallback_port : int, optional
            * default: 444
            * fallback port to attempt getting /info.json from if `port` fails

        Returns
        -------
        info_dict : dict
            * raw json response converted into python dict
            * 'diags_flat': info.json flattened out into an easier to use structure for python handling
            * 'server_info_pass_msgs': messages about successfully retrieving info.json
            * 'server_info_fail_msgs': messages about failing to retrieve info.json

        See Also
        --------
        :func:`pytan.sessions.Session._flatten_server_info` : method to flatten the dictionary received from info.json into a python friendly format

        Notes
        -----
            * 6.2 /info.json is only available on soap port (default port: 444)
            * 6.5 /info.json is only available on server port (default port: 443)
        """
        self._debug_locals(sys._getframe().f_code.co_name, locals())

        self._check_auth()

        url = self.INFO_RES
        if port is None:
            port = self.port

        req_args = {}
        req_args['port'] = port
        req_args['url'] = url
        req_args['retry_count'] = 0
        req_args['connect_timeout'] = kwargs.get('connect_timeout', self.INFO_CONNECT_TIMEOUT_SEC)
        req_args['response_timeout'] = kwargs.get(
            'response_timeout', self.INFO_RESPONSE_TIMEOUT_SEC
        )
        req_args['pytan_help'] = kwargs.get('pytan_help', '')

        info_body = ''
        server_info_pass_msgs = []
        server_info_fail_msgs = []
        ok_m = "Successfully retrieved server info from {}:{}/{}".format
        bad_m = "Failed to retrieve server info from {}:{}/{}, {}".format
        json_fail_m = "Failed to parse server info from json, error: {}".format
        diags_flat_fail_m = "Failed to flatten server info from json, error: {}".format

        try:
            info_body = self.http_get(**req_args)
            server_info_pass_msgs.append(ok_m(self.host, port, self.INFO_RES))
        except Exception as e:
            self.mylog.debug(bad_m(self.host, port, self.INFO_RES, e))
            server_info_fail_msgs.append(bad_m(self.host, port, self.INFO_RES, e))

        if not info_body:
            req_args['port'] = fallback_port
            try:
                info_body = self.http_post(**req_args)
                server_info_pass_msgs.append(ok_m(self.host, port, self.INFO_RES))
            except Exception as e:
                self.mylog.debug(bad_m(self.host, port, self.INFO_RES, e))
                server_info_fail_msgs.append(bad_m(self.host, port, self.INFO_RES, e))

        try:
            info_dict = json.loads(info_body)
        except Exception as e:
            info_dict = {'info_body_failed_json': info_body}
            server_info_fail_msgs.append(json_fail_m(e))

        try:
            diagnostics = info_dict.get('Diagnostics', [])
            info_dict['diags_flat'] = self._flatten_server_info(structure=diagnostics)
        except Exception as e:
            info_dict['diags_flat'] = {}
            server_info_fail_msgs.append(diags_flat_fail_m(e))

        info_dict['server_info_pass_msgs'] = server_info_pass_msgs
        info_dict['server_info_fail_msgs'] = server_info_fail_msgs
        return info_dict

    def get_server_version(self, **kwargs):
        """Tries to parse the server version from /info.json

        Returns
        -------
        str
            * str containing server version from /info.json
        """
        self._debug_locals(sys._getframe().f_code.co_name, locals())

        if not self._invalid_server_version():
            return self.server_version

        h = "Get the server version via /info.json"
        pytan_help = kwargs.get('pytan_help', h)
        kwargs['pytan_help'] = pytan_help

        server_version = "Unable to determine"

        if not getattr(self, 'server_info', {}):
            self.server_info = self.get_server_info(**kwargs)

        if not getattr(self, 'server_info', {}):
            return server_version

        version = None
        try:
            version = self.server_info['diags_flat']['Settings']['Version']
        except:
            m = "Unable to find Version key in Settings: {}".format
            self.mylog.debug(m(self.server_info['diags_flat']))

        if version:
            server_version = version
        else:
            m = "Unable to find Version key in Settings: {}".format
            self.mylog.debug(m(self.server_info['diags_flat']))

        if server_version:
            self.server_version = str(server_version)

        return server_version

    def get_server_stats(self, **kwargs):
        """Creates a str containing a number of stats gathered from /info.json

        Returns
        -------
        str
            * str containing stats from /info.json

        See Also
        --------
        :data:`pytan.sessions.Session.STATS_LOOP_TARGETS` : list of dict containing stat keys to pull from /info.json
        """
        self._debug_locals(sys._getframe().f_code.co_name, locals())

        try:
            self._check_auth()
        except:
            return "Not yet authenticated!"

        si = self.get_server_info(**kwargs)
        try:
            diags = si['diags_flat']
        except:
            pass

        stats_resolved = [
            self._find_stat_target(target=t, diags=diags) for t in self.STATS_LOOP_TARGETS
        ]
        stats_text = ", ".join(["{}: {}".format(*i.items()[0]) for i in stats_resolved])
        return stats_text

    def enable_stats_loop(self, sleep=None):
        """Enables the stats loop thread, which will print out the results of :func:`pytan.sessions.Session.get_server_stats` every :data:`pytan.sessions.Session.STATS_LOOP_SLEEP_SEC`

        Parameters
        ----------
        sleep : int, optional
            * when enabling the stats loop, update :data:`pytan.sessions.Session.STATS_LOOP_SLEEP_SEC` with `sleep`

        See Also
        --------
        :func:`pytan.sessions.Session._stats_loop` : method started as a thread which checks self.STATS_LOOP_ENABLED before running :func:`pytan.sessions.Session.get_server_stats`
        """
        self._debug_locals(sys._getframe().f_code.co_name, locals())

        self.STATS_LOOP_ENABLED = True
        if isinstance(sleep, int):
            self.STATS_LOOP_SLEEP_SEC = sleep

    def disable_stats_loop(self, sleep=None):
        """Disables the stats loop thread, which will print out the results of :func:`pytan.sessions.Session.get_server_stats` every :data:`pytan.sessions.Session.STATS_LOOP_SLEEP_SEC`

        Parameters
        ----------
        sleep : int, optional
            * when disabling the stats loop, update :data:`pytan.sessions.Session.STATS_LOOP_SLEEP_SEC` with `sleep`

        See Also
        --------
        :func:`pytan.sessions.Session._stats_loop` : method started as a thread which checks self.STATS_LOOP_ENABLED before running :func:`pytan.sessions.Session.get_server_stats`
        """
        self._debug_locals(sys._getframe().f_code.co_name, locals())

        self.STATS_LOOP_ENABLED = False
        if isinstance(sleep, int):
            self.STATS_LOOP_SLEEP_SEC = sleep

    def http_get(self, url, **kwargs):
        """This is an authenticated HTTP GET method. It will always forcibly use the authentication credentials that are stored in the current object when performing an HTTP GET.

        Parameters
        ----------
        url : str
            * url to fetch on the server
        host : str, optional
            * default: self.host
            * host to connect to
        port : int, optional
            * default: self.port
            * port to connect to
        headers : dict, optional
            * default: {}
            * headers to supply as part of GET request
        connect_timeout : int, optional
            * default: self.SOAP_CONNECT_TIMEOUT_SEC
            * timeout in seconds for connection to host
        response_timeout : int, optional
            * default: self.SOAP_RESPONSE_TIMEOUT_SEC
            * timeout in seconds for response from host
        debug : bool, optional
            * default: self.HTTP_DEBUG
            * False: do not print requests debug messages
            * True: print requests debug messages
        auth_retry : bool, optional
            * default: self.HTTP_AUTH_RETRY
            * True: retry authentication with username/password if session_id fails
            * False: throw exception if session_id fails
        retry_count : int, optional
            * default: self.HTTP_RETRY_COUNT
            * number of times to retry the GET request if the server fails to respond properly or in time
        pytan_help : str, optional
            * default: ''
            * help string to add to self.LAST_REQUESTS_RESPONSE.pytan_help

        Returns
        -------
        body : str
            * str containing body of response from server

        See Also
        --------
        :func:`pytan.sessions.Session._http_get` : private method used to perform the actual HTTP GET
        """
        self._debug_locals(sys._getframe().f_code.co_name, locals())

        self._check_auth()

        headers = kwargs.get('headers', {})
        headers = self._replace_auth(headers=headers)

        req_args = {}
        req_args['host'] = kwargs.get('server', self.host)
        req_args['port'] = kwargs.get('port', self.port)
        req_args['url'] = url
        req_args['headers'] = headers
        req_args['connect_timeout'] = kwargs.get('connect_timeout', self.SOAP_CONNECT_TIMEOUT_SEC)
        req_args['response_timeout'] = kwargs.get(
            'response_timeout', self.SOAP_RESPONSE_TIMEOUT_SEC
        )
        req_args['debug'] = kwargs.get('debug', self.HTTP_DEBUG)
        req_args['pytan_help'] = kwargs.get('pytan_help', '')

        auth_retry = kwargs.get('auth_retry', self.HTTP_AUTH_RETRY)
        retry_count = kwargs.get('retry_count', self.HTTP_RETRY_COUNT)

        if not retry_count or type(retry_count) != int:
            retry_count = 0

        current_try = 1

        while True:
            try:
                body = self._http_get(**req_args)
                break
            except pytan.exceptions.AuthorizationError:
                if self._session_id and auth_retry:
                    self._session_id = ''
                    self.authenticate(**kwargs)
                    body = self.http_get(auth_retry=False, **kwargs)
                else:
                    raise
            except Exception as e:
                if retry_count == 0:
                    raise
                m = "http_get failed on attempt {} out of {}: {}".format
                self.mylog.debug(m(current_try, retry_count, e))
                if current_try == retry_count:
                    self.mylog.warning(m(current_try, retry_count, e))
                    raise
                current_try += 1

        return body

    def http_post(self, **kwargs):
        """This is an authenticated HTTP POST method. It will always forcibly use the authentication credentials that are stored in the current object when performing an HTTP POST.

        Parameters
        ----------
        url : str, optional
            * default: self.SOAP_RES
            * url to fetch on the server
        host : str, optional
            * default: self.host
            * host to connect to
        port : int, optional
            * default: self.port
            * port to connect to
        headers : dict, optional
            * default: {}
            * headers to supply as part of POST request
        body : str, optional
            * default: ''
            * body to send as part of the POST request
        connect_timeout : int, optional
            * default: self.SOAP_CONNECT_TIMEOUT_SEC
            * timeout in seconds for connection to host
        response_timeout : int, optional
            * default: self.SOAP_RESPONSE_TIMEOUT_SEC
            * timeout in seconds for response from host
        debug : bool, optional
            * default: self.HTTP_DEBUG
            * False: do not print requests debug messages
            * True: print requests debug messages
        auth_retry : bool, optional
            * default: self.HTTP_AUTH_RETRY
            * True: retry authentication with username/password if session_id fails
            * False: throw exception if session_id fails
        retry_count : int, optional
            * default: self.HTTP_RETRY_COUNT
            * number of times to retry the POST request if the server fails to respond properly or in time
        pytan_help : str, optional
            * default: ''
            * help string to add to self.LAST_REQUESTS_RESPONSE.pytan_help

        Returns
        -------
        body : str
            * str containing body of response from server

        See Also
        --------
        :func:`pytan.sessions.Session._http_post` : private method used to perform the actual HTTP POST
        """
        self._debug_locals(sys._getframe().f_code.co_name, locals())

        self._check_auth()

        headers = kwargs.get('headers', {})
        headers = self._replace_auth(headers=headers)

        req_args = {}
        req_args['host'] = kwargs.get('server', self.host)
        req_args['port'] = kwargs.get('port', self.port)
        req_args['url'] = kwargs.get('url', self.SOAP_RES)
        req_args['headers'] = headers
        req_args['body'] = kwargs.get('body', None)
        req_args['connect_timeout'] = kwargs.get('connect_timeout', self.SOAP_CONNECT_TIMEOUT_SEC)
        req_args['response_timeout'] = kwargs.get(
            'response_timeout', self.SOAP_RESPONSE_TIMEOUT_SEC
        )
        req_args['debug'] = kwargs.get('debug', self.HTTP_DEBUG)
        req_args['pytan_help'] = kwargs.get('pytan_help', '')

        auth_retry = kwargs.get('auth_retry', self.HTTP_AUTH_RETRY)
        retry_count = kwargs.get('retry_count', self.HTTP_RETRY_COUNT)

        if not retry_count or type(retry_count) != int:
            retry_count = 0

        current_try = 1

        while True:
            try:
                body = self._http_post(**req_args)
                break
            except pytan.exceptions.AuthorizationError:
                if self._session_id and auth_retry:
                    self._session_id = ''
                    self.authenticate()
                    body = self.http_post(auth_retry=False, **kwargs)
                else:
                    raise
            except Exception as e:
                if retry_count == 0:
                    raise
                m = "http_post failed on attempt {} out of {}: {}".format
                self.mylog.debug(m(current_try, retry_count, e))
                if current_try == retry_count:
                    self.mylog.warning(m(current_try, retry_count, e))
                    raise
                current_try += 1

        return body

    def _http_get(self, host, port, url, headers=None, connect_timeout=15,
                  response_timeout=180, debug=False, pytan_help='', **kwargs):
        """This is an HTTP GET method that utilizes the :mod:`requests` package.

        Parameters
        ----------
        host : str
            * host to connect to
        port : int
            * port to connect to
        url : str
            * url to fetch on the server
        headers : dict, optional
            * default: None
            * headers to supply as part of POST request
        connect_timeout : int, optional
            * default: 15
            * timeout in seconds for connection to host
        response_timeout : int, optional
            * default: 180
            * timeout in seconds for response from host
        debug : bool, optional
            * default: False
            * False: do not print requests debug messages
            * True: print requests debug messages
        pytan_help : str, optional
            * default: ''
            * help string to add to self.LAST_REQUESTS_RESPONSE.pytan_help
        perform_xml_clean : bool, optional
            * default: False
            * False: Do not run the response_body through an XML cleaner
            * True: Run the response_body through an XML cleaner before returning it
        clean_restricted : bool, optional
            * default: True
            * True: When XML cleaning the response_body, remove restricted characters as well as invalid characters
            * False: When XML cleaning the response_body, remove only invalid characters
        log_clean_messages : bool, optional
            * default: True
            * True: When XML cleaning the response_body, enable logging messages about invalid/restricted matches
            * False: When XML cleaning the response_body, disable logging messages about invalid/restricted matches
        log_bad_characters : bool, optional
            * default: False
            * False: When XML cleaning the response_body, disable logging messages about the actual characters that were invalid/restricted
            * True: When XML cleaning the response_body, enable logging messages about the actual characters that were invalid/restricted

        Returns
        -------
        body : str
            * str containing body of response from server
        """
        self._debug_locals(sys._getframe().f_code.co_name, locals())

        full_url = self._full_url(host=host, port=port, url=url)
        cleaned_headers = self._clean_headers(headers=headers)

        self.httplog.debug("HTTP request: GET to {}".format(full_url))
        self.httplog.debug("HTTP request: headers: {}".format(cleaned_headers))

        req_args = {}
        req_args['headers'] = headers
        req_args['timeout'] = (connect_timeout, response_timeout)

        try:
            response = self.REQUESTS_SESSION.get(full_url, **req_args)
            response.pytan_help = pytan_help
        except Exception as e:
            m = "HTTP response: GET request to {!r} failed: {}".format
            raise pytan.exceptions.HttpError(m(full_url, e))

        self.LAST_REQUESTS_RESPONSE = response
        if self.RECORD_ALL_REQUESTS:
            self.ALL_REQUESTS_RESPONSES.append(response)

        response_body = response.text
        response_headers = response.headers

        perform_xml_clean = kwargs.get('perform_xml_clean', False)
        if perform_xml_clean:
            xml_clean_args = {}
            xml_clean_args['s'] = response_body
            xml_clean_args['clean_restricted'] = kwargs.get('clean_restricted', True)
            xml_clean_args['log_clean_messages'] = kwargs.get('log_clean_messages', True)
            xml_clean_args['log_bad_characters'] = kwargs.get('log_bad_characters', False)
            response_body = xml_cleaner(**xml_clean_args)

        m = "HTTP response: from {!r} len:{}, status:{} {}, body type: {}".format

        self.httplog.debug(m(
            full_url,
            len(response_body),
            response.status_code,
            response.reason,
            type(response_body),
        ))

        self.httplog.debug("HTTP response: headers: {}".format(response_headers))

        if response.status_code in self.AUTH_FAIL_CODES:
            m = "HTTP response: GET request to {!r} returned code: {}, body: {}".format
            raise pytan.exceptions.AuthorizationError(m(
                full_url, response.status_code, response_body))

        if not response.ok:
            m = "HTTP response: GET request to {!r} returned code: {}, body: {}".format
            raise pytan.exceptions.HttpError(m(full_url, response.status_code, response_body))

        self.bodyhttplog.debug("HTTP response: body:\n{}".format(response_body))

        return response_body

    def _http_post(self, host, port, url, body=None, headers=None, connect_timeout=15,
                   response_timeout=180, debug=False, pytan_help='', **kwargs):
        """This is an HTTP POST method that utilizes the :mod:`requests` package.

        Parameters
        ----------
        host : str
            * host to connect to
        port : int
            * port to connect to
        url : str
            * url to fetch on the server
        body : str, optional
            * default: None
            * body to send as part of the POST request
        headers : dict, optional
            * default: None
            * headers to supply as part of POST request
        connect_timeout : int, optional
            * default: 15
            * timeout in seconds for connection to host
        response_timeout : int, optional
            * default: 180
            * timeout in seconds for response from host
        debug : bool, optional
            * default: False
            * False: do not print requests debug messages
            * True: print requests debug messages
        pytan_help : str, optional
            * default: ''
            * help string to add to self.LAST_REQUESTS_RESPONSE.pytan_help
        perform_xml_clean : bool, optional
            * default: True
            * True: Run the response_body through an XML cleaner before returning it
            * False: Do not run the response_body through an XML cleaner
        clean_restricted : bool, optional
            * default: True
            * True: When XML cleaning the response_body, remove restricted characters as well as invalid characters
            * False: When XML cleaning the response_body, remove only invalid characters
        log_clean_messages : bool, optional
            * default: True
            * True: When XML cleaning the response_body, enable logging messages about invalid/restricted matches
            * False: When XML cleaning the response_body, disable logging messages about invalid/restricted matches
        log_bad_characters : bool, optional
            * default: False
            * False: When XML cleaning the response_body, disable logging messages about the actual characters that were invalid/restricted
            * True: When XML cleaning the response_body, enable logging messages about the actual characters that were invalid/restricted

        Returns
        -------
        body : str
            * str containing body of response from server

        See Also
        --------
        :func:`pytan.xml_clean.xml_cleaner` : function to remove invalid/bad characters from XML responses
        """
        self._debug_locals(sys._getframe().f_code.co_name, locals())

        full_url = self._full_url(host=host, port=port, url=url)
        cleaned_headers = self._clean_headers(headers=headers)
        self.httplog.debug("HTTP request: POST to {}".format(full_url))
        self.httplog.debug("HTTP request: headers: {}".format(cleaned_headers))

        if not body:
            print_body = ''
        else:
            print_body = '\n{}'.format(body)
        self.bodyhttplog.debug("HTTP request: body:{}".format(print_body))

        req_args = {}
        req_args['headers'] = headers
        req_args['data'] = body
        req_args['timeout'] = (connect_timeout, response_timeout)

        try:
            response = self.REQUESTS_SESSION.post(full_url, **req_args)
            response.pytan_help = pytan_help
        except Exception as e:
            m = "HTTP response: POST request to {!r} failed: {}".format
            raise pytan.exceptions.HttpError(m(full_url, e))

        self.LAST_REQUESTS_RESPONSE = response
        if self.RECORD_ALL_REQUESTS:
            self.ALL_REQUESTS_RESPONSES.append(response)

        response_body = response.text
        response_headers = response.headers

        perform_xml_clean = kwargs.get('perform_xml_clean', True)
        if perform_xml_clean:
            xml_clean_args = {}
            xml_clean_args['s'] = response_body
            xml_clean_args['clean_restricted'] = kwargs.get('clean_restricted', True)
            xml_clean_args['log_clean_messages'] = kwargs.get('log_clean_messages', True)
            xml_clean_args['log_bad_characters'] = kwargs.get('log_bad_characters', False)
            response_body = xml_cleaner(**xml_clean_args)

        m = "HTTP response: from {!r} len:{}, status:{} {}, body type: {}".format
        self.httplog.debug(m(
            full_url,
            len(response_body),
            response.status_code,
            response.reason,
            type(response_body),
        ))

        self.httplog.debug("HTTP response: headers: {}".format(response_headers))

        if response.status_code in self.AUTH_FAIL_CODES:
            m = "HTTP response: POST request to {!r} returned code: {}, body: {}".format
            m = m(full_url, response.status_code, response_body)
            raise pytan.exceptions.AuthorizationError(m)

        if not response_body:
            m = "HTTP response: POST request to {!r} returned empty body".format
            raise pytan.exceptions.HttpError(m(full_url))

        if not response.ok:
            m = "HTTP response: POST request to {!r} returned code: {}, body: {}".format
            raise pytan.exceptions.HttpError(m(full_url, response.status_code, response_body))

        self.bodyhttplog.debug("HTTP response: body:\n{}".format(response_body))

        return response_body

    def _replace_auth(self, headers):
        """Utility method for removing username, password, and/or session from supplied headers and replacing them with the current objects session or username and password

        Parameters
        ----------
        headers : dict
            * dict of key/value pairs for a set of headers for a given request

        Returns
        -------
        headers : dict
            * dict of key/value pairs for a set of headers for a given request
        """
        self._debug_locals(sys._getframe().f_code.co_name, locals())

        for k in dict(headers):
            if k in ['username', 'password', 'session']:
                self.authlog.debug("Removing header {!r}".format(k))
                headers.pop(k)

        if self._session_id:
            headers['session'] = self._session_id
            self.authlog.debug("Using session ID for authentication headers")

        elif self._username and self._password:
            headers['username'] = b64encode(self._username)
            headers['password'] = b64encode(self._password)
            self.authlog.debug("Using Username/Password for authentication headers")
        return headers

    def _full_url(self, url, **kwargs):
        """Utility method for constructing a full url

        Parameters
        ----------
        url : str
            * url to use in string
        host : str, optional
            * default: self.host
            * hostname/IP address to use in string
        port : str, optional
            * default: self.port
            * port to use in string

        Returns
        -------
        full_url : str
            * full url in the form of https://$host:$port/$url
        """
        self._debug_locals(sys._getframe().f_code.co_name, locals())

        host = kwargs.get('host', self.host)
        port = kwargs.get('port', self.port)
        full_url = "https://{0}:{1}/{2}".format(host, port, url)
        return full_url

    def _clean_headers(self, headers=None):
        """Utility method for getting the headers for the current request, combining them with the session headers used for every request, and obfuscating the value of any 'password' header.

        Parameters
        ----------
        headers : dict
            * dict of key/value pairs for a set of headers for a given request

        Returns
        -------
        headers : dict
            * dict of key/value pairs for a set of cleaned headers for a given request
        """
        self._debug_locals(sys._getframe().f_code.co_name, locals())

        clean_headers = dict(headers or {})
        return_headers = {}
        return_headers.update(self.REQUESTS_SESSION.headers)
        return_headers.update(clean_headers)
        if 'password' in return_headers:
            return_headers['password'] = '**PASSWORD**'

        return return_headers

    def _start_stats_thread(self, **kwargs):
        """Utility method starting the :func:`pytan.sessions.Session._stats_loop` method in a threaded daemon"""
        self._debug_locals(sys._getframe().f_code.co_name, locals())

        stats_thread = threading.Thread(target=self._stats_loop, args=(), kwargs=kwargs)
        stats_thread.daemon = True
        stats_thread.start()

    def platform_is_6_5(self, **kwargs):
        """Check to see if self.server_version is less than 6.5

        Returns
        -------
        is6_5 : bool
            * True if self.force_server_version is greater than or equal to 6.5
            * True if self.server_version is greater than or equal to 6.5
            * False if self.server_version is less than 6.5
        """
        self._debug_locals(sys._getframe().f_code.co_name, locals())

        if self.force_server_version:
            if self.force_server_version >= '6.5':
                return True
            else:
                return False

        if self._invalid_server_version():
            # server version is not valid, force a refresh right now
            self.get_server_version(**kwargs)

        if self._invalid_server_version():
            # server version is STILL invalid, we will assume its 6.2 since port 444 may be
            # inaccessible
            return False

        is6_5 = self.server_version >= '6.5'
        return is6_5

    def _stats_loop(self, **kwargs):
        """Utility method for logging server stats via :func:`pytan.sessions.Session.get_server_stats` every self.STATS_LOOP_SLEEP_SEC"""
        self._debug_locals(sys._getframe().f_code.co_name, locals())

        while True:
            if self.STATS_LOOP_ENABLED:
                server_stats = self.get_server_stats(**kwargs)
                self.statslog.warning(server_stats)
            time.sleep(self.STATS_LOOP_SLEEP_SEC)

    def _flatten_server_info(self, structure):
        """Utility method for flattening the JSON structure for info.json into a more python usable format

        Parameters
        ----------
        structure
            * dict/tuple/list to flatten

        Returns
        -------
        flattened
            * the dict/tuple/list flattened out
        """
        # self._debug_locals(sys._getframe().f_code.co_name, locals())

        flattened = structure
        if isinstance(structure, dict):
            for k, v in flattened.iteritems():
                flattened[k] = self._flatten_server_info(structure=v)
        elif isinstance(structure, (tuple, list)):
            if all([isinstance(x, dict) for x in structure]):
                flattened = {}
                [flattened.update(self._flatten_server_info(structure=i)) for i in structure]
        return flattened

    def _get_percentage(self, part, whole):
        """Utility method for getting percentage of part out of whole

        Parameters
        ----------
        part: int, float
        whole: int, float

        Returns
        -------
        str : the percentage of part out of whole in 2 decimal places
        """
        self._debug_locals(sys._getframe().f_code.co_name, locals())

        f = 100 * float(part) / float(whole)
        return "{0:.2f}%".format(f)

    def _find_stat_target(self, target, diags):
        """Utility method for finding a target in info.json and returning the value, optionally performing a percentage calculation on two values if the target[0] starts with percentage(

        Parameters
        ----------
        target : list
            * index0 : label : human friendly name to refer to search_path
            * index1 : search_path : / seperated search path to find a given value from info.json
        diags : dict
            * flattened dictionary of info.json diagnostics

        Returns
        -------
        dict
            * label : same as provided in `target` index0 (label)
            * result : value resolved from :func:`pytan.sessions.Session._resolve_stat_target` for `target` index1 (search_path)
        """
        self._debug_locals(sys._getframe().f_code.co_name, locals())

        try:
            label, search_path = target.items()[0]
        except Exception as e:
            label = "Parse Failure"
            result = "Unable to parse stat target: {}, exception: {}".format(target, e)
            return {label: result}

        if search_path.startswith('percentage('):
            points = search_path.lstrip('percentage(').rstrip(')')
            points = [
                self._resolve_stat_target(search_path=p, diags=diags) for p in points.split(',')
            ]
            try:
                result = self._get_percentage(part=points[0], whole=points[1])
            except:
                result = ', '.join(points)
        else:
            result = self._resolve_stat_target(search_path=search_path, diags=diags)
        return {label: result}

    def _resolve_stat_target(self, search_path, diags):
        """Utility method for resolving the value of search_path in info.json and returning the value

        Parameters
        ----------
        search_path : str
            * / seperated search path to find a given value from info.json
        diags : dict
            * flattened dictionary of info.json diagnostics

        Returns
        -------
        str
            * value resolved from `diags` for `search_path`
        """
        self._debug_locals(sys._getframe().f_code.co_name, locals())

        try:
            for i in search_path.split('/'):
                diags = diags.get(i)
        except Exception as e:
            return "Unable to find diagnostic: {}, exception: {}".format(search_path, e)
        return diags

    def _build_body(self, command, object_list, log_options=False, **kwargs):
        """Utility method for building an XML Request Body

        Parameters
        ----------
        command : str
            * text to use in command node when building template
        object_list : str
            * XML string to use in object list node when building template
        kwargs : dict, optional
            * any number of attributes that can be set via :class:`taniumpy.object_types.options.Options` that control the servers response.
        log_options : bool, optional
            * default: False
            * False: Do not print messages setting attributes in Options from keys in kwargs
            * True: Print messages setting attributes in Options from keys in kwargs

        Returns
        -------
        body : str
            * The XML request body created from the string.template self.REQUEST_BODY_TEMPLATE
        """
        self._debug_locals(sys._getframe().f_code.co_name, locals())

        options_obj = taniumpy.Options()

        for k, v in kwargs.iteritems():
            if hasattr(options_obj, k):
                if log_options:
                    m = "Setting Options attribute {!r} to value {!r}".format
                    self.mylog.debug(m(k, v))
                setattr(options_obj, k, v)
            else:
                if log_options:
                    m = "Ignoring argument {!r} for options list, not a valid attribute".format
                    self.mylog.debug(m(k))

        options = options_obj.toSOAPBody(minimal=True)
        body_template = string.Template(self.REQUEST_BODY_BASE)
        body = body_template.substitute(command=command, object_list=object_list, options=options)
        return body

    def _create_run_plugin_object_body(self, obj, **kwargs):
        """Utility method for building an XML Request Body to run a plugin

        Parameters
        ----------
        obj : :class:`taniumpy.object_types.base.BaseType`
            * object to convert into XML
        kwargs : dict, optional
            * any number of attributes that can be set via :class:`taniumpy.object_types.options.Options` that control the servers response.

        Returns
        -------
        obj_body : str
            * The XML request body created from :func:`pytan.sessions.Session._build_body`
        """
        self._debug_locals(sys._getframe().f_code.co_name, locals())

        clean_keys = ['command', 'object_list']
        clean_kwargs = pytan.utils.clean_kwargs(kwargs=kwargs, keys=clean_keys)

        object_list = obj.toSOAPBody(minimal=True)
        cmd = 'RunPlugin'
        obj_body = self._build_body(command=cmd, object_list=object_list, **clean_kwargs)
        return obj_body

    def _create_add_object_body(self, obj, **kwargs):
        """Utility method for building an XML Request Body to add an object

        Parameters
        ----------
        obj : :class:`taniumpy.object_types.base.BaseType`
            * object to convert into XML
        kwargs : dict, optional
            * any number of attributes that can be set via :class:`taniumpy.object_types.options.Options` that control the servers response.

        Returns
        -------
        obj_body : str
            * The XML request body created from :func:`pytan.sessions.Session._build_body`
        """
        self._debug_locals(sys._getframe().f_code.co_name, locals())

        clean_keys = ['command', 'object_list']
        clean_kwargs = pytan.utils.clean_kwargs(kwargs=kwargs, keys=clean_keys)

        object_list = obj.toSOAPBody(minimal=True)
        cmd = 'AddObject'
        obj_body = self._build_body(command=cmd, object_list=object_list, **clean_kwargs)
        return obj_body

    def _create_delete_object_body(self, obj, **kwargs):
        """Utility method for building an XML Request Body to delete an object

        Parameters
        ----------
        obj : :class:`taniumpy.object_types.base.BaseType`
            * object to convert into XML
        kwargs : dict, optional
            * any number of attributes that can be set via :class:`taniumpy.object_types.options.Options` that control the servers response.

        Returns
        -------
        obj_body : str
            * The XML request body created from :func:`pytan.sessions.Session._build_body`
        """
        self._debug_locals(sys._getframe().f_code.co_name, locals())

        clean_keys = ['command', 'object_list']
        clean_kwargs = pytan.utils.clean_kwargs(kwargs=kwargs, keys=clean_keys)

        object_list = obj.toSOAPBody(minimal=True)
        cmd = 'DeleteObject'
        obj_body = self._build_body(command=cmd, object_list=object_list, **clean_kwargs)
        return obj_body

    def _create_get_result_info_body(self, obj, **kwargs):
        """Utility method for building an XML Request Body to get result info for an object

        Parameters
        ----------
        obj : :class:`taniumpy.object_types.base.BaseType`
            * object to convert into XML
        kwargs : dict, optional
            * any number of attributes that can be set via :class:`taniumpy.object_types.options.Options` that control the servers response.

        Returns
        -------
        obj_body : str
            * The XML request body created from :func:`pytan.sessions.Session._build_body`
        """
        self._debug_locals(sys._getframe().f_code.co_name, locals())

        clean_keys = ['command', 'object_list']
        clean_kwargs = pytan.utils.clean_kwargs(kwargs=kwargs, keys=clean_keys)

        object_list = obj.toSOAPBody(minimal=True)
        cmd = 'GetResultInfo'
        obj_body = self._build_body(command=cmd, object_list=object_list, **clean_kwargs)
        return obj_body

    def _create_get_result_data_body(self, obj, **kwargs):
        """Utility method for building an XML Request Body to get result data for an object

        Parameters
        ----------
        obj : :class:`taniumpy.object_types.base.BaseType`
            * object to convert into XML
        kwargs : dict, optional
            * any number of attributes that can be set via :class:`taniumpy.object_types.options.Options` that control the servers response.

        Returns
        -------
        obj_body : str
            * The XML request body created from :func:`pytan.sessions.Session._build_body`
        """
        self._debug_locals(sys._getframe().f_code.co_name, locals())

        clean_keys = ['command', 'object_list']
        clean_kwargs = pytan.utils.clean_kwargs(kwargs=kwargs, keys=clean_keys)

        object_list = obj.toSOAPBody(minimal=True)
        cmd = 'GetResultData'
        obj_body = self._build_body(command=cmd, object_list=object_list, **clean_kwargs)
        return obj_body

    def _create_get_object_body(self, obj, **kwargs):
        """Utility method for building an XML Request Body to get an object

        Parameters
        ----------
        obj : :class:`taniumpy.object_types.base.BaseType`
            * object to convert into XML
        kwargs : dict, optional
            * any number of attributes that can be set via :class:`taniumpy.object_types.options.Options` that control the servers response.

        Returns
        -------
        obj_body : str
            * The XML request body created from :func:`pytan.sessions.Session._build_body`
        """
        self._debug_locals(sys._getframe().f_code.co_name, locals())

        clean_keys = ['command', 'object_list']
        clean_kwargs = pytan.utils.clean_kwargs(kwargs=kwargs, keys=clean_keys)

        if isinstance(obj, taniumpy.BaseType):
            object_list = obj.toSOAPBody(minimal=True)
        else:
            object_list = '<{}/>'.format(obj._soap_tag)

        cmd = 'GetObject'
        obj_body = self._build_body(command=cmd, object_list=object_list, **clean_kwargs)
        return obj_body

    def _create_update_object_body(self, obj, **kwargs):
        """Utility method for building an XML Request Body to update an object

        Parameters
        ----------
        obj : :class:`taniumpy.object_types.base.BaseType`
            * object to convert into XML
        kwargs : dict, optional
            * any number of attributes that can be set via :class:`taniumpy.object_types.options.Options` that control the servers response.

        Returns
        -------
        obj_body : str
            * The XML request body created from :func:`pytan.sessions.Session._build_body`
        """
        self._debug_locals(sys._getframe().f_code.co_name, locals())

        clean_keys = ['command', 'object_list']
        clean_kwargs = pytan.utils.clean_kwargs(kwargs=kwargs, keys=clean_keys)

        object_list = obj.toSOAPBody(minimal=True)
        cmd = 'UpdateObject'
        obj_body = self._build_body(command=cmd, object_list=object_list, **clean_kwargs)
        return obj_body

    def _check_auth(self):
        """Utility method to check if authentication has been done yet, and throw an exception if not """
        self._debug_locals(sys._getframe().f_code.co_name, locals())

        if not self.is_auth:
            class_name = self.__class__.__name__
            err = "Not yet authenticated, use {}.authenticate()!".format
            raise pytan.exceptions.AuthorizationError(err(class_name))

    def _regex_body_for_element(self, body, element, fail=True):
        """Utility method to use a regex to get an element from an XML body

        Parameters
        ----------
        body : str
            * XML to search
        element : str
            * element name to search for in body
        fail : bool, optional
            * default: True
            * True: throw exception if unable to find any matches for `regex` in `body`
            * False do not throw exception if unable to find any matches for `regex` in `body`

        Returns
        -------
        ret : str
            * The first value that matches the regex ELEMENT_RE_TXT with element

        Notes
        -----
            * Using regex is WAY faster than ElementTree chewing the body in and out, this matters a LOT on LARGE return bodies
        """
        self._debug_locals(sys._getframe().f_code.co_name, locals())

        regex_txt = self.ELEMENT_RE_TXT.format(element)
        regex = re.compile(regex_txt, re.IGNORECASE | re.DOTALL)

        ret = regex.search(body)

        if not ret and fail:
            m = "Unable to find {} in body: {}".format
            raise Exception(m(regex.pattern, body))
        else:
            ret = str(ret.groups()[0].strip())

        m = "Value of element '{}': '{}' (using pattern: '{}'".format
        self.mylog.debug(m(element, ret, regex.pattern))
        return ret

    def _extract_resultxml(self, response_body):
        """Utility method to get the 'ResultXML' element from an XML body

        Parameters
        ----------
        response_body : str
            * XML body to search for the 'ResultXML' element in

        Returns
        -------
        ret : str of ResultXML element
            * str if 'export_id' element found in XML
        """
        self._debug_locals(sys._getframe().f_code.co_name, locals())

        el = ET.fromstring(response_body)

        # find the ResultXML node
        resultxml_el = el.find('.//ResultXML')

        if resultxml_el is None:
            m = "Unable to find ResultXML element in XML response: {}".format
            raise pytan.exceptions.AuthorizationError(m(response_body))

        resultxml_text = resultxml_el.text

        if not resultxml_text:
            m = "Empty ResultXML element in XML response: {}".format
            raise pytan.exceptions.AuthorizationError(m(response_body))

        return resultxml_text

    def _get_response(self, request_body, **kwargs):
        """This is a wrapper around :func:`pytan.sessions.Session.http_post` for SOAP XML requests and responses.

        This method will update self.session_id if the response contains a different session_id than what is currently in this object.

        Parameters
        ----------
        request_body : str
            * the XML request body to send to the server
        connect_timeout: int, optional
            * default: self.SOAP_CONNECT_TIMEOUT_SEC
            * timeout in seconds for connection to host
        response_timeout: int, optional
            * default: self.SOAP_RESPONSE_TIMEOUT_SEC
            * timeout in seconds for response from host
        retry_auth: bool, optional
            * default: True
            * True: retry authentication with username/password if session_id fails
            * False: throw exception if session_id fails
        retry_count: int, optional
            * number of times to retry the request if the server fails to respond properly or in time
        pytan_help : str, optional
            * default: ''
            * help string to add to self.LAST_REQUESTS_RESPONSE.pytan_help

        Returns
        -------
        body : str
            * str containing body of response from server

        See Also
        --------
        :func:`pytan.sessions.Session.http_post` : wrapper method used to perform the HTTP POST
        """
        self._debug_locals(sys._getframe().f_code.co_name, locals())

        retry_auth = kwargs.get('retry_auth', True)

        self._check_auth()

        self.LAST_RESPONSE_INFO = {}

        request_command = self._regex_body_for_element(
            body=request_body, element='command', fail=True,
        )

        self.LAST_RESPONSE_INFO['request_command'] = request_command

        req_args = {}
        req_args['body'] = request_body
        req_args['headers'] = dict(self.SOAP_REQUEST_HEADERS)
        req_args['connect_timeout'] = kwargs.get('connect_timeout', self.SOAP_CONNECT_TIMEOUT_SEC)
        req_args['response_timeout'] = kwargs.get(
            'response_timeout', self.SOAP_RESPONSE_TIMEOUT_SEC
        )
        req_args['pytan_help'] = kwargs.get('pytan_help', '')

        if 'retry_count' in kwargs:
            req_args['retry_count'] = kwargs['retry_count']

        self.LAST_RESPONSE_INFO['request_args'] = req_args

        sent = datetime.utcnow()
        self.LAST_RESPONSE_INFO['sent'] = sent

        response_body = self.http_post(**req_args)

        received = datetime.utcnow()
        self.LAST_RESPONSE_INFO['received'] = received

        elapsed = received - sent
        self.LAST_RESPONSE_INFO['elapsed'] = elapsed

        # m = "HTTP Response: Timing info -- SENT: {}, RECEIVED: {}, ELAPSED: {}".format
        # self.mylog.debug(m(sent, received, elapsed))

        response_command = self._regex_body_for_element(
            body=response_body, element='command', fail=True,
        )

        self.LAST_RESPONSE_INFO['response_command'] = response_command

        if 'forbidden' in response_command.lower():
            if retry_auth:
                m = "Last request was denied, re-authenticating with user/pass".format
                self.authlog.debug(m())
                # we may have hit the 5 minute expiration for session_id, empty out session ID,
                # re-authenticate, then retry request
                self._session_id = ''
                self.authenticate(**kwargs)

                # re-issue the request
                kwargs['retry_auth'] = False
                response_body = self._get_response(request_body=request_body, **kwargs)
            else:
                m = "Access denied after re-authenticating! Server response: {}".format
                raise pytan.exceptions.AuthorizationError(m(response_command))

        elif response_command != request_command:
            for p in self.BAD_RESPONSE_CMD_PRUNES:
                response_command = response_command.replace(p, '').strip()
            m = "Response command {} does not match request command {}".format
            raise pytan.exceptions.BadResponseError(m(response_command, request_command))

        # update session_id, in case new one issued
        self.session_id = self._regex_body_for_element(
            body=response_body, element='session', fail=True,
        )

        # check to see if server_version set in response (6.5+ only)
        if self._invalid_server_version():
            server_version = self._regex_body_for_element(
                body=response_body, element='server_version', fail=False,
            )
            if server_version and self.server_version != server_version:
                self.server_version = server_version

        return response_body

    def _invalid_server_version(self):
        """Utility method to find out if self.server_version is valid or not"""
        self._debug_locals(sys._getframe().f_code.co_name, locals())

        current_server_version = getattr(self, 'server_version', '')
        if current_server_version in self.BAD_SERVER_VERSIONS:
            return True
        return False

    def _debug_locals(self, fname, flocals):
        """Method to print out locals for a function if self.DEBUG_METHOD_LOCALS is True"""
        if getattr(self, 'DEBUG_METHOD_LOCALS', False):
            m = "Local variables for {}.{}:\n{}".format
            self.methodlog.debug(m(self.__class__.__name__, fname, pprint.pformat(flocals)))
