import logging

from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorCollection

from api.server.db import get_mongo_c
from common.helpers import validate_uuid
from api.server.db.dashboard import DashboardModel, WidgetModel

router = APIRouter()
logger = logging.getLogger(__name__)


async def dashboard_getter(dashboard, dashboard_col: AsyncIOMotorCollection):
    if validate_uuid(dashboard):
        return await dashboard_col.find_one({"id_": dashboard}, projection={'_id': False})
    else:
        return await dashboard_col.find_one({"name": dashboard}, projection={'_id': False})


@router.post("/")
async def create_dashboard(*, new_dash: DashboardModel, dashboard_col: AsyncIOMotorCollection = Depends(get_mongo_c)):
    r = await dashboard_col.insert_one(dict(new_dash))
    return r.acknowledged


@router.get("/")
async def read_all_dashboards(dashboard_col: AsyncIOMotorCollection = Depends(get_mongo_c)):
    ret = []
    for app_api in (await dashboard_col.find().to_list(None)):
        ret.append(DashboardModel(**app_api))
    return ret


@router.put("/")
async def update_dashboard(new_dashboard: DashboardModel, dashboard_col: AsyncIOMotorCollection = Depends(get_mongo_c)):
    dash = await dashboard_getter(new_dashboard.name, dashboard_col)
    r = await dashboard_col.replace_one(dict(dash), dict(new_dashboard))
    return r.acknowledged


@router.get("/{dashboard}")
async def read_dashboard(dashboard: str, dashboard_col: AsyncIOMotorCollection = Depends(get_mongo_c)):
    dash = dashboard_getter(dashboard, dashboard_col)
    return dash


@router.get("/{dashboard}")
async def delete_dashboard(dashboard: str, dashboard_col: AsyncIOMotorCollection = Depends(get_mongo_c)):
    dash = dashboard_getter(dashboard, dashboard_col)
    r = await dashboard_col.delete_one(dict(dash))
    return r.acknowledged
