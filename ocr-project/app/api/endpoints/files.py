import logging
from http import HTTPStatus
from pathlib import Path

from fastapi import APIRouter, File, UploadFile
from fastapi.responses import JSONResponse
from minio.error import S3Error
from sqlalchemy.exc import SQLAlchemyError

from app.constant.constant import BUCKET_FILE_STORAGE
from app.models.file import File as FileModel
from app.models.task import Task, TaskStatus
from app.repository.file_repository import file_repo
from app.repository.task_repository import task_repo
from app.services.file.file_service import FileService
from app.services.minio.minio_service import get_minio_client
from app.storage.file_storage import FileStorage
from app.worker.file_process_worker import process_file

logger = logging.getLogger(__name__)

ALLOWED_CONTENT_TYPES = {"application/pdf", "image/png", "image/jpeg"}

file_service = FileService(BUCKET_FILE_STORAGE, ALLOWED_CONTENT_TYPES)
file_storage = FileStorage(get_minio_client())

router = APIRouter()


@router.post("/files", status_code=HTTPStatus.CREATED)
async def upload_file(file: UploadFile = File(...)) -> JSONResponse:
    if not file_service.is_allowed_file_type(file.content_type):
        return JSONResponse(
            status_code=HTTPStatus.UNSUPPORTED_MEDIA_TYPE,
            content={
                "code": HTTPStatus.UNSUPPORTED_MEDIA_TYPE,
                "message": f"File type '{file.content_type}' is not allowed."
                f" Please upload a PDF, PNG, or JPG.",
            },
        )

    file_extension = Path(file.filename).suffix
    storage_path = f"{file.filename}-{file_extension}"

    try:
        await file_storage.upload_file(file, storage_path, BUCKET_FILE_STORAGE)
    except S3Error as e:
        return JSONResponse(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            content={
                "code": HTTPStatus.INTERNAL_SERVER_ERROR,
                "message": f"Failed to upload file to storage: {e}",
            },
        )

    file_model = FileModel(
        filename=file.filename,
        storage_path=storage_path,
        file_type=file.content_type,
    )

    try:
        saved_file = file_repo.add(file_model)

        task_model = Task(
            file_id=saved_file.id,
            status=TaskStatus.PENDING,
        )
        saved_task = task_repo.add(task_model)
        logger.info(
            "Created task %s for file %s",
            saved_task.id,
            str(saved_file.id),
        )
        process_file.delay(saved_task.id)
    except SQLAlchemyError as e:
        return JSONResponse(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            content={
                "code": HTTPStatus.INTERNAL_SERVER_ERROR,
                "message": f"Failed to save file metadata to database: {e}",
            },
        )

    return JSONResponse(
        status_code=HTTPStatus.CREATED,
        content={
            "message": "File upload accepted and is being processed.",
            "task_id": str(saved_task.id),
            "filename": file.filename,
            "status": TaskStatus.PENDING.value,
        },
    )
