import logging
from http import HTTPStatus
from typing import List, Union
from uuid import UUID

from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorCollection

from api.server.db.appapi import AppApiModel
from api.server.db.mongo import get_mongo_c
from common import async_mongo_helpers as mongo_helpers

logger = logging.getLogger("API")
router = APIRouter()


@router.get("/",
            response_model=List[str], response_description="List of app names currently loaded in WALKOFF.")
async def read_all_app_names(*, app_api_col: AsyncIOMotorCollection = Depends(get_mongo_c)):
    """
    Returns a list of App names currently loaded in WALKOFF.
    """
    return await app_api_col.distinct("name")


@router.get("/apis/",
            response_model=List[AppApiModel], response_description="List of all App APIs currently loaded in WALKOFF")
async def read_all_app_apis(*, app_api_col: AsyncIOMotorCollection = Depends(get_mongo_c),
                            page: int = 1,
                            num_per_page: int = 20):
    """
    Returns a list of all App APIs currently loaded in WALKOFF.
    """
    return await mongo_helpers.get_all_items(app_api_col, AppApiModel, page=page, num_per_page=num_per_page)


@router.post("/apis/", status_code=HTTPStatus.CREATED,
             response_model=AppApiModel, response_description="The newly created App API.",
             include_in_schema=False)
async def create_app_api(*, app_api_col: AsyncIOMotorCollection = Depends(get_mongo_c),
                         new_api: AppApiModel):
    """
    Creates a new App API in WALKOFF and returns it.
    This is for internal WALKOFF application use only.
    """
    # TODO: Restrict this to internal user only and set NGINX to only accept this from inside the Docker network.
    return await mongo_helpers.create_item(app_api_col, AppApiModel, new_api)


@router.get("/apis/{app_api_name}",
            response_model=AppApiModel, response_description="The requested App API.", )
async def read_app_api(*, app_api_col: AsyncIOMotorCollection = Depends(get_mongo_c),
                       app_api_name: Union[UUID, str]):
    """
    Returns the App API for the specified app_name.
    """
    return await mongo_helpers.get_item(app_api_col, AppApiModel, app_api_name)


@router.put("/apis/{app_api_name}",
            response_model=AppApiModel, response_description="The newly updated App API.",
            include_in_schema=False)
async def update_app_api(*, app_api_col: AsyncIOMotorCollection = Depends(get_mongo_c),
                         app_api_name: Union[UUID, str],
                         new_api: AppApiModel):
    """
    Updates the App API for the specified app_name and returns it.
    This is for internal WALKOFF application use only.
    """
    # TODO: Restrict this to internal user only and set NGINX to only accept this from inside the Docker network.
    return await mongo_helpers.update_item(app_api_col, AppApiModel, app_api_name, new_api)


@router.delete("/apis/{app_api_name}",
               response_model=bool, response_description="Whether the specified App API was deleted.",
               include_in_schema=False)
async def delete_app_api(*, app_api_col: AsyncIOMotorCollection = Depends(get_mongo_c),
                         app_api_name: Union[UUID, str]):
    """
    Deletes the App API for the specified app_name and returns whether the delete was acknowledged.
    This is for internal WALKOFF application use only.
    """
    return await mongo_helpers.delete_item(app_api_col, AppApiModel, app_api_name)
