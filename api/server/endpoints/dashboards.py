import logging
from typing import List, Union
from http import HTTPStatus
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorCollection

from api.server.db import get_mongo_c
from api.server.db.dashboard import DashboardModel
from api.server.utils.problems import DoesNotExistException

from common import mongo_helpers

router = APIRouter()
logger = logging.getLogger(__name__)


async def dashboard_getter(dashboard_col: AsyncIOMotorCollection,
                           dashboard_id: Union[UUID, str],
                           operation: str) -> DashboardModel:
    dashboard = await mongo_helpers.get_item(dashboard_col, dashboard_id, DashboardModel)
    if dashboard is None:
        raise DoesNotExistException(operation, "Dashboard", dashboard_id)
    return dashboard


@router.get("/", response_model=List[DashboardModel], response_description="List of all Dashboards.")
async def read_all_dashboards(dashboard_col: AsyncIOMotorCollection = Depends(get_mongo_c)):
    """
    Returns a list of all Dashboards.
    """
    return await mongo_helpers.get_all_items(dashboard_col, DashboardModel)


@router.post("/", status_code=HTTPStatus.CREATED,
             response_model=DashboardModel, response_description="The newly created Dashboard")
async def create_dashboard(*, dashboard_col: AsyncIOMotorCollection = Depends(get_mongo_c),
                           new_dashboard: DashboardModel):
    """
    Creates a new Dashboard in WALKOFF and returns it.
    """
    return await mongo_helpers.create_item(dashboard_col, new_dashboard)


@router.get("/{dashboard_id}",
            response_model=DashboardModel, response_description="The requested Dashboard.")
async def read_dashboard(*, dashboard_col: AsyncIOMotorCollection = Depends(get_mongo_c),
                         dashboard_id: Union[UUID, str]):
    """
    Returns the Dashboard for the specified dashboard_id.
    """
    return await mongo_helpers.get_item(dashboard_col, dashboard_id, DashboardModel)


@router.put("/{dashboard_id}",
            response_model=DashboardModel, response_description="The newly updated Dashboard.")
async def update_dashboard(*, dashboard_col: AsyncIOMotorCollection = Depends(get_mongo_c),
                           dashboard_id: Union[UUID, str], new_dashboard: DashboardModel):
    """
    Updates the Dashboard for the specified dashboard_id and returns it.
    """
    return await mongo_helpers.update_item(dashboard_col, dashboard_id, new_dashboard)


@router.delete("/{dashboard_id}",
               response_model=bool, response_description="Whether the specified Dashboard was deleted.")
async def delete_dashboard(*, dashboard_col: AsyncIOMotorCollection = Depends(get_mongo_c),
                           dashboard_id: Union[UUID, str]):
    """
    Deletes the Dashboard for the specified dashboard_id and returns whether the delete was acknowledged.
    """
    return await mongo_helpers.delete_item(dashboard_col, dashboard_id)
