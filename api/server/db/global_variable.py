import logging
from uuid import uuid4, UUID

from pydantic import BaseModel

from common.helpers import fernet_decrypt, fernet_encrypt
from api.server.db.permissions import PermissionsModel
from api.server.utils.helpers import JSON


logger = logging.getLogger(__name__)


class GlobalVariable(BaseModel):
    id_: UUID = uuid4()
    _walkoff_type: str = "variable"
    name: str
    permissions: PermissionsModel
    value: str
    description: str = None


class GlobalVariableTemplate(BaseModel):
    id_: UUID = None
    _walkoff_type: str = "variable"
    name: str
    json_schema: JSON = {}
    description: str = None
