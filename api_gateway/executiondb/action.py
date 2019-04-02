import logging

from sqlalchemy import Column, ForeignKey, String, Integer, orm, event
from sqlalchemy.orm import relationship
from sqlalchemy_utils import UUIDType
from marshmallow import fields, EXCLUDE
from marshmallow_sqlalchemy import field_for

from api_gateway.executiondb import Execution_Base
from api_gateway.executiondb.parameter import Parameter, ParameterSchema, ParameterApiSchema
from api_gateway.executiondb.returns import ReturnApi, ReturnApiSchema
from api_gateway.executiondb.position import PositionSchema
from api_gateway.executiondb.executionelement import ExecutionElement
from api_gateway.executiondb.schemas import ExecutionElementBaseSchema

logger = logging.getLogger(__name__)


class ActionApi(ExecutionElement, Execution_Base):
    __tablename__ = 'action_api'
    name = Column(String(), nullable=False)
    description = Column(String())
    returns = relationship("ReturnApi", uselist=False, cascade="all, delete-orphan", passive_deletes=True)
    parameters = relationship("ParameterApi", cascade="all, delete-orphan", passive_deletes=True)
    app_api_id = Column(UUIDType(binary=False), ForeignKey('app_api.id_', ondelete='CASCADE'))
    action_id = Column(UUIDType(binary=False), ForeignKey('action.id_', ondelete='CASCADE'))

    def __init__(self, name, id_=None, errors=None, description=None, returns=None, parameters=None):
        ExecutionElement.__init__(self, id_, errors)

        self.name = name
        self.description = description if description else ""
        self.returns = returns
        self.parameters = parameters if parameters else []


class ActionApiSchema(ExecutionElementBaseSchema):
    """Schema for actions
    """
    name = field_for(ActionApi, 'name', required=True)
    description = field_for(ActionApi, 'description')
    returns = fields.Nested(ReturnApiSchema())
    parameters = fields.Nested(ParameterApiSchema, many=True)

    class Meta:
        model = ActionApi
        unknown = EXCLUDE


class Action(ExecutionElement, Execution_Base):
    __tablename__ = 'action'
    workflow_id = Column(UUIDType(binary=False), ForeignKey('workflow.id_', ondelete='CASCADE'))
    app_name = Column(String(80), nullable=False)
    app_version = Column(String(80), nullable=False)
    name = Column(String(80), nullable=False)
    label = Column(String(80), nullable=False)
    priority = Column(Integer)

    parameters = relationship('Parameter', cascade='all, delete, delete-orphan', foreign_keys=[Parameter.action_id],
                              passive_deletes=True)
    position = relationship('Position', uselist=False, cascade='all, delete-orphan', passive_deletes=True)
    children = ('parameters',)

    def __init__(self, app_name, app_version, name, label, priority=3, id_=None, parameters=None,
                 position=None, errors=None):
        """Initializes a new Action object. A Workflow has one or more actions that it executes.
        Args:
            app_name (str): The name of the app associated with the Action
            name (str): The name of the action
            label (str): The label of the Action object.
             priority (int, optional): Optional priority parameter; defaults to 3 (normal priority).
            id_ (str|UUID, optional): Optional UUID to pass into the Action. Must be UUID object or valid UUID string.
                Defaults to None.
            parameters (list[Argument], optional): A list of Argument objects that are parameters to the action.
                Defaults to None.
            position (Position, optional): Position object for the Action. Defaults to None.
        """
        ExecutionElement.__init__(self, id_, errors)

        self.app_name = app_name
        self.app_version = app_version
        self.name = name
        self.label = label
        self.priority = priority

        self.parameters = parameters if parameters else []

        self.position = position

        self.validate()

    @orm.reconstructor
    def init_on_load(self):
        """Loads all necessary fields upon Action being loaded from database"""
        if not self.errors:
            self.errors = []
        #     try:
        #         self._arguments_api = get_app_action_api(self.app_name, self.name)
        #     except UnknownApp:
        #         errors.append(f'Unknown app {self.app_name}')
        #     except UnknownAppAction:
        #         errors.append(f'Unknown app action {self.name}')
        #     self.errors = errors

    def validate(self):
        """Validates the object"""
        self.errors = []
        # try:
        #     validate_app_action_parameters(self._arguments_api, self.parameters, self.app_name, self.name)
        # except UnknownApp:
        #     errors.append(f'Unknown app {self.app_name}')
        # except UnknownAppAction:
        #     errors.append(f'Unknown app action {self.name}')
        # except InvalidParameter as e:
        #     errors.extend(e.errors)
        # self.errors = errors


@event.listens_for(Action, 'before_update')
def validate_before_update(mapper, connection, target):
    target.validate()


class ActionSchema(ExecutionElementBaseSchema):
    """Schema for actions
    """
    app_name = field_for(Action, 'app_name', required=True)
    app_version = field_for(Action, 'app_version', required=True)
    name = field_for(Action, 'name', required=True)
    label = field_for(Action, 'label', required=True)
    parameters = fields.Nested(ParameterSchema, many=True)
    priority = field_for(Action, 'priority', default=3)
    position = fields.Nested(PositionSchema())

    class Meta:
        model = Action
        unknown = EXCLUDE
