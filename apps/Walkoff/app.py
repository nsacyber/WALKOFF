import logging
import time

import requests
from requests.exceptions import Timeout

import walkoff.config
from apps import App, action

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
        self.is_https = self.device_fields['https']
        if self.is_https:
            self.walkoff_address = "https://"
        else:
            self.walkoff_address = "http://"
        self.walkoff_address += self.device_fields['ip']
        self.walkoff_address += ':{}'.format(self.device_fields['port'])

    @action
    def connect(self, timeout=DEFAULT_TIMEOUT):
        try:
            response = self._request('post', '/api/auth', timeout,
                                     data=dict(username=self.username,
                                               password=self.device.get_encrypted_field('password')))
        except Timeout:
            return False, 'TimedOut'

        status_code = response.status_code
        if status_code == 404:
            return False, 'WalkoffNotFound'
        elif status_code == 401:
            return False, 'AuthenticationError'
        elif status_code == 201:
            response = response.json()
            self.refresh_token = response['refresh_token']
            self.reset_authorization(response['access_token'])
            self.is_connected = True
            return response, 'Success'
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

    # METRICS
    @action
    def get_app_metrics(self, timeout=DEFAULT_TIMEOUT):
        return self.standard_request('get', '/metrics/apps', timeout, headers=self.headers)

    @action
    def get_workflow_metrics(self, timeout=DEFAULT_TIMEOUT):
        return self.standard_request('get', '/metrics/workflows', timeout, headers=self.headers)

    # CASES
    @action
    def get_all_cases(self, timeout=DEFAULT_TIMEOUT):
        return self.standard_request('get', '/api/cases', timeout, headers=self.headers)

    # USERS
    @action
    def get_all_users(self, timeout=DEFAULT_TIMEOUT):
        return self.standard_request('get', '/api/users', timeout, headers=self.headers)

    # WORKFLOWS
    @action
    def get_all_workflows(self, timeout=DEFAULT_TIMEOUT):
        return self.standard_request('get', '/api/playbooks', timeout, headers=self.headers)

    @action
    def get_workflow_id(self, playbook_name, workflow_name, timeout=DEFAULT_TIMEOUT):
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
                return workflow['id']

    @action
    def execute_workflow(self, workflow_id, timeout=DEFAULT_TIMEOUT):
        data = {"workflow_id": workflow_id}
        r = self.standard_request('post', '/api/workflowqueue', timeout, headers=self.headers, data=data)
        r = [r['id']]
        return r, 'Success'

    @action
    def pause_workflow(self, execution_id, timeout=DEFAULT_TIMEOUT):
        data = {"execution_id": execution_id, "status": "pause"}
        return self.standard_request('patch', '/api/workflowqueue', timeout, headers=self.headers, data=data)

    @action
    def resume_workflow(self, execution_id, timeout=DEFAULT_TIMEOUT):
        data = {"execution_id": execution_id, "status": "resume"}
        return self.standard_request('patch', '/api/workflowqueue', timeout, headers=self.headers, data=data)

    @action
    def trigger(self, execution_ids, data, arguments=None, timeout=DEFAULT_TIMEOUT):
        data = {"execution_ids": execution_ids, "data_in": data, "arguments": arguments}
        return self.standard_request('post', '/api/triggers/send_data', timeout, headers=self.headers, data=data)

    @action
    def get_workflow_results(self, timeout=DEFAULT_TIMEOUT):
        return self.standard_request('get', '/api/workflowqueue', timeout, headers=self.headers)

    @action
    def wait_for_workflow_completion(self, execution_id, timeout=60 * 5, request_timeout=DEFAULT_TIMEOUT,
                                     wait_between_requests=0.1):
        if timeout < request_timeout:
            return 'Function timeout must be greater than request timeout', 'InvalidInput'
        elif timeout < wait_between_requests:
            return 'Function timeout must be greater than wait between requests', 'InvalidInput'
        start = time.time()
        while time.time() - start < timeout:
            try:
                response = self.request_with_refresh('get', '/api/workflowqueue/{}'.format(execution_id), timeout,
                                                     headers=self.headers)
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
            return response.json(), 'Success'
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
            args['verify'] = walkoff.config.Config.CERTIFICATE_PATH
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
