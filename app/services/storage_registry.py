"""Persistence helpers for vector stores and saved query results."""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, selectinload

from app.core.config import get_settings
from app.db.models import (
    EmbeddingModel,
    QueryDivisionResult,
    QueryRun,
    QuerySource,
    VectorStore,
    VectorStorePartition,
)
from app.db.session import SessionLocal, database_available, init_db
from app.models.query import DivisionResult, QueryResponse, SourceDocument
from app.services.vector_store_service import division_acronym

logger = logging.getLogger(__name__)

DEFAULT_EMBEDDINGS = [
    ("text-embedding-ada-002", None),
    ("text-embedding-3-small", 1536),
    ("text-embedding-3-large", 3072),
]


def ensure_storage_ready() -> bool:
    """Initialize storage metadata tables and seed required registry rows.

    Args:
        None.

    Returns:
        True when the registry is available and initialized, otherwise False.
    """
    if not database_available() or SessionLocal is None:
        return False

    try:
        init_db()
        with SessionLocal() as db:
            seed_embedding_models(db)
            db.flush()
            ensure_legacy_vector_store(db)
            db.commit()
        return True
    except SQLAlchemyError:
        return False


def seed_embedding_models(db: Session) -> None:
    """Insert or update the default embedding model records.

    Args:
        db: Open SQLAlchemy session used for registry writes.

    Returns:
        None.
    """
    for name, dimensions in DEFAULT_EMBEDDINGS:
        db.merge(
            EmbeddingModel(
                id=name,
                name=name,
                dimensions=dimensions,
                is_enabled=True,
            )
        )


def ensure_legacy_vector_store(db: Session) -> VectorStore:
    """Create a registry row for the pre-existing local Chroma store when needed.

    Args:
        db: Open SQLAlchemy session used for registry reads and writes.

    Returns:
        Active or newly created VectorStore registry row.
    """
    settings = get_settings()
    active = get_active_vector_store(db)
    if active:
        return active

    existing = db.get(VectorStore, "legacy-current")
    if existing:
        return existing

    model_name = settings.embedding_model
    db.merge(EmbeddingModel(id=model_name, name=model_name, is_enabled=True))
    db.flush()

    legacy = VectorStore(
        id="legacy-current",
        name="Current Local Store",
        embedding_model_id=model_name,
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        relative_path=".",
        status="ready",
        is_active=True,
        last_ingested_at=datetime.utcnow(),
    )
    db.add(legacy)
    db.flush()

    for division, store_name in settings.subcommittee_stores.items():
        db.add(
            VectorStorePartition(
                vector_store_id=legacy.id,
                division_key=division,
                store_name=store_name,
                chunk_count=0,
                status="ready",
            )
        )
    return legacy


def get_active_vector_store(db: Session) -> VectorStore | None:
    """Load the active ready vector store with related metadata.

    Args:
        db: Open SQLAlchemy session used for registry reads.

    Returns:
        Active VectorStore when configured, otherwise None.
    """
    return db.execute(
        select(VectorStore)
        .options(selectinload(VectorStore.embedding_model), selectinload(VectorStore.partitions))
        .where(VectorStore.is_active.is_(True), VectorStore.status == "ready")
    ).scalar_one_or_none()


def vector_store_path(vector_store: VectorStore) -> Path:
    """Resolve a vector store registry row to its Chroma root path.

    Args:
        vector_store: Vector store registry row containing a relative storage path.

    Returns:
        Absolute filesystem path to that vector store root.
    """
    settings = get_settings()
    relative = vector_store.relative_path
    if relative in ("", "."):
        return Path(settings.vectorstore_dir)
    return Path(settings.vectorstore_dir) / relative


def create_vector_store_record(
    db: Session,
    *,
    name: str,
    embedding_model: str,
    chunk_size: int,
    chunk_overlap: int,
    activate: bool,
) -> VectorStore:
    """Create a building vector store registry row before ingestion starts.

    Args:
        db: Open SQLAlchemy session used for registry writes.
        name: User-facing vector store name.
        embedding_model: Embedding model identifier used for ingestion.
        chunk_size: Character size used for source chunking.
        chunk_overlap: Character overlap used between adjacent chunks.
        activate: Whether the store should become active after successful ingestion.

    Returns:
        Newly created VectorStore row in building status.
    """
    if not db.get(EmbeddingModel, embedding_model):
        db.add(EmbeddingModel(id=embedding_model, name=embedding_model, is_enabled=True))

    store = VectorStore(
        name=name.strip() or f"{embedding_model} {chunk_size}",
        embedding_model_id=embedding_model,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        relative_path="pending",
        status="building",
        is_active=False,
    )
    db.add(store)
    db.flush()
    store.relative_path = f"vector_stores/{store.id}"

    return store


