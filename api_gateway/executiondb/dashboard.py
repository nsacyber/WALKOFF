import logging
from uuid import uuid4, UUID

from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship, backref
from sqlalchemy_utils import UUIDType, JSONType

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
    options = Column(JSONType)

    def __init__(self, id_=None, name=None, type_=None, x=None, y=None, cols=None, rows=None, options=None):
        self.id_ = validate_uuid4(id_)
        self.name = name if name else ""
        self.type_ = type_ if type_ else ""
        self.x = x if x else 0
        self.y = y if y else 0
        self.cols = cols if cols else 1
        self.rows = rows if rows else 1
        self.options = options
