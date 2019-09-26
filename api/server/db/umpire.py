import logging

from pydantic import BaseModel, ValidationError, validator

logger = logging.getLogger(__name__)


class UploadFile(BaseModel):

    app_name: str = None
    app_version: str = None
    file_path: str
    file_data: str = None


