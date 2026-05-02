"""Vector store access and source-chunk shaping."""

from __future__ import annotations

import gc
import logging
import os
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

from chromadb.api.shared_system_client import SharedSystemClient
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings

from app.core.config import FY2026_DIVISION_ACRONYMS, get_settings

logger = logging.getLogger(__name__)

DIVISION_ACRONYMS = FY2026_DIVISION_ACRONYMS

EMBEDDING_MODEL_FILE = ".embedding_model"


def read_persisted_embedding_model(vectorstore_dir: str | Path) -> str | None:
    """Read the embedding model that was used to build persisted Chroma stores.

    Args:
        vectorstore_dir: Chroma root directory containing the embedding model marker file.

    Returns:
        Persisted embedding model name, or None when unavailable.
    """
    model_file = Path(vectorstore_dir) / EMBEDDING_MODEL_FILE
    if not model_file.exists():
        return None

    model = model_file.read_text(encoding="utf-8").strip()
    return model or None


def write_persisted_embedding_model(vectorstore_dir: str | Path, embedding_model: str) -> None:
    """Persist the embedding model alongside Chroma stores for restart-safe queries.

    Args:
        vectorstore_dir: Chroma root directory where the marker file should be written.
        embedding_model: Embedding model name to persist.

    Returns:
        None.
    """
    vectorstore_path = Path(vectorstore_dir)
    vectorstore_path.mkdir(parents=True, exist_ok=True)
    (vectorstore_path / EMBEDDING_MODEL_FILE).write_text(embedding_model, encoding="utf-8")


def clear_chroma_system_cache() -> None:
    """Release cached Chroma clients before deleting or rebuilding persisted stores.

    Args:
        None.

    Returns:
        None.
    """
    try:
        SharedSystemClient.clear_system_cache()
    except Exception:
        pass
    gc.collect()


def division_acronym(division: str) -> str:
    """Return a compact marker for division-level citations.

    Args:
        division: Full division name.

    Returns:
        Known division acronym or a derived fallback acronym.
    """
    if division in DIVISION_ACRONYMS:
        return DIVISION_ACRONYMS[division]

    words = re.findall(r"[A-Z]+", division)
    return "".join(word[0] for word in words[:5]) or "SRC"


