from sqlalchemy.exc import SQLAlchemyError

from app.db.session import SessionLocal
from app.models.task import Task


class TaskRepository:
    def add(self, task: Task) -> None:
        session = SessionLocal()
        try:
            session.add(task)
            session.commit()
        except SQLAlchemyError:
            session.rollback()
            raise
        finally:
            session.close()

    def get_by_id(self, task_id: str) -> Task | None:
        session = SessionLocal()
        try:
            return session.query(Task).filter(Task.id == task_id).first()
        except SQLAlchemyError:
            session.rollback()
            raise
        finally:
            session.close()

    def update(self, task: Task) -> None:
        session = SessionLocal()
        try:
            session.merge(task)
            session.commit()
        except SQLAlchemyError:
            session.rollback()
            raise
        finally:
            session.close()


task_repo = TaskRepository()
