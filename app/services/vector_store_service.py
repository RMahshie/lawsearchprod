"""Vector store access and source-chunk shaping."""

from __future__ import annotations

import hashlib
import gc
import os
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

from chromadb.api.shared_system_client import SharedSystemClient
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings

from app.core.config import get_settings


DIVISION_ACRONYMS = {
    "MILITARY CONSTRUCTION, VETERANS AFFAIRS, AND RELATED AGENCIES": "MCVA",
    "AGRICULTURE, RURAL DEVELOPMENT, FOOD AND DRUG ADMINISTRATION, AND RELATED AGENCIES": "AG",
    "COMMERCE, JUSTICE, SCIENCE, AND RELATED AGENCIES": "CJS",
    "ENERGY AND WATER DEVELOPMENT AND RELATED AGENCIES": "EWD",
    "DEPARTMENT OF THE INTERIOR, ENVIRONMENT, AND RELATED AGENCIES": "INT",
    "TRANSPORTATION, HOUSING AND URBAN DEVELOPMENT, AND RELATED AGENCIES": "THUD",
    "OTHER MATTERS": "OM",
    "DEPARTMENT OF DEFENSE": "DOD",
    "FINANCIAL SERVICES AND GENERAL GOVERNMENT": "FSGG",
    "DEPARTMENT OF HOMELAND SECURITY": "DHS",
    "DEPARTMENTS OF LABOR, HEALTH AND HUMAN SERVICES, AND EDUCATION, AND RELATED AGENCIES": "LHHS",
    "LEGISLATIVE BRANCH": "LEG",
    "DEPARTMENT OF STATE, FOREIGN OPERATIONS, AND RELATED PROGRAMS": "SFOPS",
    "OTHER MATTERS (FURTHER)": "OMF",
}

EMBEDDING_MODEL_FILE = ".embedding_model"


def read_persisted_embedding_model(vectorstore_dir: str | Path) -> str | None:
    """Read the embedding model that was used to build persisted Chroma stores."""
    model_file = Path(vectorstore_dir) / EMBEDDING_MODEL_FILE
    if not model_file.exists():
        return None

    model = model_file.read_text(encoding="utf-8").strip()
    return model or None


def write_persisted_embedding_model(vectorstore_dir: str | Path, embedding_model: str) -> None:
    """Persist the embedding model alongside Chroma stores for restart-safe queries."""
    vectorstore_path = Path(vectorstore_dir)
    vectorstore_path.mkdir(parents=True, exist_ok=True)
    (vectorstore_path / EMBEDDING_MODEL_FILE).write_text(embedding_model, encoding="utf-8")


def clear_chroma_system_cache() -> None:
    """Release cached Chroma clients before deleting or rebuilding persisted stores."""
    try:
        SharedSystemClient.clear_system_cache()
    except Exception:
        pass
    gc.collect()


def division_acronym(division: str) -> str:
    """Return a compact marker for division-level citations."""
    if division in DIVISION_ACRONYMS:
        return DIVISION_ACRONYMS[division]

    words = re.findall(r"[A-Z]+", division)
    return "".join(word[0] for word in words[:5]) or "SRC"


def stable_chunk_id(division: str, index: int, content: str) -> str:
    """Create a deterministic chunk id for citations and UI lookup."""
    digest = hashlib.sha1(f"{division}:{index}:{content}".encode("utf-8")).hexdigest()[:8]
    return f"{division_acronym(division)}-{index + 1}-{digest}"


class VectorStoreService:
    """Loads Chroma stores and returns division-tagged chunks."""

    def __init__(self, embedding_model: str | None = None):
        self.settings = get_settings()
        persisted_model = read_persisted_embedding_model(self.settings.vectorstore_dir)
        self.embedding_model = embedding_model or persisted_model or self.settings.embedding_model
        self.settings.embedding_model = self.embedding_model
        self.embedder = OpenAIEmbeddings(model=self.embedding_model)

    @lru_cache(maxsize=None)
    def get_store(self, store_name: str) -> Chroma:
        """Lazily load one persisted Chroma store."""
        path = os.path.join(str(self.settings.vectorstore_dir), store_name)
        return Chroma(
            persist_directory=path,
            embedding_function=self.embedder,
        )

    def reset_embedding_model(self, embedding_model: str) -> None:
        """Switch embeddings after ingestion and clear cached stores."""
        self.clear_cached_stores()
        self.embedding_model = embedding_model
        self.embedder = OpenAIEmbeddings(model=embedding_model)
        self.settings.embedding_model = embedding_model

    def clear_cached_stores(self) -> None:
        """Drop cached Chroma handles before destructive vector store operations."""
        self.get_store.cache_clear()
        clear_chroma_system_cache()

    def retrieve(self, question: str, division: str, k: int) -> list[dict[str, Any]]:
        """Retrieve k chunks for a division, preserving division metadata."""
        store_name = self.settings.subcommittee_stores[division]
        store = self.get_store(store_name)
        docs_with_scores = store.similarity_search_with_score(question, k=k)

        chunks: list[dict[str, Any]] = []
        for index, item in enumerate(docs_with_scores):
            doc, score = item
            chunks.append(self._chunk_from_document(division, index, doc, score))
        return chunks

    def _chunk_from_document(
        self,
        division: str,
        index: int,
        doc: Document,
        score: float | None,
    ) -> dict[str, Any]:
        content = doc.page_content
        return {
            "chunk_id": stable_chunk_id(division, index, content),
            "division": division,
            "division_acronym": division_acronym(division),
            "content": content,
            "chunk_summary": None,
            "score": score,
            "metadata": dict(doc.metadata or {}),
        }