def mark_vector_store_ready(
    db: Session,
    store: VectorStore,
    partitions: dict[str, int],
    chunk_count: int,
    activate: bool = False,
) -> None:
    """Mark a vector store ready and record per-division chunk counts.

    Args:
        db: Open SQLAlchemy session used for registry writes.
        store: VectorStore row to update.
        partitions: Mapping of division names to ingested chunk counts.
        chunk_count: Total chunks ingested across all divisions.
        activate: Whether to make this store the active ready store.

    Returns:
        None.
    """
    store.status = "ready"
    store.chunk_count = chunk_count
    store.last_ingested_at = datetime.utcnow()
    store.error_message = None
    if activate:
        for existing in db.execute(select(VectorStore).where(VectorStore.is_active.is_(True))).scalars():
            existing.is_active = False
        store.is_active = True
    for division, count in partitions.items():
        store_name = get_settings().subcommittee_stores[division]
        db.add(
            VectorStorePartition(
                vector_store_id=store.id,
                division_key=division,
                store_name=store_name,
                chunk_count=count,
                status="ready",
            )
        )


def mark_vector_store_failed(db: Session, store: VectorStore, error: str) -> None:
    """Mark a vector store ingestion as failed and save the error message.

    Args:
        db: Open SQLAlchemy session used for registry writes.
        store: VectorStore row to update.
        error: Human-readable failure message.

    Returns:
        None.
    """
    store.status = "failed"
    store.error_message = error
    store.is_active = False


def activate_vector_store(db: Session, store_id: str) -> VectorStore:
    """Make one ready vector store active and deactivate any previous active store.

    Args:
        db: Open SQLAlchemy session used for registry reads and writes.
        store_id: Identifier of the vector store to activate.

    Returns:
        Activated VectorStore row.
    """
    store = db.get(VectorStore, store_id)
    if not store or store.status != "ready":
        raise ValueError("Vector store is not ready or does not exist")
    for existing in db.execute(select(VectorStore).where(VectorStore.is_active.is_(True))).scalars():
        existing.is_active = False
    store.is_active = True
    return store


def query_reference_count(db: Session, store_id: str) -> int:
    """Count saved query runs that reference a vector store.

    Args:
        db: Open SQLAlchemy session used for history reads.
        store_id: Identifier of the vector store to check.

    Returns:
        Number of saved query runs linked to the vector store.
    """
    return db.scalar(select(func.count()).select_from(QueryRun).where(QueryRun.vector_store_id == store_id)) or 0


def save_query_response(
    db: Session,
    *,
    response: QueryResponse,
    question: str,
    vector_store: VectorStore | None,
) -> None:
    """Persist a successful query response as a saved question result snapshot.

    Args:
        db: Open SQLAlchemy session used for history writes.
        response: Completed query response to persist.
        question: Original user question text.
        vector_store: Vector store used for the query, if available.

    Returns:
        None.
    """
    run = QueryRun(
        id=response.query_id or "",
        question=question,
        answer=response.answer,
        status="completed",
        vector_store_id=vector_store.id if vector_store else None,
        processing_time=response.processing_time,
        created_at=response.timestamp,
        completed_at=datetime.utcnow(),
    )
    db.merge(run)
    db.flush()

    sources_by_chunk = {source.chunk_id: source for source in response.sources or []}

    for order, division in enumerate(response.division_results):
        division_row = QueryDivisionResult(
            query_run_id=run.id,
            division_key=division.division,
            answer=division.answer,
            chunks_retrieved=division.chunks_retrieved,
            sort_order=order,
        )
        db.add(division_row)
        db.flush()

        for rank, chunk_id in enumerate(division.source_chunk_ids, start=1):
            source = sources_by_chunk.get(chunk_id)
            db.add(
                QuerySource(
                    query_run_id=run.id,
                    query_division_result_id=division_row.id,
                    chunk_id=chunk_id,
                    rank=rank,
                    chunk_summary=source.chunk_summary if source else None,
                    chunk_snapshot=source.chunk_snapshot if source else None,
                )
            )

    if vector_store:
        vector_store.last_used_at = datetime.utcnow()


