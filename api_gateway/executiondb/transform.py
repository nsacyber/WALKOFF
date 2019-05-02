import logging

from sqlalchemy import Column, String, JSON, ForeignKey, event
from sqlalchemy_utils import UUIDType
from marshmallow import EXCLUDE

from api_gateway.executiondb import Base, NodeMixin, BaseSchema

logger = logging.getLogger(__name__)


class Transform(NodeMixin, Base):
    __tablename__ = 'transform'
    workflow_id = Column(UUIDType(binary=False), ForeignKey('workflow.id_', ondelete='CASCADE'))

    transform = Column(String(80), nullable=False)
    parameter = Column(JSON, nullable=False)

    def __init__(self, **kwargs):
        super(Transform, self).__init__(**kwargs)
        self.validate()

    def validate(self):
        """Validates the object"""
        # TODO: Implement validation of transform against asteval library if/when advanced transforms are implemented
        self.errors = []


@event.listens_for(Transform, 'before_update')
def validate_before_update(mapper, connection, target):
    target.validate()


class TransformSchema(BaseSchema):
    """Schema for transforms
    """

    class Meta:
        model = Transform
        unknown = EXCLUDE
