from app.services.ingestion_service import IngestionService


def test_fy2026_extraction_uses_body_header_not_table_of_contents():
    service = IngestionService()
    division = "AGRICULTURE, RURAL DEVELOPMENT, FOOD AND DRUG ADMINISTRATION, AND RELATED AGENCIES"
    source_part = service._source_parts_for_division(division)[0]
    bill_path = service._resolve_source_path(source_part)

    text = service._extract_division_text(bill_path, source_part["source_division_letter"])
    docs = service._chunk_documents(
        text,
        division,
        bill_path.name,
    )

    assert len(docs) > 2
    assert "Food and Drug Administration" in text
    assert "DIVISION C--" not in text


def test_chunk_documents_uses_explicit_overlap():
    service = IngestionService()

    docs = service._chunk_documents(
        "abcdefghijklmnopqrstuvwxyz",
        "CONTINUING APPROPRIATIONS, EXTENDERS, HOMELAND SECURITY, AND OTHER MATTERS",
        "bill.html",
        chunk_size=10,
        chunk_overlap=4,
    )

    assert [doc.page_content for doc in docs[:3]] == [
        "abcdefghij",
        "ghijklmnop",
        "mnopqrstuv",
    ]


def test_chunk_documents_clamps_overlap_below_chunk_size():
    service = IngestionService()

    docs = service._chunk_documents(
        "abcdefghijkl",
        "CONTINUING APPROPRIATIONS, EXTENDERS, HOMELAND SECURITY, AND OTHER MATTERS",
        "bill.html",
        chunk_size=10,
        chunk_overlap=20,
    )

    assert docs[0].page_content == "abcdefghij"
    assert docs[1].page_content == "bcdefghijk"


def test_crx_chunks_preserve_original_source_division_metadata():
    service = IngestionService()
    division = "CONTINUING APPROPRIATIONS, EXTENDERS, HOMELAND SECURITY, AND OTHER MATTERS"
    source_part = service._source_parts_for_division(division)[0]

    docs = service._chunk_documents(
        "abcdefghijklmnopqrstuvwxyz",
        division,
        "bill.html",
        chunk_size=10,
        chunk_overlap=0,
        metadata_extra=service._metadata_for_source_part(division, source_part),
    )

    assert docs[0].metadata["division_acronym"] == "CRX"
    assert docs[0].metadata["source_bucket"] == "CRX"
    assert docs[0].metadata["source_public_law"] == "P.L. 119-37"
    assert docs[0].metadata["source_division_letter"] == "A"


def test_fy2026_consolidated_division_g_extraction_is_a_legitimate_short_part():
    service = IngestionService()
    division = "CONTINUING APPROPRIATIONS, EXTENDERS, HOMELAND SECURITY, AND OTHER MATTERS"
    source_part = next(
        part
        for part in service._source_parts_for_division(division)
        if part["source_file"] == "2026/FY2026_CONSOLIDATED.htm" and part["source_division_letter"] == "G"
    )
    bill_path = service._resolve_source_path(source_part)

    text = service._extract_division_text(bill_path, "G")
    docs = service._chunk_documents(
        text,
        "CONTINUING APPROPRIATIONS, EXTENDERS, HOMELAND SECURITY, AND OTHER MATTERS",
        bill_path.name,
    )

    assert "DIVISION G--OTHER MATTERS" in text
    assert "SEC. 101. FUNDING LIMITATION." in text
    assert "United Nations Relief and" in text
    assert "Works Agency" in text
    assert "DIVISION H--" not in text
    assert len(docs) == 1
    assert source_part["min_chunks"] == 1
