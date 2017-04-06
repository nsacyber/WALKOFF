import ast
import json

from core.arguments import Argument
from core.filter import Filter
from core.flag import Flag
from .database import db, Base


class Triggers(Base):
    __tablename__ = "triggers"
    name = db.Column(db.String(255), nullable=False)
    playbook = db.Column(db.String(255), nullable=False)
    workflow = db.Column(db.String(255), nullable=False)
    condition = db.Column(db.String(255, convert_unicode=False), nullable=False)

    def __init__(self, name, playbook, workflow, condition):
        self.name = name
        self.playbook = playbook
        self.workflow = workflow
        self.condition = condition

    def edit_trigger(self, form=None):
        if form:
            if form.name.data:
                self.name = form.name.data

            if form.playbook.data:
                self.playbook = form.playbook.data

            if form.playbook.data:
                self.workflow = form.workflow.data

            if form.conditional.data:
                self.condition = json.dumps(form.conditional.data)
        return True

    def as_json(self):
        return {'name': self.name,
                'conditions': json.loads(self.condition),
                'playbook': self.playbook,
                'workflow': self.workflow}

    @staticmethod
    def execute(data_in):
        triggers = Triggers.query.all()
        from server.flaskServer import running_context
        for trigger in triggers:
            conditionals = json.loads(trigger.condition)
            if all(Triggers.__execute_trigger(conditional, data_in) for conditional in conditionals):
                workflow_to_be_executed = running_context.controller.get_workflow(trigger.playbook, trigger.workflow)
                if workflow_to_be_executed:
                    workflow_to_be_executed.execute()
                    return {"status": "success"}
                else:
                    return {"status": "error: workflow could not be found"}
        return {"status": "warning: no trigger found valid for data in"}

    @staticmethod
    def __execute_trigger(conditional, data_in):
        conditional = json.loads(conditional)
        flag_args = {arg['key']: Argument(key=arg['key'],
                                          value=arg['value'],
                                          format=arg.get('format', 'str'))
                     for arg in conditional['args']}
        filters = [Filter(action=filter_element['action'],
                          args={arg['key']: Argument(key=arg['key'],
                                                     value=arg['value'],
                                                     format=arg.get('format', 'str'))
                                for arg in filter_element['args']}
                          )
                   for filter_element in conditional['filters']]
        return Flag(action=conditional['flag'], args=flag_args, filters=filters)(data_in)

    def __repr__(self):
        return json.dumps(self.as_json())

    def __str__(self):
        out = {'name': self.name,
               'conditions': json.loads(self.condition),
               'play': self.play}
        return json.dumps(out)
