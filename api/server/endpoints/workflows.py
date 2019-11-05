import json
import logging
from copy import deepcopy
from io import BytesIO
from typing import List, Union
from uuid import UUID

from fastapi import APIRouter, Depends, UploadFile, File
from motor.motor_asyncio import AsyncIOMotorDatabase
from starlette.requests import Request
from starlette.responses import StreamingResponse

from api.server.db.mongo import get_mongo_d
from api.server.db.permissions import AccessLevel, auth_check, creator_only_permissions, \
    default_permissions, append_super_and_internal
from api.server.db.workflow import WorkflowModel, CopyWorkflowModel
from api.server.security import get_jwt_identity
from api.server.utils.helpers import regenerate_workflow_ids
from api.server.utils.problems import UniquenessException, DoesNotExistException, UnauthorizedException, \
    InvalidInputException
from common import async_mongo_helpers as mongo_helpers

router = APIRouter()
logger = logging.getLogger("API")


async def set_permissions(new_workflow: WorkflowModel, curr_user_id: UUID, walkoff_db: AsyncIOMotorDatabase):
    permissions = new_workflow.permissions
    access_level = permissions.access_level
    if access_level == AccessLevel.CREATOR_ONLY:
        permissions_model = await creator_only_permissions(curr_user_id)
        new_workflow.permissions = permissions_model
    elif access_level == AccessLevel.EVERYONE:
        permissions_model = await default_permissions(curr_user_id, walkoff_db, "workflows")
        new_workflow.permissions = permissions_model
    elif access_level == AccessLevel.ROLE_BASED:
        new_workflow.permissions = await append_super_and_internal(new_workflow.permissions)
        new_workflow.permissions.creator = curr_user_id


@router.post("/upload",
             response_model=WorkflowModel,
             response_description="The newly imported Workflow.",
             status_code=201)
async def upload_workflow(*, walkoff_db: AsyncIOMotorDatabase = Depends(get_mongo_d),
                          request: Request, file: UploadFile = File(...)):
    """
    Imports a new Workflow in WALKOFF and returns it.
    """
    workflow_col = walkoff_db.workflows
    curr_user_id = await get_jwt_identity(request)

    new_workflow = WorkflowModel(**json.loads((await file.read()).decode('utf-8')))

    try:
        # Add projections here to get rid of execution_id
        workflow_exists_already = await mongo_helpers.get_item(workflow_col, WorkflowModel, new_workflow.id_)
    except DoesNotExistException:
        workflow_exists_already = None

    if workflow_exists_already:
        old_workflow = await mongo_helpers.get_item(workflow_col, WorkflowModel, new_workflow.id_)
        new_workflow = await upload_workflow_helper(curr_user_id=curr_user_id, old_workflow=old_workflow,
                                             new_workflow=new_workflow, walkoff_db=walkoff_db)

    await set_permissions(new_workflow, curr_user_id, walkoff_db)

    try:
        return await mongo_helpers.create_item(workflow_col, WorkflowModel, new_workflow)
    except:
        raise UniquenessException("workflow", "create", new_workflow.name)


async def upload_workflow_helper(curr_user_id: UUID, old_workflow, new_workflow: WorkflowModel, walkoff_db):
    to_update = await auth_check(old_workflow, curr_user_id, "update", walkoff_db=walkoff_db)
    if not to_update:
        raise UnauthorizedException("import", "Workflow", old_workflow['name'])

    to_regenerate = dict(new_workflow)
    try:
        regenerate_workflow_ids(to_regenerate)
    except (KeyError, ValueError, TypeError) as e:
        raise InvalidInputException("import", "workflow", new_workflow.id_, errors={"exception": str(e)})
    new_workflow = WorkflowModel(**to_regenerate)

    new_workflow.name += "." + str(new_workflow.id_)

    return new_workflow


@router.post("/copy",
             response_model=WorkflowModel,
             response_description="The newly copied Workflow.",
             status_code=201)
async def copy_workflow(*, walkoff_db: AsyncIOMotorDatabase = Depends(get_mongo_d),
                        source: str, name_body: CopyWorkflowModel, request: Request):
    """
    Copied a Workflow in WALKOFF and returns it.
    """
    workflow_col = walkoff_db.workflows
    curr_user_id = await get_jwt_identity(request)
    try:
        existing_workflow = await mongo_helpers.get_item(workflow_col, WorkflowModel, UUID(source))
    except:
        raise DoesNotExistException("copy", "Workflow", source)

    new_workflow = await copy_workflow_helper(curr_user_id=curr_user_id, old_workflow=existing_workflow,
                                              new_name=name_body.name, walkoff_db=walkoff_db)

    await set_permissions(new_workflow, curr_user_id, walkoff_db)

    try:
        return await mongo_helpers.create_item(workflow_col, WorkflowModel, new_workflow)
    except:
        raise UniquenessException("workflow", "create", new_workflow.name)


