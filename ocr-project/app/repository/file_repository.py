from sqlalchemy.exc import SQLAlchemyError

from app.db.session import SessionLocal
from app.models.file import File


class FileRepository:
    def add(self, file: File) -> File:
        session = SessionLocal()
        try:
            session.add(file)
            session.flush()
            session.commit()
            session.refresh(file)
        except SQLAlchemyError:
            session.rollback()
            raise
        finally:
            session.close()

        return file

    def get_by_id(self, file_id: str) -> File | None:
        session = SessionLocal()
        try:
            return session.query(File).filter(File.id == file_id).first()
        except SQLAlchemyError:
            session.rollback()
            raise
        finally:
            session.close()

    def update(self, file: File) -> None:
        session = SessionLocal()
        try:
            session.merge(file)
            session.commit()
        except SQLAlchemyError:
            session.rollback()
            raise
        finally:
            session.close()


file_repo = FileRepository()
