import logging
from sqlalchemy import Column, ForeignKey, Enum, orm
from sqlalchemy.orm import relationship, backref

from walkoff.coredb import Device_Base
from walkoff.coredb.executionelement import ExecutionElement
from walkoff.dbtypes import Guid
from uuid import uuid4
from walkoff.helpers import InvalidExecutionElement
logger = logging.getLogger(__name__)


class ConditionalExpression(ExecutionElement, Device_Base):
    __tablename__ = 'conditional_expression'
    id = Column(Guid(), primary_key=True, default=uuid4)
    _action_id = Column(Guid(), ForeignKey('action.id'))
    _branch_id = Column(Guid(), ForeignKey('branch.id'))
    _parent_id = Column(Guid(), ForeignKey(id))
    operator = Column(Enum('truth', 'not', 'and', 'or', 'xor', name='operator_types'), nullable=False)
    child_expressions = relationship('ConditionalExpression',
                                     cascade='all, delete-orphan',
                                     backref=backref('parent', remote_side=id))
    conditions = relationship(
        'Condition',
        backref=backref('_expression'),
        cascade='all, delete-orphan')

    def __init__(self, operator, id=None, child_expressions=None, conditions=None, parent=None):
        ExecutionElement.__init__(self, id)
        if operator in ('truth', 'not') and len(child_expressions or []) + len(conditions or []) != 1:
            raise InvalidExecutionElement(
                self.id, 'None',
                'Conditional Expressions using "truth" or "not" must have 1 condition or child_expression')
        self.operator = operator
        if child_expressions:
            self._construct_children(child_expressions)
        self.child_expressions = child_expressions if child_expressions is not None else []
        self.conditions = conditions if conditions is not None else []
        self.__operator_lookup = {'and': self._and,
                                  'or': self._or,
                                  'xor': self._xor,
                                  'truth': self._truth,
                                  'not': self._not}
        self.parent = parent

    def _construct_children(self, child_expressions):
        for child in child_expressions:
            child.parent = self

    @orm.reconstructor
    def init_on_load(self):
        self.__operator_lookup = {'and': self._and,
                                  'or': self._or,
                                  'xor': self._xor,
                                  'truth': self._truth,
                                  'not': self._not}

    def execute(self, data_in, accumulator):
        return self.__operator_lookup[self.operator](data_in, accumulator)

    def _and(self, data_in, accumulator):
        return (all(condition.execute(data_in, accumulator) for condition in self.conditions)
                and all(expression.execute(data_in, accumulator) for expression in self.child_expressions))

    def _or(self, data_in, accumulator):
        return (any(condition.execute(data_in, accumulator) for condition in self.conditions)
                or any(expression.execute(data_in, accumulator) for expression in self.child_expressions))

    def _xor(self, data_in, accumulator):
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

    def __get_single_target(self):
        return self.conditions[0] if self.conditions else self.child_expressions[0]

    def _truth(self, data_in, accumulator):
        return self.__get_single_target().execute(data_in, accumulator)

    def _not(self, data_in, accumulator):
        return not self.__get_single_target().execute(data_in, accumulator)
