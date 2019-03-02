import logging

from sqlalchemy import Column, ForeignKey, event, orm
from sqlalchemy_utils import UUIDType

from api_gateway.executiondb import Execution_Base
from api_gateway.executiondb.executionelement import ExecutionElement

logger = logging.getLogger(__name__)


class Branch(ExecutionElement, Execution_Base):
    __tablename__ = 'branch'
    workflow_id = Column(UUIDType(binary=False), ForeignKey('workflow.id_', ondelete='CASCADE'))
    source_id = Column(UUIDType(binary=False), nullable=False)
    destination_id = Column(UUIDType(binary=False), nullable=False)

    def __init__(self, source_id, destination_id, id_=None, errors=None):
        """Initializes a new Branch object.
        
        Args:
            source_id (int): The ID of the source action that will be sending inputs to this Branch.
            destination_id (int): The ID of the destination action that will be returned if the conditions for this
                Branch are met.
            id_ (str|UUID, optional): Optional UUID to pass into the Action. Must be UUID object or valid UUID string.
                Defaults to None.
        """
        ExecutionElement.__init__(self, id_, errors)
        self.source_id = source_id
        self.destination_id = destination_id

        self.validate()

    @orm.reconstructor
    def init_on_load(self):
        """Loads all necessary fields upon Branch being loaded from database"""
        pass

    def validate(self):
        pass


@event.listens_for(Branch, 'before_update')
def validate_before_update(mapper, connection, target):
    target.validate()
