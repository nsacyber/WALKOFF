from collections import namedtuple
import logging
from core.flag import Flag
from core.step import Step
from core.nextstep import NextStep
from core.case.callbacks import data_sent
import uuid
import json
from core import contextdecorator
import core.config.config

logger = logging.getLogger(__name__)

_Widget = namedtuple('Widget', ['app', 'widget'])


class TriggerStep(Step):
    def __init__(self,
                 name='',
                 device='',
                 next_steps=None,
                 flags=None,
                 tag=None,
                 position=None,
                 widgets=None,
                 risk=0,
                 uid=None,
                 templated=False,
                 raw_json=None):
        """Initializes a new Step Trigger object. A Workflow has many steps that it executes.
        
        Args:
            name (str, optional): The name of the Step Trigger object. Defaults to an empty string.
            flags (list[Flag], optional): A list of Flag objects for the Step Trigger object. Defaults to None.
            position (dict, optional): A dictionary with the x and y coordinates of the Step Trigger object. This is 
                used for UI display purposes. Defaults to None.
            widgets (list[tuple(str, str)], optional): A list of widget tuples, which holds the app and the
                corresponding widget. Defaults to None.
            risk (int, optional): The risk associated with the Step. Defaults to 0.
            uid (str, optional): A universally unique identifier for this object.
                Created from uuid.uuid4().hex in Python
            raw_json (dict, optional): JSON representation of this object. Used for Jinja templating
        """
        Step.__init__(name, device, next_steps, position, widgets, risk, uid, raw_json)

        self.templated = templated
        self.flags = flags if flags is not None else []
        self.tag = tag

    def _update_json(self, updated_json):
        self.device = updated_json['device'] if 'device' in updated_json else ''
        self.risk = updated_json['risk'] if 'risk' in updated_json else 0
        self.conditionals = [NextStep.from_json(cond_json) for cond_json in updated_json['next']]

    @contextdecorator.context
    def render_step(self, **kwargs):
        """Uses JINJA templating to render a Step object.

        Args:
            kwargs (dict[str]): Arguments to use in the JINJA templating.
        """
        if self.templated:
            from jinja2 import Environment
            env = Environment().from_string(json.dumps(self.raw_json)).render(core.config.config.JINJA_GLOBALS,
                                                                              **kwargs)
            self._update_json(updated_json=json.loads(env))

    def __repr__(self):
        output = {'uid': self.uid,
                  'name': self.name,
                  'flags': [flag.as_json() for flag in self.flags],
                  'tag': self.tag,
                  'device': self.device,
                  'risk': str(self.risk),
                  'next': [next_step for next_step in self.conditionals],
                  'nextUp': self.next_up,
                  'position': self.position,
                  'widget': str([{'app': widget.app, 'name': widget.widget} for widget in self.widgets])}
        if self.output:
            output["output"] = self.output.as_json()
        return str(output)

    def as_json(self):
        output = {'uid': self.uid,
                  'name': self.name,
                  'flags': [flag.as_json() for flag in self.flags],
                  'tag': self.tag,
                  'device': self.device,
                  'risk': str(self.risk),
                  'next': [next_step for next_step in self.conditionals],
                  'nextUp': self.next_up,
                  'position': self.position,
                  'widget': str([{'app': widget.app, 'name': widget.widget} for widget in self.widgets])}
        if self.output:
            output["output"] = self.output.as_json()
        return output

    def execute(self, data_in, accumulator):
        if data_in is not None:
            if all(flag(data_in=data_in.result, accumulator=accumulator) for flag in self.flags):
                data_sent.send(self, callback_name="Trigger Step Taken", object_type="Step")
                logger.debug('TriggerStep is valid for input {0}'.format(data_in))

                return self.name
            else:
                logger.debug('TriggerStep is not valid for input {0}'.format(data_in))
                data_sent.send(self, callback_name="Trigger Step Not Taken", object_type="Step")
                return None
        else:
            return None

    @staticmethod
    def from_json(json_in, position):
        """Forms a TriggerStep object from the provided JSON object.

        Args:
            json_in (dict): The JSON object to convert from.
            position (dict): position of the step node of the form {'x': <x position>, 'y': <y position>}

        Returns:
            The Step object parsed from the JSON object.
        """
        device = json_in['device'] if ('device' in json_in
                                       and json_in['device'] is not None
                                       and json_in['device'] != 'None') else ''
        risk = json_in['risk'] if 'risk' in json_in else 0
        tag = json_in['tag'] if 'tag' in json_in else None
        widgets = []
        uid = json_in['uid'] if 'uid' in json_in else uuid.uuid4().hex
        if 'widgets' in json_in:
            widgets = [(widget['app'], widget['name'])
                       for widget in json_in['widgets'] if ('app' in widget and 'name' in widget)]
        conditionals = []
        if 'next' in json_in:
            conditionals = [NextStep.from_json(next_step) for next_step in json_in['next'] if next_step]
        flags = []
        if 'flags' in json_in:
            flags = [Flag.from_json(flag) for flag in json_in['flags'] if flag]
        return TriggerStep(name=json_in['name'],
                           flags=flags,
                           tag=tag,
                           device=device,
                           risk=risk,
                           next_steps=conditionals,
                           position={key: value for key, value in position.items()},
                           widgets=widgets,
                           uid=uid,
                           templated=json_in['templated'] if 'templated' in json_in else False,
                           raw_json=json_in)
