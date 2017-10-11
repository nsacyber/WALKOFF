from collections import namedtuple
import logging
from core.executionelement import ExecutionElement
from core.case.callbacks import data_sent

logger = logging.getLogger(__name__)

_Widget = namedtuple('Widget', ['app', 'widget'])


class Step(ExecutionElement):
    def __init__(self,
                 name='',
                 device='',
                 next_steps=None,
                 position=None,
                 widgets=None,
                 risk=0,
                 uid=None,
                 raw_json=None):
        """Initializes a new Step object. A Workflow has many steps that it executes. A Step object can be either a Step
           Action or Step Trigger object. 

        Args:
            name (str, optional): The name of the Step object. Defaults to an empty string.
            action (str, optional): The name of the action associated with a Step. Defaults to an empty string.
            app (str, optional): The name of the app associated with the Step. Defaults to an empty string.
            device (str, optional): The name of the device associated with the app associated with the Step. Defaults
                to an empty string.
            inputs (dict, optional): A dictionary of Argument objects that are input to the step execution. Defaults
                to None.
            next_steps (list[NextStep], optional): A list of NextStep objects for the Step object. Defaults to None.
            position (dict, optional): A dictionary with the x and y coordinates of the Step object. This is used
                for UI display purposes. Defaults to None.
            widgets (list[tuple(str, str)], optional): A list of widget tuples, which holds the app and the
                corresponding widget. Defaults to None.
            risk (int, optional): The risk associated with the Step. Defaults to 0.
            uid (str, optional): A universally unique identifier for this object.
                Created from uuid.uuid4().hex in Python
            raw_json (dict, optional): JSON representation of this object. Used for Jinja templating
        """
        ExecutionElement.__init__(self, name, uid)

        self.device = device
        self.risk = risk
        self.conditionals = next_steps if next_steps is not None else []
        self.position = position if position is not None else {}
        self.widgets = [_Widget(widget_app, widget_name)
                        for (widget_app, widget_name) in widgets] if widgets is not None else []

        self.output = None
        self.next_up = None
        self.raw_json = raw_json if raw_json is not None else {}
        self.execution_uid = 'default'
        self.execution_uid = None

    def get_next_step(self, accumulator):
        """Gets the NextStep object to be executed after the current Step.

        Args:
            accumulator (dict): A record of teh previously-executed steps. Of form {step_name: result}

        Returns:
            The NextStep object to be executed.
        """

        for next_step in self.conditionals:
            next_step = next_step(self.output, accumulator)
            if next_step is not None:
                self.next_up = next_step
                data_sent.send(self, callback_name="Conditionals Executed", object_type="Step")
                return next_step

    def as_json(self):
        raise NotImplementedError('as_json has not been implemented')