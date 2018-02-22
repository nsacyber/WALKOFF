from sqlalchemy_utils import UUIDType

from sqlalchemy import Column
from uuid import uuid4


class ExecutionElement(object):
    id = Column(UUIDType(), primary_key=True, nullable=False, default=uuid4)

    def __init__(self, id):
        if id:
            self.id = id

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

    @staticmethod
    def __is_list_of_dicts_with_uids(value):
        return (isinstance(value, list)
                and all(isinstance(list_value, dict) and 'id' in list_value for list_value in value))
