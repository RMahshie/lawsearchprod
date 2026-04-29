import pytest

from app.models.query import QueryRequest
from app.models.storage import CreateVectorStoreRequest


def test_divisions_filter_is_preserved_for_routing_bypass():
    request = QueryRequest(
        question="How much funding did CRX receive?",
        divisions_filter=["CONTINUING APPROPRIATIONS, EXTENDERS, HOMELAND SECURITY, AND OTHER MATTERS"],
        max_results=3,
    )

    assert request.divisions_filter == ["CONTINUING APPROPRIATIONS, EXTENDERS, HOMELAND SECURITY, AND OTHER MATTERS"]
    assert request.max_results == 3


def test_invalid_division_filter_is_rejected():
    with pytest.raises(ValueError):
        QueryRequest(
            question="How much funding did CRX receive?",
            divisions_filter=["NOT A REAL DIVISION"],
        )


def test_create_vector_store_request_accepts_overlap():
    request = CreateVectorStoreRequest(
        name="FY2026 1500 chunks",
        embedding_model="text-embedding-3-large",
        chunk_size=1500,
        chunk_overlap=350,
    )

    assert request.chunk_size == 1500
    assert request.chunk_overlap == 350


def test_create_vector_store_request_rejects_overlap_at_or_above_chunk_size():
    with pytest.raises(ValueError):
        CreateVectorStoreRequest(
            name="Bad overlap",
            embedding_model="text-embedding-3-large",
            chunk_size=800,
            chunk_overlap=800,
        )
