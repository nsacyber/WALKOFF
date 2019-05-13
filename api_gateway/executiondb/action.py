import logging
from uuid import uuid4

from sqlalchemy import Column, Boolean, ForeignKey, String, Integer, JSON
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship

from marshmallow import fields, EXCLUDE
from marshmallow_sqlalchemy import field_for

from api_gateway.executiondb import Base, BaseSchema
from api_gateway.executiondb.parameter import Parameter, ParameterSchema, ParameterApiSchema
from api_gateway.executiondb.returns import ReturnApiSchema

logger = logging.getLogger(__name__)


class ActionApi(Base):
    __tablename__ = 'action_api'

    # Columns common to all DB models
    id_ = Column(UUID(as_uuid=True), primary_key=True, unique=True, nullable=False, default=uuid4)

    # Columns specific to ActionApi
    name = Column(String(), nullable=False)
    # ToDo: determine if a separate condition/transform api object is needed
    node_type = Column(String(), nullable=False, default="ACTION")
    location = Column(String(), nullable=False)
    description = Column(String(), default="")
    returns = relationship("ReturnApi", uselist=False, cascade="all, delete-orphan", passive_deletes=True)
    parameters = relationship("ParameterApi", cascade="all, delete-orphan", passive_deletes=True)

    app_api_id = Column(UUID(as_uuid=True), ForeignKey('app_api.id_', ondelete='CASCADE'))


class ActionApiSchema(BaseSchema):
    """
    Schema for actions
    """

    location = field_for(ActionApi, "location", load_only=True)
    returns = fields.Nested(ReturnApiSchema)
    parameters = fields.Nested(ParameterApiSchema, many=True)

    class Meta:
        model = ActionApi
        unknown = EXCLUDE


class Action(Base):
    __tablename__ = 'action'

    # Columns common to all DB models
    id_ = Column(UUID(as_uuid=True), primary_key=True, unique=True, nullable=False, default=uuid4)

    # Columns common to validatable Workflow components
    errors = Column(ARRAY(String), default=[])
    is_valid = Column(Boolean, default=True)

    # Columns common to Workflow nodes
    app_name = Column(String(80), nullable=False)
    app_version = Column(String(80), nullable=False)
    name = Column(String(255), nullable=False)
    label = Column(String(80), nullable=False)
    position = Column(JSON, default={"x": 0, "y": 0})
    workflow_id = Column(UUID(as_uuid=True), ForeignKey('workflow.id_', ondelete='CASCADE'))

    # Columns specific to Actions
    priority = Column(Integer, default=3)
    parallel_parameter = relationship('Parameter', cascade='all, delete, delete-orphan',
                                      uselist=False, foreign_keys=[Parameter.parallel_action_id], passive_deletes=True)
    parameters = relationship('Parameter', cascade='all, delete, delete-orphan', foreign_keys=[Parameter.action_id],
                              passive_deletes=True)

    children = []

    def __init__(self, **kwargs):
        super(Action, self).__init__(**kwargs)
        self.validate()

    def validate(self):
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


class ActionSchema(BaseSchema):
    """
    Schema for actions
    """
    errors = field_for(Action, "errors", dump_only=True)
    is_valid = field_for(Action, "is_valid", dump_only=True)
    parameters = fields.Nested(ParameterSchema, many=True)
    parallel_parameter = fields.Nested(ParameterSchema)

    class Meta:
        model = Action
        unknown = EXCLUDE
