import logging

from sqlalchemy import Column, String, JSON, ForeignKey, event
from sqlalchemy_utils import UUIDType
from marshmallow import EXCLUDE

from api_gateway.executiondb import Base, ValidatableMixin, BaseSchema

logger = logging.getLogger(__name__)


class Transform(ValidatableMixin, Base):
    __tablename__ = 'transform'
    workflow_id = Column(UUIDType(binary=False), ForeignKey('workflow.id_', ondelete='CASCADE'))

    name = Column(String(255), nullable=False)
    transform = Column(String(80), nullable=False)
    parameter = Column(JSON, nullable=False)
    position = Column(JSON, default={"x": 0, "y": 0})

    def __init__(self, **kwargs):
        super(Transform, self).__init__(**kwargs)
        self.validate()

    def validate(self):
        """Validates the object"""
        # TODO: Implement validation of transform against asteval library if/when advanced transforms are implemented
        pass


@event.listens_for(Transform, 'before_update')
def validate_before_update(mapper, connection, target):
    target.validate()


class TransformSchema(BaseSchema):
    """Schema for transforms
    """

    class Meta:
        model = Transform
        unknown = EXCLUDE