async def copy_workflow_helper(curr_user_id: UUID, old_workflow, new_name: str, walkoff_db: AsyncIOMotorDatabase):
    to_update = await auth_check(old_workflow, curr_user_id, "update", walkoff_db=walkoff_db)
    if not to_update:
        raise UnauthorizedException("copy", "Workflow", old_workflow["name"])

    copied_workflow = deepcopy(old_workflow)
    workflow_dict = dict(copied_workflow)
    regenerate_workflow_ids(workflow_dict)
    copied_workflow = WorkflowModel(**workflow_dict)

    if new_name:
        copied_workflow.name = new_name
    else:
        copied_workflow.name += " (Copy)"

    # TODO: UI element for new permissions for copied workflows
    # copied_workflow.permissions = new_workflow.permissions

    return copied_workflow


@router.post("/",
             response_model=WorkflowModel,
             response_description="The newly created Workflow.",
             status_code=201)
async def create_workflow(*, walkoff_db: AsyncIOMotorDatabase = Depends(get_mongo_d),
                          request: Request, new_workflow: WorkflowModel):
    """
    Creates a new Workflow in WALKOFF and returns it.
    """
    workflow_col = walkoff_db.workflows
    curr_user_id = await get_jwt_identity(request)

    await set_permissions(new_workflow, curr_user_id, walkoff_db)
    try:
        return await mongo_helpers.create_item(workflow_col, WorkflowModel, new_workflow)
    except:
        raise UniquenessException("workflow", "create", new_workflow.name)


@router.get("/",
            response_model=List[WorkflowModel],
            response_description="List of all Workflows currently loaded in WALKOFF",
            status_code=200)
async def read_all_workflows(*, walkoff_db: AsyncIOMotorDatabase = Depends(get_mongo_d),
                             request: Request):
    """
    Returns a list of all Workflows currently loaded in WALKOFF.
    """
    workflow_col = walkoff_db.workflows
    curr_user_id = await get_jwt_identity(request)

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
async def read_workflow(*, walkoff_db: AsyncIOMotorDatabase = Depends(get_mongo_d),
                        mode: str = None, workflow_name_id: Union[UUID, str],
                        request: Request):
    """
    Returns the Workflow for the specified id or name.
    """
    workflow_col = walkoff_db.workflows
    curr_user_id = await get_jwt_identity(request)

    workflow = await mongo_helpers.get_item(workflow_col, WorkflowModel, workflow_name_id)

    to_read = await auth_check(workflow, curr_user_id, "read", walkoff_db=walkoff_db)
    if to_read:
        if mode == "export":
            workflow_str = workflow.json().encode('utf-8')

            workflow_file = BytesIO()
            workflow_file.write(workflow_str)
            workflow_file.seek(0)
            return StreamingResponse(workflow_file, media_type="application/json")
        else:
            return workflow
    else:
        raise UnauthorizedException("read data for", "Workflow", workflow.name)


@router.put("/{workflow_name_id}",
            response_model=WorkflowModel,
            response_description="The newly updated Workflow.",
            status_code=200)
async def update_workflow(*, walkoff_db: AsyncIOMotorDatabase = Depends(get_mongo_d),
                          workflow_name_id: Union[UUID, str],
                          request: Request, updated_workflow: WorkflowModel):
    """
    Updates a specific Workflow object (fetched by id or name) and returns it.
    """
    workflow_col = walkoff_db.workflows
    curr_user_id = await get_jwt_identity(request)
    old_workflow = await mongo_helpers.get_item(workflow_col, WorkflowModel, workflow_name_id)

    to_update = await auth_check(old_workflow, curr_user_id, "update", walkoff_db=walkoff_db)
    if to_update:
        await set_permissions(updated_workflow, curr_user_id, walkoff_db)
        try:
            return await mongo_helpers.update_item(workflow_col, WorkflowModel, old_workflow.id_, updated_workflow)
        except:
            raise UniquenessException("workflow", "update", updated_workflow.name)

    else:
        raise UnauthorizedException("update data for", "Workflow", old_workflow.name)


@router.delete("/{workflow_name_id}",
               response_model=bool,
               response_description="Whether the specified Workflow was deleted.",
               status_code=200)
async def delete_workflow(*, walkoff_db: AsyncIOMotorDatabase = Depends(get_mongo_d),
                          request: Request, workflow_name_id: Union[UUID, str]):
    """
    Deletes a specific Workflow object (fetched by id or name).
    """
    workflow_col = walkoff_db.workflows
    curr_user_id = await get_jwt_identity(request)

    workflow = await mongo_helpers.get_item(workflow_col, WorkflowModel, workflow_name_id)
    to_delete = await auth_check(workflow, curr_user_id, "delete", walkoff_db=walkoff_db)
    if to_delete:
        return await mongo_helpers.delete_item(workflow_col, WorkflowModel, workflow.id_)
    else:
        raise UnauthorizedException("delete data for", "Workflow", workflow.name)

