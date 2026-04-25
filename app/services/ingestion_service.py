"""HTML bill ingestion into per-division Chroma stores."""

from __future__ import annotations

import os
import re
import shutil
from pathlib import Path

from bs4 import BeautifulSoup
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings

from app.core.config import get_settings
from app.services.vector_store_service import division_acronym


class IngestionService:
    """Build persisted Chroma stores from the source bill HTML files."""

    def __init__(self):
        self.settings = get_settings()

    def ingest(self, embedding_model: str, clear_existing: bool = True) -> int:
        """Rebuild per-division Chroma stores and return processed count."""
        vectorstore_dir = Path(self.settings.vectorstore_dir)
        if clear_existing and vectorstore_dir.exists():
            shutil.rmtree(vectorstore_dir)
        vectorstore_dir.mkdir(parents=True, exist_ok=True)

        embeddings = OpenAIEmbeddings(model=embedding_model)
        divisions_processed = 0

        for division, store_name in self.settings.subcommittee_stores.items():
            bill_path = self._bill_path_for_store(store_name)
            text = self._extract_division_text(bill_path, self._division_letter(store_name))
            documents = self._chunk_documents(text, division, bill_path.name)
            if not documents:
                continue

            persist_directory = vectorstore_dir / store_name
            persist_directory.mkdir(parents=True, exist_ok=True)
            Chroma.from_documents(
                documents=documents,
                embedding=embeddings,
                persist_directory=str(persist_directory),
            )
            divisions_processed += 1

        return divisions_processed

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
        text = re.sub(r"\n{3,}", "\n\n", text)

        starts = [m.start() for m in re.finditer(rf"DIVISION\s+{letter}\s*--", text)]
        if not starts:
            return text

        start = starts[1] if len(starts) > 1 else starts[0]
        next_starts = [
            m.start()
            for m in re.finditer(r"DIVISION\s+[A-G]\s*--", text[start + 1 :])
        ]
        end = start + 1 + min(next_starts) if next_starts else len(text)
        return text[start:end].strip()

    def _chunk_documents(self, text: str, division: str, source_file: str) -> list[Document]:
        chunk_size = self.settings.chunk_size
        overlap = self.settings.chunk_overlap
        docs: list[Document] = []

        start = 0
        while start < len(text):
            chunk = text[start : start + chunk_size].strip()
            if chunk:
                docs.append(
                    Document(
                        page_content=chunk,
                        metadata={
                            "division": division,
                            "division_acronym": division_acronym(division),
                            "source_file": source_file,
                            "chunk_index": len(docs),
                        },
                    )
                )
            start += max(chunk_size - overlap, 1)

        return docs
