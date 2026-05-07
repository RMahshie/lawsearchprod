"""Storage manager and saved conversation endpoints."""

from __future__ import annotations

import logging
import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import require_db
from app.api.errors import api_error
from app.db.models import EmbeddingModel, VectorStore
from app.models.storage import (
    ConversationDetail,
    ConversationListResponse,
    CreateVectorStoreRequest,
    EmbeddingModelInfo,
    VectorStoreInfo,
)
from app.services.embedding_factory import (
    EmbeddingModelUnavailableError,
    ensure_embedding_model_available,
    is_embedding_model_available,
)
from app.services.rag_service import get_rag_service
from app.services.storage_registry import (
    activate_vector_store,
    delete_vector_store_with_saved_questions,
    list_conversations,
    load_conversation,
    query_reference_count,
    vector_store_path,
)

logger = logging.getLogger(__name__)
router = APIRouter()


def _store_info(db: Session, store: VectorStore) -> VectorStoreInfo:
    """Convert a vector store database row into an API response model.

    Args:
        db: Open SQLAlchemy session used to count saved query references.
        store: VectorStore row to serialize.

    Returns:
        VectorStoreInfo response model for the storage manager UI.
    """
    return VectorStoreInfo(
        id=store.id,
        name=store.name,
        embedding_model=store.embedding_model_id,
        chunk_size=store.chunk_size,
        chunk_overlap=store.chunk_overlap,
        status=store.status,
        is_active=store.is_active,
        created_at=store.created_at,
        last_ingested_at=store.last_ingested_at,
        last_used_at=store.last_used_at,
        chunk_count=store.chunk_count,
        query_count=query_reference_count(db, store.id),
        error_message=store.error_message,
    )


@router.get("/storage/vector-stores", response_model=list[VectorStoreInfo])
async def list_vector_stores(db: Session = Depends(require_db)) -> list[VectorStoreInfo]:
    """Return all registered vector stores for the storage manager.

    Args:
        db: Injected SQLAlchemy session.

    Returns:
        List of vector store records.
    """
    try:
        stores = db.execute(
            select(VectorStore)
            .options(selectinload(VectorStore.embedding_model))
            .order_by(VectorStore.created_at.desc())
        ).scalars().all()
        return [_store_info(db, store) for store in stores]
    except Exception:
        logger.exception("Failed to list vector stores")
        return []


@router.post("/storage/vector-stores", response_model=VectorStoreInfo)
async def create_vector_store(
    request: CreateVectorStoreRequest,
    db: Session = Depends(require_db),
) -> VectorStoreInfo:
    """Create a new versioned vector store by running ingestion.

    Args:
        request: Storage manager request containing name, embedding model, chunk size, overlap, and activation preference.
        db: Injected SQLAlchemy session.

    Returns:
        VectorStoreInfo for the newly registered vector store.
    """
    rag_service = get_rag_service()
    ingest_id = f"ingest_{uuid.uuid4().hex[:10]}"
    try:
        ensure_embedding_model_available(request.embedding_model, rag_service.settings)
    except EmbeddingModelUnavailableError as exc:
        raise api_error(
            status_code=status.HTTP_400_BAD_REQUEST,
            error="embedding_model_unavailable",
            message=str(exc),
        ) from exc
    except ValueError as exc:
        raise api_error(
            status_code=status.HTTP_400_BAD_REQUEST,
            error="embedding_model_unsupported",
            message=str(exc),
        ) from exc
    try:
        await rag_service.ingest_data(
            embedding_model=request.embedding_model,
            chunk_size=request.chunk_size,
            chunk_overlap=request.chunk_overlap,
            clear_existing=True,
            ingest_id=ingest_id,
            name=request.name,
            activate=request.activate,
        )
    except Exception as exc:
        logger.error("Storage ingestion failed: %s", exc, exc_info=True)
        raise api_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error="ingestion_failed",
            message=str(exc),
        ) from exc

    store = db.execute(select(VectorStore).order_by(VectorStore.created_at.desc())).scalars().first()
    if not store:
        raise api_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error="store_not_registered",
            message="Vector store was not registered",
        )
    return _store_info(db, store)


