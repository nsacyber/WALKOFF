from api.server.db import Base, db
from sqlalchemy import Column, DateTime


class TrackModificationsMixIn(Base):
    created_at = Column(DateTime, default=db.func.current_timestamp())
    modified_at = Column(DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
