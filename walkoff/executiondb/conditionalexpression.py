import logging
from sqlalchemy import Column, ForeignKey, Enum, orm, Boolean
from sqlalchemy.orm import relationship, backref
from sqlalchemy_utils import UUIDType

from walkoff.executiondb import Device_Base
from walkoff.executiondb.executionelement import ExecutionElement
from uuid import uuid4
from walkoff.helpers import InvalidArgument
from walkoff.events import WalkoffEvent
logger = logging.getLogger(__name__)

valid_operators = ('and', 'or', 'xor')


class ConditionalExpression(ExecutionElement, Device_Base):
    __tablename__ = 'conditional_expression'
    id = Column(UUIDType(), primary_key=True, default=uuid4)
    action_id = Column(UUIDType(), ForeignKey('action.id'))
    branch_id = Column(UUIDType(), ForeignKey('branch.id'))
    parent_id = Column(UUIDType(), ForeignKey(id))
    operator = Column(Enum(*valid_operators, name='operator_types'), nullable=False)
    is_negated = Column(Boolean, default=False)
    child_expressions = relationship('ConditionalExpression',
                                     cascade='all, delete-orphan',
                                     backref=backref('parent', remote_side=id))
    conditions = relationship(
        'Condition',
        cascade='all, delete-orphan')

    def __init__(self, operator='and', id=None, is_negated=False, child_expressions=None, conditions=None):
        ExecutionElement.__init__(self, id)
        self.operator = operator
        self.is_negated = is_negated
        if child_expressions:
            self._construct_children(child_expressions)
        self.child_expressions = child_expressions if child_expressions is not None else []
        self.conditions = conditions if conditions is not None else []
        self.__operator_lookup = {'and': self._and,
                                  'or': self._or,
                                  'xor': self._xor}

    @orm.reconstructor
    def init_on_load(self):
        self.__operator_lookup = {'and': self._and,
                                  'or': self._or,
                                  'xor': self._xor}

    def validate(self):
        pass

    def _construct_children(self, child_expressions):
        for child in child_expressions:
            child.parent = self

    def execute(self, data_in, accumulator):
        try:
            result = self.__operator_lookup[self.operator](data_in, accumulator)
            if self.is_negated:
                result = not result
            if result:
                WalkoffEvent.CommonWorkflowSignal.send(self, event=WalkoffEvent.ConditionalExpressionTrue)
            else:
                WalkoffEvent.CommonWorkflowSignal.send(self, event=WalkoffEvent.ConditionalExpressionFalse)
            return result
        except (InvalidArgument, Exception) as e:
            WalkoffEvent.CommonWorkflowSignal.send(self, event=WalkoffEvent.ConditionalExpressionError)
            return False

    def _and(self, data_in, accumulator):
        return (all(condition.execute(data_in, accumulator) for condition in self.conditions)
                and all(expression.execute(data_in, accumulator) for expression in self.child_expressions))

    def _or(self, data_in, accumulator):
        if not self.conditions and not self.child_expressions:
            return True
        return (any(condition.execute(data_in, accumulator) for condition in self.conditions)
                or any(expression.execute(data_in, accumulator) for expression in self.child_expressions))

    def _xor(self, data_in, accumulator):
        if not self.conditions and not self.child_expressions:
            return True
        is_one_found = False
        for condition in self.conditions:
            if condition.execute(data_in, accumulator):
                if is_one_found:
                    return False
                is_one_found = True
        for expression in self.child_expressions:
            if expression.execute(data_in, accumulator):
                if is_one_found:
                    return False
                is_one_found = True
        return is_one_found
