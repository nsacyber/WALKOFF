import logging
import re
import json
import asyncio
from pathlib import Path


from compose.cli.command import get_project


from common.config import config
from common.helpers import load_docker_env, validate_app_api


logging.basicConfig(level=logging.info, format="{asctime} - {name} - {levelname}:{message}", style='{')
logger = logging.getLogger("AppRepo")


class AppRepo(dict):
    class RepositoryNotInitialized(Exception): pass

    def __init__(self, path, db, **apps):
        self.path = Path(path)
        self.db = db
        super().__init__(**apps)

    @classmethod
    async def create(cls, path, db):
        inst = AppRepo(path, db)
        apps = await inst.load_apps_and_apis()
        return AppRepo(path, db, **apps)

    async def store_api(self, api, api_name):
        # TODO: Store apis in db and not redis. "We get the validation for free" - adpham
        await self.db.hset(config["REDIS"]["api_key"], api_name, json.dumps(api))

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
                    if re.fullmatch(r"(v(\d\.?)+)", version.name):
                        try:
                            # Store the api while we've got it here
                            api_name = app.name  # TODO: f"{app.name}-{version.name}"
                            await self.store_api(validate_app_api(version / "api.yaml"), api_name)

                            project = get_project(project_dir=version, environment=load_docker_env())
                            if not len(project.services) == 1:
                                logger.error(
                                    f"{app.name}-{version.name} compose file must define exactly one(1) service.")
                            else:
                                apps[app.name][version.name] = project

                        except ConnectionError:
                            logger.exception("Error connecting to Docker daemon while getting project.")

                        # TODO: Improve the error handling here
                        except Exception:
                            logger.exception(f"Error during {app.name}-{version.name} load.")

                logger.info(f"Loaded {app.name} versions: {apps[app.name].keys()}")
        return apps


if __name__ == "__main__":
    async def run():
        db = None  # Set this to whatever sqlalchemy session management type object you have
        apps = await AppRepo.create(config["UMPIRE"]["apps_path"], db)

        if len(apps) < 1:
            logger.error("Walkoff must be loaded with at least one app. Please check that applications dir exists.")
            exit(1)

    asyncio.run(run())
