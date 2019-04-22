import logging

from jsonschema import Draft4Validator, SchemaError, ValidationError as JSONSchemaValidationError
from sqlalchemy import Column, ForeignKey, String, JSON
from sqlalchemy_utils import UUIDType
from marshmallow import EXCLUDE, validates_schema, ValidationError as MarshmallowValidationError
from marshmallow_sqlalchemy import field_for

from api_gateway.executiondb import Base, IDMixin, BaseSchema

logger = logging.getLogger(__name__)


class ReturnApi(IDMixin, Base):
    __tablename__ = 'return_api'
    location = Column(String(), nullable=False)
    description = Column(String(), default="")
    example = Column(JSON, default="")
    schema = Column(JSON, default={})

    action_api_id = Column(UUIDType(binary=False), ForeignKey('action_api.id_', ondelete='CASCADE'))


class ReturnApiSchema(BaseSchema):

    location = field_for(ReturnApi, "location", load_only=True)

    class Meta:
        model = ReturnApi
        unknown = EXCLUDE

    @validates_schema
    def validate_parameter_api(self, data):
        try:
            if "schema" in data:
                Draft4Validator.check_schema(data["schema"])
        except (SchemaError, JSONSchemaValidationError) as e:
            raise MarshmallowValidationError(e)
