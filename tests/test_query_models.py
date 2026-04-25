import pytest

from app.models.query import QueryRequest


def test_divisions_filter_is_preserved_for_routing_bypass():
    request = QueryRequest(
        question="How much funding did DHS receive?",
        divisions_filter=["DEPARTMENT OF HOMELAND SECURITY"],
        max_results=3,
    )

    assert request.divisions_filter == ["DEPARTMENT OF HOMELAND SECURITY"]
    assert request.max_results == 3


def test_invalid_division_filter_is_rejected():
    with pytest.raises(ValueError):
        QueryRequest(
            question="How much funding did DHS receive?",
            divisions_filter=["NOT A REAL DIVISION"],
        )

