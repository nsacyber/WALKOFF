from uuid import uuid4

from pydantic import BaseModel


class IDBaseModel(BaseModel):

    _id_field: str = "id_"
    _name_field: str = "name"

    def __init__(self, **kwargs):
        super(IDBaseModel, self).__init__(**kwargs)
        if not getattr(self, self._id_field):
            setattr(self, self._id_field, uuid4())
