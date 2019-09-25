from pydantic import BaseModel, Any
from typing import List


class ResourceModel(BaseModel):
    name: str
    permissions: List[str]
