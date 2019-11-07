import logging
from typing import Union
from uuid import UUID

from api.server.db import IDBaseModel
from api.server.utils.helpers import JSONOrString
from common.workflow_types import ParameterVariant

# from jsonschema import Draft4Validator, SchemaError, ValidationError as JSONSchemaValidationError
#
# from sqlalchemy import Column, ForeignKey, String, JSON, Enum, Boolean
# from sqlalchemy.dialects.postgresql import UUID
#
# from marshmallow import EXCLUDE, validates_schema, ValidationError as MarshmallowValidationError
# from marshmallow_sqlalchemy import field_for, ModelSchema
# from marshmallow_enum import EnumField
#
# from api.server.db import Base, BaseSchema
#
# from common.workflow_types import ParameterVariant

logger = logging.getLogger("API")


class ParameterApiModel(IDBaseModel):
    id_: UUID = None
    name: str
    location: str = ""
    description: str = ""
    required: bool = False
    parallelizable: bool = False
    placeholder: Union[str, int, bool, dict, list, None] = None
    json_schema: dict = {}


class ParameterModel(IDBaseModel):
    id_: UUID = None
    name: str
    variant: ParameterVariant
    value: JSONOrString = None
    parallelized: bool = False
    walkoff_type_: str = "parameter"

    # @validator('value')
    # def global_variable_check(cls, value, values):
    #     global_col = mongo.reg_client.walkoff_db.globals
    #     if values.get("variant") == ParameterVariant.GLOBAL:
    #         global_check = global_col.find_one({"id_": values.get("id_")})
    #         if not global_check:
    #             raise ValidationError
    #     else:
    #         return value
    #
    # @validator('value')
    # def workflow_variable_check(cls, value, values):
    #     global_col = mongo.reg_client.walkoff_db.globals
    #     if values.get("variant") == ParameterVariant.WORKFLOW_VARIABLE:
    #         global_check = global_col.find_one({"id_": values.get("id_")})
    #         if not global_check:
    #             raise ValidationError
    #     else:
    #         return value
    #
    # @validator('value')
    # def action_result_check(cls, value, values):
    #     global_col = mongo.reg_client.walkoff_db.globals
    #     if values.get("variant") == ParameterVariant.ACTION_RESULT:
    #         global_check = global_col.find_one({"id_": values.get("id_")})
    #         if not global_check:
    #             raise ValidationError
    #     else:
    #         return value

# class ParameterApi(Base):
#     __tablename__ = 'parameter_api'
#
#     # Columns common to all DB models
#     id_ = Column(UUID(as_uuid=True), primary_key=True, unique=True, nullable=False, default=uuid4)
#
#     # Columns specific to ParameterApi
#     name = Column(String(), nullable=False)
#     location = Column(String(), nullable=False)
#     description = Column(String(), default="")
#     required = Column(Boolean(), default=False)
#     parallelizable = Column(Boolean(), default=False)
#     placeholder = Column(JSON, default="")
#     json_schema = Column(JSON, default={})
#     action_api_id = Column(UUID(as_uuid=True), ForeignKey('action_api.id_', ondelete='CASCADE'))
#
#
# class ParameterApiSchema(BaseSchema):
#
#     location = field_for(ParameterApi, "location", load_only=True)
#
#     class Meta:
#         model = ParameterApi
#         unknown = EXCLUDE
#
#     @validates_schema
#     def validate_parameter_api(self, data, **kwargs):
#         try:
#             if "json_schema" in data:
#                 Draft4Validator.check_schema(data["json_schema"])
#         except (SchemaError, JSONSchemaValidationError) as e:
#             raise MarshmallowValidationError(str(e))

#
# class Parameter(Base):
#     __tablename__ = 'parameter'
#
#     # Columns common to all DB models
#     id_ = Column(UUID(as_uuid=True), primary_key=True, unique=True, nullable=False, default=uuid4)
#
#     # Columns common to all Variable models
#     name = Column(String(80), nullable=False)
#     value = Column(JSON)
#
#     # Columns specific to Parameter model
#     action_id = Column(UUID(as_uuid=True), ForeignKey('action.id_', ondelete='CASCADE'))
#     parallelized = Column(Boolean(), nullable=False, default=False)
#     # parallel_action_id = Column(UUID(as_uuid=True), ForeignKey('action.id_', ondelete='CASCADE'))
#     variant = Column(Enum(ParameterVariant), nullable=False)
#     _walkoff_type = Column(String(80), default=__tablename__)
#
#     def __init__(self, **kwargs):
#         super(Parameter, self).__init__(**kwargs)
#         self._walkoff_type = self.__tablename__
#
#
# class ParameterSchema(ModelSchema):
#
#     variant = EnumField(ParameterVariant)
#
#     class Meta:
#         model = Parameter
#         unknown = EXCLUDE
