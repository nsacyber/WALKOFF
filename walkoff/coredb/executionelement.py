from walkoff.core.representable import Representable
from walkoff.dbtypes import Guid
from sqlalchemy import Column
from uuid import uuid4


class ExecutionElement(Representable):
    id = Column(Guid(), primary_key=True, default=uuid4, nullable=False, unique=True)

    def __init__(self, id):
        if id:
            self.uid = id

    def __repr__(self):
        representation = self.read()
        out = '<{0} at {1} : '.format(self.__class__.__name__, hex(id(self)))
        first = True
        for key, value in representation.items():
            if self.__is_list_of_dicts_with_uids(value):
                out += ', {0}={1}'.format(key, [list_value['uid'] for list_value in value])
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
                and all(isinstance(list_value, dict) and 'uid' in list_value for list_value in value))
