import json
import logging

from io import BytesIO
from copy import deepcopy
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, UploadFile, HTTPException, File
from starlette.requests import Request
from starlette.responses import StreamingResponse

from motor.motor_asyncio import AsyncIOMotorCollection

from api.server.security import get_jwt_identity
from api.server.db import get_mongo_c, get_mongo_d
from api.server.db.workflow import WorkflowModel
from api.server.db.permissions import AccessLevel, auth_check, creator_only_permissions, \
    default_permissions, append_super_and_internal
from api.server.utils.helpers import regenerate_workflow_ids
from api.server.utils.problems import UniquenessException, DoesNotExistException
from common import mongo_helpers

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/upload",
             response_model=WorkflowModel,
             response_description="The newly created Workflow.",
             status_code=201)
async def upload_workflow(request: Request, file: UploadFile = File(...),
                          workflow_col: AsyncIOMotorCollection = Depends(get_mongo_c)):
    """
    Creates a new Workflow in WALKOFF and returns it.
    """
    walkoff_db = get_mongo_d(request)
    curr_user_id = UUID(await get_jwt_identity(request))

    new_workflow = WorkflowModel(**json.loads((await file.read()).decode('utf-8')))

    try:
        workflow_exists_already = await mongo_helpers.get_item(workflow_col, WorkflowModel, new_workflow.id_)
    except DoesNotExistException:
        workflow_exists_already = None

    if workflow_exists_already:
        old_workflow = await mongo_helpers.get_item(workflow_col, WorkflowModel, new_workflow.id_)
        new_workflow = await import_existing(curr_user_id=curr_user_id, old_workflow=old_workflow,
                                             new_workflow=new_workflow, walkoff_db=walkoff_db)
    permissions = new_workflow.permissions
    access_level = permissions.access_level
    if access_level == AccessLevel.CREATOR_ONLY:
        permissions_model = await creator_only_permissions(curr_user_id)
        new_workflow.permissions = permissions_model
    elif access_level == AccessLevel.EVERYONE:
        permissions_model = await default_permissions(curr_user_id, walkoff_db, "global_variables")
        new_workflow.permissions = permissions_model
    elif access_level == AccessLevel.ROLE_BASED:
        new_workflow.permissions = await append_super_and_internal(new_workflow.permissions)
        new_workflow.permissions.creator = curr_user_id

    try:
        return await mongo_helpers.create_item(workflow_col, WorkflowModel, new_workflow)
    except:
        raise UniquenessException("workflow", "create", new_workflow.name)


@router.post("/",
             response_model=WorkflowModel,
             response_description="The newly created Workflow.",
             status_code=201)
async def create_workflow(request: Request, new_workflow: WorkflowModel,
                          workflow_col: AsyncIOMotorCollection = Depends(get_mongo_c), source: str = None):
    """
    Creates a new Workflow in WALKOFF and returns it.
    """
    walkoff_db = get_mongo_d(request)
    curr_user_id = UUID(await get_jwt_identity(request))

    permissions = new_workflow.permissions
    access_level = permissions.access_level

    if access_level == AccessLevel.CREATOR_ONLY:
        permissions_model = await creator_only_permissions(curr_user_id)
        new_workflow.permissions = permissions_model
    elif access_level == AccessLevel.EVERYONE:
        permissions_model = await default_permissions(curr_user_id, walkoff_db, "global_variables")
        new_workflow.permissions = permissions_model
    elif access_level == AccessLevel.ROLE_BASED:
        new_workflow.permissions = await append_super_and_internal(new_workflow.permissions)
        new_workflow.permissions.creator = curr_user_id

    # copying workflows
    if source:
        old_workflow = await mongo_helpers.get_item(workflow_col, WorkflowModel, UUID(source))
        new_workflow = await copy_workflow(curr_user_id=curr_user_id, old_workflow=old_workflow,
                                           new_workflow=new_workflow, walkoff_db=walkoff_db)
    try:
        return await mongo_helpers.create_item(workflow_col, WorkflowModel, new_workflow)
    except:
        raise UniquenessException("workflow", "create", new_workflow.name)


async def import_existing(curr_user_id: UUID, old_workflow, new_workflow: WorkflowModel, walkoff_db):
    to_update = await auth_check(old_workflow, curr_user_id, "update", walkoff_db=walkoff_db)
    if (not to_update):
        raise HTTPException(status_code=403, detail="Forbidden")

    to_regenerate = dict(new_workflow)
    regenerate_workflow_ids(to_regenerate)
    new_workflow = WorkflowModel(**to_regenerate)

    new_workflow.name += "." + str(new_workflow.id_)

    return new_workflow