class VectorStoreService:
    """Loads Chroma stores and returns division-tagged chunks."""

    def __init__(self, embedding_model: str | None = None):
        """Initialize vector store access with an embedding model.

        Args:
            embedding_model: Optional embedding model override.

        Returns:
            None.
        """
        self.settings = get_settings()
        persisted_model = read_persisted_embedding_model(self.settings.vectorstore_dir)
        self.embedding_model = embedding_model or persisted_model or self.settings.embedding_model
        self.settings.embedding_model = self.embedding_model
        self.embedder = OpenAIEmbeddings(model=self.embedding_model)

    @lru_cache(maxsize=None)
    def get_store(self, vectorstore_root: str, store_name: str) -> Chroma:
        """Lazily load one persisted Chroma store.

        Args:
            vectorstore_root: Root directory for a versioned vector store.
            store_name: Division-specific Chroma directory name.

        Returns:
            Chroma store handle for the requested division.
        """
        path = os.path.join(vectorstore_root, store_name)
        return Chroma(
            persist_directory=path,
            embedding_function=self.embedder,
        )

    def reset_embedding_model(self, embedding_model: str) -> None:
        """Switch embeddings after ingestion and clear cached stores.

        Args:
            embedding_model: Embedding model name to use for future Chroma queries.

        Returns:
            None.
        """
        self.clear_cached_stores()
        self.embedding_model = embedding_model
        self.embedder = OpenAIEmbeddings(model=embedding_model)
        self.settings.embedding_model = embedding_model

    def clear_cached_stores(self) -> None:
        """Drop cached Chroma handles before destructive vector store operations.

        Args:
            None.

        Returns:
            None.
        """
        self.get_store.cache_clear()
        clear_chroma_system_cache()

    def use_embedding_model(self, embedding_model: str) -> None:
        """Switch to a requested embedding model when it differs from the active one.

        Args:
            embedding_model: Embedding model name required for a vector store.

        Returns:
            None.
        """
        if embedding_model != self.embedding_model:
            self.reset_embedding_model(embedding_model)

    def _resolve_store(
        self,
        division: str,
        vectorstore_root: str | Path | None,
        embedding_model: str | None,
        *,
        context: str,
    ) -> tuple[str, Any]:
        """Validate per-call store params and return the loaded Chroma store.

        Args:
            division: Full division name used to look up the store name.
            vectorstore_root: Root directory for the versioned vector store.
            embedding_model: Embedding model used by that vector store.
            context: Short label used in error messages (e.g. "retrieval", "load chunk X").

        Returns:
            Tuple of (root_str, store) for downstream Chroma operations.
        """
        if not vectorstore_root:
            raise ValueError(f"Vector store root is required for {context}")
        if not embedding_model:
            raise ValueError(f"Embedding model is required for {context}")
        self.use_embedding_model(embedding_model)
        store_name = self.settings.subcommittee_stores[division]
        root = str(vectorstore_root)
        return root, self.get_store(root, store_name)

    def retrieve(
        self,
        question: str,
        division: str,
        k: int,
        vectorstore_root: str | Path | None = None,
        embedding_model: str | None = None,
    ) -> list[dict[str, Any]]:
        """Retrieve k chunks for a division, preserving division metadata.

        Args:
            question: Retrieval query text.
            division: Full division name to search.
            k: Maximum number of chunks to retrieve.
            vectorstore_root: Optional root directory for a versioned vector store.
            embedding_model: Optional embedding model used by that vector store.

        Returns:
            List of chunk dictionaries with content, score, id, division, and metadata.
        """
        root, store = self._resolve_store(
            division,
            vectorstore_root,
            embedding_model,
            context=f"retrieval in {division_acronym(division)}",
        )
        store_name = self.settings.subcommittee_stores[division]
        docs_with_scores = store.similarity_search_with_score(question, k=k)
        if self.settings.debug:
            logger.info(
                "VECTOR_DEBUG retrieve root=%s store_name=%s division=%s embedding_model=%s requested_k=%s returned=%s",
                root,
                store_name,
                division_acronym(division),
                self.embedding_model,
                k,
                len(docs_with_scores),
            )
            for index, item in enumerate(docs_with_scores[:3]):
                doc, score = item
                metadata = dict(doc.metadata or {})
                logger.info(
                    "VECTOR_DEBUG retrieved_doc root=%s store_name=%s division=%s index=%s score=%s "
                    "metadata_keys=%s metadata_chunk_id=%s metadata_vector_store_id=%s content_hash=%s content_preview=%s",
                    root,
                    store_name,
                    division_acronym(division),
                    index,
                    score,
                    sorted(metadata.keys()),
                    metadata.get("chunk_id"),
                    metadata.get("vector_store_id"),
                    _content_hash(doc.page_content),
                    doc.page_content[:120].replace("\n", "\\n"),
                )

        chunks: list[dict[str, Any]] = []
        for index, item in enumerate(docs_with_scores):
            doc, score = item
            chunks.append(self._chunk_from_document(division, index, doc, score))
        return chunks

    def get_chunk(
        self,
        division: str,
        chunk_id: str,
        vectorstore_root: str | Path | None = None,
        embedding_model: str | None = None,
    ) -> dict[str, Any] | None:
        """Load one source chunk by persisted Chroma document id.

        Args:
            division: Full division name for store selection.
            chunk_id: Stable Chroma document id to load.
            vectorstore_root: Optional root directory for a versioned vector store.
            embedding_model: Optional embedding model used by that vector store.

        Returns:
            Chunk dictionary when found, otherwise None.
        """
        _, store = self._resolve_store(
            division,
            vectorstore_root,
            embedding_model,
            context=f"loading chunk {chunk_id}",
        )
        result = store._collection.get(ids=[chunk_id], include=["documents", "metadatas"])  # noqa: SLF001
        documents = result.get("documents") or []
        if not documents:
            return None
        metadatas = result.get("metadatas") or [{}]
        return {
            "chunk_id": chunk_id,
            "division": division,
            "division_acronym": division_acronym(division),
            "content": documents[0],
            "metadata": dict(metadatas[0] or {}),
        }

    def _chunk_from_document(
        self,
        division: str,
        index: int,
        doc: Document,
        score: float | None,
    ) -> dict[str, Any]:
        """Convert a LangChain document and score into the API chunk shape.

        Args:
            division: Full division name associated with the document.
            index: Retrieval result index used only for fallback ids.
            doc: LangChain source document returned by Chroma.
            score: Optional similarity score returned by Chroma.

        Returns:
            Chunk dictionary consumed by the RAG graph.
        """
        content = doc.page_content
        metadata_chunk_id = doc.metadata.get("chunk_id")
        chunk_id = str(metadata_chunk_id) if metadata_chunk_id else None
        if self.settings.debug and chunk_id is None:
            logger.info(
                "VECTOR_DEBUG missing_chunk_id division=%s index=%s metadata_keys=%s content_hash=%s",
                division_acronym(division),
                index,
                sorted((doc.metadata or {}).keys()),
                _content_hash(content),
            )
        return {
            "chunk_id": chunk_id,
            "division": division,
            "division_acronym": division_acronym(division),
            "content": content,
            "chunk_summary": None,
            "score": score,
            "metadata": dict(doc.metadata or {}),
        }


def _content_hash(content: str) -> str:
    """Return a short diagnostic hash for source text without exposing full content."""
    import hashlib

    return hashlib.sha1(content.encode("utf-8")).hexdigest()[:8]
