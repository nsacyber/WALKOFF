import logging
import base64
import json
from uuid import uuid4

from flask import current_app
from jsonschema import Draft4Validator, SchemaError, ValidationError as JSONSchemaValidationError

from sqlalchemy import Column, String, JSON, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from marshmallow import fields, EXCLUDE, validates_schema, ValidationError as MarshmallowValidationError

from common.config import config
from common.helpers import fernet_decrypt, fernet_encrypt
from api_gateway.executiondb import Base, BaseSchema

logger = logging.getLogger(__name__)


class GlobalVariableTemplate(Base):

    __tablename__ = 'global_variable_template'

    # Columns common to all DB models
    id_ = Column(UUID(as_uuid=True), primary_key=True, unique=True, nullable=False, default=uuid4)

    # Columns specific to GlobalVariableTemplates
    name = Column(String(), nullable=False)
    schema = Column(JSON, default={}, nullable=False)
    description = Column(String(255), default="")
    _walkoff_type = Column(String(80), default="variable")


class GlobalVariable(Base):
    """SQLAlchemy ORM class for Global, which are variables that can be dynamically loaded into workflow
       execution

    Attributes:
        id_ (UUID): The ID of the object
        name (str): The name of the environment variable
        value (any): The value of the object
        description (str): A description of the object

    """
    __tablename__ = 'global_variable'

    # Columns common to all DB models
    id_ = Column(UUID(as_uuid=True), primary_key=True, unique=True, nullable=False, default=uuid4)

    # Columns common to all Variable models
    name = Column(String(80), nullable=False)
    value = Column(JSON)

    # Columns specific to GlobalVariables
    description = Column(String(255), default="")
    schema_id = Column(UUID(as_uuid=True), ForeignKey('global_variable_template.id_', ondelete='CASCADE'))
    permissions = Column(JSON)
    access_level = Column(Integer, default=1)
    creator = Column(Integer, default=2)
    _walkoff_type = Column(String(80), default="variable")


class GlobalVariableTemplateSchema(BaseSchema):
    """Schema for global variable template
    """

    class Meta:
        model = GlobalVariableTemplate
        unknown = EXCLUDE

    @validates_schema
    def validate_global_template(self, data, **kwargs):
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
    def validate_global(self, data, **kwargs):
        try:
            if "schema" in data:
                key = config.get_from_file(config.ENCRYPTION_KEY_PATH, 'rb')
                temp = fernet_decrypt(key, data['value'])
                Draft4Validator(data['schema']['schema']).validate(temp)

        except (SchemaError, JSONSchemaValidationError):
            raise MarshmallowValidationError(f"Global variable did not validate with provided schema: "
                                             f"{data['schema']['schema']}")
