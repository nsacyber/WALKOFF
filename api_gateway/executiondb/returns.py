import logging

from jsonschema import Draft4Validator, SchemaError, ValidationError as JSONSchemaValidationError
from sqlalchemy import Column, ForeignKey, String, JSON
from sqlalchemy_utils import UUIDType
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
    example = Column(JSON)
    schema = Column(JSON)

    def __init__(self, id_=None, errors=None, description=None, example=None, schema=None):
        ExecutionElement.__init__(self, id_, errors)
        self.description = description if description else ""
        self.example = example if example else ""
        self.schema = schema if schema else ""


class ReturnApiSchema(ExecutionElementBaseSchema):
    description = field_for(ReturnApi, 'description')
    example = field_for(ReturnApi, 'example')
    schema = field_for(ReturnApi, 'schema')

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
