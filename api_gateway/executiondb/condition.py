import logging
from uuid import uuid4

from sqlalchemy import Column, String, Boolean, ForeignKey, JSON, event
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from asteval import Interpreter

from marshmallow import EXCLUDE

from api_gateway.executiondb import Base, BaseSchema

logger = logging.getLogger(__name__)


class Condition(Base):
    __tablename__ = 'condition'

    # Columns common to all DB models
    id_ = Column(UUID(as_uuid=True), primary_key=True, unique=True, nullable=False, default=uuid4)

    # Columns common to validatable Workflow components
    errors = Column(ARRAY(String))
    is_valid = Column(Boolean, default=True)

    # Columns common to Workflow nodes
    app_name = Column(String(80), nullable=False)
    app_version = Column(String(80), nullable=False)
    name = Column(String(255), nullable=False)
    label = Column(String(80), nullable=False)
    position = Column(JSON, default={"x": 0, "y": 0})
    workflow_id = Column(UUID(as_uuid=True), ForeignKey('workflow.id_', ondelete='CASCADE'))

    # Columns specific to Condition model
    conditional = Column(String(512), nullable=False)
    children = []

    def __init__(self, **kwargs):
        super(Condition, self).__init__(**kwargs)
        self.validate()

    def validate(self):
        """Validates the object"""
        self.errors = []

    def is_valid_rec(self):
        if self.errors:
            return False
        for child in self.children:
            child = getattr(self, child, None)
            if isinstance(child, list):
                for actual_child in child:
                    if not actual_child.is_valid_rec():
                        return False
            elif child is not None:
                if not child.is_valid_rec():
                    return False
        return True


class ConditionSchema(BaseSchema):
    """Schema for conditions
    """
    class Meta:
        model = Condition
        unknown = EXCLUDE
        dump_only = ("errors", "is_valid")

