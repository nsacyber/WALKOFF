from .database import db, Base
import logging
import json
from core.scheduler import construct_scheduler

logger = logging.getLogger(__name__)


class ScheduledWorkflow(Base):
    __tablename__ = 'scheduled_workflow'
    uid = db.Column(db.String(50), nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey('scheduled_task.id'))


class ScheduledTask(Base):

    __tablename__ = 'scheduled_task'
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    status = db.Column(db.Enum('running', 'stopped'))
    workflows = db.relationship('ScheduledWorkflow',
                                cascade="all, delete-orphan",
                                backref='post',
                                lazy='dynamic')
    scheduler_type = db.Column(db.Enum('date', 'interval', 'cron', 'unspecified'))
    scheduler_args = db.Column(db.String(255))

    def __init__(self, name, description='', status='stopped', workflows=None, scheduler=None):
        self.name = name
        self.description = description
        if workflows is not None:
            for workflow in set(workflows):
                self.workflows.append(ScheduledWorkflow(uid=workflow))
        if scheduler is not None:
            construct_scheduler(scheduler)  # Throws an error if the args are invalid
            self.scheduler_type = scheduler['type']
            self.scheduler_args = json.dumps(scheduler['args'])
        else:
            self.scheduler_type = 'unspecified'
            self.scheduler_args = '{}'
        self.status = status if status in ('running', 'stopped') else 'stopped'
        if self.status == 'running' and self.scheduler_type != 'unspecified':
            self._start_workflows()

    def update(self, json_in):
        scheduler = None
        if 'scheduler' in json_in and json_in['scheduler']:
            scheduler = construct_scheduler(json_in['scheduler'])  # Throws an error if the args are invalid
            self._update_scheduler(scheduler)
            self.scheduler_type = json_in['scheduler']['type']
            self.scheduler_args = json.dumps(json_in['scheduler']['args'])
        if 'name' in json_in:
            self.name = json_in['name']
        if 'description' in json_in:
            self.description = json_in['description']
        if 'workflows' in json_in and json_in['workflows']:
            self._modify_workflows(json_in, scheduler=scheduler)
        if 'status' in json_in and json_in['status'] != self.status:
            self._update_status(json_in)

    def start(self):
        if self.status != 'running':
            self.status = 'running'
            if self.scheduler_type != 'unspecified':
                self._start_workflows()

    def stop(self):
        if self.status != 'stopped':
            self.status = 'stopped'
            self._stop_workflows()

    def _update_status(self, json_in):
        self.status = json_in['status']
        if self.status == 'running':
            self._start_workflows(scheduler=scheduler)
        elif self.status == 'stopped':
            self._stop_workflows()

    def _start_workflows(self, scheduler=None):
        from server.flaskserver import running_context
        scheduler = scheduler if scheduler is not None else construct_scheduler(self._reconstruct_scheduler_args())
        running_context.controller.schedule_workflows(self.id, self._get_workflow_uids_as_list(), scheduler)

    def _stop_workflows(self):
        from server.flaskserver import running_context
        running_context.controller.scheduler.unschedule_workflows(self.id, self._get_workflow_uids_as_list())

    def _modify_workflows(self, json_in, scheduler):
        from server.flaskserver import running_context

        new, removed = self.__get_different_workflows(json_in)
        for workflow in self.workflows:
            self.workflows.remove(workflow)
        for workflow in json_in['workflows']:
            self.workflows.append(ScheduledWorkflow(uid=workflow))
        if self.scheduler_type != 'unspecified' and self.status == 'running':
            scheduler = scheduler if scheduler is not None else construct_scheduler(self._reconstruct_scheduler_args())
            if new:
                running_context.controller.schedule_workflows(self.id, new, scheduler)
            if removed:
                running_context.controller.scheduler.unschedule_workflows(self.id, removed)

    def _update_scheduler(self, scheduler):
        from server.flaskserver import running_context
        running_context.controller.scheduler.update_workflows(self.id, scheduler)

    def _reconstruct_scheduler_args(self):
        return {'type': self.scheduler_type, 'args': json.loads(self.scheduler_args)}

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
                'scheduler': self._reconstruct_scheduler_args()}