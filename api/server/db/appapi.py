import logging
from typing import List
from uuid import UUID

import semver
from pydantic import BaseModel, validator, AnyUrl, EmailStr

from api.server.db import IDBaseModel
from api.server.db.action import ActionApiModel  # ActionApiSchema,

logger = logging.getLogger("API")


class AppApiContactModel(BaseModel):
    name: str = ""
    url: AnyUrl = None
    email: EmailStr = None


class AppApiLicenseModel(BaseModel):
    name: str = ""
    url: AnyUrl = None


class AppExternalDocModel(BaseModel):
    description: str = ""
    url: AnyUrl = None


class AppApiModel(IDBaseModel):
    id_: UUID = None
    name: str
    app_version: str = "1.0.0"
    walkoff_version: str = "1.0.0"
    description: str = ""
    contact_info: AppApiContactModel = None
    license_info: AppApiLicenseModel = None
    external_docs: AppExternalDocModel = None
    actions: List[ActionApiModel]

    @validator('app_version')
    def app_version_is_semver(cls, value, values):
        semver.parse(value)
        return value

    @validator('walkoff_version')
    def walkoff_version_is_semver(cls, value, values):
        semver.parse(value)
        return value


# class AppApi(Base):
#     __tablename__ = "app_api"
#
#     # Columns common to all DB models
#     id_ = Column(UUID(as_uuid=True), primary_key=True, unique=True, nullable=False, default=uuid4)
#
#     # Columns specific to AppApi model
#     name = Column(String(), nullable=False, unique=True)
#     app_version = Column(String(), nullable=False)
#     walkoff_version = Column(String(), nullable=False)
#     description = Column(String(), default="")
#     contact_info = Column(JSON, default={})
#     license_info = Column(JSON, default={})
#     external_docs = Column(JSON, default={})
#     actions = relationship('ActionApi', backref='app_api', cascade="all, delete-orphan", passive_deletes=True)
#
#     def __init__(self, **kwargs):
#         super(AppApi, self).__init__(**kwargs)
#         self.validate()
#
#     def validate(self):
#         """Validates the object"""
#         # ToDo: Allow broken App APIs to be visible on frontend with errors
#         pass
#
#
# class AppApiSchema(BaseSchema):
#     """
#     Schema for App API
#     """
#     actions = fields.Nested(ActionApiSchema, many=True)
#
#     class Meta:
#         model = AppApi
#         unknown = EXCLUDE

    # @validates_schema
    # def validate_app_api(self, data, **kwargs):
    #     # Enforce Semantic Versioning
    #     for key in ("walkoff_version", "app_version"):
    #         try:
    #             semver.parse(data[key])
    #         except ValueError as e:
    #             raise MarshmallowValidationError(f"Error in {key}: {e}")

        # # Version in name and app_version must match
        # name = data["name"].split(":")
        # if len(name) != 2:
        #     raise MarshmallowValidationError(f"App name must follow the format app_name:1.2.3")
        # else:
        #     if name[1] != data["app_version"]:
        #         raise MarshmallowValidationError(f"Version in app_name must match version in app_version")
