import json
import logging
import uuid
from core.executionelements.executionelement import ExecutionElement
from core import contextdecorator
from core.case.callbacks import data_sent
import core.config.config
from jinja2 import Environment

logger = logging.getLogger(__name__)


class Step(ExecutionElement):

    _templatable = True

    def __init__(self,
                 name='',
                 uid=None,
                 next_steps=None,
                 position=None,
                 risk=0,
                 templated=False,
                 raw_representation=None):
        """Initializes a new Step object. A Workflow has many steps that it executes. A Step object can be either a Step
           Action or Step Trigger object. 

        Args:
            name (str, optional): The name of the Step object. Defaults to an empty string.
            next_steps (list[NextStep], optional): A list of NextStep objects for the Step object. Defaults to None.
            position (dict, optional): A dictionary with the x and y coordinates of the Step object. This is used
                for UI display purposes. Defaults to None.
            risk (int, optional): The risk associated with the Step. Defaults to 0.
            uid (str, optional): A universally unique identifier for this object.
                Created from uuid.uuid4().hex in Python
            raw_representation (dict, optional): JSON representation of this object. Used for Jinja templating
        """
        ExecutionElement.__init__(self, uid=uid)
        self.name = name
        self.risk = risk
        self.next_steps = next_steps if next_steps is not None else []
        self.position = position if position is not None else {}
        self.templated = templated

        self._output = None
        self._next_up = None
        self._raw_representation = raw_representation if raw_representation is not None else {}
        self._execution_uid = 'default'

    def get_next_step(self, accumulator):
        """Gets the NextStep object to be executed after the current Step.

        Args:
            accumulator (dict): A record of teh previously-executed steps. Of form {step_name: result}

        Returns:
            The NextStep object to be executed.
        """

        for next_step in self.next_steps:
            next_step = next_step.execute(self._output, accumulator)
            if next_step is not None:
                self._next_up = next_step
                data_sent.send(self, callback_name="Conditionals Executed", object_type="Step")
                return next_step

    @contextdecorator.context
    def render_step(self, **kwargs):
        """Uses JINJA templating to render a Step object.

        Args:
            kwargs (dict[str]): Arguments to use in the JINJA templating.
        """
        if self.templated:
            env = Environment().from_string(json.dumps(self._raw_representation)).render(
                core.config.config.JINJA_GLOBALS, **kwargs)
            self._update_json_from_template(json.loads(env))

    def get_execution_uid(self):
        return self._execution_uid

    def generate_execution_uid(self):
        self._execution_uid = str(uuid.uuid4())

    def get_output(self):
        return self._output

    def set_next_up(self, next_up):
        self._next_up = next_up

    def _update_json_from_template(self, updated_json):
        raise NotImplementedError('_update_json_from_template not implemented')

    def execute(self, data_in, accumulator):
        raise NotImplementedError('execute not implemented')
