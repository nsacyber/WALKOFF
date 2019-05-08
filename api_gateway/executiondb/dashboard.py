import logging
from uuid import uuid4

from sqlalchemy import Column, String, Integer, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, backref
from sqlalchemy_utils import UUIDType
from marshmallow import fields, EXCLUDE

from api_gateway.executiondb import Base, BaseSchema

logger = logging.getLogger(__name__)


class Dashboard(Base):
    __tablename__ = 'dashboard'
    id_ = Column(UUID(as_uuid=True), primary_key=True, unique=True, nullable=False, default=uuid4)

    name = Column(String(255), nullable=False, unique=True)
    widgets = relationship('Widget', backref=backref('dashboard'), cascade="all, delete-orphan", passive_deletes=True)


class Widget(Base):
    __tablename__ = 'widget'
    id_ = Column(UUID(as_uuid=True), primary_key=True, unique=True, nullable=False, default=uuid4)

    name = Column(String, nullable=False)
    type_ = Column(String, nullable=False)
    x = Column(Integer, nullable=False)
    y = Column(Integer, nullable=False)
    cols = Column(Integer, nullable=False)
    rows = Column(Integer, nullable=False)
    options = Column(JSON, default={})

    dashboard_id = Column(UUIDType(binary=False), ForeignKey('dashboard.id_', ondelete='CASCADE'))


class WidgetSchema(BaseSchema):
    """Schema for Dashboard Widgets"""

    class Meta:
        model = Widget
        unknown = EXCLUDE
        # exclude = ('dashboard',)


class DashboardSchema(BaseSchema):
    """Schema for Dashboards"""

    widgets = fields.Nested(WidgetSchema, many=True)

    class Meta:
        model = Dashboard
        unknown = EXCLUDE
