from uuid import UUID

from pydantic import BaseModel, Schema


class SettingsModel(BaseModel):
    id_: UUID
    access_token_life_mins: int = Schema(15, gt=1)
    refresh_token_life_days: int = Schema(90, gt=1)
    _name_field = "id_"
