import logging
from uuid import UUID

from api.server.db import IDBaseModel
from api.server.db.permissions import PermissionsModel

logger = logging.getLogger("API")


class GlobalVariable(IDBaseModel):
    id_: UUID = None
    walkoff_type_: str = "variable"
    name: str
    permissions: PermissionsModel
    value: str
    description: str = None

    class Config:
        schema_extra = {
            'example': [
                {
                    "name": "my_global",
                    "permissions": {
                        "access_level": 2,
                        "creator": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                        "role_permissions": [
                            {
                                "role": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                                "permissions": [
                                    "read",
                                    "update",
                                    "delete"
                                ]
                            }
                        ]
                    },
                    "value": "global_value",
                    "id_": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                    "description": "This is an example of a Global Variable."
                }
            ]
        }


class GlobalVariableTemplate(IDBaseModel):
    id_: UUID = None
    walkoff_type_: str = "variable"
    name: str
    json_schema: dict = {}
    description: str = None

