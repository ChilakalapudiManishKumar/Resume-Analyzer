"""
SQLAlchemy engine and session factory.

`Base` is the class every ORM model inherits from — SQLAlchemy uses it to
know which Python classes map to which database tables.

`get_db` is a generator used as a FastAPI dependency: it opens a session,
hands it to the route function, and guarantees the session is closed
afterwards (even if the route raises an exception) via try/finally.
"""
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import get_settings

settings = get_settings()

# check_same_thread=False is only needed for SQLite (it's single-threaded
# by default); it's harmless and ignored when the URL is postgresql://.
connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(settings.DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
