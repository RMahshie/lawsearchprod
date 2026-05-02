"""LangGraph RAG package for LawSearch AI.

The Query Pipeline (Classify -> Route -> Rewrite -> Retrieve -> Map -> Reduce ->
Synthesize) and its supporting subsystems are split across modules in this
package. Public callers should import :class:`RAGService` and
:func:`get_rag_service` from :mod:`app.services.rag_service`, which re-exports
the names defined here.
"""

from app.services.rag.service import RAGService, get_rag_service

__all__ = ["RAGService", "get_rag_service"]
