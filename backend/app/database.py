from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from .config import settings

# check_same_thread is a SQLite-only requirement for FastAPI's threaded workers.
connect_args = (
    {"check_same_thread": False}
    if settings.database_url.startswith("sqlite")
    else {}
)

engine = create_engine(settings.database_url, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI dependency: yields a session and always closes it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create tables and seed the two MVP users if absent."""
    from . import models  # noqa: F401 — register models on Base

    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        if db.query(models.User).count() == 0:
            db.add_all(
                [
                    models.User(name="Adi", role="requester"),
                    models.User(name="Faktor", role="developer"),
                ]
            )
            db.commit()
    finally:
        db.close()
