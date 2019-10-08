import logging
from uuid import uuid4, UUID
from typing import List
from pydantic import BaseModel, ValidationError, validator


logger = logging.getLogger(__name__)


class TransformModel(BaseModel):
    id_: UUID = None
    errors: List[str] = []
    is_valid: bool = True
    app_name: str
    app_version: str = None
    name: str
    label: str
    position: dict = {"x": 0, "y": 0, "_walkoff_type": "position"}
    _walkoff_type: str = "transform"


# class Transform(Base):
#     __tablename__ = 'transform'
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
#     children = []
#
#     # Columns specific to Transform model
#     transform = Column(String(), nullable=False)
#
#     def __init__(self, **kwargs):
#         super(Transform, self).__init__(**kwargs)
#         self.position["_walkoff_type"] = "position"
#         self._walkoff_type = self.__tablename__
#         self.validate()
#
#     def validate(self):
#         """Validates the object"""
#         # TODO: Implement validation of transform against asteval library if/when advanced transforms are implemented
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
# class TransformSchema(BaseSchema):
#     """Schema for transforms
#     """
#     errors = field_for(Transform, "errors", dump_only=True)
#     is_valid = field_for(Transform, "is_valid", dump_only=True)
#
#     class Meta:
#         model = Transform
#         unknown = EXCLUDE
