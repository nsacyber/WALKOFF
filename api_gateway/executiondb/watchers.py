import logging
from uuid import uuid4

from sqlalchemy import Column, ForeignKey, String, JSON, Enum, Boolean
from sqlalchemy.dialects.postgresql import UUID

from marshmallow import EXCLUDE, validates_schema, ValidationError as MarshmallowValidationError

from api_gateway.executiondb import Base, BaseSchema


logger = logging.getLogger(__name__)

class WatcherApi(Base):
    __tablename__ = 'watcher_api'

    # Columns common to all DB models
    id_ = Column(UUID(as_uuid=True), primary_key=True, unique=True, nullable=False, default=uuid4)

    # Columns specific to ParameterApi
    name = Column(String(), nullable=False)
    description = Column(String(), default="")
    arguments = Column(JSON, default="{}")
    action_api_id = Column(UUID(as_uuid=True), ForeignKey('action_api.id_', ondelete='CASCADE'))

class WatcherApiSchema(BaseSchema):
    class Meta:
        model = WatcherApi
        unknown = EXCLUDE


class Watcher(Base):
    __tablename__ = 'watcher'

    # Columns common to all DB models
    id_ = Column(UUID(as_uuid=True), primary_key=True, unique=True, nullable=False, default=uuid4)

    # Columns common to all Variable models
    name = Column(String(80), nullable=False)
    arguments = Column(JSON, default="{}")
    action_id = Column(UUID(as_uuid=True), ForeignKey('action.id_', ondelete='CASCADE'))
    _walkoff_type = Column(String(80), default=__tablename__)

    def __init__(self, **kwargs):
        super(Watcher, self).__init__(**kwargs)
        self._walkoff_type = self.__tablename__


class WatcherSchema(BaseSchema):
    class Meta:
        model = Watcher
        unknown = EXCLUDE
