import logging
from uuid import uuid4

from flask import current_app
from jsonschema import Draft4Validator, SchemaError, ValidationError as JSONSchemaValidationError

from sqlalchemy import Column, Integer, ForeignKey, String, orm, event, Boolean
from sqlalchemy_utils import UUIDType, JSONType, ScalarListType
from marshmallow import fields, EXCLUDE, validates_schema, ValidationError as MarshmallowValidationError
from marshmallow_sqlalchemy import field_for

from common.workflow_types import ParameterVariant

from api_gateway.executiondb.schemas import ExecutionElementBaseSchema

from api_gateway.helpers import validate_uuid4
from api_gateway.executiondb import Execution_Base
from api_gateway.executiondb.executionelement import ExecutionElement

logger = logging.getLogger(__name__)


class ParameterApi(Execution_Base, ExecutionElement):
    __tablename__ = 'parameter_api'
    action_api_id = Column(UUIDType(binary=False), ForeignKey('action_api.id_', ondelete='CASCADE'))
    name = Column(String(), nullable=False)
    location = Column(String(), nullable=False)
    description = Column(String())
    example = Column(JSONType)
    required = Column(Boolean())
    placeholder = Column(JSONType)
    schema = Column(JSONType)

    def __init__(self, name, location, id_=None, errors=None, description=None, example=None, required=False, placeholder=None,
                 schema=None):
        ExecutionElement.__init__(self, id_, errors)
        self.name = name
        self.location = location
        self.description = description if description else ""
        self.example = example if example else ""
        self.required = required if required else ""
        self.placeholder = placeholder if placeholder else ""
        self.schema = schema if schema else ""


class ParameterApiSchema(ExecutionElementBaseSchema):
    name = field_for(ParameterApi, 'name', required=True)
    location = field_for(ParameterApi, 'location', required=True)
    description = field_for(ParameterApi, 'description')
    example = fields.Raw()
    required = field_for(ParameterApi, 'required')
    placeholder = fields.Raw()
    schema = fields.Raw()

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
                message = f"Example given ({data['example']}) is not valid under the schema {data['schema']}"
            elif stage == "placeholder":
                message = f"Placeholder given ({data['placeholder']}) is not valid under the schema {data['schema']}"
            raise MarshmallowValidationError(message)


class Parameter(Execution_Base, ExecutionElement):
    __tablename__ = 'parameter'
    action_id = Column(UUIDType(binary=False), ForeignKey('action.id_', ondelete='CASCADE'))
    transform_id = Column(UUIDType(binary=False), ForeignKey('transform.id_', ondelete='CASCADE'))
    name = Column(String(255), nullable=False)
    variant = Column(String(255), nullable=False)
    value = Column(JSONType)

    def __init__(self, name, variant, id_=None, errors=None, value=None):
        """Initializes an Parameter object.

        Args:
            name (str): The name of the Parameter.
            value (any, optional): The value of the Parameter. Defaults to None. Value or reference must be included.
            variant (str): string corresponding to a ParameterVariant. Denotes static value, action output, global, etc.
            reference (int, optional): The ID of the Action, global, or WorkflowVariable from which to grab the result.
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
        # if self.variant != ParameterVariant.STATIC_VALUE.name:
        #     # Parameter is a reference, verify the uuid is valid
        #     if not validate_uuid4(self.value):
        #         message = f"Value is a reference but {self.value} is not a valid uuid4"
        #         logger.error(message)
        #         self.errors = [message]
        #     # ToDo: verify that the uuid exists in the workflow.
        #     # Doing this with SQLAlchemy results in circular imports.
        # else:
        #     # Parameter is a value, verify that the value is valid under the schema given in App Api, if applicable
        #     api = current_app.running_context.execution_db.session.query(ParameterApi).filter(
        #         ParameterApi.location == self.api_location
        #     ).first()
        #     try:
        #         Draft4Validator(api.schema).validate(self.value)
        #     except JSONSchemaValidationError as e:
        #         message = f"Parameter {self.name} has value {self.value} that is not valid under schema {api.schema}."
        #         logger.error(message)
        #         self.errors = [message]

    # def __eq__(self, other):
    #     return self.name == other.name and self.value == other.value and self.reference == other.reference \
    #            and self.variant == other.variant
    #
    # def __hash__(self):
    #     return hash(self.id_)


@event.listens_for(Parameter, 'before_update')
def validate_before_update(mapper, connection, target):
    target.validate()


class ParameterSchema(ExecutionElementBaseSchema):
    """The schema for arguments.

    This class handles constructing the argument specially so that either a reference or a value is always non-null,
    but never both.
    """
    name = field_for(Parameter, 'name', required=True)
    value = fields.Raw()
    variant = field_for(Parameter, 'variant', required=True)

    class Meta:
        model = Parameter
        unknown = EXCLUDE

    # @validates_schema
    # def validate_argument(self, data):
    #     has_value = 'value' in data
    #     has_reference = 'reference' in data and bool(data['reference'])
    #     if (not has_value and not has_reference) or (has_value and has_reference):
    #         raise ValidationError('Parameters must have either a value or a reference.', ['value'])
    #
    # @post_load
    # def make_instance(self, data):
    #     instance = self.instance or self.get_instance(data)
    #     if instance is not None:
    #         for key, value in data.items():
    #             setattr(instance, key, value)
    #         return instance
    #     return self.opts.model(**data)


