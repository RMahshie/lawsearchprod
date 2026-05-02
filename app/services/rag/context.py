"""Shared dependency container passed to pure pipeline-stage functions.

Stage modules must not reach back into ``RAGService`` directly. Instead they
take a :class:`RAGContext` carrying the runtime dependencies they need:
settings (for division/store mappings, debug gating), the vector store
service, and the two RAGService callbacks they cannot replicate themselves
(progress emission and debug logging).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    from app.core.config import Settings
    from app.services.rag.state import RAGState
    from app.services.vector_store_service import VectorStoreService


@dataclass(frozen=True)
class RAGContext:
    """Bundles the per-service dependencies stage functions need."""

    settings: "Settings"
    vectorstores: "VectorStoreService"
    emit_progress: Callable[..., None]
    debug_log: Callable[..., None]


__all__ = ["RAGContext"]
