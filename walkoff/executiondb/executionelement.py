from uuid import uuid4

from sqlalchemy import Column
from sqlalchemy_utils import UUIDType, ScalarListType

from walkoff.executiondb.validatable import Validatable


class ExecutionElement(Validatable):
    id = Column(UUIDType(binary=False), primary_key=True, nullable=False, default=uuid4)
    errors = Column(ScalarListType(), nullable=True)

    def __init__(self, id=None, errors=None):
        if id:
            self.id = id
        if errors:
            self.errors = errors

    def __repr__(self):
        from .schemas import dump_element

        representation = dump_element(self)
        out = '<{0} at {1} : '.format(self.__class__.__name__, hex(id(self)))
        first = True
        for key, value in representation.items():
            if self.__is_list_of_dicts_with_uids(value):
                out += ', {0}={1}'.format(key, [list_value['id'] for list_value in value])
            else:
                out += ', {0}={1}'.format(key, value)

            if first:
                out = out.replace(" ,", "")
                first = False

        out += '>'
        return out

    def validate(self):
        pass

    @staticmethod
    def __is_list_of_dicts_with_uids(value):
        return (isinstance(value, list)
                and all(isinstance(list_value, dict) and 'id' in list_value for list_value in value))
