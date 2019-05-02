import logging

from sqlalchemy import Column, ForeignKey, String, Integer, JSON
from sqlalchemy.orm import relationship
from sqlalchemy_utils import UUIDType
from marshmallow import fields, EXCLUDE
from marshmallow_sqlalchemy import field_for

from api_gateway.executiondb import Base, IDMixin, BaseSchema, NodeMixin
from api_gateway.executiondb.parameter import Parameter, ParameterSchema, ParameterApiSchema
from api_gateway.executiondb.returns import ReturnApiSchema

logger = logging.getLogger(__name__)


class ActionApi(IDMixin, Base):
    __tablename__ = 'action_api'
    name = Column(String(), nullable=False)
    node_type = Column(String(), nullable=False, default="ACTION")  # ToDo: determine if a separate condition/transform api object is needed
    location = Column(String(), nullable=False)
    description = Column(String(), default="")
    returns = relationship("ReturnApi", uselist=False, cascade="all, delete-orphan", passive_deletes=True)
    parameters = relationship("ParameterApi", cascade="all, delete-orphan", passive_deletes=True)

    app_api_id = Column(UUIDType(binary=False), ForeignKey('app_api.id_', ondelete='CASCADE'))


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


class Action(NodeMixin, Base):
    __tablename__ = 'action'
    priority = Column(Integer, default=3)
    parameters = relationship('Parameter', cascade='all, delete, delete-orphan', foreign_keys=[Parameter.action_id],
                              passive_deletes=True)

    workflow_id = Column(UUIDType(binary=False), ForeignKey('workflow.id_', ondelete='CASCADE'))

    def __init__(self, **kwargs):
        super(Action, self).__init__(**kwargs)
        self.validate()

    def validate(self):
        self.errors = []


class ActionSchema(BaseSchema):
    """
    Schema for actions
    """
    parameters = fields.Nested(ParameterSchema, many=True)

    class Meta:
        model = Action
        unknown = EXCLUDE
        dump_only = ("errors", "is_valid")
