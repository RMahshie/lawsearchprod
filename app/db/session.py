"""Database session setup for persistent app state."""

from __future__ import annotations

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import get_settings


class Base(DeclarativeBase):
    pass


def _connect_args(database_url: str) -> dict[str, object]:
    """Return SQLAlchemy driver-specific connection arguments.

    Args:
        database_url: Database URL used to create the engine.

    Returns:
        Dictionary of connect_args passed to create_engine.
    """
    if database_url.startswith("sqlite"):
        return {"check_same_thread": False}
    return {}


settings = get_settings()
engine = (
    create_engine(
        settings.database_url,
        connect_args=_connect_args(settings.database_url),
        pool_pre_ping=True,
    )
    if settings.database_url
    else None
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False) if engine else None


def database_available() -> bool:
    """Report whether application metadata storage is configured.

    Args:
        None.

    Returns:
        True when an engine and session factory exist, otherwise False.
    """
    return engine is not None and SessionLocal is not None


def init_db() -> None:
    """Create application metadata tables if database storage is available.

    Args:
        None.

    Returns:
        None.
    """
    if engine is None:
        raise RuntimeError("DATABASE_URL is not configured")

    import app.db.models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    _add_query_run_columns()
    _drop_removed_query_source_columns()


def _add_query_run_columns() -> None:
    """Add compatible query history columns for existing SQLite metadata databases."""
    if engine is None:
        return

    with engine.begin() as connection:
        inspector = inspect(connection)
        if "query_runs" not in inspector.get_table_names():
            return

        existing_columns = {column["name"] for column in inspector.get_columns("query_runs")}
        if "number_annotations" not in existing_columns:
            connection.execute(text("ALTER TABLE query_runs ADD COLUMN number_annotations JSON"))


def _drop_removed_query_source_columns() -> None:
    """Drop obsolete saved-source columns from older metadata databases.

    Args:
        None.

    Returns:
        None.
    """
    if engine is None:
        return

    removed_columns = {"score", "content_snippet", "source_metadata"}
    with engine.begin() as connection:
        inspector = inspect(connection)
        if "query_sources" not in inspector.get_table_names():
            return

        existing_columns = {column["name"] for column in inspector.get_columns("query_sources")}
        for column in sorted(removed_columns & existing_columns):
            connection.execute(text(f"ALTER TABLE query_sources DROP COLUMN {column}"))


def get_db_session():
    """Yield a database session for FastAPI dependency injection.

    Args:
        None.

    Yields:
        SQLAlchemy session bound to the configured metadata database.
    """
    if SessionLocal is None:
        raise RuntimeError("DATABASE_URL is not configured")

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
