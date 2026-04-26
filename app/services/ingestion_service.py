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
        self.settings = get_settings()

    def ingest(
        self,
        embedding_model: str,
        clear_existing: bool = True,
        chunk_size: int | None = None,
        vectorstore_dir: str | Path | None = None,
        vector_store_id: str | None = None,
    ) -> tuple[int, dict[str, int], int]:
        """Rebuild per-division Chroma stores and return processed count."""
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
            bill_path = self._bill_path_for_store(store_name)
            text = self._extract_division_text(bill_path, self._division_letter(store_name))
            documents = self._chunk_documents(text, division, bill_path.name, chunk_size, vector_store_id)
            if not documents:
                continue

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

    def _bill_path_for_store(self, store_name: str) -> Path:
        if store_name.startswith("Consolidated_Appropriations"):
            return Path(self.settings.data_dir) / "Consolidated_Appropriations_Act_2024_Public_Law.html"
        return Path(self.settings.data_dir) / "Further_Consolidated_Appropriations_Act_2024_Public_Law.html"

    def _division_letter(self, store_name: str) -> str:
        match = re.search(r"_Division_([A-G])_", store_name)
        if not match:
            raise ValueError(f"Could not determine division letter from store name: {store_name}")
        return match.group(1)

    def _extract_division_text(self, bill_path: Path, letter: str) -> str:
        html = bill_path.read_text(encoding="utf-8", errors="ignore")
        text = BeautifulSoup(html, "html.parser").get_text("\n")
        text = re.sub(r"<<NOTE:[^>]+>>", "", text)
        text = re.sub(r"\n{3,}", "\n\n", text)

        matches = list(DIVISION_PATTERN.finditer(text))
        if not matches:
            return text

        matching_indexes = [index for index, match in enumerate(matches) if match.group(1).upper() == letter]
        if not matching_indexes:
            return text

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
        vector_store_id: str | None = None,
    ) -> list[Document]:
        chunk_size = chunk_size or self.settings.chunk_size
        overlap = min(self.settings.chunk_overlap, max(chunk_size // 8, 1))
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
                            "chunk_index": len(docs),
                        },
                    )
                )
            start += max(chunk_size - overlap, 1)

        return docs
