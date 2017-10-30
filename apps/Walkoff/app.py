import logging
from apps import App, action
import requests
from requests.exceptions import Timeout
import json
from core.config.paths import certificate_path
import time

logger = logging.getLogger(__name__)


class Unauthorized(Exception):
    pass


class UnknownResponse(Exception):
    pass


class NotConnected(Exception):
    pass


DEFAULT_TIMEOUT = 2


class Walkoff(App):
    def __init__(self, name=None, device=None):
        App.__init__(self, name, device)
        self.is_connected = False
        self.headers = None
        self.refresh_token = None
        self.username = self.device_fields['username']
        self.walkoff_address = self.device_fields['ip']
        port = self.device_fields['port']
        if port:
            self.walkoff_address += ':{}'.format(port)
        self.is_https = self.walkoff_address.startswith('https')

    @action
    def connect(self, timeout=DEFAULT_TIMEOUT):
        try:
            response = self._request('post', '/api/auth', timeout,
                                     data=dict(username=self.username,
                                               password=self.device.get_encrypted_field('password')))
        except Timeout:
            return 'Connection timed out', 'TimedOut'

        status_code = response.status_code
        if status_code == 404:
            return 'Could not locate Walkoff instance', 'WalkoffNotFound'
        elif status_code == 401:
            return 'Invalid login', 'AuthenticationError'
        elif status_code == 201:
            response = response.json()
            self.refresh_token = response['refresh_token']
            self.reset_authorization(response['access_token'])
            self.is_connected = True
            return 'Success'
        else:
            return 'Unknown response {}'.format(status_code), 'UnknownResponse'

    @action
    def disconnect(self, timeout=DEFAULT_TIMEOUT):
        if self.is_connected:
            try:
                self._request('post', '/api/auth/logout', timeout, headers=self.headers,
                              data=dict(refresh_token=self.refresh_token))
                return 'Success'
            except Timeout:
                return 'Connection timed out', 'TimedOut'
        else:
            return 'Not connected to Walkoff', 'NotConnected'

    @action
    def is_connected(self):
        return self.is_connected

    @action
    def get_all_workflows(self, timeout=DEFAULT_TIMEOUT):
        return self.standard_request('get', '/api/playbooks', timeout, headers=self.headers)

    @action
    def get_workflow_uid(self, playbook_name, workflow_name, timeout=DEFAULT_TIMEOUT):
        try:
            response = self.request_with_refresh('get', '/api/playbooks', timeout, headers=self.headers)
        except Timeout:
            return 'Connection timed out', 'TimedOut'
        except Unauthorized:
            return 'Unauthorized credentials', 'Unauthorized'
        except NotConnected:
            return 'Not connected to Walkoff', 'NotConnected'
        except UnknownResponse:
            return 'Unknown error occurred', 'UnknownResponse'
        else:
            response = response.json()
            playbook = next((playbook for playbook in response if playbook['name'] == playbook_name), None)
            if playbook is None:
                return 'Playbook not found', 'WorkflowNotFound'
            workflow = next((workflow for workflow in playbook['workflows'] if workflow['name'] == workflow_name), None)
            if workflow is None:
                return 'Workflow not found', 'WorkflowNotFound'
            else:
                return workflow['uid']

    @action
    def trigger(self, names=None, inputs=None, data=None, tags=None, timeout=DEFAULT_TIMEOUT):
        trigger_data = {}
        if names:
            trigger_data['names'] = names
        if inputs:
            trigger_data['inputs'] = inputs
        if data:
            trigger_data['data'] = data
        if tags:
            trigger_data['tags'] = tags

        return self.standard_request('post', '/api/triggers/execute', timeout, headers=self.headers, data=data)

    @action
    def get_workflow_results(self, timeout=DEFAULT_TIMEOUT):
        return self.standard_request('get', '/api/workflowresults', timeout, headers=self.headers)

    @action
    def wait_for_workflow_completion(self, execution_uid, timeout=60*5, request_timeout=DEFAULT_TIMEOUT, wait_between_requests=0.1):
        if timeout < request_timeout:
            return 'Function timeout must be greater than request timeout', 'InvalidInput'
        elif timeout < wait_between_requests:
            return 'Function timeout must be greater than wait between requests', 'InvalidInput'
        start = time.time()
        while time.time() - start < timeout:
            try:
                response = self.request_with_refresh('get', '/api/workflowresults/{}'.format(execution_uid), timeout, headers=self.headers)
                if response.status_code == 200:
                    response = response.json()
                    if response['status'] == 'completed':
                        return response
                time.sleep(wait_between_requests)
            except Timeout:
                return 'Connection timed out', 'TimedOut'
            except Unauthorized:
                return 'Unauthorized credentials', 'Unauthorized'
            except NotConnected:
                return 'Not connected to Walkoff', 'NotConnected'
            except UnknownResponse:
                return 'Unknown error occurred', 'UnknownResponse'

    def standard_request(self, method, address, timeout, headers=None, data=None, **kwargs):
        try:
            response = self.request_with_refresh(method, address, timeout, headers=headers, data=data, **kwargs)
            if response.status_code == 400:
                return 'Bad Request', 'BadRequest'
            return response.json()
        except Timeout:
            return 'Connection timed out', 'TimedOut'
        except Unauthorized:
            return 'Unauthorized credentials', 'Unauthorized'
        except NotConnected:
            return 'Not connected to Walkoff', 'NotConnected'
        except UnknownResponse:
            return 'Unknown error occurred', 'UnknownResponse'

    def _format_request_args(self, address, timeout, headers=None, data=None, **kwargs):
        address = '{0}{1}'.format(self.walkoff_address, address)
        args = kwargs
        args['timeout'] = timeout
        if not (self.headers is None and headers is None):
            args['headers'] = headers if headers is not None else self.headers
        if data is not None:
            args['json'] = data
        if self.is_https:
            args['verify'] = certificate_path
        return address, args

    def _request(self, method, address, timeout, headers=None, data=None, **kwargs):
        address, args = self._format_request_args(address, timeout, headers, data, **kwargs)
        if method == 'put':
            return requests.put(address, **args)
        elif method == 'post':
            return requests.post(address, **args)
        elif method == 'get':
            return requests.get(address, **args)
        elif method == 'delete':
            return requests.delete(address, **args)

    def request_with_refresh(self, method, address, timeout, headers=None, data=None, **kwargs):
        if self.is_connected:
            response = self._request(method, address, timeout, headers, data, **kwargs)
            if response.status_code != 401:
                return response
            else:
                self.refresh_token(timeout)
                response = self._request(method, address, timeout, headers, data, **kwargs)
                if response.status_code == 401:
                    self.is_connected = False
                    raise Unauthorized
                else:
                    return response
        else:
            raise NotConnected

    def refresh_token(self, timeout):
        headers = {'Authorization': 'Bearer {}'.format(self.refresh_token)}
        response = self._post('/api/auth/refresh', timeout, headers=headers)
        if response.status_code == 401:
            raise Unauthorized
        elif response.status_code == 201:
            key = response.json()
            self.reset_authorization(key['access_token'])
        else:
            raise UnknownResponse

    def reset_authorization(self, token):
        self.headers = {'Authorization': 'Bearer {}'.format(token)}

    def shutdown(self):
        try:
            self._request('post', '/api/auth/logout', DEFAULT_TIMEOUT, headers=self.headers,
                          data=dict(refresh_token=self.refresh_token))
        except Timeout:
            logger.warning('Could not log out. Connection timed out')
