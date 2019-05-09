import logging
import base64
from uuid import uuid4

from Crypto import Random
from Crypto.Cipher import AES
from flask import current_app
from jsonschema import Draft4Validator, SchemaError, ValidationError as JSONSchemaValidationError

from sqlalchemy import Column, String, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from marshmallow import fields, EXCLUDE, pre_load, validates_schema, ValidationError as MarshmallowValidationError

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
        f = open('/run/secrets/encryption_key')
        key = f.read()
        my_cipher = GlobalCipher(key)
        data['value'] = my_cipher.encrypt(data['value']).decode('utf-8')

        try:
            if "schema" in data:
                template = current_app.running_context.execution_db.session.query(GlobalVariableTemplate).filter(
                    GlobalVariableTemplate.id_ == data['schema']
                ).first()
                Draft4Validator(template.schema).validate(data['value'])
        except (SchemaError, JSONSchemaValidationError) as e:
            raise MarshmallowValidationError(str(e))


class GlobalCipher(object):

    def __init__(self, key):
        self.key = key

    def encrypt(self, raw):
        raw = self.pad(raw)
        iv = Random.new().read(AES.block_size)
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return base64.b64encode(iv + cipher.encrypt(raw))

    def decrypt(self, enc):
        enc = base64.b64decode(enc)
        iv = enc[:AES.block_size]
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return self.unpad(cipher.decrypt(enc[AES.block_size:])).decode('utf-8')

    @staticmethod
    def pad(x):
        return x + (32 - len(x) % 32) * chr(32 - len(x) % 32)

    @staticmethod
    def unpad(x):
        return x[:-ord(x[len(x)-1:])]
