import logging

from sqlalchemy import Column, PickleType

from walkoff.dbtypes import Json
from walkoff.coredb import Device_Base
from walkoff.dbtypes import Guid
logger = logging.getLogger(__name__)


class SavedWorkflow(Device_Base):
    __tablename__ = 'saved_workflow'
    id = Column(Guid(), primary_key=True)
    workflow_id = Column(Guid(), nullable=False)
    action_id = Column(Guid(), nullable=False)
    accumulator = Column(Json(), nullable=False)
    app_instances = Column(PickleType(), nullable=False)

    def __init__(self, id, workflow_id, action_id, accumulator, app_instances):
        """Initializes an Argument object.

        Args:
            id (str): The workflow execution UID that this saved state refers to.
            workflow_id (str): The ID of the workflow that this saved state refers to.
            action_id (str): The currently executing action ID.
            accumulator (dict): The accumulator up to this point in the workflow.
            app_instances (str): The pickled app instances for the saved workflow
        """
        self.id = id
        self.workflow_id = workflow_id
        self.action_id = action_id
        self.accumulator = accumulator
        self.app_instances = app_instances
