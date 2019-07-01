import logging
from uuid import uuid4

from jsonschema import Draft4Validator, SchemaError, ValidationError as JSONSchemaValidationError

from sqlalchemy import Column, ForeignKey, String, JSON, Enum, Boolean
from sqlalchemy.dialects.postgresql import UUID

from marshmallow import EXCLUDE, validates_schema, ValidationError as MarshmallowValidationError
from marshmallow_sqlalchemy import field_for
from marshmallow_enum import EnumField

from api_gateway.executiondb import Base, BaseSchema

from common.workflow_types import ParameterVariant

logger = logging.getLogger(__name__)


class ParameterApi(Base):
    __tablename__ = 'parameter_api'

    # Columns common to all DB models
    id_ = Column(UUID(as_uuid=True), primary_key=True, unique=True, nullable=False, default=uuid4)

    # Columns specific to ParameterApi
    name = Column(String(), nullable=False)
    location = Column(String(), nullable=False)
    description = Column(String(), default="")
    required = Column(Boolean(), default=False)
    parallelizable = Column(Boolean(), default=False)
    placeholder = Column(JSON, default="")
    schema = Column(JSON, default={})
    action_api_id = Column(UUID(as_uuid=True), ForeignKey('action_api.id_', ondelete='CASCADE'))


class ParameterApiSchema(BaseSchema):

    location = field_for(ParameterApi, "location", load_only=True)

    class Meta:
        model = ParameterApi
        unknown = EXCLUDE

    @validates_schema
    def validate_parameter_api(self, data, **kwargs):
        try:
            if "schema" in data:
                Draft4Validator.check_schema(data["schema"])
        except (SchemaError, JSONSchemaValidationError) as e:
            raise MarshmallowValidationError(str(e))


class Parameter(Base):
    __tablename__ = 'parameter'

    # Columns common to all DB models
    id_ = Column(UUID(as_uuid=True), primary_key=True, unique=True, nullable=False, default=uuid4)

    # Columns common to all Variable models
    name = Column(String(80), nullable=False)
    value = Column(JSON)

    # Columns specific to Parameter model
    action_id = Column(UUID(as_uuid=True), ForeignKey('action.id_', ondelete='CASCADE'))
    parallelized = Column(Boolean(), nullable=False, default=False)
    # parallel_action_id = Column(UUID(as_uuid=True), ForeignKey('action.id_', ondelete='CASCADE'))
    variant = Column(Enum(ParameterVariant), nullable=False)


class ParameterSchema(BaseSchema):

    variant = EnumField(ParameterVariant)

    class Meta:
        model = Parameter
        unknown = EXCLUDE
