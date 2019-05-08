import logging
from uuid import uuid4

from sqlalchemy import Column, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy_utils import UUIDType
from marshmallow import EXCLUDE

from api_gateway.executiondb import Base, BaseSchema


logger = logging.getLogger(__name__)


class Branch(Base):
    __tablename__ = 'branch'
    id_ = Column(UUID(as_uuid=True), primary_key=True, unique=True, nullable=False, default=uuid4)

    source_id = Column(UUIDType(binary=False), nullable=False)
    destination_id = Column(UUIDType(binary=False), nullable=False)

    workflow_id = Column(UUIDType(binary=False), ForeignKey('workflow.id_', ondelete='CASCADE'))


class BranchSchema(BaseSchema):
    """Schema for branches
    """

    class Meta:
        model = Branch
        unknown = EXCLUDE
        dump_only = ("errors", "is_valid")
