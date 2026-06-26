"""
Synchronous SQLAlchemy database setup.
Supports SQLite (default) and PostgreSQL via DATABASE_URL.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from typing import Generator

from app.config import get_settings

settings = get_settings()

# Adjust database URL if it uses async drivers (e.g. sqlite+aiosqlite -> sqlite)
database_url = settings.DATABASE_URL
if database_url.startswith("sqlite+aiosqlite"):
    database_url = database_url.replace("sqlite+aiosqlite", "sqlite")
elif database_url.startswith("postgresql+asyncpg"):
    database_url = database_url.replace("postgresql+asyncpg", "postgresql")

# For SQLite, we need connect_args to allow multi-threaded access
connect_args = {}
if database_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    database_url,
    echo=False,
    connect_args=connect_args,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a database session."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_db() -> None:
    """Create all database tables on startup."""
    from app.models import UseCase, Recommendation, Feedback  # noqa: F401
    Base.metadata.create_all(bind=engine)
