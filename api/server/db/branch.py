import logging
from uuid import UUID

from api.server.db import IDBaseModel

logger = logging.getLogger("API")


class BranchModel(IDBaseModel):
    id_: UUID = None
    source_id: UUID
    destination_id: UUID
    walkoff_type_: str = "branch"


# class Branch(Base):
#     __tablename__ = 'branch'
#     id_ = Column(UUID(as_uuid=True), primary_key=True, unique=True, nullable=False, default=uuid4)
#
#     source_id = Column(UUID(as_uuid=True), nullable=False)
#     destination_id = Column(UUID(as_uuid=True), nullable=False)
#     _walkoff_type = Column(String(80), default=__tablename__)
#
#     workflow_id = Column(UUID(as_uuid=True), ForeignKey('workflow.id_', ondelete='CASCADE'))
#
#     def __init__(self, **kwargs):
#         super(Branch, self).__init__(**kwargs)
#         self._walkoff_type = self.__tablename__
#
#
# class BranchSchema(BaseSchema):
#     """Schema for branches
#     """
#
#     class Meta:
#         model = Branch
#         unknown = EXCLUDE
#         dump_only = ("errors", "is_valid")
