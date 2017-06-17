import json
import logging
from core.filter import Filter
from core.flag import Flag
from .database import db, Base

logger = logging.getLogger(__name__)


class Triggers(Base):
    """
    ORM for the triggers in the Walkoff database
    """
    __tablename__ = "triggers"
    name = db.Column(db.String(255), nullable=False)
    playbook = db.Column(db.String(255), nullable=False)
    workflow = db.Column(db.String(255), nullable=False)
    condition = db.Column(db.String(255, convert_unicode=False), nullable=False)
    tag = db.Column(db.String(255), nullable=False)

    def __init__(self, name, playbook, workflow, condition, tag=''):
        """
        Constructs a Trigger object
        
        Args:
            name (str): Name of the trigger object
            playbook (str): Playbook of the workflow to be connected to the trigger
            workflow (str): The workflow to be connected to the trigger
            condition (str): String of the JSON representation of the conditional to be checked by the trigger
            tag (str): An optional tag (grouping parameter) for the trigger
        """
        self.name = name
        self.playbook = playbook
        self.workflow = workflow
        self.condition = condition
        self.tag = tag

    def edit_trigger(self, form=None):
        """Edits a trigger
        
        Args:
            form (form, optional): Wtf-form containing the edited information
            
        Returns:
            True on successful edit, False otherwise.
        """
        if form:
            if form.name.data:
                self.name = form.name.data

            if form.playbook.data:
                self.playbook = form.playbook.data

            if form.playbook.data:
                self.workflow = form.workflow.data

            if form.conditional.data:
                try:
                    json.loads(form.conditional.data)
                    self.condition = form.conditional.data
                except ValueError:
                    return False

            if form.tag.data:
                self.tag = form.tag.data

        return True

    @staticmethod
    def update_playbook(old_playbook, new_playbook):
        if new_playbook:
            triggers = Triggers.query.filter_by(playbook=old_playbook).all()
            for trigger in triggers:
                trigger.playbook = new_playbook
        db.session.commit()

    @staticmethod
    def update_workflow(old_workflow, new_workflow):
        if new_workflow:
            triggers = Triggers.query.filter_by(workflow=old_workflow).all()
            for trigger in triggers:
                trigger.workflow = new_workflow
        db.session.commit()

    def as_json(self):
        """ Gets the JSON representation of all the Trigger object.
        
        Returns:
            The JSON representation of the Trigger object.
        """
        return {'name': self.name,
                'conditions': json.loads(self.condition),
                'playbook': self.playbook,
                'workflow': self.workflow,
                'tag': self.tag}

    @staticmethod
    def execute(data_in, input_in, trigger_name=None, tags=None):
        """Tries to match the data_in against the conditionals of all the triggers registered in the database.
        
        Args:
            data_in (str): Data to be used to match against the conditionals
            input_in (list): The input to the first step of the workflow
            trigger_name (str): The name of the specific trigger to execute
            tags (list): A list of tags to find the specific triggers to execute
            
        Returns:
            Dictionary of {"status": <status string>}
        """
        triggers = set()
        if trigger_name:
            t = Triggers.query.filter_by(name=trigger_name).first()
            if t:
                triggers.add(t)
        if tags:
            for tag in tags:
                if len(Triggers.query.filter_by(tag=tag).all()) > 1:
                    for t in Triggers.query.filter_by(tag=tag):
                        triggers.add(t)
                elif len(Triggers.query.filter_by(tag=tag).all()) == 1:
                    triggers.add(Triggers.query.filter_by(tag=tag).first())
        if not (trigger_name or tags):
            triggers = Triggers.query.all()
        returned_json = {'executed': [], 'errors': []}
        from server.flaskserver import running_context
        for trigger in triggers:
            conditionals = json.loads(trigger.condition)
            if all(Triggers.__execute_trigger(conditional, data_in) for conditional in conditionals):
                workflow_to_be_executed = running_context.controller.get_workflow(trigger.playbook, trigger.workflow)

                if workflow_to_be_executed:
                    if input_in:
                        logger.info(
                            'Workflow {0} executing with input {1}'.format(workflow_to_be_executed.name, input_in))
                    else:
                        logger.info('Workflow {0} executing with no input'.format(workflow_to_be_executed.name))
                    try:
                        uid = running_context.controller.execute_workflow(playbook_name=trigger.playbook,
                                                                          workflow_name=trigger.workflow,
                                                                          start_input=input_in)
                        returned_json["executed"].append({'name': trigger.name, 'id': uid})

                    except Exception as e:
                        returned_json["errors"].append({trigger.name: "Error executing workflow: {0}".format(str(e))})
                else:
                    logger.error('Workflow associated with trigger is not in controller')
                    returned_json["errors"].append({trigger.name: "Workflow could not be found."})

        if not (returned_json["executed"] or returned_json["errors"]):
            logging.debug('No trigger matches data input')

        return returned_json

    @staticmethod
    def __execute_trigger(conditional, data_in):
        filters = [Filter(action=filter_element['action'],
                          args=filter_element['args'])
                   for filter_element in conditional['filters']]
        return Flag(action=conditional['flag'], args=conditional['args'], filters=filters)(data_in=data_in)

    def __repr__(self):
        return json.dumps(self.as_json())

    def __str__(self):
        out = {'name': self.name,
               'conditions': json.loads(self.condition),
               'play': self.playbook,
               'tag': self.tag}
        return json.dumps(out)