async def copy_workflow(curr_user_id: UUID, old_workflow, new_workflow: WorkflowModel, walkoff_db):
    to_update = await auth_check(old_workflow, curr_user_id, "update", walkoff_db=walkoff_db)
    if (not to_update):
        raise HTTPException(status_code=403, detail="Forbidden")

    copied_workflow = deepcopy(old_workflow)
    workflow_dict = dict(copied_workflow)
    regenerate_workflow_ids(workflow_dict)
    copied_workflow = WorkflowModel(**workflow_dict)

    if new_workflow.name:
        copied_workflow.name = new_workflow.name
    else:
        copied_workflow.name += " (Copy)"

    copied_workflow.permissions = new_workflow.permissions

    return copied_workflow


@router.get("/",
            response_model=List[WorkflowModel],
            response_description="List of all Workflows currently loaded in WALKOFF",
            status_code=200)
async def read_all_workflows(request: Request, workflow_col: AsyncIOMotorCollection = Depends(get_mongo_c)):
    """
    Returns a list of all Workflows currently loaded in WALKOFF.
    """
    walkoff_db = get_mongo_d(request)
    curr_user_id = UUID(await get_jwt_identity(request))

    ret = []
    query = await mongo_helpers.get_all_items(workflow_col, WorkflowModel)

    for workflow in query:
        to_read = await auth_check(workflow, curr_user_id, "read", walkoff_db=walkoff_db)
        if to_read:
            ret.append(workflow)

    return ret


@router.get("/{workflow_name_id}",
            response_model=WorkflowModel,
            response_description="The requested Workflow.",
            status_code=200)
async def read_workflow(request: Request, workflow_name_id, mode: str = None,
                        workflow_col: AsyncIOMotorCollection = Depends(get_mongo_c)):
    """
    Returns the Workflow for the specified id or name.
    """
    walkoff_db = get_mongo_d(request)
    curr_user_id = UUID(await get_jwt_identity(request))

    workflow = await mongo_helpers.get_item(workflow_col, WorkflowModel, workflow_name_id)

    to_read = await auth_check(workflow, curr_user_id, "read", walkoff_db=walkoff_db)

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


@router.put("/{workflow_name_id}",
            response_model=WorkflowModel,
            response_description="The newly updated Workflow.",
            status_code=200)
async def update_workflow(request: Request, updated_workflow: WorkflowModel, workflow_name_id: str,
                          workflow_col: AsyncIOMotorCollection = Depends(get_mongo_c)):
    """
    Updates a specific Workflow object (fetched by id or name) and returns it.
    """
    walkoff_db = get_mongo_d(request)
    curr_user_id = UUID(await get_jwt_identity(request))
    old_workflow = await mongo_helpers.get_item(workflow_col, WorkflowModel, workflow_name_id)

    new_permissions = updated_workflow.permissions
    access_level = new_permissions.access_level

    to_update = await auth_check(old_workflow, curr_user_id, "update", walkoff_db=walkoff_db)
    if to_update:
        if access_level == AccessLevel.CREATOR_ONLY:
            updated_workflow.permissions = await creator_only_permissions(curr_user_id)
        elif access_level == AccessLevel.EVERYONE:
            updated_workflow.permissions = await default_permissions(curr_user_id, walkoff_db, "global_variables")
        elif access_level == AccessLevel.ROLE_BASED:
            await append_super_and_internal(updated_workflow.permissions)
            updated_workflow.permissions.creator = curr_user_id

        try:
            return await mongo_helpers.update_item(workflow_col, WorkflowModel, old_workflow.id_, updated_workflow)
        except:
            raise UniquenessException("workflow", "update", updated_workflow.name)

    else:
        raise HTTPException(status_code=403, detail="Forbidden")


@router.delete("/{workflow_name_id}",
               response_model=bool,
               response_description="Whether the specified Workflow was deleted.",
               status_code=204)
async def delete_workflow(request: Request, workflow_name_id,
                          workflow_col: AsyncIOMotorCollection = Depends(get_mongo_c)):
    """
    Deletes a specific Workflow object (fetched by id or name).
    """
    walkoff_db = get_mongo_d(request)
    curr_user_id = UUID(await get_jwt_identity(request))

    workflow = await mongo_helpers.get_item(workflow_col, WorkflowModel, workflow_name_id)
    to_delete = await auth_check(workflow, curr_user_id, "delete", walkoff_db=walkoff_db)
    if to_delete:
        return await workflow_col.delete_one(dict(workflow))
    else:
        raise HTTPException(status_code=403, detail="Forbidden")
