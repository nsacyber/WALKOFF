import logging

from sqlalchemy import Column, Enum

from walkoff.coredb import Device_Base, WorkflowStatusEnum
from walkoff.dbtypes import Guid
logger = logging.getLogger(__name__)


class WorkflowStatus(Device_Base):
    __tablename__ = 'workflow_status'
    workflow_execution_id = Column(Guid(), primary_key=True)
    workflow_id = Column(Guid(), nullable=False)
    status = Column(Enum(WorkflowStatusEnum), nullable=False)

    def __init__(self, workflow_execution_id, workflow_id, status):
        """Initializes an Argument object.

        Args:
            workflow_execution_id (str): The workflow execution UID that this saved state refers to.
            workflow_id (str): The ID of the workflow that this saved state refers to.
            status (enum): The status of the executing workflow.
        """
        self.workflow_execution_id = workflow_execution_id
        self.workflow_id = workflow_id
        self.status = status