@router.post("/storage/vector-stores/{store_id}/activate", response_model=VectorStoreInfo)
async def activate_store(
    store_id: str,
    db: Session = Depends(require_db),
) -> VectorStoreInfo:
    """Set a ready vector store as the active retrieval store.

    Args:
        store_id: Identifier of the vector store to activate.
        db: Injected SQLAlchemy session.

    Returns:
        VectorStoreInfo for the activated store.
    """
    try:
        store = activate_vector_store(db, store_id)
    except ValueError as exc:
        raise api_error(
            status_code=status.HTTP_404_NOT_FOUND,
            error="store_not_found",
            message=str(exc),
        ) from exc
    db.commit()
    db.refresh(store)
    get_rag_service().vectorstores.clear_cached_stores()
    return _store_info(db, store)


@router.delete(
    "/storage/vector-stores/{store_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
async def delete_store(
    store_id: str,
    db: Session = Depends(require_db),
) -> None:
    """Delete an inactive vector store, its saved questions, and its Chroma files.

    Args:
        store_id: Identifier of the vector store to delete.
        db: Injected SQLAlchemy session.

    Returns:
        None.
    """
    store = db.get(VectorStore, store_id)
    if not store:
        raise api_error(
            status_code=status.HTTP_404_NOT_FOUND,
            error="store_not_found",
            message="Vector store not found",
        )
    if store.is_active:
        raise api_error(
            status_code=status.HTTP_400_BAD_REQUEST,
            error="store_active",
            message="Cannot delete the active vector store",
        )
    path = vector_store_path(store)
    deleted_saved_questions = delete_vector_store_with_saved_questions(db, store)
    db.commit()
    logger.info(
        "Deleted vector store %s and %s saved questions",
        store_id,
        deleted_saved_questions,
    )

    if path.exists() and path != Path(get_rag_service().settings.vectorstore_dir):
        shutil.rmtree(path)
    get_rag_service().vectorstores.clear_cached_stores()


@router.get("/storage/embedding-models", response_model=list[EmbeddingModelInfo])
async def list_embedding_models(db: Session = Depends(require_db)) -> list[EmbeddingModelInfo]:
    """Return embedding models available to the storage manager.

    Args:
        db: Injected SQLAlchemy session.

    Returns:
        List of embedding model records.
    """
    try:
        rag_service = get_rag_service()
        models = db.execute(select(EmbeddingModel).order_by(EmbeddingModel.name)).scalars().all()
        return [
            EmbeddingModelInfo(
                id=model.id,
                name=model.name,
                provider=model.provider,
                dimensions=model.dimensions,
                is_enabled=model.is_enabled,
                is_available=is_embedding_model_available(model.id, rag_service.settings),
            )
            for model in models
        ]
    except Exception:
        logger.exception("Failed to list embedding models")
        return []


@router.get("/conversations", response_model=ConversationListResponse)
async def conversations(db: Session = Depends(require_db)) -> ConversationListResponse:
    """Return saved question summaries for the history rail.

    Args:
        db: Injected SQLAlchemy session.

    Returns:
        ConversationListResponse containing recent saved question summaries.
    """
    try:
        return ConversationListResponse(conversations=list_conversations(db))
    except Exception:
        logger.exception("Failed to list conversations")
        return ConversationListResponse(conversations=[])


@router.get("/conversations/{query_id}", response_model=ConversationDetail)
async def conversation_detail(
    query_id: str,
    db: Session = Depends(require_db),
) -> ConversationDetail:
    """Return one saved question hydrated into the normal query response shape.

    Args:
        query_id: Saved query identifier to load.
        db: Injected SQLAlchemy session.

    Returns:
        ConversationDetail containing the rendered QueryResponse.
    """
    rag_service = get_rag_service()

    def load_chunk(store: VectorStore | None, division: str, chunk_id: str):
        """Load a saved source chunk from the vector store when still available.

        Args:
            store: Vector store row associated with the saved query.
            division: Division key for the saved source.
            chunk_id: Stable source chunk identifier.

        Returns:
            Chunk dictionary when found in Chroma, otherwise None.
        """
        if not store:
            return None
        return rag_service.vectorstores.get_chunk(
            division,
            chunk_id,
            vectorstore_root=vector_store_path(store),
            embedding_model=store.embedding_model_id,
        )

    try:
        response = load_conversation(db, query_id, load_chunk)
    except ValueError as exc:
        raise api_error(
            status_code=status.HTTP_404_NOT_FOUND,
            error="conversation_not_found",
            message=str(exc),
        ) from exc
    return ConversationDetail(response=response)
