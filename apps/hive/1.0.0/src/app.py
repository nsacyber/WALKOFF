import logging
import asyncio
import json
import os
from thehive4py.api import TheHiveApi
from thehive4py.models import Case, CaseObservable
from walkoff_app_sdk.app_base import AppBase

logger = logging.getLogger("apps")


def create_observable(case_id, api, message, obs_data, typ='other', ioc=False):

    tags = [message, typ]
    r = api.create_case_observable(case_id, CaseObservable(dataType=typ, message=message, tags=tags, ioc=ioc,
                                                           sighted=False,
                                                           data=obs_data))
    return r


def obs_pol(case_id, api, data, log):
    for k, v in data.items():
        if k.startswith('idm_'):
            typ = 'idm'
        elif k.startswith('kong_'):
            typ = 'kong'
        elif k.startswith('free_ipa_'):
            typ = 'free_ipa'
        elif k.startswith('bro_'):
            typ = 'bro'
        else:
            typ = 'other'
        log.info("adding case observable: {}".format(k))
        create_observable(case_id, api, k, str(v), typ)
    return


class Hive(AppBase):
    __version__ = "1.0.0"
    app_name = "hive"

    def __init__(self, redis, logger, console_logger=None):
        super().__init__(redis, logger, console_logger)

    async def create_case(self, log_data, url, api_key, title, description="", tlp=1, severity=1, tags=[], tasks=[]):
        self.logger.info('Creating a case in TheHive')
        self.logger.info('TheHive URL: {}'.format(url))
        self.logger.info('TheHive API key: {}'.format(api_key))

        if isinstance(log_data, str):
            log_data = json.loads(log_data)

        if url.startswith('http://'):
            pass
        elif url.startswith('https://'):
            url = url.replace('https://', 'http://')
        else:
            url = 'http://'+url

        # dir_path = os.path.dirname(os.path.realpath(__file__))
        # rel_path = 'Case-Template__' + case_template + '.json'
        # file_path = os.path.join(dir_path, rel_path)
        api = TheHiveApi(url, api_key)

        self.logger.info('TheHive API connected')

        # with open(file_path) as f:
        #     template = json.load(f)

        # self.logger.info('Loaded Case Template: {}'.format(case_template))

        data = log_data
        # tags = template['tags']
        tags = ['Walkoff']

        exec_id = self.current_execution_id

        # tags.append('walkoff_execution_id: ' + str(exec_id))

        try:
            user_id = data.get('user', None)
            tags.append('user_id: ' + str(user_id))
        except:
            self.logger.debug('No user ID')

        case = Case(title=title,
                    description=description,
                    tlp=tlp,
                    severity=severity,
                    tags=tags,
                    tasks=tasks)
        # case = api.case.create(title='From TheHive4Py', description='N/A', tlp=3, flag=True,
        #                        tags=['TheHive4Py', 'sample'], tasks=[])
        response = api.create_case(case)

        if response.status_code == 201:
            # self.logger.info(json.dumps(response.json(), indent=4, sort_keys=True))
            case_id = response.json()['id']
            self.logger.info('created case: {}'.format(case_id))
        else:
            self.logger.info('failed to create case')
            self.logger.info('ko: {}/{}'.format(response.status_code, response.text))
            return 'Failed'
        log = self.logger
        obs_pol(case_id, api, data, log)
        return case_id

    async def update_case(self, log_data, id, severity, url, api_key):
        self.logger.info('Updating a case in TheHive')
        self.logger.info('TheHive URL: {}'.format(url))
        self.logger.info('TheHive API key: {}'.format(api_key))

        input = log_data.get("walkoff")
        self.logger.info('The data: {}'.format(input))

        if isinstance(input, str):
            input = json.loads(input)

        if url.startswith('http://'):
            pass
        elif url.startswith('https://'):
            url = url.replace('https://', 'http://')
        else:
            url = 'http://'+url

        api = TheHiveApi(url, api_key)
        hive_case = api.case(id)

        self.logger.info('TheHive API connected')

        data = input
        tags = ['Walkoff']

        try:
            user_id = data.get('user', None)
            tags.append('user_id: ' + str(user_id))
        except:
            self.logger.debug('No user ID')

        hive_case.severity = severity
        # case = api.case.create(title='From TheHive4Py', description='N/A', tlp=3, flag=True,
        #                        tags=['TheHive4Py', 'sample'], tasks=[])
        response = api.update_case(hive_case)

        if response.status_code == 200:
            case_id = response.json()['id']
            self.logger.info('Updated case: {}'.format(case_id))
        else:
            return response.status_code

        log = self.logger
        obs_pol(id, api, data, log)
        return case_id

    async def close_case(self, case_id, url, api_key, resolution_status, impact_status, tags, summary):
        # if url.startswith('http://'):
        #     pass
        # elif url.startswith('https://'):
        #     url = url.replace('https://', 'http://')
        # else:
        #     url = 'http://'+url

        self.logger.info('closing case: {}'.format(case_id))
        api = TheHiveApi(url, api_key)
        hive_case = api.case(case_id)

        hive_case.status = 'Resolved'
        hive_case.resolutionStatus = resolution_status

        hive_case.impactStatus = 'NotApplicable'
        if impact_status == 'TruePositive':
            hive_case.impactStatus = impact_status

        hive_case.tags = tags.split(',')
        hive_case.summary = summary

        response = api.update_case(hive_case, ['status', 'resolutionStatus', 'impactStatus', 'tags', 'summary'])

        if response.status_code == 200:
            self.logger.info('closed case: {}'.format(case_id))
        else:
            self.logger.info('failed to close case: {}'.format(case_id))
            self.logger.info('ko: {}/{}'.format(response.status_code, response.text))
        return case_id


if __name__ == "__main__":
    asyncio.run(Hive.run())
