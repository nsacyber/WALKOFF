from typing import List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from common.minio_helper import MinioApi


router = APIRouter()


class ListAllFilesReq(BaseModel):
    app_name: str
    app_version: str

@router.post("/files", summary="List all files given an app name and version.",
             response_model=List[str], response_description="List of all files in an app version.")
async def list_all_files(request: ListAllFilesReq):
    """
    Returns all files that exist under the specified app_name and version.

    Request Body Example:
    ```
    {
        "app_name": "hello_world",
        "app_version": "1.0.0"
    }
    ```

    Response Example:
    ```
    [
        "Dockerfile",
        "api.yaml",
        "docker-compose.yml",
        "env.txt",
        "requirements.txt",
        "src/app.py"
    ]
    ```
    """
    result = await MinioApi.list_files(request.app_name, request.app_version)
    return result


class GetFile(BaseModel):
    app_name: str
    app_version: str
    file_path: str

@router.post("/file", summary="Get contents of file given an app name, version, and file path relative to the app",
            response_description="Contents of file.")
async def get_file_contents(request: GetFile):
    """
    Returns contents of file at the specified app name, version, file path.

    Request Body Example:
    ```
    {
        "app_name": "hello_world",
        "app_version": "1.0.0",
        "file_path": "Dockerfile"
    }
    ```

    Response Example:
    ```
    # Use the Walkoff App SDK as a base image
    FROM 127.0.0.1:5000/walkoff_app_sdk as base

    # Stage - Install/build Python dependencies
    FROM base as builder

    <...the rest of the file...>
    ```
    """
    file_data = await MinioApi.get_file(request.app_name, request.app_version, request.file_path)
    return file_data


class UpdateFile(BaseModel):
    app_name: str
    app_version: str
    file_path: str
    file_data: str

# POST http://localhost:2828/file
# Body Params: app_name, app_version, file_path, file_data, file_size
#
@router.post("/file-upload", summary="Update contents of file given an app name, version, file path, and file data.",
             response_description="New contents of file.")
async def update_file(request: UpdateFile):
    """
    Updates contents of file at the specified app name, version, file path with the file data.

    Request Body Example:
    ```
    {
        "app_name": "hello_world",
        "app_version": "1.0.0",
        "file_path": "Dockerfile"
    }
    ```

    Response Example:
    ```
    # Use the Walkoff App SDK as a base image
    FROM 127.0.0.1:5000/walkoff_app_sdk as base

    # Stage - Install/build Python dependencies
    FROM base as builder

    <...the rest of the file...>
    ```
    """

    file_data_bytes = request.file_data.encode('utf-8')
    file_size = len(file_data_bytes)

    success, message = await MinioApi.update_file(request.app_name, request.app_version, request.file_path,
                                                  file_data_bytes, file_size)
    if success:
        await MinioApi.save_file(request.app_name, request.app_version)
        return f"You have updated {request.file_path}: {message}"
    else:
        raise HTTPException(status_code=400, detail="FILE NOT FOUND")


class SaveFile(BaseModel):
    app_name: str
    app_version: str


@router.post("/save")
async def save_file(request: SaveFile):
    app_name = request.app_name
    version = request.app_version
    result = await MinioApi.save_file(app_name, version)
    if result:
        return "Successful Update to Local Repo"
    else:
        return "Failed"
