import logging

from sqlalchemy import Column, Integer, ForeignKey, String, event, orm
from sqlalchemy.orm import relationship
from sqlalchemy_utils import UUIDType

from walkoff.events import WalkoffEvent
from walkoff.executiondb import Execution_Base
from walkoff.executiondb.executionelement import ExecutionElement

logger = logging.getLogger(__name__)


class Branch(ExecutionElement, Execution_Base):
    __tablename__ = 'branch'
    workflow_id = Column(UUIDType(binary=False), ForeignKey('workflow.id'))
    source_id = Column(UUIDType(binary=False), nullable=False)
    destination_id = Column(UUIDType(binary=False), nullable=False)
    status = Column(String(80))
    condition = relationship('ConditionalExpression', cascade='all, delete-orphan', uselist=False)
    priority = Column(Integer)
    children = ('condition',)

    def __init__(self, source_id, destination_id, id=None, status='Success', condition=None, priority=999):
        """Initializes a new Branch object.
        
        Args:
            source_id (int): The ID of the source action that will be sending inputs to this Branch.
            destination_id (int): The ID of the destination action that will be returned if the conditions for this
                Branch are met.
            id (str|UUID, optional): Optional UUID to pass into the Action. Must be UUID object or valid UUID string.
                Defaults to None.
            status (str, optional): Optional field to keep track of the status of the Branch. Defaults to
                "Success".
            condition (ConditionalExpression, optional): The condition which must be fulfilled for this branch.
                Defaults to None.
            priority (int, optional): Optional priority parameter to specify which Branch in the Workflow's
                list of Branches should be executed if multiple have conditions resulting to True.
                Defaults to 999 (lowest priority).
        """
        ExecutionElement.__init__(self, id)
        self.source_id = source_id
        self.destination_id = destination_id
        self.status = status
        self.priority = priority
        self.condition = condition
        self._counter = 0

        self.validate()

    @orm.reconstructor
    def init_on_load(self):
        """Loads all necessary fields upon Branch being loaded from database"""
        self._counter = 0

    def validate(self):
        pass

    def execute(self, action_execution_strategy, data_in, accumulator):
        """Executes the Branch object, determining if this Branch should be taken.

        Args:
            data_in (dict): The input to the Condition objects associated with this Branch.
            accumulator (dict): The accumulated data from previous Actions.

        Returns:
            (UUID): Destination UID for the next Action that should be taken, None if the data_in was not valid
                for this Branch.
        """
        logger.debug('Executing branch {}'.format(str(self.id)))
        self._counter += 1
        accumulator[self.id] = self._counter

        if data_in is not None and data_in.status == self.status:
            if self.condition is None or self.condition.execute(action_execution_strategy, data_in=data_in.result, accumulator=accumulator):
                WalkoffEvent.CommonWorkflowSignal.send(self, event=WalkoffEvent.BranchTaken)
                logger.debug('Branch is valid for input {0}'.format(data_in))
                return self.destination_id
            else:
                logger.debug('Branch is not valid for input {0}'.format(data_in))
                WalkoffEvent.CommonWorkflowSignal.send(self, event=WalkoffEvent.BranchNotTaken)
                return None
        else:
            return None


@event.listens_for(Branch, 'before_update')
def validate_before_update(mapper, connection, target):
    target.validate()
