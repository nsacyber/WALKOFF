import logging
import asyncio
import json
import os
import time

from thehive4py.api import TheHiveApi
from thehive4py.models import CaseHelper, CaseTask, CaseObservable
from walkoff_app_sdk.app_base import AppBase

logger = logging.getLogger("apps")


class Hive(AppBase):
    __version__ = "1.0.0"
    app_name = "hive"

    def __init__(self, redis, logger):
        super().__init__(redis, logger)

    async def create_case(self, url, api_key, title, description="", tlp=2, severity=1, tags=None):
        tags = tags if tags else []

        if not url.startswith("http"):
            url = f"http://{url}"

        api = TheHiveApi(url, api_key)
        self.logger.info('Creating a case in TheHive...')
        case_helper = CaseHelper(api)
        tags.append(f"walkoff_execution_id: {self.current_execution_id}")

        case_kwargs = {
            "tlp": tlp,
            "severity": severity,
            "tags": tags if tags is not None else []
        }

        return case_helper.create(title, description, **case_kwargs).id

    async def update_case(self, case_id, url, api_key, title=None, description=None, tlp=None, severity=None,
                          tags=None, tags_mode="append"):

        self.logger.info(f'Updating case {case_id} in TheHive...')

        if not url.startswith("http"):
            url = f"http://{url}"

        api = TheHiveApi(url, api_key)
        case_helper = CaseHelper(api)

        case_kwargs = {}
        if title:
            case_kwargs["title"] = title
        if description:
            case_kwargs["description"] = description
        if tlp:
            case_kwargs["tlp"] = tlp
        if severity:
            case_kwargs["severity"] = severity
        if tags is not None:
            if tags_mode == "append":
                tags = case_helper(case_id).tags + tags
            case_kwargs["tags"] = tags

        return case_helper.update(case_id, **case_kwargs).id

    async def close_case(self, case_id, url, api_key, resolution_status, impact_status, summary, tags=None,
                         tags_mode="append"):
        self.logger.info(f'Closing case {case_id} in TheHive...')

        if not url.startswith("http"):
            url = f"http://{url}"

        api = TheHiveApi(url, api_key)
        case_helper = CaseHelper(api)

        case_kwargs = {"status": "Resolved",
                       "resolutionStatus": resolution_status,
                       "impactStatus": impact_status,
                       "summary": summary}

        if tags is not None:
            if tags_mode == "append":
                tags = case_helper(case_id).tags + tags
            case_kwargs["tags"] = tags

        return case_helper.update(case_id, **case_kwargs).id

    async def create_case_task(self, case_id, url, api_key, data=None):

        self.logger.info(f'Creating task for {case_id} in TheHive...')

        if not url.startswith("http"):
            url = f"http://{url}"

        api = TheHiveApi(url, api_key)

        results = {}
        for item in data:
            try:
                title = item["title"]
                description = item["description"]
                startDate = time.time_ns() // 1000000
                task = CaseTask(title=title, description=description, startDate=startDate)

                r = api.create_case_task(case_id, task)

                if r.status_code == 201:
                    results[title] = r.json()
                else:
                    raise IOError(r.text)
            except Exception as e:
                self.logger.info(f"Failed to create task with input {item} because: {e}")

        return results

    async def update_case_task(self, url, api_key, task_id, title=None, description=None, status=None, flag=None):
        self.logger.info(f'Updating task {task_id} in TheHive...')

        if not url.startswith("http"):
            url = f"http://{url}"

        api = TheHiveApi(url, api_key)
        task = CaseTask(**api.get_case_task(task_id).json())
        task.id = task_id

        if title:
            task.title = title
        if description:
            task.description = description
        if status:
            task.status = status
        if flag is not None:
            task.flag = flag
        r = api.update_case_task(task)

        if r.status_code == 200:
            return r.json()
        else:
            raise IOError(r.text)

    async def create_case_observable(self, case_id, url, api_key, data_type, data, description=None, tlp=0,
                                     is_ioc=False, is_sighted=False, tags=None):

        tags = tags if tags is not None else []

        self.logger.info(f'Creating observable for {case_id} in TheHive...')

        if not url.startswith("http"):
            url = f"http://{url}"

        api = TheHiveApi(url, api_key)

        obs = CaseObservable(dataType=data_type,
                             message=description,
                             tlp=tlp,
                             tags=tags,
                             ioc=is_ioc,
                             sighted=is_sighted,
                             data=data)

        r = api.create_case_observable(case_id, obs)

        if r.status_code == 201:
            return r.json()
        else:
            raise IOError(r.text)

    async def update_case_observable(self, url, api_key, case_id, obs_id, description=None, tlp=0,
                                     is_ioc=False, is_sighted=False, tags=None, tags_mode=None):
        self.logger.info(f'Updating observable {obs_id} in case {case_id} in TheHive...')

        if not url.startswith("http"):
            url = f"http://{url}"

        api = TheHiveApi(url, api_key)
        obs_list = api.get_case_observables(case_id).json()
        obs_json = [obs for obs in obs_list if obs["id"] == obs_id][0]
        obs = CaseObservable(**obs_json)
        obs.id = obs_id

        if description:
            obs.description = description
        if tlp:
            obs.tlp = tlp
        if is_ioc is not None:
            obs.ioc = is_ioc
        if is_sighted is not None:
            obs.sighted = is_sighted
        if tags is not None:
            if tags_mode == "append":
                tags = obs.tags + tags
            obs.tags = tags

        r = api.update_case_observables(obs)

        if r.status_code == 200:
            return r.json()
        else:
            raise IOError(r.text)

    async def lock_hive_user(self, url, api_key, users):

        if not url.startswith("http"):
            url = f"http://{url}"

        api = TheHiveApi(url, api_key)
        result = {}

        for user in users:
            self.logger.info(f'Locking user {user} in TheHive...')
            r = api.do_patch(f'/api/user/{user}', **{'status': "Locked"})

            if r.status_code == 200:
                result[user] = r.json()
            else:
                self.logger.info(f'Error locking user {user} in TheHive: {r.text()}')

        return result

    async def unlock_hive_user(self, url, api_key, users):

        if not url.startswith("http"):
            url = f"http://{url}"

        api = TheHiveApi(url, api_key)
        result = {}

        for user in users:
            self.logger.info(f'Unlocking user {user} in TheHive...')
            r = api.do_patch(f'/api/user/{user}', **{'status': "Ok"})

            if r.status_code == 200:
                result[user] = r.json()
            else:
                self.logger.info(f'Error Unlocking user {user} in TheHive: {r.text()}')

        return result


if __name__ == "__main__":
    asyncio.run(Hive.run())
