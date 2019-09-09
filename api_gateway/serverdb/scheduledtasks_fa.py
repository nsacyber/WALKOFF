import json
import logging

from sqlalchemy_utils import UUIDType

from api_gateway.extensions_fa import Base
from sqlalchemy.orm import relationship
from sqlalchemy import Column, ForeignKey, Integer, String, Enum
from api_gateway.scheduler import construct_trigger
from api_gateway.serverdb.mixins import TrackModificationsMixIn
from api_gateway.server.endpoints.workflowqueue import execute_workflow_helper

logger = logging.getLogger(__name__)


class ScheduledWorkflow(Base):
    """A SqlAlchemy table representing a workflow scheduled for execution

    Attributes:
        id (int): The primary key
        workflow_id (UUID): The id of the workflow scheduled for execution
    """
    __tablename__ = 'scheduled_workflow'
    id = Column(Integer, primary_key=True, autoincrement=True)
    workflow_id = Column(UUIDType(binary=False), nullable=False)
    task_id = Column(Integer, ForeignKey('scheduled_task.id', ondelete='CASCADE'))


class ScheduledTask(Base, TrackModificationsMixIn):
    """A SqlAlchemy table representing a a task scheduled for periodic execution

    Attributes:
        id (int): The primary key
        name (str): The name of the task
        description (str): A description of the task
        status (str): The status of the task. either "running" or "stopped"
        workflows (list[ScheduledWorkflow]): The workflows attached to this task
        trigger_type (str): The type of trigger to use for the scheduler. Either "date", "interval", "cron", or
            "unspecified"
        trigger_args (str): The arguments for the scheduler trigger

    Args:
        name (str): The name of the task
        description (str, optional): A description of the task. Defaults to empty string
        workflows (list[str], optional): The uuids of the workflows attached to this task. Defaults to empty list,
        task_trigger (dict): A dict containing two fields: "type", which contains the type of trigger to use for the
            scheduler ("date", "interval", "cron", or "unspecified"), and "args", which contains the arguments for the
            scheduler trigger
    """
    __tablename__ = 'scheduled_task'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    description = Column(String(255), nullable=False)
    status = Column(Enum('running', 'stopped', name='task_statuses'))
    workflows = relationship('ScheduledWorkflow', back_populates='post')
    #workflows = db.relationship('ScheduledWorkflow', cascade="all, delete-orphan", backref='post', lazy='dynamic',
    #                            passive_deletes=True)
    trigger_type = Column(Enum('date', 'interval', 'cron', 'unspecified', name='trigger_types'))
    trigger_args = Column(String(255))

    def __init__(self, name, description='', status='running', workflows=None, task_trigger=None):
        self.name = name
        self.description = description
        if workflows is not None:
            for workflow in set(workflows):
                self.workflows.append(ScheduledWorkflow(workflow_id=workflow))
        if task_trigger is not None:
            construct_trigger(task_trigger)  # Throws an error if the args are invalid
            self.trigger_type = task_trigger['type']
            self.trigger_args = json.dumps(task_trigger['args'])
        else:
            self.trigger_type = 'unspecified'
            self.trigger_args = '{}'
        self.status = status if status in ('running', 'stopped') else 'running'
        if self.status == 'running' and self.trigger_type != 'unspecified':
            self._start_workflows()

    def update(self, json_in):
        """Updates this task from a JSON representation of it

        Args:
            json_in (dict): The JSON representation of the updated task
        """
        trigger = None
        if 'task_trigger' in json_in and json_in['task_trigger']:
            trigger = construct_trigger(json_in['task_trigger'])  # Throws an error if the args are invalid
            self._update_scheduler(trigger)
            self.trigger_type = json_in['task_trigger']['type']
            self.trigger_args = json.dumps(json_in['task_trigger']['args'])
        if 'name' in json_in:
            self.name = json_in['name']
        if 'description' in json_in:
            self.description = json_in['description']
        if 'workflows' in json_in and json_in['workflows']:
            self._modify_workflows(json_in, trigger=trigger)
        if 'status' in json_in and json_in['status'] != self.status:
            self._update_status(json_in)

    def start(self):
        """Start executing this task
        """
        if self.status != 'running':
            self.status = 'running'
            if self.trigger_type != 'unspecified':
                self._start_workflows()

    def stop(self):
        """Stop executing this scheduled task
        """
        if self.status != 'stopped':
            self.status = 'stopped'
            self._stop_workflows()

    def _update_status(self, json_in):
        self.status = json_in['status']
        if self.status == 'running':
            self._start_workflows()
        elif self.status == 'stopped':
            self._stop_workflows()

    def _start_workflows(self, trigger=None):
        from flask import current_app
        trigger = trigger if trigger is not None else construct_trigger(self._reconstruct_scheduler_args())
        current_app.running_context.scheduler.schedule_workflows(self.id,
                                                                 execute_workflow_helper,
                                                                 self._get_workflow_ids_as_list(), trigger)

    def _stop_workflows(self):
        from flask import current_app
        current_app.running_context.scheduler.unschedule_workflows(self.id, self._get_workflow_ids_as_list())

    def _modify_workflows(self, json_in, trigger):
        from flask import current_app

        new, removed = self.__get_different_workflows(json_in)
        for workflow in self.workflows:
            self.workflows.remove(workflow)
        for workflow in json_in['workflows']:
            self.workflows.append(ScheduledWorkflow(workflow_id=workflow))
        if self.trigger_type != 'unspecified' and self.status == 'running':
            trigger = trigger if trigger is not None else construct_trigger(self._reconstruct_scheduler_args())
            if new:
                current_app.running_context.scheduler.schedule_workflows(self.id,
                                                                         execute_workflow_helper,
                                                                         new, trigger)
            if removed:
                current_app.running_context.scheduler.unschedule_workflows(self.id, removed)

    def _update_scheduler(self, trigger):
        from flask import current_app
        current_app.running_context.scheduler.update_workflows(self.id, trigger)

    def _reconstruct_scheduler_args(self):
        return {'type': self.trigger_type, 'args': json.loads(self.trigger_args)}

    def _get_workflow_ids_as_list(self):
        return [workflow.workflow_id for workflow in self.workflows]

    def __get_different_workflows(self, json_in):
        original_workflows = set(self._get_workflow_ids_as_list())
        incoming_workflows = set(json_in['workflows'])
        new = incoming_workflows - original_workflows
        removed = original_workflows - incoming_workflows
        return new, removed

    def as_json(self):
        """Gets a JSON representation of this ScheduledTask

        Returns:
            (dict): The JSON representation of this ScheduledTask
        """
        return {'id': self.id,
                'name': self.name,
                'description': self.description,
                'status': self.status,
                'workflows': self._get_workflow_ids_as_list(),
                'task_trigger': self._reconstruct_scheduler_args()}
