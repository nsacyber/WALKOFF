import logging

from sqlalchemy import Column, ForeignKey
from sqlalchemy_utils import UUIDType
from marshmallow import EXCLUDE
from marshmallow_sqlalchemy import field_for

from api_gateway.executiondb import Base, IDMixin, BaseSchema


logger = logging.getLogger(__name__)


class Branch(IDMixin, Base):
    __tablename__ = 'branch'
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
