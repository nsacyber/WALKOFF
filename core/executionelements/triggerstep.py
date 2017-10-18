import logging
from gevent.event import AsyncResult
from core.executionelements.step import Step
from core.executionelements.nextstep import NextStep
from core.case.callbacks import data_sent

logger = logging.getLogger(__name__)


class TriggerStep(Step):

    def __init__(self,
                 name='',
                 uid=None,
                 flags=None,
                 next_steps=None,
                 position=None,
                 risk=0,
                 templated=False,
                 raw_representation=None):
        """Initializes a new Step Trigger object. A Workflow has many steps that it executes.
        
        Args:
            name (str, optional): The name of the Step Trigger object. Defaults to an empty string.
            flags (list[Flag], optional): A list of Flag objects for the Step Trigger object. Defaults to None.
            position (dict, optional): A dictionary with the x and y coordinates of the Step Trigger object. This is 
                used for UI display purposes. Defaults to None.
            risk (int, optional): The risk associated with the Step. Defaults to 0.
            uid (str, optional): A universally unique identifier for this object.
                Created from uuid.uuid4().hex in Python
            raw_representation (dict, optional): JSON representation of this object. Used for Jinja templating
        """
        Step.__init__(self, name, uid, next_steps, position, risk, templated, raw_representation)
        self.flags = flags if flags is not None else []
        self._incoming_data = AsyncResult()

    def _update_json(self, updated_json):
        self.device = updated_json['device'] if 'device' in updated_json else ''
        self.risk = updated_json['risk'] if 'risk' in updated_json else 0
        self.next_steps = [NextStep.create(cond_json) for cond_json in updated_json['next']]

    def execute(self, accumulator):
        self.generate_execution_uid()

        while True:
            data_in = self._incoming_data.get()

            if all(flag.execute(data_in=data_in, accumulator=accumulator) for flag in self.flags):
                data_sent.send(self, callback_name="Trigger Step Taken", object_type="Step")
                logger.debug('TriggerStep is valid for input {0}'.format(data_in))
                accumulator[self.name] = data_in
                return True
            else:
                logger.debug('TriggerStep is not valid for input {0}'.format(data_in))
                data_sent.send(self, callback_name="Trigger Step Not Taken", object_type="Step")
