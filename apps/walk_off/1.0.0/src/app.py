import socket
import asyncio
import aiohttp
import time
import logging
import json

from common.config import config
from walkoff_app_sdk.app_base import AppBase

logger = logging.getLogger("apps")

DEFAULT_TIMEOUT = 2
WALKOFF_ADDRESS_DEFAULT = config.API_URI


class Walkoff(AppBase):
    __version__ = "1.0.0"
    app_name = "walk_off"

    def __init__(self, redis, logger):
        super().__init__(redis, logger)

    async def connect(self, username, password, timeout=None):
        if timeout is None:
            timeout = DEFAULT_TIMEOUT
        try:
            response = await self._request('post', '/walkoff/api/auth', timeout,
                                           data=dict(username=username, password=password))
        except asyncio.CancelledError:
            return False, 'TimedOut'

        resp_json = await response.json()
        status_code = response.status

        if status_code == 404:
            return False, 'WalkoffNotFound'
        elif status_code == 401:
            return False, 'AuthenticationError'
        elif status_code == 201:
            # returns access token and refresh token
            return resp_json
        else:
            return 'Unknown response {}'.format(status_code), 'UnknownResponse'

    async def disconnect(self, refresh_token, timeout=None):
        if timeout is None:
            timeout = DEFAULT_TIMEOUT
        new_refresh_token = await self.refresh_token(DEFAULT_TIMEOUT, refresh_token)
        headers = self.retrieve_header(new_refresh_token)
        try:
            response = await self._request('post', '/walkoff/api/auth/logout', timeout, headers=headers,
                                           data=dict(refresh_token=new_refresh_token))

        except asyncio.CancelledError:
            return False, 'TimedOut'

        resp_json = await response.json()
        status_code = response.status

        if status_code == 400:
            return resp_json, 'Invalid refresh token'
        elif status_code == 204:
            return 'Success'
        else:
            return resp_json, 'UnknownResponse'

    # USERS
    async def get_all_users(self, access_token, timeout=None):
        if timeout is None:
            timeout = DEFAULT_TIMEOUT
        headers = self.retrieve_header(access_token)
        try:
            response = await self.standard_request('get', '/walkoff/api/users', timeout=DEFAULT_TIMEOUT,
                                                   headers=headers)
            if response.status == 200:
                resp = await response.json()
                return resp, 'Success'
            else:
                return 'Invalid Credentials'
        except asyncio.CancelledError:
            return False, 'TimedOut'

    # WORKFLOWS
    async def get_all_workflows(self, access_token, timeout=None):
        if timeout is None:
            timeout = DEFAULT_TIMEOUT
        headers = self.retrieve_header(access_token)
        try:
            response = await self.standard_request('get', '/walkoff/api/workflowqueue', timeout=DEFAULT_TIMEOUT,
                                                   headers=headers)
            if response.status == 200:
                resp = await response.json()
                return resp, 'Success'
            else:
                return 'Invalid Credentials'
        except asyncio.CancelledError:
            return False, 'TimedOut'

    async def execute_workflow(self, workflow_id, access_token, timeout=None):
        if timeout is None:
            timeout = DEFAULT_TIMEOUT
        headers = self.retrieve_header(access_token)
        try:
            response = await self.standard_request('post', '/walkoff/api/workflowqueue', timeout=timeout,
                                                   headers=headers, data=dict(workflow_id=workflow_id))
            if response.status == 202:
                resp_json = await response.json()
                return resp_json
            elif response.status == 404:
                return "Workflow does not exist."
            elif response.status == 400:
                return "Invalid Input error."
            else:
                return response.status, "UnknownResponse"
        except asyncio.CancelledError:
            return False, 'TimedOut'

    # async def get_workflow_status(self, execution_id, access_token, timeout=None):
    #     if timeout is None:
    #         timeout=DEFAULT_TIMEOUT
    #     headers = self.retrieve_header(access_token)
    #     try:
    #         response = await self.standard_request('get', "/walkoff/api/workflowqueue", data = dict(execution_id=execution_id), timeout=timeout, headers=headers)
    #         if response.status == 200:
    #             resp_json = await response.json()
    #             return resp_json, "Success"
    #         elif response.status == 404:
    #             return "Object does not exist"
    #         else:
    #             return response.status, "UnknownResponse"
    #     except asyncio.CancelledError:
    #         return False, 'TimedOut'

    # SHUTDOWN WALKOFF
    async def shutdown(self, refresh_token, timeout=None):
        if timeout is None:
            timeout = DEFAULT_TIMEOUT
        new_refresh_token = await self.refresh_token(DEFAULT_TIMEOUT, refresh_token)
        headers = self.retrieve_header(new_refresh_token)
        try:
            await self._request('post', '/walkoff/api/auth/logout', timeout=timeout, headers=headers,
                                data=dict(refresh_token=new_refresh_token))
            return "Successfully logged out."
        except asyncio.CancelledError:
            return False, 'TimedOut'

    async def standard_request(self, method, address, timeout, headers=None, data=None, **kwargs):
        try:
            response = await self.request_with_refresh(method, address, timeout, headers=headers, data=data, **kwargs)
        except asyncio.CancelledError:
            return False, 'TimedOut'
        except:
            return response, "UnknownResponse"

        if response.status == 400:
            return 'Bad Request', 'BadRequest'
        else:
            return response

    async def fetch_http(self, method, url, **kwargs):
        session = aiohttp.ClientSession()
        try:
            async with session.get(url) as response:
                resp = await session.request(method=method, url=url, **kwargs)
                return resp
        finally:
            await session.close()

    async def _request(self, method, address, timeout=5, headers=None, data=None, **kwargs):
        address = '{0}{1}'.format(WALKOFF_ADDRESS_DEFAULT, address)
        args = kwargs
        args['timeout'] = timeout
        if not (headers is None):
            args['headers'] = headers
        if data is not None:
            args['json'] = data

        if method == 'put':
            return await self.fetch_http('PUT', address, **args)
        elif method == 'post':
            return await self.fetch_http('POST', address, **args)
        elif method == 'get':
            return await self.fetch_http('GET', address, **args)
        elif method == 'delete':
            return await self.fetch_http('DELETE', address, **args)

    async def request_with_refresh(self, method, address, timeout, headers=None, data=None, **kwargs):
        response = await self._request(method, address, timeout, headers, data, **kwargs)
        if response.status != 401:
            return response
        else:
            response = await self._request(method, address, timeout, headers, data, **kwargs)
            if response.status == 401:
                return "Unauthorized"
            else:
                return response

    async def refresh_token(self, timeout, token):
        headers = {'Authorization': 'Bearer {}'.format(token)}
        response = await self._request('post', '/walkoff/api/auth/refresh', timeout, headers=headers)
        if response.status == 401:
            return 'Unauthorized'
        elif response.status == 201:
            key = await response.text()
            key = json.loads(key)
            return key['access_token']
        else:
            return (await response.json()), 'UnknownResponse'

    def retrieve_header(self, token):
        headers = {'Authorization': 'Bearer {}'.format(token)}
        return headers


if __name__ == "__main__":
    asyncio.run(Walkoff.run())
