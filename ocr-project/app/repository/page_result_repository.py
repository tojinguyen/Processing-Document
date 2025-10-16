from sqlalchemy.exc import SQLAlchemyError

from app.db.session import SessionLocal
from app.models import PageResult


class PageResultRepository:
    def add(self, page_result: PageResult) -> None:
        session = SessionLocal()
        try:
            session.add(page_result)
            session.commit()
        except SQLAlchemyError:
            session.rollback()
            raise
        finally:
            session.close()


page_result_repo = PageResultRepository()
