from http import HTTPStatus

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.repository.task_repository import task_repo

router = APIRouter()


@router.get("/tasks/{task_id}/status")
def get_task_status(task_id: str) -> JSONResponse:
    task = task_repo.get_by_id(task_id)
    if not task:
        return JSONResponse(
            status_code=HTTPStatus.NOT_FOUND,
            content={"detail": f"Task with ID {task_id} not found."},
        )

    return JSONResponse(
        status_code=HTTPStatus.OK,
        content={
            "task_id": str(task.id),
            "status": task.status.value,
            "error_message": task.error_message,
            "created_at": task.created_at,
            "updated_at": task.updated_at,
        },
    )
