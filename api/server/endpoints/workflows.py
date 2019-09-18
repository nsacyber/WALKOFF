import json
import logging
from http import HTTPStatus
from io import BytesIO
from copy import deepcopy
from typing import Union

from pydantic import UUID4
from fastapi import APIRouter, Depends, File, UploadFile
from starlette.responses import StreamingResponse

import pymongo
from motor.motor_asyncio import AsyncIOMotorCollection

from api.server.db import get_mongo_c
from api.server.db.workflow import WorkflowModel
from api.server.db.permissions import PermissionsModel, AccessLevel
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
async def create_workflow(
        new_workflow: WorkflowModel,
        workflow_coll: AsyncIOMotorCollection = Depends(get_mongo_c),
        source: str = None,
        # file: UploadFile = File(...)
):
    # if file:
    #     new_workflow = WorkflowModel(**json.loads((await file.read()).decode('utf-8')))

    if source:
        old_workflow: WorkflowModel = await workflow_getter(workflow_coll, source)
        new_workflow = await copy_workflow(old_workflow=old_workflow, new_workflow=new_workflow)

    # # ToDo: Why do we accept the same workflow again?
    # if await workflow_getter(workflow_coll, new_workflow.id_):
    #     return import_workflow_and_regenerate_ids(new_workflow, None)

    r: pymongo.results.InsertOneResult = await workflow_coll.insert_one(dict(new_workflow))
    if r.acknowledged:
        result = WorkflowModel(**(await workflow_getter(workflow_coll, new_workflow.id_)))
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
async def read_all_workflows(
        workflow_coll: AsyncIOMotorCollection = Depends(get_mongo_c),
):
    # username = get_jwt_claims().get('username', None)
    # curr_user_id = (db.session.query(User).filter(User.username == username).first()).id

    ret = []
    for workflow in (await workflow_coll.find().to_list(None)):
        ret.append(WorkflowModel(**workflow))
    #
    # for workflow in r:
    #     to_read = auth_check(str(workflow.id_), "read", "workflows")
    #     if (workflow.creator == curr_user_id) or to_read:
    #         workflow_schema.dump(workflow)
    #         ret.append(workflow)
    return ret


@router.get("/{workflow_name_id}")
async def read_workflow(
        workflow_name_id: str,
        mode: str = None,
        workflow_coll: AsyncIOMotorCollection = Depends(get_mongo_c)
):
    # username = get_jwt_claims().get('username', None)
    # curr_user_id = (db.session.query(User).filter(User.username == username).first()).id

    # to_read = auth_check(str(workflow.id_), "read", "workflows")

    workflow = await workflow_getter(workflow_coll, workflow_name_id)

    if mode == "export":
        workflow_str = json.dumps(dict(workflow), sort_keys=True, indent=4, separators=(',', ': ')).encode('utf-8')
        workflow_file = BytesIO()
        workflow_file.write(workflow_str)
        workflow_file.seek(0)
        return StreamingResponse(workflow_file, media_type="application/json")
    else:
        return workflow

    # if (workflow.creator == curr_user_id) or to_read:
    #     workflow_json = workflow_schema.dump(workflow)
    #     if request.args.get('mode') == "export":
    #         f = BytesIO()
    #         f.write(json.dumps(workflow_json, sort_keys=True, indent=4, separators=(',', ': ')).encode('utf-8'))
    #         f.seek(0)
    #         return send_file(f, attachment_filename=workflow.name + '.json', as_attachment=True), HTTPStatus.OK
    #     else:
    #         return workflow_json, HTTPStatus.OK
    # else:
    #     return None, HTTPStatus.FORBIDDEN


@router.put("/{workflow_name_id}")
async def update_workflow(
        updated_workflow: WorkflowModel,
        workflow_name_id: str,
        workflow_coll: AsyncIOMotorCollection = Depends(get_mongo_c)
):
    # username = get_jwt_claims().get('username', None)
    # curr_user_id = (db.session.query(User).filter(User.username == username).first()).id

    # to_update = auth_check(str(workflow.id_), "update", "workflows")
    # if (workflow.creator == curr_user_id) or to_update:
    #     if access_level == 0:
    #         auth_check(str(workflow.id_), "update", "workflows",
    #                    updated_roles=[{"role": 1, "permissions": ["delete", "execute", "read", "update"]}])
    #     elif access_level == 1:
    #         default_permissions("workflows", str(workflow.id_), data=data)
    #     elif access_level == 2:
    #         auth_check(str(workflow.id_), "update", "workflows", updated_roles=new_permissions)
    #     # if new_permissions:
    #     #     auth_check(str(workflow.id_), "update", "workflows", updated_roles=new_permissions)
    #     # else:
    #     #     default_permissions("workflows", str(workflow.id_), data=data)

    old_workflow = await workflow_getter(workflow_coll, workflow_name_id)
    r = await workflow_coll.replace_one(dict(old_workflow), dict(updated_workflow))
    if r.acknowledged:
        result = await workflow_getter(workflow_coll, updated_workflow.id_)
        logger.info(f"Updated Workflow {result.name} ({result.id_})")
        return result


@router.delete("/{workflow_name_id}")
async def delete_workflow(
        workflow_name_id: str,
        workflow_coll: AsyncIOMotorCollection = Depends(get_mongo_c)
):
    # username = get_jwt_claims().get('username', None)
    # curr_user_id = (db.session.query(User).filter(User.username == username).first()).id

    workflow_to_delete = await workflow_getter(workflow_coll, workflow_name_id)
    r = await workflow_coll.delete_one(dict(workflow_to_delete))
    if r.acknowledged:
        return


    # to_delete = auth_check(str(workflow.id_), "delete", "workflows")
    # if (workflow.creator == curr_user_id) or to_delete:
    #     current_app.running_context.execution_db.session.delete(workflow)
    #     current_app.logger.info(f"Removed workflow {workflow.name} ({workflow.id_})")
    #     current_app.running_context.execution_db.session.commit()
    #     return None, HTTPStatus.NO_CONTENT
    # else:
    #     return None, HTTPStatus.FORBIDDEN
