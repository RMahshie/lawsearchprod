"""Shared FastAPI dependencies."""

from __future__ import annotations

from collections.abc import Iterator

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.api.errors import api_error
from app.db.session import SessionLocal, database_available


def require_db() -> Iterator[Session]:
    """Yield a SQLAlchemy session, or raise 503 if metadata storage is down.

    Returns:
        SQLAlchemy session bound to the configured database.

    Raises:
        HTTPException: 503 when DATABASE_URL is unset or the engine is unavailable.
    """
    if not database_available() or SessionLocal is None:
        raise api_error(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            error="storage_unavailable",
            message="Storage metadata is unavailable",
        )
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
