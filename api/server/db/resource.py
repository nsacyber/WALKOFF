from typing import List

from pydantic import BaseModel


class ResourceModel(BaseModel):
    name: str
    permissions: List[str]
