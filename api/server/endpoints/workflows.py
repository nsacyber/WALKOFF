import json
import logging

from io import BytesIO
from copy import deepcopy
from typing import Union

from pydantic import UUID4
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from starlette.requests import Request
from starlette.responses import StreamingResponse

import pymongo
from motor.motor_asyncio import AsyncIOMotorCollection

from api.security import get_jwt_identity
from api.server.db import get_mongo_c, get_mongo_d
from api.server.db.workflow import WorkflowModel
from api.server.db.permissions import PermissionsModel, AccessLevel, auth_check, creator_only_permissions, \
    default_permissions
from api.server.utils.helpers import regenerate_workflow_ids

# from common.roles_helpers import auth_check, update_permissions, default_permissions
from common.helpers import validate_uuid

router = APIRouter()
logger = logging.getLogger(__name__)


async def workflow_getter(workflow_col: AsyncIOMotorCollection, workflow: Union[str, UUID4]):
    if validate_uuid(workflow):
        return await workflow_col.find_one({"id_": workflow}, projection={'_id': False})
    else:
        return await workflow_col.find_one({"name": workflow}, projection={'_id': False})


@router.post("/")
async def create_workflow(request: Request, new_workflow: WorkflowModel, workflow_col: AsyncIOMotorCollection = Depends(get_mongo_c), source: str = None):
    walkoff_db = get_mongo_d(request)
    curr_user_id = get_jwt_identity(request)

    # if file:
    #     new_workflow = WorkflowModel(**json.loads((await file.read()).decode('utf-8')))

    if source:
        old_workflow: WorkflowModel = await workflow_getter(workflow_col, source)
        new_workflow = await copy_workflow(old_workflow=old_workflow, new_workflow=new_workflow)

    # # ToDo: Why do we accept the same workflow again?
    # if await workflow_getter(workflow_col, new_workflow.id_):
    #     return import_workflow_and_regenerate_ids(new_workflow, None)

    r: pymongo.results.InsertOneResult = await workflow_col.insert_one(dict(new_workflow))
    if r.acknowledged:
        result = WorkflowModel(**(await workflow_getter(workflow_col, new_workflow.id_)))
        logger.info(f"Created Workflow {result.name} ({result.id_})")
        return result


# def import_workflow_and_regenerate_ids(workflow, creator=None):
#     # new_permissions = workflow_json['permissions']
#     # access_level = workflow_json['access_level']
#
#     regenerate_workflow_ids(workflow)
#
#     if workflow.access_level == AccessLevel.CREATOR_ONLY:
#         update_permissions("workflows", workflow.id_,
#                            new_permissions=[{"role": 1, "permissions": ["delete", "execute", "read", "update"]}],
#                            creator=creator)
#     elif workflow.access_level == AccessLevel.ROLE_BASED:
#         default_permissions("workflows", workflow.id_, data=workflow, creator=creator)
#     elif workflow.access_level == AccessLevel.EVERYONE:
#         update_permissions("workflows", workflow.id_, new_permissions=workflow.permissions, creator=creator)
#
#     # if new_permissions:
#     #     update_permissions("workflows", workflow_json['id_'], new_permissions=new_permissions, creator=creator)
#     # else:
#     #     default_permissions("workflows", workflow_json['id_'], data=workflow_json, creator=creator)
#
#     try:
#         new_workflow = workflow_schema.load(workflow_json)
#         current_app.running_context.execution_db.session.add(new_workflow)
#         current_app.running_context.execution_db.session.commit()
#         return workflow_schema.dump(new_workflow), HTTPStatus.CREATED
#     except IntegrityError:
#         current_app.running_context.execution_db.session.rollback()
#         current_app.logger.error(f" Could not import workflow {workflow_json['name']}. Unique constraint failed")
#         return unique_constraint_problem('workflow', 'import', workflow_json['name'])
#

