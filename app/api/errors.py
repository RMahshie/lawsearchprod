"""Shared API error helpers."""

from __future__ import annotations

from typing import Any

from fastapi import HTTPException


def api_error(
    *,
    status_code: int,
    error: str,
    message: str,
    **extra: Any,
) -> HTTPException:
    """Build an HTTPException with a structured detail payload.

    Args:
        status_code: HTTP status code to return.
        error: Short machine-readable error code.
        message: Human-readable error message.
        **extra: Additional keys to merge into the detail object.

    Returns:
        HTTPException whose detail is `{"error": ..., "message": ..., **extra}`.
    """
    detail: dict[str, Any] = {"error": error, "message": message}
    detail.update(extra)
    return HTTPException(status_code=status_code, detail=detail)
