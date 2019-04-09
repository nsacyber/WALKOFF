import logging
from uuid import uuid4

from sqlalchemy import Column, String, Integer, ForeignKey, JSON
from sqlalchemy.orm import relationship, backref
from sqlalchemy_utils import UUIDType
from marshmallow import fields, EXCLUDE
from marshmallow_sqlalchemy import field_for

from api_gateway.executiondb.schemas import ExecutionBaseSchema
from api_gateway.helpers import validate_uuid4
from api_gateway.executiondb import Execution_Base

logger = logging.getLogger(__name__)


class Dashboard(Execution_Base):
    __tablename__ = 'dashboard'

    id_ = Column(UUIDType(binary=False), primary_key=True, default=uuid4)
    name = Column(String(255), nullable=False, unique=True)
    widgets = relationship('Widget', backref=backref('dashboard'), cascade="all, delete-orphan", passive_deletes=True)

    def __init__(self, name, id_=None, widgets=None):
        self.id_ = validate_uuid4(id_)
        self.name = name
        self.widgets = widgets


class Widget(Execution_Base):
    __tablename__ = 'widget'

    id_ = Column(UUIDType(binary=False), primary_key=True, default=uuid4)
    dashboard_id = Column(UUIDType(binary=False), ForeignKey('dashboard.id_', ondelete='CASCADE'))
    name = Column(String, nullable=False)
    type_ = Column(String, nullable=False)
    x = Column(Integer, nullable=False)
    y = Column(Integer, nullable=False)
    cols = Column(Integer, nullable=False)
    rows = Column(Integer, nullable=False)
    options = Column(JSON)

    def __init__(self, id_=None, name=None, type_=None, x=None, y=None, cols=None, rows=None, options=None):
        self.id_ = validate_uuid4(id_)
        self.name = name if name else ""
        self.type_ = type_ if type_ else ""
        self.x = x if x else 0
        self.y = y if y else 0
        self.cols = cols if cols else 1
        self.rows = rows if rows else 1
        self.options = options


class WidgetSchema(ExecutionBaseSchema):
    """Schema for Dashboard Widgets"""

    name = field_for(Widget, 'name', required=True)
    type_ = field_for(Widget, 'type_', required=True)
    x = field_for(Widget, 'x', required=True)
    y = field_for(Widget, 'y', required=True)
    cols = field_for(Widget, 'cols', required=True)
    rows = field_for(Widget, 'rows', required=True)
    options = field_for(Widget, 'options')

    class Meta:
        model = Widget
        exclude = ('dashboard',)
        unknown = EXCLUDE


class DashboardSchema(ExecutionBaseSchema):
    """Schema for Dashboards"""

    name = field_for(Dashboard, 'name')
    widgets = fields.Nested(WidgetSchema, many=True)

    class Meta:
        model = Dashboard
        unknown = EXCLUDE
