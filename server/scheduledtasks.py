from .database import db, Base
import logging
import json

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
                                # secondary=tasks_workflows,
                                cascade="all, delete-orphan",
                                backref='post',
                                lazy='dynamic')
    scheduler_type = db.Column(db.Enum('date', 'interval', 'cron', 'unspecified'))
    scheduler_args = db.Column(db.String(255))

    def __init__(self, name, description='', status='stopped', workflows=None, scheduler=None):
        self.name = name
        self.description = description
        self.status = status
        # TODO: If enabled, add in controller
        if workflows is not None:
            for workflow in set(workflows):
                self.workflows.append(ScheduledWorkflow(uid=workflow))
        if scheduler is not None:
            self.scheduler_type = scheduler['type']
            self.scheduler_args = json.dumps(scheduler['args'])
        else:
            self.scheduler_type = 'unspecified'
            self.scheduler_args = '{}'

    def update(self, json_in):
        if 'name' in json_in:
            self.name = json_in['name']
        if 'description' in json_in:
            self.description = json_in['description']
        if 'status' in json_in:
            self.status = json_in['status']
            # TODO: If enabled, add in controller
        if 'workflows' in json_in and json_in['workflows']:
            for workflow in self.workflows:
                self.workflows.remove(workflow)
            for workflow in json_in['workflows']:
                self.workflows.append(ScheduledWorkflow(uid=workflow))
        if 'scheduler' in json_in and json_in['scheduler']:
            self.scheduler_type = json_in['scheduler']['type']
            self.scheduler_args = json.dumps(json_in['scheduler']['args'])

    def start(self):
        self.status = 'running'
        # TODO: Add in controller

    def stop(self):
        self.status = 'stopped'
        # TODO: remove from in controller

    def as_json(self):
        return {'id': self.id,
                'name': self.name,
                'description': self.description,
                'status': self.status,
                'workflows': [workflow.uid for workflow in self.workflows],
                'scheduler': {'type': self.scheduler_type,
                              'args': json.loads(self.scheduler_args)}}