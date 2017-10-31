from functools import total_ordering
import logging
import sys

from core.case.callbacks import data_sent
from core.executionelements.executionelement import ExecutionElement

logger = logging.getLogger(__name__)


@total_ordering
class NextStep(ExecutionElement):
    def __init__(self, src, dst, status='Success', conditions=None, priority=sys.maxint, uid=None):
        """Initializes a new NextStep object.
        
        Args:
            src (str): The UID of the source step that will be sending inputs to this NextStep.
            dst (str): The UID of the destination step that will be returned if the conditions for this NextStep
                are met.
            status (str, optional): Optional field to keep track of the status of the NextStep. Defaults to
                "Success".
            conditions (list[Condition], optional): A list of Condition objects for the NextStep object.
                Defaults to None.
            priority (int, optional): Optional priority paramter to specify which NextStep in the Workflow's
                list of NextSteps should be executed if mutliple have conditions resulting to True. Defaults to MAXINT.
            uid (str, optional): A universally unique identifier for this object. Created from uuid.uuid4() in Python.
        """
        ExecutionElement.__init__(self, uid)
        self.src = src
        self.dst = dst
        self.status = status
        self.conditions = conditions if conditions is not None else []
        self.priority = priority

    def __eq__(self, other):
        return self.src == other.src and self.dst == other.dst and self.status == other.status \
               and set(self.conditions) == set(other.conditions)

    def __lt__(self, other):
        return self.priority < other.priority

    def execute(self, data_in, accumulator):
        if data_in is not None and data_in.status == self.status:
            if all(condition.execute(data_in=data_in.result, accumulator=accumulator) for condition in self.conditions):
                data_sent.send(self, callback_name="Next Step Taken", object_type="NextStep")
                logger.debug('NextStep is valid for input {0}'.format(data_in))
                return self.dst
            else:
                logger.debug('NextStep is not valid for input {0}'.format(data_in))
                data_sent.send(self, callback_name="Next Step Not Taken", object_type="NextStep")
                return None
        else:
            return None
