import logging

from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorCollection

from api.server.db import get_mongo_c
from common.helpers import validate_uuid
from api.server.db.dashboard import DashboardModel, WidgetModel

router = APIRouter()
logger = logging.getLogger(__name__)


def dashboard_getter(dashboard, app_api_col: AsyncIOMotorCollection):
    if validate_uuid(dashboard):
        return await app_api_col.find_one({"id_": dashboard}, projection={'_id': False})
    else:
        return await app_api_col.find_one({"name": dashboard}, projection={'_id': False})


@router.post("/")
async def create_dashboard(*, new_dash: DashboardModel, app_api_col: AsyncIOMotorCollection = Depends(get_mongo_c)):
    r = await app_api_col.insert_one(dict(new_dash))
    return r.acknowledged


@router.get("/")
async def read_all_dashboards(app_api_col: AsyncIOMotorCollection = Depends(get_mongo_c)):
    ret = []
    for app_api in (await app_api_col.find().to_list(None)):
        ret.append(DashboardModel(**app_api))
    return ret


@router.put("/")
async def update_dashboard(new_dashboard: DashboardModel, app_api_col: AsyncIOMotorCollection = Depends(get_mongo_c)):
    dash = await dashboard_getter(new_dashboard.name, app_api_col)
    r = await app_api_col.replace_one(dict(dash), dict(new_dashboard))
    return r.acknowledged


@router.get("/{dashboard}")
async def read_dashboard(dashboard: UUID, app_api_col: AsyncIOMotorCollection = Depends(get_mongo_c)):
    dash = dashboard_getter(dashboard, app_api_col)
    return dash


@router.get("/{dashboard}")
async def delete_dashboard(dashboard: UUID, app_api_col: AsyncIOMotorCollection = Depends(get_mongo_c)):
    dash = dashboard_getter(dashboard, app_api_col)
    r = await app_api_col.delete_one(dict(dash))
    return r.acknowledged
