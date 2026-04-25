from app.services.ingestion_service import IngestionService


def test_dhs_extraction_uses_body_header_not_table_of_contents():
    service = IngestionService()
    store_name = service.settings.subcommittee_stores["DEPARTMENT OF HOMELAND SECURITY"]
    bill_path = service._bill_path_for_store(store_name)

    text = service._extract_division_text(bill_path, "C")
    docs = service._chunk_documents(
        text,
        "DEPARTMENT OF HOMELAND SECURITY",
        bill_path.name,
    )

    assert len(docs) > 50
    assert "Federal Emergency Management Agency" in text
    assert "$20,261,000,000" in text
