import json
from sqlalchemy import String
from sqlalchemy.types import TypeDecorator, CHAR
from sqlalchemy.dialects.postgresql import UUID
import uuid


class Json(TypeDecorator):
    impl = String

    def process_bind_param(self, value, dialect):
        try:
            ret = json.dumps(value)
        except ValueError:
            ret = str(value)
        return ret

    def process_result_value(self, value, dialect):
        try:
            ret = json.loads(value)
        except ValueError:
            ret = value
        return ret

    def copy(self, **kw):
        return self.adapt(self.__class__)


class Guid(TypeDecorator):
    """Platform-independent GUID type
    """
    impl = CHAR

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(UUID())
        else:
            return dialect.type_descriptor(CHAR(32))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return str(value)
        else:
            if not isinstance(value, uuid.UUID):
                return '%.32x' % uuid.UUID(value)
            else:
                return '%.32x' % value

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        else:
            return uuid.UUID(value)
