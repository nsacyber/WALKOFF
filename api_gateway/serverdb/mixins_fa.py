from sqlalchemy import Column, DateTime, func


class TrackModificationsMixIn(object):
    created_at = Column(DateTime, default=func.current_timestamp())
    modified_at = Column(DateTime, default=func.current_timestamp(), onupdate=func.current_timestamp())
