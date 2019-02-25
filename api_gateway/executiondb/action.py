import logging

from sqlalchemy import Column, ForeignKey, String, Integer, orm, event
from sqlalchemy.orm import relationship
from sqlalchemy_utils import UUIDType

from api_gateway.appgateway.apiutil import get_app_action_api, UnknownApp, UnknownAppAction, InvalidParameter
from api_gateway.appgateway.validator import validate_app_action_parameters
from api_gateway.executiondb import Execution_Base
from api_gateway.executiondb.parameter import Parameter
from api_gateway.executiondb.executionelement import ExecutionElement

logger = logging.getLogger(__name__)


class Action(ExecutionElement, Execution_Base):
    __tablename__ = 'action'
    workflow_id = Column(UUIDType(binary=False), ForeignKey('workflow._id', ondelete='CASCADE'))
    app_name = Column(String(80), nullable=False)
    action_name = Column(String(80), nullable=False)
    name = Column(String(80), nullable=False)
    priority = Column(Integer)

    parameters = relationship('Parameter', cascade='all, delete, delete-orphan', foreign_keys=[Parameter.action_id],
                              passive_deletes=True)
    position = relationship('Position', uselist=False, cascade='all, delete-orphan', passive_deletes=True)
    children = ('parameters',)

    def __init__(self, app_name, action_name, name, priority=3, _id=None, parameters=None,
                 position=None, errors=None):
        """Initializes a new Action object. A Workflow has one or more actions that it executes.
        Args:
            app_name (str): The name of the app associated with the Action
            action_name (str): The name of the action associated with a Action
            name (str): The name of the Action object.
             priority (int, optional): Optional priority parameter; defaults to 3 (normal priority).
            _id (str|UUID, optional): Optional UUID to pass into the Action. Must be UUID object or valid UUID string.
                Defaults to None.
            parameters (list[Argument], optional): A list of Argument objects that are parameters to the action.
                Defaults to None.
            position (Position, optional): Position object for the Action. Defaults to None.
        """
        ExecutionElement.__init__(self, _id, errors)

        self.app_name = app_name
        self.action_name = action_name
        self.name = name
        self.priority = priority

        self.parameters = []
        if parameters:
            self.parameters = parameters

        self.position = position

        self._arguments_api = None
        self.validate()

    @orm.reconstructor
    def init_on_load(self):
        """Loads all necessary fields upon Action being loaded from database"""
        if not self.errors:
            errors = []
            try:
                self._arguments_api = get_app_action_api(self.app_name, self.action_name)
            except UnknownApp:
                errors.append('Unknown app {}'.format(self.app_name))
            except UnknownAppAction:
                errors.append('Unknown app action {}'.format(self.action_name))
            self.errors = errors

    def validate(self):
        """Validates the object"""
        errors = []
        try:
            self._arguments_api = get_app_action_api(self.app_name, self.action_name)
            validate_app_action_parameters(self._arguments_api, self.parameters, self.app_name, self.action_name)
        except UnknownApp:
            errors.append('Unknown app {}'.format(self.app_name))
        except UnknownAppAction:
            errors.append('Unknown app action {}'.format(self.action_name))
        except InvalidParameter as e:
            errors.extend(e.errors)
        self.errors = errors


@event.listens_for(Action, 'before_update')
def validate_before_update(mapper, connection, target):
    target.validate()
