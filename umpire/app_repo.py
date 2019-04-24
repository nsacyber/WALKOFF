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
    #  TODO: Actually validate the api
    with open(api_file, 'r') as fp:
        try:
            return yaml.load(fp)
        except yaml.YAMLError as exc:
            logger.exception(exc)


class AppRepo(dict):
    class RepositoryNotInitialized(Exception):
        pass

    def __init__(self, path, session, **apps):
        self.path = Path(path)
        self.session = session
        self.token = None
        super().__init__(**apps)

    @classmethod
    async def create(cls, path, db):
        inst = AppRepo(path, db)
        apps = await inst.load_apps_and_apis()
        return AppRepo(path, db, **apps)

    async def store_api(self, api):
        url = f"{config.API_GATEWAY_URI}/api/apps/apis"
        while True:
            try:
                headers, self.token = await get_walkoff_auth_header(self.session, self.token)
                # Do an explicit check to see if we have previously stored the api and update it if so.
                async with self.session.get(url + f"/{api['name']}", headers=headers) as resp:
                    api_exists = resp.status == 200

                if api_exists:
                    async with self.session.put(url + f"/{api['name']}", json=api, headers=headers) as resp:
                        results = await resp.json()
                        logger.debug(f"API-Gateway app-api update response: {results}")
                        return results
                else:
                    async with self.session.post(url, json=api, headers=headers) as resp:
                        results = await resp.json()
                        logger.debug(f"API-Gateway app-api create response: {results}")
                        return results
            except aiohttp.ClientConnectionError as e:
                logger.error(f"Could not send app api to {url}: {e!r}")

    async def load_apps_and_apis(self):
        if not getattr(self, "path", False) and getattr(self, "db", False):
            raise AppRepo.RepositoryNotInitialized

        apps = {}
        for app in self.path.iterdir():
            #  grabs only directories and ignores all __* directories i.e. __pycache__
            if app.is_dir() and not re.fullmatch(r"(__.*)", app.name):
                apps[app.name] = {}
                for version in app.iterdir():
                    # grabs all valid version directories of form "v0.12.3.45..."
                    if re.fullmatch(r"((\d\.?)+)", version.name):
                        try:
                            # Store the api while we've got it here
                            app_api_path = {fname for fname in {"api.yaml", "api.yml"} if (version / fname).exists()}
                            await self.store_api(load_app_api(version / app_api_path.pop()))

                            project = get_project(version)
                            if not len(project.services) == 1:
                                logger.error(
                                    f"{app.name}:{version.name} compose file must define exactly one(1) service.")
                            else:
                                apps[app.name][version.name] = project

                        except ConnectionError:
                            logger.exception("Error connecting to Docker daemon while getting project.")

                        # TODO: Improve the error handling here
                        except Exception:
                            logger.exception(f"Error during {app.name}:{version.name} load.")

                logger.info(f"Loaded {app.name} versions: {[k for k in apps[app.name].keys()]}")
        return apps


if __name__ == "__main__":
    async def run():
        db = None  # Set this to whatever sqlalchemy session management type object you have
        apps = await AppRepo.create(config.APPS_PATH, db)

        if len(apps) < 1:
            logger.error("Walkoff must be loaded with at least one app. Please check that applications dir exists.")
            exit(1)

    asyncio.run(run())
