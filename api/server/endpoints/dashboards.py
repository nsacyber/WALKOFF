import logging
from typing import List, Union
from http import HTTPStatus
from uuid import UUID
from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorCollection

from api.server.db import get_mongo_c
from api.server.db.dashboard import DashboardModel
from api.server.utils.problems import DoesNotExistException

from common import mongo_helpers

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/",
            response_model=List[DashboardModel], response_description="List of all Dashboards.")
async def read_all_dashboards(*, dashboard_col: AsyncIOMotorCollection = Depends(get_mongo_c),
                              page: int = 1,
                              num_per_page: int = 20):
    """
    Returns a list of all Dashboards.
    """
    return await mongo_helpers.get_all_items(dashboard_col, DashboardModel, page=page, num_per_page=num_per_page)


@router.post("/", status_code=HTTPStatus.CREATED,
             response_model=DashboardModel, response_description="The newly created Dashboard")
async def create_dashboard(*, dashboard_col: AsyncIOMotorCollection = Depends(get_mongo_c),
                           new_dashboard: DashboardModel):
    """
    Creates a new Dashboard in WALKOFF and returns it.
    """
    return await mongo_helpers.create_item(dashboard_col, DashboardModel, new_dashboard)


@router.get("/{dashboard_id}",
            response_model=DashboardModel, response_description="The requested Dashboard.")
async def read_dashboard(*, dashboard_col: AsyncIOMotorCollection = Depends(get_mongo_c),
                         dashboard_id: Union[UUID, str]):
    """
    Returns the Dashboard for the specified dashboard_id.
    """
    return await mongo_helpers.get_item(dashboard_col, DashboardModel, dashboard_id)


@router.put("/{dashboard_id}",
            response_model=DashboardModel, response_description="The newly updated Dashboard.")
async def update_dashboard(*, dashboard_col: AsyncIOMotorCollection = Depends(get_mongo_c),
                           dashboard_id: Union[UUID, str],
                           new_dashboard: DashboardModel):
    """
    Updates the Dashboard for the specified dashboard_id and returns it.
    """
    return await mongo_helpers.update_item(dashboard_col, DashboardModel, dashboard_id, new_dashboard)


@router.delete("/{dashboard_id}",
               response_model=bool, response_description="Whether the specified Dashboard was deleted.")
async def delete_dashboard(*, dashboard_col: AsyncIOMotorCollection = Depends(get_mongo_c),
                           dashboard_id: Union[UUID, str]):
    """
    Deletes the Dashboard for the specified dashboard_id and returns whether the delete was acknowledged.
    """
    return await mongo_helpers.delete_item(dashboard_col, DashboardModel, dashboard_id)
