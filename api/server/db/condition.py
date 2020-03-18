import logging
from typing import List
from uuid import UUID

from api.server.db import IDBaseModel

logger = logging.getLogger("API")


class ConditionModel(IDBaseModel):
    id_: UUID = None
    errors: List[str] = []
    is_valid: bool = True
    app_name: str
    app_version: str = None
    name: str
    label: str
    position: dict = {"x": 0, "y": 0, "walkoff_type_": "position"}
    conditional: str = ""
    walkoff_type_: str = "condition"


# class Condition(Base):
#     __tablename__ = 'condition'
#
#     # Columns common to all DB models
#     id_ = Column(UUID(as_uuid=True), primary_key=True, unique=True, nullable=False, default=uuid4)
#
#     # Columns common to validatable Workflow components
#     errors = Column(ARRAY(String))
#     is_valid = Column(Boolean, default=True)
#
#     # Columns common to Workflow nodes
#     app_name = Column(String(80), nullable=False)
#     app_version = Column(String(80), nullable=False)
#     name = Column(String(255), nullable=False)
#     label = Column(String(80), nullable=False)
#     position = Column(JSON, default={"x": 0, "y": 0, "_walkoff_type": "position"})
#     workflow_id = Column(UUID(as_uuid=True), ForeignKey('workflow.id_', ondelete='CASCADE'))
#     _walkoff_type = Column(String(80), default=__tablename__)
#
#
#     # Columns specific to Condition model
#     conditional = Column(String(), nullable=False)
#     children = []
#
#     def __init__(self, **kwargs):
#         super(Condition, self).__init__(**kwargs)
#         self.position["_walkoff_type"] = "position"
#         self._walkoff_type = self.__tablename__
#         self.validate()
#
#     def validate(self):
#         """Validates the object"""
#         self.errors = []
#
#     def is_valid_rec(self):
#         if self.errors:
#             return False
#         for child in self.children:
#             child = getattr(self, child, None)
#             if isinstance(child, list):
#                 for actual_child in child:
#                     if not actual_child.is_valid_rec():
#                         return False
#             elif child is not None:
#                 if not child.is_valid_rec():
#                     return False
#         return True
#
#
# class ConditionSchema(BaseSchema):
#     """Schema for conditions
#     """
#     class Meta:
#         model = Condition
#         unknown = EXCLUDE
#         dump_only = ("errors", "is_valid")
#
