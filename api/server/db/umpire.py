import logging

from pydantic import BaseModel

logger = logging.getLogger("API")


class UploadFile(BaseModel):
    app_name: str = None
    app_version: str = None
    file_path: str
    file_data: str = None


