"""Backwards-compatible shim for the LangGraph RAG service.

The implementation moved to :mod:`app.services.rag`. This module re-exports
the names that callers and tests already import from
``app.services.rag_service`` so existing imports keep working.
"""

from app.services.rag.schemas import (
    AnswerModeDecision,
    AnswerModeFlags,
    DivisionQueryDecision,
    DivisionQueryPlan,
    MappedFact,
    MappedFacts,
    MarkedAnswer,
    ProposedDerivedAnnotation,
    RouteDecision,
    SourceNumberCandidate,
)
from app.services.rag.service import RAGService, get_rag_service

__all__ = [
    "AnswerModeDecision",
    "AnswerModeFlags",
    "DivisionQueryDecision",
    "DivisionQueryPlan",
    "MappedFact",
    "MappedFacts",
    "MarkedAnswer",
    "ProposedDerivedAnnotation",
    "RAGService",
    "RouteDecision",
    "SourceNumberCandidate",
    "get_rag_service",
]
