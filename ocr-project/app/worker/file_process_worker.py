import json
import logging
import uuid

from sqlalchemy.exc import SQLAlchemyError

from app.constant.constant import BUCKET_FILE_STORAGE, BUCKET_RESULT_STORAGE
from app.models import PageResult
from app.models.task import TaskStatus
from app.repository.file_repository import file_repo
from app.repository.page_result_repository import page_result_repo
from app.repository.task_repository import task_repo
from app.services.minio.minio_service import get_minio_client
from app.storage.result_storage import ResultStorage

from .celery import celery_app

logger = logging.getLogger(__name__)


@celery_app.task
def process_file(task_id: uuid.uuid4) -> None:
    task = task_repo.get_by_id(task_id)
    if not task:
        logger.error("Task with ID %s not found.", task_id)
        return

    file = file_repo.get_by_id(task.file_id)
    if not file:
        logger.error(
            "File with ID %s not found for task %s.",
            task.file_id,
            task_id,
        )
        task.status = TaskStatus.FAILED
        task.error_message = "Associated file not found."
        task_repo.update(task)
        return

    minio_client = get_minio_client()
    result_storage = ResultStorage(minio_client)

    # Update task status to PROCESSING
    try:
        task.status = TaskStatus.PROCESSING
        task_repo.update(task)
    except SQLAlchemyError:
        logger.exception(
            "Failed to update task %s status to PROCESSING",
            task_id,
        )
        return

    try:
        file_object = minio_client.get_object(
            BUCKET_FILE_STORAGE,
            file.storage_path,
        )
        file_data = file_object.read()
    except Exception as e:
        logger.exception(
            "Failed to retrieve file %s from MinIO for task %s",
            file.id,
            task_id,
        )
        task.status = TaskStatus.FAILED
        task.error_message = f"Failed to retrieve file: {e}"
        task_repo.update(task)
        return

    ocr_result = mock_ai_service(file_data, file.file_type)

    # Create PageResult entries and store results
    for page_data in ocr_result.get("pages", []):
        page_number = page_data["page_number"]
        page_text = page_data["text"]

        result_path = f"{file.id}/page_{page_number}.json"
        result_content = json.dumps({"text": page_text})

        logger.info(
            "Uploading result for file %s, page %d to %s",
            file.id,
            page_number,
            result_path,
        )

        result_storage.upload_result(
            result_content,
            result_path,
            BUCKET_RESULT_STORAGE,
        )

        page_result_entry = PageResult(
            task_id=task.id,
            file_id=file.id,
            page_number=page_number,
            result_path=result_path,
        )
        page_result_repo.add(page_result_entry)
        logger.info(
            "Saved PageResult for file %s, page %d",
            file.id,
            page_number,
        )

    # Update file and task status
    file.total_pages = ocr_result.get("total_pages")
    file_repo.update(file)

    # Mark task as completed
    task.status = TaskStatus.COMPLETED
    task_repo.update(task)


def mock_ai_service(file_data: bytes, file_type: str) -> dict:
    logger.info("Mock AI service processing file of type %s", file_type)
    logger.debug("File data size: %d bytes", len(file_data))
    if "pdf" in file_type:
        return {
            "total_pages": 3,
            "pages": [
                {"page_number": 1, "text": "This is the content of page 1."},
                {"page_number": 2, "text": "This is the content of page 2."},
                {"page_number": 3, "text": "This is the content of page 3."},
            ],
        }
    return {
        "total_pages": 1,
        "pages": [
            {"page_number": 1, "text": "This is the content of the image."},
        ],
    }
