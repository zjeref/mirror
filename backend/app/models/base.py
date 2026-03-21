import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import create_engine, func
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(default=func.now())
    updated_at: Mapped[datetime] = mapped_column(default=func.now(), onupdate=func.now())


def make_uuid() -> str:
    return str(uuid.uuid4())


# Lazy engine/session - initialized on first use
_engine = None
_SessionLocal = None


def get_engine():
    global _engine
    if _engine is None:
        from app.config import settings

        connect_args = {"check_same_thread": False} if settings.is_sqlite else {}
        _engine = create_engine(settings.database_url, connect_args=connect_args)
    return _engine


def get_session_factory():
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(bind=get_engine(), autocommit=False, autoflush=False)
    return _SessionLocal


def init_db(engine=None):
    """Create all tables. Used in dev/testing. Production uses Alembic."""
    target_engine = engine or get_engine()
    Base.metadata.create_all(bind=target_engine)


def get_session():
    session = get_session_factory()()
    try:
        yield session
    finally:
        session.close()
