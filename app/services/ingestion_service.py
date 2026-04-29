"""HTML bill ingestion into per-division Chroma stores."""

from __future__ import annotations

import os
import re
import shutil
import uuid
from pathlib import Path

from bs4 import BeautifulSoup
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings

from app.core.config import get_settings
from app.services.vector_store_service import (
    clear_chroma_system_cache,
    division_acronym,
    write_persisted_embedding_model,
)


DIVISION_PATTERN = re.compile(
    r"^\s*DIVISION\s+([A-Z])\s*--\s*(?:(OTHER MATTERS)|((?:(?!APPROPRIATIONS).)+))",
    re.IGNORECASE | re.MULTILINE | re.DOTALL,
)


class IngestionService:
    """Build persisted Chroma stores from the source bill HTML files."""

    def __init__(self):
        """Initialize ingestion service settings.

        Args:
            None.

        Returns:
            None.
        """
        self.settings = get_settings()

    def ingest(
        self,
        embedding_model: str,
        clear_existing: bool = True,
        chunk_size: int | None = None,
        chunk_overlap: int | None = None,
        vectorstore_dir: str | Path | None = None,
        vector_store_id: str | None = None,
    ) -> tuple[int, dict[str, int], int]:
        """Rebuild per-division Chroma stores from source bill HTML.

        Args:
            embedding_model: Embedding model used to vectorize chunks.
            clear_existing: Whether to delete the target vector store directory first.
            chunk_size: Optional character count per chunk.
            chunk_overlap: Optional character overlap between adjacent chunks.
            vectorstore_dir: Optional target Chroma root directory.
            vector_store_id: Optional registry id stored in chunk metadata.

        Returns:
            Tuple of processed division count, per-division chunk counts, and total chunks.
        """
        vectorstore_dir = Path(vectorstore_dir or self.settings.vectorstore_dir)
        clear_chroma_system_cache()
        if clear_existing and vectorstore_dir.exists():
            shutil.rmtree(vectorstore_dir)
        vectorstore_dir.mkdir(parents=True, exist_ok=True)

        embeddings = OpenAIEmbeddings(model=embedding_model)
        divisions_processed = 0
        partition_counts: dict[str, int] = {}
        total_chunks = 0

        for division, store_name in self.settings.subcommittee_stores.items():
            documents: list[Document] = []
            for source_part in self._source_parts_for_division(division):
                bill_path = self._resolve_source_path(source_part)
                source_letter = source_part["source_division_letter"]
                text = self._extract_division_text(bill_path, source_letter)
                part_documents = self._chunk_documents(
                    text,
                    division,
                    bill_path.name,
                    chunk_size=chunk_size,
                    chunk_overlap=chunk_overlap,
                    vector_store_id=vector_store_id,
                    metadata_extra=self._metadata_for_source_part(division, source_part),
                    chunk_index_offset=len(documents),
                )
                if len(part_documents) < 2:
                    raise ValueError(
                        "Suspiciously small FY2026 source part during ingestion: "
                        f"division={division!r}, source_file={source_part['source_file']!r}, "
                        f"source_division_letter={source_letter!r}, extracted_chars={len(text)}, "
                        f"chunks={len(part_documents)}"
                    )
                documents.extend(part_documents)
            if not documents:
                raise ValueError(f"No documents produced for configured FY2026 division: {division}")

            persist_directory = vectorstore_dir / store_name
            persist_directory.mkdir(parents=True, exist_ok=True)
            chunk_ids = [str(doc.metadata["chunk_id"]) for doc in documents]
            Chroma.from_documents(
                documents=documents,
                embedding=embeddings,
                persist_directory=str(persist_directory),
                ids=chunk_ids,
            )
            divisions_processed += 1
            partition_counts[division] = len(documents)
            total_chunks += len(documents)

        write_persisted_embedding_model(vectorstore_dir, embedding_model)
        return divisions_processed, partition_counts, total_chunks

    def _source_parts_for_division(self, division: str) -> list[dict[str, str]]:
        """Return configured FY2026 source parts for one routable division.

        Args:
            division: Canonical FY2026 division label.

        Returns:
            Source-part dictionaries from settings.
        """
        parts = self.settings.fy2026_source_parts.get(division)
        if not parts:
            raise ValueError(f"Missing FY2026 source-part configuration for division: {division}")
        return parts

    def _resolve_source_path(self, source_part: dict[str, str]) -> Path:
        """Resolve and validate the configured source file for one source part.

        Args:
            source_part: Source-part manifest entry.

        Returns:
            Existing source HTML path.
        """
        bill_path = Path(self.settings.data_dir) / source_part["source_file"]
        if not bill_path.exists():
            raise FileNotFoundError(f"Configured FY2026 source file is missing: {bill_path}")
        return bill_path

    def _metadata_for_source_part(self, division: str, source_part: dict[str, str]) -> dict[str, str]:
        """Return metadata to preserve for chunks from a configured source part."""
        if division_acronym(division) != "CRX":
            return {}
        return {
            "source_public_law": source_part["source_public_law"],
            "source_division_letter": source_part["source_division_letter"],
            "source_division_title": source_part["source_division_title"],
            "source_bucket": "CRX",
        }

    def _extract_division_text(self, bill_path: Path, letter: str) -> str:
        """Extract the text for one division from a bill HTML file.

        Args:
            bill_path: Path to a source bill HTML file.
            letter: Division letter to extract.

        Returns:
            Cleaned text for the matching division.
        """
        if not bill_path.exists():
            raise FileNotFoundError(f"Configured FY2026 source file is missing: {bill_path}")
        html = bill_path.read_text(encoding="utf-8", errors="ignore")
        text = BeautifulSoup(html, "html.parser").get_text("\n")
        text = re.sub(r"<<NOTE:[^>]+>>", "", text)
        text = re.sub(r"\n{3,}", "\n\n", text)

        matches = list(DIVISION_PATTERN.finditer(text))
        if not matches:
            raise ValueError(f"No division headers found in configured FY2026 source file: {bill_path}")

        requested_letter = letter.upper()
        matching_indexes = [index for index, match in enumerate(matches) if match.group(1).upper() == requested_letter]
        if not matching_indexes:
            raise ValueError(
                f"Division {requested_letter} header not found in configured FY2026 source file: {bill_path}"
            )

        match_index = matching_indexes[-1]
        start = matches[match_index].start()
        end = matches[match_index + 1].start() if match_index + 1 < len(matches) else len(text)
        return text[start:end].strip()

    def _chunk_documents(
        self,
        text: str,
        division: str,
        source_file: str,
        chunk_size: int | None = None,
        chunk_overlap: int | None = None,
        vector_store_id: str | None = None,
        metadata_extra: dict[str, str] | None = None,
        chunk_index_offset: int = 0,
    ) -> list[Document]:
        """Split division text into LangChain documents with stable metadata.

        Args:
            text: Source division text to chunk.
            division: Full division name for metadata and citations.
            source_file: Source HTML filename for metadata.
            chunk_size: Optional character count per chunk.
            chunk_overlap: Optional character overlap between adjacent chunks.
            vector_store_id: Optional vector store registry id for metadata.
            metadata_extra: Optional source-part metadata to carry into Chroma.
            chunk_index_offset: Offset used when combining multiple source parts in one store.

        Returns:
            List of LangChain Document objects ready for Chroma ingestion.
        """
        chunk_size = chunk_size or self.settings.chunk_size
        overlap = chunk_overlap if chunk_overlap is not None else self.settings.chunk_overlap
        overlap = min(overlap, max(chunk_size - 1, 0))
        docs: list[Document] = []

        start = 0
        while start < len(text):
            chunk = text[start : start + chunk_size].strip()
            if chunk:
                docs.append(
                    Document(
                        page_content=chunk,
                        metadata={
                            "chunk_id": str(uuid.uuid4()),
                            "vector_store_id": vector_store_id,
                            "division": division,
                            "division_acronym": division_acronym(division),
                            "source_file": source_file,
                            "chunk_index": chunk_index_offset + len(docs),
                            **(metadata_extra or {}),
                        },
                    )
                )
            start += max(chunk_size - overlap, 1)

        return docs
