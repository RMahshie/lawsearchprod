"""Storage manager and saved conversation endpoints."""

from __future__ import annotations

import logging
import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.models import EmbeddingModel, VectorStore
from app.db.session import SessionLocal, database_available
from app.models.storage import (
    ConversationDetail,
    ConversationListResponse,
    CreateEmbeddingModelRequest,
    CreateVectorStoreRequest,
    EmbeddingModelInfo,
    VectorStoreInfo,
)
from app.services.rag_service import get_rag_service
from app.services.storage_registry import (
    activate_vector_store,
    list_conversations,
    load_conversation,
    query_reference_count,
    vector_store_path,
)

logger = logging.getLogger(__name__)
router = APIRouter()


def _store_info(db, store: VectorStore) -> VectorStoreInfo:
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
async def list_vector_stores() -> list[VectorStoreInfo]:
    if not database_available() or SessionLocal is None:
        return []

    try:
        with SessionLocal() as db:
            stores = db.execute(
                select(VectorStore)
                .options(selectinload(VectorStore.embedding_model))
                .order_by(VectorStore.created_at.desc())
            ).scalars().all()
            return [_store_info(db, store) for store in stores]
    except Exception:
        return []


@router.post("/storage/vector-stores", response_model=VectorStoreInfo)
async def create_vector_store(request: CreateVectorStoreRequest) -> VectorStoreInfo:
    if not database_available() or SessionLocal is None:
        raise HTTPException(status_code=503, detail="Storage metadata is unavailable")

    rag_service = get_rag_service()
    ingest_id = f"ingest_{uuid.uuid4().hex[:10]}"
    try:
        await rag_service.ingest_data(
            embedding_model=request.embedding_model,
            chunk_size=request.chunk_size,
            clear_existing=True,
            ingest_id=ingest_id,
            name=request.name,
            activate=request.activate,
        )
    except Exception as exc:
        logger.error("Storage ingestion failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    with SessionLocal() as db:
        store = db.execute(select(VectorStore).order_by(VectorStore.created_at.desc())).scalars().first()
        if not store:
            raise HTTPException(status_code=500, detail="Vector store was not registered")
        return _store_info(db, store)


@router.post("/storage/vector-stores/{store_id}/activate", response_model=VectorStoreInfo)
async def activate_store(store_id: str) -> VectorStoreInfo:
    if not database_available() or SessionLocal is None:
        raise HTTPException(status_code=503, detail="Storage metadata is unavailable")

    with SessionLocal() as db:
        try:
            store = activate_vector_store(db, store_id)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        db.commit()
        db.refresh(store)
        get_rag_service().vectorstores.clear_cached_stores()
        return _store_info(db, store)


@router.delete("/storage/vector-stores/{store_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_store(store_id: str, force: bool = False) -> None:
    if not database_available() or SessionLocal is None:
        raise HTTPException(status_code=503, detail="Storage metadata is unavailable")

    with SessionLocal() as db:
        store = db.get(VectorStore, store_id)
        if not store:
            raise HTTPException(status_code=404, detail="Vector store not found")
        if store.is_active:
            raise HTTPException(status_code=400, detail="Cannot delete the active vector store")
        references = query_reference_count(db, store_id)
        if references and not force:
            raise HTTPException(status_code=409, detail=f"Vector store is referenced by {references} saved queries")
        path = vector_store_path(store)
        db.delete(store)
        db.commit()

    if path.exists() and path != Path(get_rag_service().settings.vectorstore_dir):
        shutil.rmtree(path)
    get_rag_service().vectorstores.clear_cached_stores()


@router.get("/storage/embedding-models", response_model=list[EmbeddingModelInfo])
async def list_embedding_models() -> list[EmbeddingModelInfo]:
    if not database_available() or SessionLocal is None:
        return []

    try:
        with SessionLocal() as db:
            models = db.execute(select(EmbeddingModel).order_by(EmbeddingModel.name)).scalars().all()
            return [
                EmbeddingModelInfo(
                    id=model.id,
                    name=model.name,
                    provider=model.provider,
                    dimensions=model.dimensions,
                    is_enabled=model.is_enabled,
                )
                for model in models
            ]
    except Exception:
        return []


@router.post("/storage/embedding-models", response_model=EmbeddingModelInfo)
async def create_embedding_model(request: CreateEmbeddingModelRequest) -> EmbeddingModelInfo:
    if not database_available() or SessionLocal is None:
        raise HTTPException(status_code=503, detail="Storage metadata is unavailable")

    with SessionLocal() as db:
        existing = db.get(EmbeddingModel, request.name)
        if existing:
            existing.is_enabled = True
            model = existing
        else:
            model = EmbeddingModel(
                id=request.name,
                name=request.name,
                provider=request.provider,
                dimensions=request.dimensions,
                is_enabled=True,
            )
            db.add(model)
        db.commit()
        db.refresh(model)
        return EmbeddingModelInfo(
            id=model.id,
            name=model.name,
            provider=model.provider,
            dimensions=model.dimensions,
            is_enabled=model.is_enabled,
        )


@router.get("/conversations", response_model=ConversationListResponse)
async def conversations() -> ConversationListResponse:
    if not database_available() or SessionLocal is None:
        return ConversationListResponse(conversations=[])

    try:
        with SessionLocal() as db:
            return ConversationListResponse(conversations=list_conversations(db))
    except Exception:
        return ConversationListResponse(conversations=[])


@router.get("/conversations/{query_id}", response_model=ConversationDetail)
async def conversation_detail(query_id: str) -> ConversationDetail:
    if not database_available() or SessionLocal is None:
        raise HTTPException(status_code=503, detail="Question history is unavailable")

    rag_service = get_rag_service()

    def load_chunk(store: VectorStore | None, division: str, chunk_id: str):
        if not store:
            return None
        return rag_service.vectorstores.get_chunk(
            division,
            chunk_id,
            vectorstore_root=vector_store_path(store),
            embedding_model=store.embedding_model_id,
        )

    with SessionLocal() as db:
        try:
            response = load_conversation(db, query_id, load_chunk)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return ConversationDetail(response=response)
