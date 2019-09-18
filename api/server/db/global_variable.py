import logging

from sqlalchemy.dialects.postgresql import UUID
from pydantic import BaseModel


from api.server.db.permissions import PermissionsModel

logger = logging.getLogger(__name__)


class GlobalVariable(BaseModel):
    id_: UUID = None
    _walkoff_type: str = "variable"
    name: str
    permissions: PermissionsModel
    value: str
    description: str = None


class GlobalVariableTemplate(BaseModel):
    id_: UUID = None
    _walkoff_type: str = "variable"
    name: str
    schema: object
    description: str = None
