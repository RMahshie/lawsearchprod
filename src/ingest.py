#!/usr/bin/env python3
# MUST be at the very top before any other imports
import sys
try:
    import pysqlite3
    sys.modules["sqlite3"] = pysqlite3
except ImportError:
    pass  # Will use system sqlite if pysqlite3 not available

import re
import os
import shutil
import glob

# Import libraries for web scraping and document processing
from bs4 import BeautifulSoup
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from src.config import DATA_DIR, VECTORSTORE_DIR, EMBEDDING_MODEL, CHUNK_SIZE, CHUNK_OVERLAP

# Get OpenAI API key from environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Regex pattern for division headers - matches patterns like "DIVISION A -- DEPARTMENT OF DEFENSE"
# This captures the division letter and the agency/department name that follows
division_pattern = re.compile(
    r'^\s*DIVISION\s+([A-Z])\s*--\s*(?:(OTHER MATTERS)|((?:(?!APPROPRIATIONS).)+))',
    re.IGNORECASE | re.MULTILINE | re.DOTALL
)

def process_file(path: str) -> dict[str, str]:
    """Split a single HTML bill into division-labeled text chunks."""
    # Read and parse the HTML file containing the congressional bill
    html = open(path, encoding="utf-8").read()
    soup = BeautifulSoup(html, "html.parser")
    
    # Extract plain text from HTML and clean up formatting
    full_text = soup.get_text(separator="\n")
    # Remove legislative note markers that clutter the text
    clean_text = re.sub(r'<<NOTE:[^>]+>>', '', full_text)

    # Find all division headers in the document
    matches = list(division_pattern.finditer(clean_text))
    if not matches:
        return {}

    # Map division letter to agency name - creates a lookup table
    # For example: {'A': 'DEPARTMENT OF DEFENSE', 'B': 'DEPARTMENT OF HOMELAND SECURITY'}
    division_names: dict[str, str] = {}
    for m in matches:
        div = m.group(1).upper()  # Extract the division letter (A, B, C, etc.)
        raw = m.group(2) or m.group(3) or ''  # Extract the agency/department name
        division_names[div] = ' '.join(raw.split())  # Clean up whitespace

    # Build list of (start position, letter) pairs and slice the text accordingly
    # This creates separate text chunks for each division
    headers = sorted((m.start(), m.group(1).upper()) for m in matches)
    chunks: dict[str, str] = {}
    for i, (start, div) in enumerate(headers):
        # Find where this division ends (start of next division or end of document)
        end = headers[i+1][0] if i+1 < len(headers) else len(clean_text)
        chunk_text = clean_text[start:end].strip()
        # Create a descriptive label that includes filename, division, and agency
        label = f"{os.path.basename(path)} - Division {div} - {division_names[div]}"
        chunks[label] = chunk_text
    return chunks


def ingest_all():
    """Ingest all HTML files in DATA_DIR into per-division Chroma databases."""
    # Create the vectorstore directory if it doesn't exist
    os.makedirs(VECTORSTORE_DIR, exist_ok=True)
    
    # Find all HTML files in the data directory
    html_files = glob.glob(os.path.join(DATA_DIR, '*.html'))
    if not html_files:
        raise RuntimeError(f"No HTML files found in {DATA_DIR}")

    # Process each HTML file and collect all division chunks
    all_chunks: dict[str, str] = {}
    for file in html_files:
        divisions = process_file(file)
        print(f"Found {len(divisions)} divisions in {os.path.basename(file)}")
        all_chunks.update(divisions)

    # Initialize the embedding model and text splitter for creating vector embeddings
    embedder = OpenAIEmbeddings(model=EMBEDDING_MODEL)
    # Split large division texts into smaller, overlapping chunks for better retrieval
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP
    )

    # Create or refresh each division's vectorstore - one database per division
    for label, text in all_chunks.items():
        # Split the division text into smaller chunks that the LLM can process
        docs = splitter.split_documents([
            Document(page_content=text, metadata={'division': label})
        ])
        
        # Create a safe filename by replacing special characters with underscores
        safe_name = re.sub(r'[^\w]+', '_', label)
        db_path = os.path.join(VECTORSTORE_DIR, safe_name)
        
        # Remove existing database if it exists to ensure fresh data
        if os.path.exists(db_path):
            shutil.rmtree(db_path)
        os.makedirs(db_path, exist_ok=True)

        # Create ChromaDB vectorstore with embeddings for fast similarity search
        Chroma.from_documents(
            docs,
            embedder,
            persist_directory=db_path
        )
        print(f"Created Chroma DB for '{label}' at '{db_path}'")


if __name__ == '__main__':
    ingest_all()
