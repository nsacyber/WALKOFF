import json
from sqlalchemy import String
from sqlalchemy.types import TypeDecorator


class Json(TypeDecorator):
    impl = String

    def process_bind_param(self, value, dialect):
        try:
            ret = json.dumps(value)
        except ValueError:
            ret = value
        return ret

    def process_result_value(self, value, dialect):
        try:
            ret = json.loads(value)
        except ValueError:
            ret = json.loads(value)
        return ret

    def copy(self, **kw):
        return self.adapt(self.__class__)
