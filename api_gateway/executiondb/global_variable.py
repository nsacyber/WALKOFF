import logging
from uuid import UUID

from sqlalchemy import Column, String
from marshmallow import EXCLUDE
from marshmallow_sqlalchemy import field_for

from api_gateway.executiondb import Base, VariableMixin, BaseSchema


logger = logging.getLogger(__name__)


# TODO: add in an is_encrypted bool for globals
class GlobalVariable(VariableMixin, Base):
    """SQLAlchemy ORM class for Global, which are variables that can be dynamically loaded into workflow
       execution

    Attributes:
        id_ (UUID): The ID of the object
        name (str): The name of the environment variable
        value (any): The value of the object
        description (str): A description of the object

    """
    __tablename__ = 'global_variable'
    description = Column(String(255), default="")

class GlobalVariableSchema(BaseSchema):
    """Schema for global variables
    """

    class Meta:
        model = GlobalVariable
        unknown = EXCLUDE

