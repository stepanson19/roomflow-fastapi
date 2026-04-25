from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.settings import get_settings


class Base(DeclarativeBase):
    pass


settings = get_settings()
connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=connect_args)
session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db: Session = session_factory()
    try:
        yield db
    finally:
        db.close()
