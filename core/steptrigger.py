from collections import namedtuple
import logging
from core.executionelement import ExecutionElement
from core.helpers import (InvalidElementConstructed)
from core.flag import Flag
import uuid
logger = logging.getLogger(__name__)

_Widget = namedtuple('Widget', ['app', 'widget'])


class StepTrigger(ExecutionElement):
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
        """Initializes a new Step Trigger object. A Workflow has many steps that it executes.
        
        Args:
            name (str, optional): The name of the Step Trigger object. Defaults to an empty string.
            action (str, optional): The name of the action associated with a Step Trigger. Defaults to an empty string.
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
        ExecutionElement.__init__(self, name, uid)
        if action == '':
            raise InvalidElementConstructed('Either action or xml must be specified '
                                            'in step trigger constructor')
        if  app is not '' and device is not '' and inputs is not None and next_steps is not None and risk is not 0:
            raise InvalidElementConstructed('App, device, inputs, next steps, and risk must be specified in '
                                            'an action step constructor and not a trigger step constructor')
        self.action = action
        self.templated = templated
        self.flags = flags if flags is not None else []
        self.status = status
        self.position = position if position is not None else {}
        self.widgets = [_Widget(widget_app, widget_name)
                        for (widget_app, widget_name) in widgets] if widgets is not None else []

        self.output = None
        self.next_up = None
        self.raw_json = raw_json if raw_json is not None else {}
        self.execution_uid = 'default'
        self.results_sock = None
        self.execution_uid = None

    def __call__(self, data_in, accumulator):
        for flag in self.flags:
            flag.results_sock = self.results_sock
        if data_in is not None and data_in.status == self.status:
            if all(flag(data_in=data_in.result, accumulator=accumulator) for flag in self.flags):
                self.__send_callback("Trigger Step Taken")
                logger.debug('TriggerStep is valid for input {0}'.format(data_in))

                return self.name
            else:
                logger.debug('TriggerStep is not valid for input {0}'.format(data_in))
                self.__send_callback("Trigger Step Not Taken")
                return None
        else:
            return None

    def __send_callback(self, callback_name, data={}):
        data['sender'] = {}
        data['sender']['name'] = self.name
        data['sender']['action'] = self.action
        data['callback_name'] = callback_name
        data['sender']['id'] = self.name
        data['sender']['execution_uid'] = self.execution_uid
        data['sender']['uid'] = self.uid
        if self.results_sock:
            self.results_sock.send_json(data)

    def __repr__(self):
        output = {'uid': self.uid,
                  'name': self.name,
                  'action': self.action,
                  'flags': [flag.as_json() for flag in self.flags],
                  'status': self.status,
                  'position': self.position,
                  'widget': str([{'app': widget.app, 'name': widget.widget} for widget in self.widgets])}
        if self.output:
            output["output"] = self.output.as_json()
        return str(output)

    def as_json(self):
        """Gets the JSON representation of a Step Trigger object.

        Returns:
            The JSON representation of a Step Trigger object.
        """
        output = {"uid": self.uid,
                  "name": str(self.name),
                  "action": str(self.action),
                  "flags": [flag.as_json() for flag in self.flags],
                  "status": self.status,
                  "widgets": [{'app': widget.app, 'name': widget.widget} for widget in self.widgets],
                  "position": self.position}
        if self.output:
            output["output"] = self.output.as_json()
        return output

    @staticmethod
    def from_json(json_in, position):
        """Forms a Step Trigger object from the provided JSON object.
        
        Args:
            json_in (dict): The JSON object to convert from.
            position (dict): position of the step node of the form {'x': <x position>, 'y': <y position>}
            
        Returns:
            The Step Trigger object parsed from the JSON object.
        """
        widgets = []
        uid = json_in['uid'] if 'uid' in json_in else uuid.uuid4().hex
        if 'widgets' in json_in:
            widgets = [(widget['app'], widget['name'])
                       for widget in json_in['widgets'] if ('app' in widget and 'name' in widget)]
        flags = []
        if 'flags' in json_in:
            flags = [Flag.from_json(flag) for flag in json_in['flags'] if flag]
        status = json_in['status'] if 'status' in json_in else 'Success'
        return StepTrigger(name=json_in['name'],
                    action=json_in['action'],
                    flags=flags,
                    status=status,
                    position={key: value for key, value in position.items()},
                    widgets=widgets,
                    uid=uid,
                    templated=json_in['templated'] if 'templated' in json_in else False,
                    raw_json=json_in)
