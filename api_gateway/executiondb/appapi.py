import logging

from sqlalchemy import Column, String, ForeignKey, UniqueConstraint, Boolean, event
from sqlalchemy.orm import relationship, backref
from sqlalchemy_utils import UUIDType, JSONType
from marshmallow import fields, EXCLUDE
from marshmallow_sqlalchemy import field_for

from api_gateway.executiondb.schemas import ExecutionElementBaseSchema
from api_gateway.executiondb import Execution_Base
from api_gateway.executiondb.executionelement import ExecutionElement
from api_gateway.executiondb.action import ActionApiSchema

logger = logging.getLogger(__name__)


class AppApi(ExecutionElement, Execution_Base):
    __tablename__ = "app_api"
    name = Column(String(), nullable=False, unique=True)
    app_version = Column(String(), nullable=False)
    walkoff_version = Column(String(), nullable=False)
    description = Column(String())
    contact = Column(JSONType)
    license_ = Column(JSONType)
    external_docs = Column(JSONType)
    actions = relationship('ActionApi', backref='app_api', cascade="all, delete-orphan", passive_deletes=True)
    # __table_args__ = (UniqueConstraint("playbook_id", "name", name="_playbook_workflow"),)

    def __init__(self, name, app_version, walkoff_version, id_=None, errors=None, description=None, contact=None,
                 license_=None, external_docs=None, actions=None):
        ExecutionElement.__init__(self, id_, errors)
        self.name = name
        self.app_version = app_version
        self.walkoff_version = walkoff_version
        self.description = description
        self.contact = contact
        self.license_ = license_
        self.external_docs = external_docs
        self.actions = actions if actions is not None else []
        self.validate()

    def validate(self):
        """Validates the object"""


class AppApiSchema(ExecutionElementBaseSchema):
    name = field_for(AppApi, 'name', required=True)
    app_version = field_for(AppApi, 'app_version', required=True)
    walkoff_version = field_for(AppApi, 'walkoff_version', required=True)
    description = field_for(AppApi, 'description')
    contact = fields.Raw()
    license_ = fields.Raw()
    external_docs = fields.Raw()
    actions = fields.Nested(ActionApiSchema, many=True)

    class Meta:
        model = AppApi
        unknown = EXCLUDE
