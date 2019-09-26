import logging
from typing import List, Union
from uuid import uuid4, UUID

from motor.motor_asyncio import AsyncIOMotorCollection
from pydantic import BaseModel

from common.helpers import validate_uuid


logger = logging.getLogger(__name__)


class WidgetModel(BaseModel):
    id_: UUID = None
    name: str
    type_: str
    x: int
    y: int
    cols: int
    rows: int
    options: dict = {}


class DashboardModel(BaseModel):
    id_: UUID = None
    name: str
    widgets: List[WidgetModel]
    _secondary_id = "name"

# class Dashboard(Base):
#     __tablename__ = 'dashboard'
#     id_ = Column(UUID(as_uuid=True), primary_key=True, unique=True, nullable=False, default=uuid4)
#
#     name = Column(String(255), nullable=False, unique=True)
#     widgets = relationship('Widget', backref=backref('dashboard'), cascade="all, delete-orphan", passive_deletes=True)


# class Widget(Base):
#     __tablename__ = 'widget'
#     id_ = Column(UUID(as_uuid=True), primary_key=True, unique=True, nullable=False, default=uuid4)
#
#     name = Column(String, nullable=False)
#     type_ = Column(String, nullable=False)
#     x = Column(Integer, nullable=False)
#     y = Column(Integer, nullable=False)
#     cols = Column(Integer, nullable=False)
#     rows = Column(Integer, nullable=False)
#     options = Column(JSON, default={})
#
#     dashboard_id = Column(UUID(as_uuid=True), ForeignKey('dashboard.id_', ondelete='CASCADE'))

#
# class WidgetSchema(BaseSchema):
#     """Schema for Dashboard Widgets"""
#
#     class Meta:
#         model = Widget
#         unknown = EXCLUDE
        # exclude = ('dashboard',)


# class DashboardSchema(BaseSchema):
#     """Schema for Dashboards"""
#
#     widgets = fields.Nested(WidgetSchema, many=True)
#
#     class Meta:
#         model = Dashboard
#         unknown = EXCLUDE
