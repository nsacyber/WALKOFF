import logging
from uuid import UUID

from flask import current_app
from jsonschema import Draft4Validator, SchemaError, ValidationError as JSONSchemaValidationError

from sqlalchemy import Column, String, JSON, ForeignKey
from sqlalchemy_utils import UUIDType
from sqlalchemy.orm import relationship
from marshmallow import fields, EXCLUDE, validates_schema, ValidationError as MarshmallowValidationError

from api_gateway.executiondb import IDMixin, Base, VariableMixin, BaseSchema


logger = logging.getLogger(__name__)


class GlobalVariableTemplate(IDMixin, Base):

    __tablename__ = 'global_variable_template'
    name = Column(String(), nullable=False)
    schema = Column(JSON, default={}, nullable=False)
    description = Column(String(255), default="")


# TODO: add in an is_encrypted bool for globals
class GlobalVariable(VariableMixin, Base):
    """SQLAlchemy ORM class for Global, which are variables that can be dynamically loaded into workflow
       execution

    Attributes:
        id_ (UUID): The ID of the object
        name (str): The name of the environment variable
        value (any): The value of the object
        description (str): A description of the object

    """
    __tablename__ = 'global_variable'
    description = Column(String(255), default="")
    schema_id = Column(UUIDType(binary=False), ForeignKey('global_variable_template.id_', ondelete='CASCADE'))


class GlobalVariableTemplateSchema(BaseSchema):
    """Schema for global variable template
    """

    class Meta:
        model = GlobalVariableTemplate
        unknown = EXCLUDE

    @validates_schema
    def validate_global_template(self, data):
        try:
            Draft4Validator.check_schema(data["schema"])
        except (SchemaError, JSONSchemaValidationError) as e:
            raise MarshmallowValidationError(str(e))


class GlobalVariableSchema(BaseSchema):
    """Schema for global variables
    """

    schema = fields.Nested(GlobalVariableTemplateSchema)

    class Meta:
        model = GlobalVariable
        unknown = EXCLUDE

    @validates_schema
    def validate_global(self, data):
        try:
            if "schema" in data:
                template = current_app.running_context.execution_db.session.query(GlobalVariableTemplate).filter(
                    GlobalVariableTemplate.id_ == data['schema']
                ).first()
                Draft4Validator(template.schema).validate(data['value'])
        except (SchemaError, JSONSchemaValidationError) as e:
            raise MarshmallowValidationError(str(e))

