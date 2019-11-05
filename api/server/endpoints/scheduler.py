import logging
from typing import Union, List
from uuid import UUID

# from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.schedulers import SchedulerAlreadyRunningError, SchedulerNotRunningError
from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorCollection, AsyncIOMotorDatabase

from api.server.db.mongo import get_mongo_d
from api.server.db.scheduledtasks import ScheduledTask, SchedulerStatusResp, NewStatusState
from api.server.endpoints.workflowqueue import execute_workflow_helper
from api.server.scheduler import Scheduler, get_scheduler
from api.server.utils.problems import InvalidInputException, DoesNotExistException
from common import async_mongo_helpers as mongo_helpers

logger = logging.getLogger("API")
router = APIRouter()


async def check_workflows_exist(workflow_col: AsyncIOMotorCollection, task: ScheduledTask):
    workflow_id: UUID
    for workflow_id in task.workflows:
        if not await mongo_helpers.count_items(workflow_col, query={"id_": workflow_id}):
            raise InvalidInputException("create", "ScheduledTask", task.name,
                                        errors={"error": f"{workflow_id} does not exist"})

@router.get("/",
            response_model=SchedulerStatusResp,
            response_description="Current scheduler status in WALKOFF.",
            status_code=200)
async def get_scheduler_status(*, scheduler: Scheduler = Depends(get_scheduler)):
    return SchedulerStatusResp(status=scheduler.scheduler.state)


@router.put("/",
            response_model=SchedulerStatusResp,
            response_description="The updated scheduler status in WALKOFF.",
            status_code=200)
async def update_scheduler_status(*, scheduler: Scheduler = Depends(get_scheduler),
                                  new_state: NewStatusState):
    try:
        if new_state == "start":
            scheduler.start()
        elif new_state == "stop":
            scheduler.stop()
        elif new_state == "pause":
            scheduler.pause()
        elif new_state == "resume":
            scheduler.resume()
    except SchedulerAlreadyRunningError:
        raise InvalidInputException(new_state, "Scheduler", "", errors={"error": "Scheduler already running."})
    except SchedulerNotRunningError:
        raise InvalidInputException(new_state, "Scheduler", "", errors={"error": "Scheduler is not running."})
    return SchedulerStatusResp(status=scheduler.scheduler.state)


@router.get("/tasks/",
            response_model=List[ScheduledTask],
            response_description="A list of all currently scheduled tasks.",
            status_code=200)
async def read_all_scheduled_tasks(*, walkoff_db: AsyncIOMotorDatabase = Depends(get_mongo_d),
                                   page: int = 1,
                                   num_per_page: int = 20):
    task_col = walkoff_db.tasks

    return await mongo_helpers.get_all_items(task_col, ScheduledTask, page=page, num_per_page=num_per_page)
    # page = request.args.get('page', 1, type=int)
    # return [task.as_json() for task in
    #         ScheduledTask.query.paginate(page, current_app.config['ITEMS_PER_PAGE'], False).items], HTTPStatus.OK


@router.post("/tasks/")
async def create_scheduled_task(*, walkoff_db: AsyncIOMotorDatabase = Depends(get_mongo_d),
                                new_task: ScheduledTask):
    task_col = walkoff_db.tasks
    workflow_col = walkoff_db.workflows

    await check_workflows_exist(workflow_col, new_task)
    return await mongo_helpers.create_item(task_col, ScheduledTask, new_task)
    # data = request.get_json()
    # invalid_uuids = validate_uuids(data['workflows'])
    # if invalid_uuids:
    #     return invalid_uuid_problem(invalid_uuids)
    # task = ScheduledTask.query.filter_by(name=data['name']).first()
    # if task is None:
    #     try:
    #         task = ScheduledTask(**data)
    #     except InvalidTriggerArgs:
    #         return invalid_scheduler_args_problem
    #     else:
    #         db.session.add(task)
    #         db.session.commit()
    #         return task.as_json(), HTTPStatus.CREATED
    # else:
    #     return scheduled_task_name_already_exists_problem(data['name'], 'create')


@router.get("/tasks/{task_id}")
async def read_scheduled_task(*, walkoff_db: AsyncIOMotorDatabase = Depends(get_mongo_d),
                              task_id: Union[UUID, str]):
    task_col = walkoff_db.tasks

    return await mongo_helpers.get_item(task_col, ScheduledTask, task_id)


@router.post("/tasks/{task_id}")
async def control_scheduled_task(*, scheduler: Scheduler = Depends(get_scheduler),
                                 walkoff_db: AsyncIOMotorDatabase = Depends(get_mongo_d),
                                 task_id: Union[UUID, str],
                                 new_status: NewStatusState):
    task_col = walkoff_db.tasks

    task: ScheduledTask = await mongo_helpers.get_item(task_col, ScheduledTask, task_id)
    if not task:
        raise DoesNotExistException("control", "Scheduled Task", task_id)

    if new_status == 'start':
        scheduler.schedule_workflows(task_id, execute_workflow_helper, task.workflows, task.trigger_type)
    elif new_status == 'stop':
        scheduler.unschedule_workflows(task_id, task.workflows)


@router.put("/tasks/{task_id}")
async def update_scheduled_task(*, walkoff_db: AsyncIOMotorDatabase = Depends(get_mongo_d),
                                task_id: Union[UUID, str],
                                new_task: ScheduledTask):
    task_col = walkoff_db.tasks
    workflow_col = walkoff_db.workflows

    await check_workflows_exist(workflow_col, new_task)
    return await mongo_helpers.update_item(task_col, ScheduledTask, task_id, new_task)

    # data = request.get_json()
    # invalid_uuids = validate_uuids(data.get('workflows', []))
    # if invalid_uuids:
    #     return invalid_uuid_problem(invalid_uuids)
    # if 'name' in data:
    #     same_name = ScheduledTask.query.filter_by(name=data['name']).first()
    #     if same_name is not None and same_name.id != data['id']:
    #         return scheduled_task_name_already_exists_problem(same_name, 'update')
    # try:
    #     scheduled_task_id.update(data)
    # except InvalidTriggerArgs:
    #     return invalid_scheduler_args_problem
    # else:
    #     db.session.commit()
    #     return scheduled_task_id.as_json(), HTTPStatus.OK


@router.delete("/tasks/{task_id}",
               response_model=bool,
               response_description="",
               status_code=200)
async def delete_scheduled_task(*, walkoff_db: AsyncIOMotorDatabase = Depends(get_mongo_d),
                                task_id: Union[UUID, str]):
    task_col = walkoff_db.tasks

    return await mongo_helpers.delete_item(task_col, ScheduledTask, task_id)
