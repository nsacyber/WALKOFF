import logging
from uuid import uuid4

from jsonschema import Draft4Validator, SchemaError, ValidationError as JSONSchemaValidationError
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Column, ForeignKey, String, JSON

from marshmallow import EXCLUDE, validates_schema, ValidationError as MarshmallowValidationError
from marshmallow_sqlalchemy import field_for

from api_gateway.executiondb import Base, BaseSchema

logger = logging.getLogger(__name__)


class ReturnApi(Base):
    __tablename__ = 'return_api'

    # Columns common to all DB models
    id_ = Column(UUID(as_uuid=True), primary_key=True, unique=True, nullable=False, default=uuid4)

    # Columns specific to ReturnApi model
    location = Column(String(), nullable=False)
    description = Column(String(), default="")
    example = Column(JSON, default="")
    schema = Column(JSON, default={})
    action_api_id = Column(UUID(as_uuid=True), ForeignKey('action_api.id_', ondelete='CASCADE'))


class ReturnApiSchema(BaseSchema):

    location = field_for(ReturnApi, "location", load_only=True)

    class Meta:
        model = ReturnApi
        unknown = EXCLUDE

    @validates_schema
    def validate_parameter_api(self, data, **kwargs):
        try:
            if "schema" in data:
                Draft4Validator.check_schema(data["schema"])
        except (SchemaError, JSONSchemaValidationError) as e:
            raise MarshmallowValidationError(e)
