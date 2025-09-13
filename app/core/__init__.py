"""
Core package

Contains configuration, dependencies, and core utilities.
"""

from .config import (
    Settings,
    get_settings,
    get_vectorstore_dir,
    get_data_dir,
    get_subcommittee_stores,
    get_routing_prompt
)

__all__ = [
    "Settings",
    "get_settings",
    "get_vectorstore_dir", 
    "get_data_dir",
    "get_subcommittee_stores",
    "get_routing_prompt"
]