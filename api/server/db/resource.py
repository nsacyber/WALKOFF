from pydantic import BaseModel, Any
from sqlalchemy import Column, String, JSON, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship, backref
from sqlalchemy.types import ARRAY
from typing import List


class ResourceModel(BaseModel):
    name: str
    permissions: List[str]
