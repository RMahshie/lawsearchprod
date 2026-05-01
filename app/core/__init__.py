"""
Core package

Contains configuration, dependencies, and core utilities.
"""

from .config import (
    Settings,
    get_settings,
)

__all__ = [
    "Settings",
    "get_settings",
]
