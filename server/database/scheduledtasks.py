import json
import logging

from core.scheduler import construct_trigger
from server.extensions import db
from server.database.mixins import TrackModificationsMixIn

logger = logging.getLogger(__name__)


class ScheduledWorkflow(db.Model):
    __tablename__ = 'scheduled_workflow'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    uid = db.Column(db.String(50), nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey('scheduled_task.id'))


class ScheduledTask(db.Model, TrackModificationsMixIn):
    __tablename__ = 'scheduled_task'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    status = db.Column(db.Enum('running', 'stopped'))
    workflows = db.relationship('ScheduledWorkflow',
                                cascade="all, delete-orphan",
                                backref='post',
                                lazy='dynamic')
    trigger_type = db.Column(db.Enum('date', 'interval', 'cron', 'unspecified'))
    trigger_args = db.Column(db.String(255))

    def __init__(self, name, description='', status='running', workflows=None, task_trigger=None):
        self.name = name
        self.description = description
        if workflows is not None:
            for workflow in set(workflows):
                self.workflows.append(ScheduledWorkflow(uid=workflow))
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
        if self.status != 'running':
            self.status = 'running'
            if self.trigger_type != 'unspecified':
                self._start_workflows()

    def stop(self):
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
        from server.flaskserver import running_context
        trigger = trigger if trigger is not None else construct_trigger(self._reconstruct_scheduler_args())
        running_context.controller.schedule_workflows(self.id, self._get_workflow_uids_as_list(), trigger)

    def _stop_workflows(self):
        from server.flaskserver import running_context
        running_context.controller.scheduler.unschedule_workflows(self.id, self._get_workflow_uids_as_list())

    def _modify_workflows(self, json_in, trigger):
        from server.flaskserver import running_context

        new, removed = self.__get_different_workflows(json_in)
        for workflow in self.workflows:
            self.workflows.remove(workflow)
        for workflow in json_in['workflows']:
            self.workflows.append(ScheduledWorkflow(uid=workflow))
        if self.trigger_type != 'unspecified' and self.status == 'running':
            trigger = trigger if trigger is not None else construct_trigger(self._reconstruct_scheduler_args())
            if new:
                running_context.controller.schedule_workflows(self.id, new, trigger)
            if removed:
                running_context.controller.scheduler.unschedule_workflows(self.id, removed)

    def _update_scheduler(self, trigger):
        from server.flaskserver import running_context
        running_context.controller.scheduler.update_workflows(self.id, trigger)

    def _reconstruct_scheduler_args(self):
        return {'type': self.trigger_type, 'args': json.loads(self.trigger_args)}

    def _get_workflow_uids_as_list(self):
        return [workflow.uid for workflow in self.workflows]

    def __get_different_workflows(self, json_in):
        original_workflows = set(self._get_workflow_uids_as_list())
        incoming_workflows = set(json_in['workflows'])
        new = incoming_workflows - original_workflows
        removed = original_workflows - incoming_workflows
        return new, removed

    def as_json(self):
        return {'id': self.id,
                'name': self.name,
                'description': self.description,
                'status': self.status,
                'workflows': self._get_workflow_uids_as_list(),
                'task_trigger': self._reconstruct_scheduler_args()}