def list_conversations(db: Session, limit: int = 50) -> list[dict[str, Any]]:
    """List recent saved question summaries.

    Args:
        db: Open SQLAlchemy session used for history reads.
        limit: Maximum number of saved questions to return.

    Returns:
        List of dictionaries containing saved question summary fields.
    """
    rows = db.execute(select(QueryRun).order_by(QueryRun.created_at.desc()).limit(limit)).scalars().all()
    return [
        {
            "id": row.id,
            "question": row.question,
            "answer_preview": row.answer[:180],
            "created_at": row.created_at,
            "processing_time": row.processing_time,
            "status": row.status,
        }
        for row in rows
    ]


def load_conversation(db: Session, query_id: str, chunk_loader) -> QueryResponse:
    """Load a saved question and hydrate it into the normal query response shape.

    Args:
        db: Open SQLAlchemy session used for history reads.
        query_id: Saved query identifier to load.
        chunk_loader: Callable that resolves vector-store chunks by store, division, and chunk id.

    Returns:
        QueryResponse suitable for rendering in the existing results UI.
    """
    run = db.execute(
        select(QueryRun)
        .options(
            selectinload(QueryRun.division_results).selectinload(QueryDivisionResult.sources),
            selectinload(QueryRun.vector_store),
        )
        .where(QueryRun.id == query_id)
    ).scalar_one_or_none()
    if not run:
        raise ValueError("Conversation not found")

    division_results: list[DivisionResult] = []
    sources: list[SourceDocument] = []
    settings = get_settings()
    debug_enabled = bool(settings.debug)
    saved_source_count = 0
    missing_chunk_count = 0

    for division in run.division_results:
        hydrated_chunk_ids: list[str] = []
        division_saved_count = len(division.sources)
        saved_source_count += division_saved_count

        for source in division.sources:
            loaded = chunk_loader(run.vector_store, division.division_key, source.chunk_id) if run.vector_store else None
            if not loaded:
                missing_chunk_count += 1
                continue

            content = loaded.get("content")
            if not content:
                missing_chunk_count += 1
                continue

            metadata = loaded.get("metadata")
            hydrated_chunk_ids.append(source.chunk_id)
            sources.append(
                SourceDocument(
                    division=division.division_key,
                    division_acronym=division_acronym(division.division_key),
                    chunk_id=source.chunk_id,
                    content_snippet=content,
                    chunk_summary=source.chunk_summary,
                    chunk_snapshot=source.chunk_snapshot,
                    confidence_score=None,
                    metadata={**(metadata or {}), "source_available": bool(loaded)},
                )
            )

        division_results.append(
            DivisionResult(
                division=division.division_key,
                division_acronym=division_acronym(division.division_key),
                chunks_retrieved=division.chunks_retrieved,
                answer=division.answer,
                source_chunk_ids=hydrated_chunk_ids,
            )
        )
        if debug_enabled:
            logger.info(
                "HISTORY_DEBUG division query_id=%s division=%s chunks_retrieved=%s "
                "saved_source_ids_count=%s hydrated_source_ids_count=%s hydrated_source_ids=%s",
                query_id,
                division_acronym(division.division_key),
                division.chunks_retrieved,
                division_saved_count,
                len(hydrated_chunk_ids),
                hydrated_chunk_ids,
            )

    response = QueryResponse(
        answer=run.answer,
        processing_time=run.processing_time,
        selected_divisions=[item.division for item in division_results],
        division_results=division_results,
        sources=sources,
        query_id=run.id,
        timestamp=run.created_at,
    )
    if debug_enabled:
        logger.info(
            "HISTORY_DEBUG load query_id=%s answer_chars=%s divisions=%s saved_source_rows=%s "
            "hydrated_sources=%s missing_chunks=%s first_hydrated_chunk_ids=%s",
            query_id,
            len(run.answer),
            len(division_results),
            saved_source_count,
            len(sources),
            missing_chunk_count,
            [source.chunk_id for source in sources[:5]],
        )
    return response
