import logging

from jsonschema import Draft4Validator, SchemaError, ValidationError as JSONSchemaValidationError

from sqlalchemy import Column, ForeignKey, String, JSON, Enum, Boolean
from sqlalchemy_utils import UUIDType
from marshmallow import EXCLUDE, validates_schema, ValidationError as MarshmallowValidationError
from marshmallow_sqlalchemy import field_for
from marshmallow_enum import EnumField

from api_gateway.executiondb import Base, IDMixin, VariableMixin, BaseSchema

from common.workflow_types import ParameterVariant

logger = logging.getLogger(__name__)


class ParameterApi(IDMixin, Base):
    __tablename__ = 'parameter_api'
    name = Column(String(), nullable=False)
    location = Column(String(), nullable=False)
    description = Column(String(), default="")
    required = Column(Boolean(), default=False)
    placeholder = Column(JSON, default="")
    schema = Column(JSON, default={})

    action_api_id = Column(UUIDType(binary=False), ForeignKey('action_api.id_', ondelete='CASCADE'))


class ParameterApiSchema(BaseSchema):

    location = field_for(ParameterApi, "location", load_only=True)

    class Meta:
        model = ParameterApi
        unknown = EXCLUDE

    @validates_schema
    def validate_parameter_api(self, data):
        try:
            if "schema" in data:
                Draft4Validator.check_schema(data["schema"])
        except (SchemaError, JSONSchemaValidationError) as e:
            raise MarshmallowValidationError(str(e))


class Parameter(VariableMixin, Base):
    __tablename__ = 'parameter'
    action_id = Column(UUIDType(binary=False), ForeignKey('action.id_', ondelete='CASCADE'))
    variant = Column(Enum(ParameterVariant), nullable=False)


class ParameterSchema(BaseSchema):

    variant = EnumField(ParameterVariant)

    class Meta:
        model = Parameter
        unknown = EXCLUDE
