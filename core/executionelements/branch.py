from functools import total_ordering
import logging

from core.events import WalkoffEvent
from core.executionelements.executionelement import ExecutionElement

logger = logging.getLogger(__name__)


@total_ordering
class Branch(ExecutionElement):
    def __init__(self, source_uid, destination_uid, status='Success', conditions=None, priority=999, uid=None):
        """Initializes a new Branch object.
        
        Args:
            source_uid (str): The UID of the source action that will be sending inputs to this Branch.
            destination_uid (str): The UID of the destination action that will be returned if the conditions for this
                Branch are met.
            status (str, optional): Optional field to keep track of the status of the Branch. Defaults to
                "Success".
            conditions (list[Condition], optional): A list of Condition objects for the Branch object.
                Defaults to None.
            priority (int, optional): Optional priority parameter to specify which Branch in the Workflow's
                list of Branches should be executed if multiple have conditions resulting to True.
                Defaults to 999 (lowest priority).
            uid (str, optional): A universally unique identifier for this object. Created from uuid.uuid4() in Python.
        """
        ExecutionElement.__init__(self, uid)
        self.source_uid = source_uid
        self.destination_uid = destination_uid
        self.status = status
        self.conditions = conditions if conditions is not None else []
        self.priority = priority

    def __eq__(self, other):
        return self.source_uid == other.source_uid and self.destination_uid == other.destination_uid and self.status == other.status \
               and set(self.conditions) == set(other.conditions)

    def __lt__(self, other):
        return self.priority < other.priority

    def execute(self, data_in, accumulator):
        """Executes the Branch object, determining if this Branch should be taken.

        Args:
            data_in (): The input to the Condition objects associated with this Branch.
            accumulator (dict): The accumulated data from previous Actions.

        Returns:
            Destination UID for the next Action that should be taken, None if the data_in was not valid
                for this Branch.
        """
        if data_in is not None and data_in.status == self.status:
            if all(condition.execute(data_in=data_in.result, accumulator=accumulator) for condition in self.conditions):
                WalkoffEvent.CommonWorkflowSignal.send(self, event=WalkoffEvent.BranchTaken)
                logger.debug('Branch is valid for input {0}'.format(data_in))
                return self.destination_uid
            else:
                logger.debug('Branch is not valid for input {0}'.format(data_in))
                WalkoffEvent.CommonWorkflowSignal.send(self, event=WalkoffEvent.BranchNotTaken)
                return None
        else:
            return None
