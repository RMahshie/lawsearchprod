"""Persistence helpers for vector stores and saved query results."""

from __future__ import annotations

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
from app.models.query import DebugChunk, DivisionResult, QueryResponse, SourceDocument
from app.services.vector_store_service import division_acronym


DEFAULT_EMBEDDINGS = [
    ("text-embedding-ada-002", None),
    ("text-embedding-3-small", 1536),
    ("text-embedding-3-large", 3072),
]


def ensure_storage_ready() -> bool:
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
    return db.execute(
        select(VectorStore)
        .options(selectinload(VectorStore.embedding_model), selectinload(VectorStore.partitions))
        .where(VectorStore.is_active.is_(True), VectorStore.status == "ready")
    ).scalar_one_or_none()


def vector_store_path(vector_store: VectorStore) -> Path:
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
    store.status = "failed"
    store.error_message = error
    store.is_active = False


def activate_vector_store(db: Session, store_id: str) -> VectorStore:
    store = db.get(VectorStore, store_id)
    if not store or store.status != "ready":
        raise ValueError("Vector store is not ready or does not exist")
    for existing in db.execute(select(VectorStore).where(VectorStore.is_active.is_(True))).scalars():
        existing.is_active = False
    store.is_active = True
    return store


def query_reference_count(db: Session, store_id: str) -> int:
    return db.scalar(select(func.count()).select_from(QueryRun).where(QueryRun.vector_store_id == store_id)) or 0


def save_query_response(
    db: Session,
    *,
    response: QueryResponse,
    question: str,
    vector_store: VectorStore | None,
) -> None:
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
    debug_by_chunk = {chunk.chunk_id: chunk for chunk in response.debug_chunks or []}

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
            debug = debug_by_chunk.get(chunk_id)
            snippet = source.content_snippet if source else (debug.content if debug else "")
            db.add(
                QuerySource(
                    query_run_id=run.id,
                    query_division_result_id=division_row.id,
                    chunk_id=chunk_id,
                    rank=rank,
                    score=debug.score if debug else None,
                    chunk_summary=source.chunk_summary if source else None,
                    chunk_snapshot=source.chunk_snapshot if source else None,
                    content_snippet=snippet[:5000],
                    source_metadata=source.metadata if source else {},
                )
            )

    if vector_store:
        vector_store.last_used_at = datetime.utcnow()


def list_conversations(db: Session, limit: int = 50) -> list[dict[str, Any]]:
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
    debug_chunks: list[DebugChunk] = []

    for division in run.division_results:
        chunk_ids = [source.chunk_id for source in division.sources]
        division_results.append(
            DivisionResult(
                division=division.division_key,
                division_acronym=division_acronym(division.division_key),
                chunks_retrieved=division.chunks_retrieved,
                answer=division.answer,
                source_chunk_ids=chunk_ids,
            )
        )

        for source in division.sources:
            loaded = chunk_loader(run.vector_store, division.division_key, source.chunk_id) if run.vector_store else None
            content = loaded.get("content") if loaded else source.content_snippet
            metadata = loaded.get("metadata") if loaded else source.source_metadata
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
            debug_chunks.append(
                DebugChunk(
                    chunk_id=source.chunk_id,
                    division=division.division_key,
                    division_acronym=division_acronym(division.division_key),
                    content=content,
                    chunk_summary=source.chunk_summary,
                    chunk_snapshot=source.chunk_snapshot,
                    score=source.score,
                    metadata={**(metadata or {}), "source_available": bool(loaded)},
                )
            )

    return QueryResponse(
        answer=run.answer,
        processing_time=run.processing_time,
        selected_divisions=[item.division for item in division_results],
        division_results=division_results,
        sources=sources,
        debug_chunks=debug_chunks,
        query_id=run.id,
        timestamp=run.created_at,
    )
