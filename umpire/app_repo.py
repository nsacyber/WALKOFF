import logging
import re
import asyncio
from pathlib import Path

import aiohttp
import yaml
from compose.cli.command import get_project


from common.config import config
from common.docker_helpers import get_project
from common.helpers import get_walkoff_auth_header

logging.basicConfig(level=logging.info, format="{asctime} - {name} - {levelname}:{message}", style='{')
logger = logging.getLogger("AppRepo")


def load_app_api(api_file):
    with open(api_file, 'r') as fp:
        try:
            return yaml.load(fp)
        except yaml.YAMLError as exc:
            logger.exception(f"Invalid yaml on app api: {api_file}. {exc}")


class AppRepo:
    class RepositoryNotInitialized(Exception):
        pass

    def __init__(self, path, session):
        self.path = Path(path)
        self.session = session
        self.token = None
        self.apps = {}
        self.loaded_apis = {}

    @classmethod
    async def create(cls, path, db):
        inst = AppRepo(path, db)
        await inst.get_loaded_apis()
        await inst.load_apps_and_apis()
        return inst

    async def get_loaded_apis(self):
        url = f"{config.API_GATEWAY_URI}/api/apps/apis"
        timeout = 0.25
        while True:
            try:
                # Do an explicit check to see if we have previously stored the api and update it if so.
                headers, self.token = await get_walkoff_auth_header(self.session, self.token)
                async with self.session.get(url, headers=headers) as resp:
                    if resp.status == 200:
                        results = await resp.json()
                        self.loaded_apis = {api["name"]: api for api in results}
                        return

            except (asyncio.TimeoutError, aiohttp.ClientConnectionError) as e:
                logger.error(f"Could not load app apis at {url}: {e!r}. Retrying...")
                timeout *= 2  # Let's sleep so as not to hammer the api_gateway
                await asyncio.sleep(timeout)

    async def store_api(self, api):
        url = f"{config.API_GATEWAY_URI}/api/apps/apis"
        try:
            headers, self.token = await get_walkoff_auth_header(self.session, self.token)
            if api.get("name") in self.loaded_apis :
                async with self.session.put(url + f"/{api['name']}", json=api, headers=headers) as resp:
                    if resp.status == 200:
                        results = await resp.json()
                        self.loaded_apis[results["name"]] = results
                        logger.debug(f"API-Gateway app-api update response: {results}")
                        return results
                    elif resp.status == 400:
                        results = await resp.json()

                        # it's invalid so toast any old versions from the db
                        await self.session.delete(url + f"/{api['name']}", headers=headers)
                        logger.error(f"App api {api.get('name')} is invalid. Check api_gateway logs for more info.")
            else:
                async with self.session.post(url, json=api, headers=headers) as resp:
                    if resp.status == 200:
                        results = await resp.json()
                        self.loaded_apis[results["name"]] = results
                        logger.debug(f"API-Gateway app-api create response: {results}")
                        return results
                    elif resp.status == 400:
                        results = await resp.json()
                        logger.error(f"App api {api.get('name')} is invalid. {results.get('detail')}")

        except (asyncio.TimeoutError, aiohttp.ClientConnectionError) as e:
            logger.error(f"Could not send app api to {url}: {e!r}")

    async def load_apps_and_apis(self):
        if not getattr(self, "path", False) and getattr(self, "db", False):
            raise AppRepo.RepositoryNotInitialized

        self.apps = {}
        for app in self.path.iterdir():
            #  grabs only directories and ignores all __* directories i.e. __pycache__
            if app.is_dir() and not re.fullmatch(r"(__.*)", app.name):
                self.apps[app.name] = {}
                for version in app.iterdir():
                    # grabs all valid version directories of form "v0.12.3.45..."
                    if re.fullmatch(r"((\d\.?)+)", version.name):
                        try:
                            # Store the api while we've got it here
                            app_api_path = {fname for fname in {"api.yaml", "api.yml"} if (version / fname).exists()}
                            api = load_app_api(version / app_api_path.pop())

                            if api is None:  # The yaml was invalid and we logged that so lets skip it.
                                continue

                            await self.store_api(api)

                            project = get_project(version)
                            if not len(project.services) == 1:
                                logger.error(
                                    f"{app.name}:{version.name} compose file must define exactly one(1) service.")
                            else:
                                self.apps[app.name][version.name] = project

                        except ConnectionError:
                            logger.exception("Error connecting to Docker daemon while getting project.")

                        # TODO: Improve the error handling here
                        except Exception:
                            logger.exception(f"Error during {app.name}:{version.name} load.")

                logger.info(f"Loaded {app.name} versions: {[k for k in self.apps[app.name].keys()]}")
