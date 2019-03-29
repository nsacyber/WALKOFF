import logging
from uuid import uuid4

from jsonschema import Draft4Validator, SchemaError, ValidationError as JSONSchemaValidationError
from sqlalchemy import Column, ForeignKey, String
from sqlalchemy_utils import UUIDType, JSONType
from marshmallow import fields, EXCLUDE, validates_schema, ValidationError as MarshmallowValidationError
from marshmallow_sqlalchemy import field_for

from api_gateway.executiondb import Execution_Base
from api_gateway.executiondb.executionelement import ExecutionElement
from api_gateway.executiondb.schemas import ExecutionElementBaseSchema

logger = logging.getLogger(__name__)


class ReturnApi(ExecutionElement, Execution_Base):
    __tablename__ = 'return_api'
    action_api_id = Column(UUIDType(binary=False), ForeignKey('action_api.id_', ondelete='CASCADE'))
    description = Column(String())
    location = Column(String(), nullable=False)
    example = Column(JSONType)
    schema = Column(JSONType)

    def __init__(self, location, id_=None, errors=None, description=None, example=None, schema=None):
        ExecutionElement.__init__(self, id_, errors)
        self.location = location
        self.description = description
        self.example = example
        self.schema = schema


class ReturnApiSchema(ExecutionElementBaseSchema):
    location = field_for(ReturnApi, 'location', required=True)
    description = field_for(ReturnApi, 'description')
    example = fields.Raw()
    schema = fields.Raw()

    class Meta:
        model = ReturnApi
        unknown = EXCLUDE

    @validates_schema
    def validate_parameter_api(self, data):
        stage = ""
        try:
            if "schema" in data:
                stage = "schema"
                Draft4Validator.check_schema(data["schema"])
                v = Draft4Validator(data["schema"])
                if "example" in data:
                    stage = "example"
                    v.validate(data["example"])
        except (SchemaError, JSONSchemaValidationError) as e:
            message = "Unspecified Error"
            if stage == "schema":
                message = str(e)
            elif stage == "example":
                message = f"Example given ({data['example']}) is not valid under the schema {data['schema']}"
            raise MarshmallowValidationError(message)
