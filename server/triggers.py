import json
import logging

from core.executionelements.filter import Filter
from core.executionelements.flag import Flag
from core.helpers import format_exception_message
from .database import db

logger = logging.getLogger(__name__)


class Triggers(db.Model):
    """
    ORM for the triggers in the Walkoff database
    """
    __tablename__ = "triggers"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False)
    playbook = db.Column(db.String(255), nullable=False)
    workflow = db.Column(db.String(255), nullable=False)
    condition = db.Column(db.String(255, convert_unicode=False), nullable=False)
    tag = db.Column(db.String(255), nullable=False)

    def __init__(self, name, playbook, workflow, conditions, tag=''):
        """
        Constructs a Trigger object.
        
        Args:
            name (str): Name of the trigger object.
            playbook (str): Playbook of the workflow to be connected to the trigger.
            workflow (str): The workflow to be connected to the trigger;
            conditions (str): String of the JSON representation of the conditional to be checked by the trigger.
            tag (str, optional): An optional tag (grouping parameter) for the trigger.
        """
        self.name = name
        self.playbook = playbook
        self.workflow = workflow
        self.condition = json.dumps(conditions)
        self.tag = tag

    def edit_trigger(self, data):
        """Edits a Trigger object.
        
        Args:
            data (dict): JSON containing the edited information.
            
        Returns:
            True on successful edit, False otherwise.
        """
        if 'name' in data:
            self.name = data['name']

        if 'playbook':
            self.playbook = data['playbook']

        if 'workflow':
            self.workflow = data['workflow']

        if 'conditions' in data:
            self.condition = json.dumps(data['conditions'])

        if 'tag' in data:
            self.tag = data['tag']

    @staticmethod
    def update_playbook(old_playbook, new_playbook):
        """Updates the Trigger objects associated with a playbook that has since changed its name.

        Args:
            old_playbook (str): The previous name of the playbook.
            new_playbook (str): The new name of the playbook.
        """
        if new_playbook:
            triggers = Triggers.query.filter_by(playbook=old_playbook).all()
            for trigger in triggers:
                trigger.playbook = new_playbook
        db.session.commit()

    @staticmethod
    def update_workflow(old_workflow, new_workflow):
        """Updates the Trigger objects associated with a workflow that has since changed its name.

        Args:
            old_workflow (str): The previous name of the workflow.
            new_workflow (str): The new name of the workflow.
        """
        if new_workflow:
            triggers = Triggers.query.filter_by(workflow=old_workflow).all()
            for trigger in triggers:
                trigger.workflow = new_workflow
        db.session.commit()

    def as_json(self):
        """ Gets the JSON representation of the Trigger object.
        
        Returns:
            The JSON representation of the Trigger object.
        """
        return {'name': self.name,
                'conditions': json.loads(self.condition),
                'playbook': self.playbook,
                'workflow': self.workflow,
                'tag': self.tag}

    @staticmethod
    def execute(data, inputs, triggers=None, tags=None):
        """Tries to match the data in against the conditionals of all the triggers registered in the database.
        
        Args:
            data (str): Data to be used to match against the conditionals
            inputs (list): The input to the first step of the workflow
            triggers (list[str], optional): List of names of the specific trigger to execute
            tags (list[str], optional): A list of tags to find the specific triggers to execute
            
        Returns:
            Dictionary of {"status": <status string>}
        """
        from server.flaskserver import running_context
        triggers_to_execute = set()
        if triggers is not None:
            for trigger in triggers:
                t = Triggers.query.filter_by(name=trigger).first()
                if t:
                    triggers_to_execute.add(t)
        if tags is not None:
            for tag in tags:
                if len(Triggers.query.filter_by(tag=tag).all()) > 1:
                    for t in Triggers.query.filter_by(tag=tag):
                        triggers_to_execute.add(t)
                elif len(Triggers.query.filter_by(tag=tag).all()) == 1:
                    triggers_to_execute.add(Triggers.query.filter_by(tag=tag).first())
        if not (triggers or tags):
            triggers_to_execute = Triggers.query.all()
        returned_json = {'executed': [], 'errors': []}
        for trigger in triggers_to_execute:
            conditionals = json.loads(trigger.condition)
            if all(Triggers.__execute_trigger(conditional, data) for conditional in conditionals):
                workflow_to_be_executed = running_context.controller.get_workflow(trigger.playbook, trigger.workflow)
                if workflow_to_be_executed:
                    if inputs:
                        logger.info(
                            'Workflow {0} executing with input {1}'.format(workflow_to_be_executed.name, inputs))
                    else:
                        logger.info('Workflow {0} executing with no input'.format(workflow_to_be_executed.name))
                    try:
                        uid = running_context.controller.execute_workflow(playbook_name=trigger.playbook,
                                                                          workflow_name=trigger.workflow,
                                                                          start_input=inputs)
                        returned_json["executed"].append({'name': trigger.name, 'id': uid})
                    except Exception as e:
                        returned_json["errors"].append(
                            {trigger.name: "Error executing workflow: {0}".format(format_exception_message(e))})
                else:
                    logger.error('Workflow associated with trigger is not in controller')
                    returned_json["errors"].append({trigger.name: "Workflow could not be found."})

        if not (returned_json["executed"] or returned_json["errors"]):
            logging.debug('No trigger matches data input')

        return returned_json

    @staticmethod
    def __to_new_input_format(args_json):
        return {arg['name']: arg['value'] for arg in args_json}

    @staticmethod
    def __execute_trigger(conditional, data_in):
        filters = [Filter(action=filter_element['action'],
                          args=Triggers.__to_new_input_format(filter_element['args']))
                   for filter_element in conditional['filters']]
        return Flag(action=conditional['action'],
                    args=Triggers.__to_new_input_format(conditional['args']),
                    filters=filters).execute(data_in, {})

    def __repr__(self):
        return json.dumps(self.as_json())

    def __str__(self):
        out = {'name': self.name,
               'conditions': json.loads(self.condition),
               'play': self.playbook,
               'tag': self.tag}
        return json.dumps(out)