async def copy_workflow(old_workflow: WorkflowModel, new_workflow: WorkflowModel):
    # update_check = auth_check(workflow_json["id_"], "update", "workflows")
    # if (not update_check) and (workflow_json['creator'] != creator):
    #     return None, HTTPStatus.FORBIDDEN

    regenerate_workflow_ids(old_workflow)

    if new_workflow.name:
        old_workflow.name = new_workflow.name
    else:
        old_workflow.name += " (Copy)"

    old_workflow.permissions = new_workflow.permissions

    return old_workflow
    # if permissions:
    #     update_permissions("workflows", workflow_json['id_'], new_permissions=permissions, creator=creator)
    # else:
    #     default_permissions("workflows", workflow_json['id_'], data=workflow_json, creator=creator)


@router.get("/")
async def read_all_workflows(request: Request, workflow_col: AsyncIOMotorCollection = Depends(get_mongo_c)):
    walkoff_db = get_mongo_d(request)
    curr_user_id = get_jwt_identity(request)

    ret = []
    temp = []
    for workflow in (await workflow_col.find().to_list(None)):
        temp.append(WorkflowModel(**workflow))

    for workflow in temp:
        to_read = auth_check(curr_user_id, str(workflow.id_), "read", "workflows", walkoff_db=walkoff_db)
        if to_read:
            ret.append(workflow)

    return ret


@router.get("/{workflow_name_id}")
async def read_workflow(request: Request, workflow_name_id: str, mode: str = None, workflow_col: AsyncIOMotorCollection = Depends(get_mongo_c)):
    walkoff_db = get_mongo_d(request)
    curr_user_id = get_jwt_identity(request)
    workflow = await workflow_getter(workflow_col, workflow_name_id)

    to_read = auth_check(curr_user_id, str(workflow.id_), "read", "workflows", walkoff_db=walkoff_db)

    if to_read:
        if mode == "export":
            workflow_str = json.dumps(dict(workflow), sort_keys=True, indent=4, separators=(',', ': ')).encode('utf-8')
            workflow_file = BytesIO()
            workflow_file.write(workflow_str)
            workflow_file.seek(0)
            return StreamingResponse(workflow_file, media_type="application/json")
        else:
            return workflow
    else:
        raise HTTPException(status_code=403, detail="Forbidden")


@router.put("/{workflow_name_id}")
async def update_workflow(request: Request, updated_workflow: WorkflowModel, workflow_name_id: str, workflow_col: AsyncIOMotorCollection = Depends(get_mongo_c)):
    walkoff_db = get_mongo_d(request)
    curr_user_id = get_jwt_identity(request)
    workflow = await workflow_getter(workflow_col, workflow_name_id)

    updated_workflow_dict = dict(updated_workflow)
    new_permissions = updated_workflow_dict["permissions"]
    access_level = new_permissions["access_level"]

    to_update = auth_check(curr_user_id, str(workflow.id_), "update", "workflows", walkoff_db=walkoff_db)
    if to_update:
        if access_level == AccessLevel.CREATOR_ONLY:
            updated_workflow_dict["permissions"] = creator_only_permissions(curr_user_id)
        elif access_level == AccessLevel.EVERYONE:
            updated_workflow_dict["permissions"] = default_permissions(curr_user_id, walkoff_db, "global_variables")
        elif access_level == AccessLevel.ROLE_BASED:
            updated_workflow_dict["permissions"]["creator"] = curr_user_id

        old_workflow = await workflow_getter(workflow_col, workflow_name_id)
        r = await workflow_col.replace_one(dict(old_workflow), updated_workflow_dict)
        if r.acknowledged:
            result = await workflow_getter(workflow_col, updated_workflow.id_)
            logger.info(f"Updated Workflow {result.name} ({result.id_})")
            return result
    else:
        raise HTTPException(status_code=403, detail="Forbidden")


@router.delete("/{workflow_name_id}")
async def delete_workflow(request: Request, workflow_name_id: str, workflow_col: AsyncIOMotorCollection = Depends(get_mongo_c)):
    walkoff_db = get_mongo_d(request)
    curr_user_id = get_jwt_identity(request)

    to_delete = auth_check(curr_user_id, workflow_name_id, "delete", "workflows", walkoff_db=walkoff_db)

    if to_delete:
        workflow_to_delete = await workflow_getter(workflow_col, workflow_name_id)
        r = await workflow_col.delete_one(dict(workflow_to_delete))
        if r.acknowledged:
            return
    else:
        raise HTTPException(status_code=403, detail="Forbidden")

