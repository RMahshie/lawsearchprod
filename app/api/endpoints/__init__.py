"""
API endpoints package

Contains all route handlers and endpoint definitions.
"""

from .query import router as query_router

__all__ = [
    "query_router"
]