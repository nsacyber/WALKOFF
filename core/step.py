from collections import namedtuple
import logging
from core.stepaction import StepAction
from core.steptrigger import StepTrigger

logger = logging.getLogger(__name__)

_Widget = namedtuple('Widget', ['app', 'widget'])


class Step(StepAction, StepTrigger):
    def __init__(self,
                 name='',
                 action='',
                 app='',
                 device='',
                 inputs=None,
                 next_steps=None,
                 flags=None,
                 status='Success',
                 position=None,
                 widgets=None,
                 risk=0,
                 uid=None,
                 templated=False,
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
        super(Step, self).__init__(name, action, app, device, inputs, next_steps, flags, status, position, widgets,
            risk, uid, templated, raw_json)

    def __repr__(self):
        output = {'uid': self.uid,
                  'name': self.name,
                  'action': self.action,
                  'position': self.position,
                  'widget': str([{'app': widget.app, 'name': widget.widget} for widget in self.widgets])}
        for attr, value in self.__dict__.items():
            if attr == 'risk':
                output[attr] = str(value)
            elif attr == 'next_step':
                output[attr] = [next_step for next_step in self.conditionals]
            elif attr == 'flags':
                output[attr] = [flag.as_json() for flag in self.flags]
            else:
                output[attr] = value

        if self.output:
            output["output"] = self.output.as_json()
        return str(output)