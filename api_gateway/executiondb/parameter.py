import logging

from jsonschema import Draft4Validator, SchemaError, ValidationError as JSONSchemaValidationError

from sqlalchemy import Column, ForeignKey, String, JSON, orm, event, Boolean
from sqlalchemy_utils import UUIDType
from marshmallow import fields, EXCLUDE, validates_schema, ValidationError as MarshmallowValidationError
from marshmallow_sqlalchemy import field_for

from api_gateway.executiondb.schemas import ExecutionElementBaseSchema

from api_gateway.executiondb import Execution_Base
from api_gateway.executiondb.executionelement import ExecutionElement

from common.workflow_types import ParameterVariant

logger = logging.getLogger(__name__)


class ParameterApi(Execution_Base, ExecutionElement):
    __tablename__ = 'parameter_api'
    action_api_id = Column(UUIDType(binary=False), ForeignKey('action_api.id_', ondelete='CASCADE'))
    name = Column(String(), nullable=False)
    location = Column(String(), nullable=False)
    description = Column(String())
    example = Column(JSON)
    required = Column(Boolean())
    placeholder = Column(JSON)
    schema = Column(JSON)

    def __init__(self, name, location, id_=None, errors=None, description=None, example=None, required=False,
                 placeholder=None, schema=None):
        ExecutionElement.__init__(self, id_, errors)
        self.name = name
        self.location = location
        self.description = description if description else ""
        self.example = example if example else ""
        self.required = required if required else False
        self.placeholder = placeholder if placeholder else ""
        self.schema = schema if schema else {}

    def generate_parameter_from_default(self):
        return Parameter(self.name, ParameterVariant.STATIC_VALUE.name, value=self.placeholder)


class ParameterApiSchema(ExecutionElementBaseSchema):
    name = field_for(ParameterApi, 'name', required=True)
    location = field_for(ParameterApi, 'location', required=True)
    description = field_for(ParameterApi, 'description')
    example = field_for(ParameterApi, 'example')
    required = field_for(ParameterApi, 'required')
    placeholder = field_for(ParameterApi, 'placeholder')
    schema = field_for(ParameterApi, 'schema')

    class Meta:
        model = ParameterApi
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
                if "placeholder" in data:
                    stage = "placeholder"
                    v.validate(data["placeholder"])
        except (SchemaError, JSONSchemaValidationError) as e:
            message = "Unspecified Error"
            if stage == "schema":
                message = str(e)
            elif stage == "example":
                message = (f"Parameter {data['name']} has example {data['example']} which is not valid under the "
                           f"given schema {data['schema']}")
            elif stage == "placeholder":
                message = (f"Parameter {data['name']} has placeholder {data['placeholder']} which is not valid under "
                           f"the given schema {data['schema']}")
            raise MarshmallowValidationError(message)


class Parameter(Execution_Base, ExecutionElement):
    __tablename__ = 'parameter'
    action_id = Column(UUIDType(binary=False), ForeignKey('action.id_', ondelete='CASCADE'))
    transform_id = Column(UUIDType(binary=False), ForeignKey('transform.id_', ondelete='CASCADE'))
    name = Column(String(255), nullable=False)
    variant = Column(String(255), nullable=False)
    value = Column(JSON)

    def __init__(self, name, variant, id_=None, errors=None, value=None):
        """Initializes an Parameter object.

        Args:
            name (str): The name of the Parameter.
            value (any, optional): The value of the Parameter. Defaults to None. Value or reference must be included.
            variant (str): string corresponding to a ParameterVariant. Denotes static value, action output, global, etc.
        """
        ExecutionElement.__init__(self, id_, errors)
        self.name = name
        self.variant = variant
        self.value = value
        self.validate()

    @orm.reconstructor
    def init_on_load(self):
        """Loads all necessary fields upon Parameter being loaded from database"""
        pass

    def validate(self):
        pass


@event.listens_for(Parameter, 'before_update')
def validate_before_update(mapper, connection, target):
    target.validate()


class ParameterSchema(ExecutionElementBaseSchema):
    """The schema for arguments.

    This class handles constructing the argument specially so that either a reference or a value is always non-null,
    but never both.
    """
    name = field_for(Parameter, 'name', required=True)
    value = field_for(Parameter, 'value')
    variant = field_for(Parameter, 'variant', required=True)

    class Meta:
        model = Parameter
        unknown = EXCLUDE
