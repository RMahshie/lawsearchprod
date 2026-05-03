import os

import app.core.config as config_module
from app.core.config import (
    FY2026_INCOMPATIBLE_QUESTION_ANSWER,
    Settings,
    _export_langsmith_environment,
    get_settings,
)
from app.services.llm_factory import describe_model_strategy, resolve_model
from app.services.rag.stages.rewrite import rewrite_division_queries
from app.services.rag_service import RAGService
from app.services.vector_store_service import VectorStoreService, division_acronym


_CREATE_CHAT_MODEL_TARGETS = (
    "app.services.rag.stages.classify.create_chat_model",
    "app.services.rag.stages.route.create_chat_model",
    "app.services.rag.stages.rewrite.create_chat_model",
    "app.services.rag.stages.map_chunk.create_chat_model",
    "app.services.rag.stages.reduce.create_chat_model",
    "app.services.rag.stages.synthesize.create_chat_model",
)


def _patch_create_chat_model(monkeypatch, factory):
    """Patch ``create_chat_model`` on every stage module so tests can intercept
    LLM construction regardless of which pipeline stage they exercise.
    """
    for target in _CREATE_CHAT_MODEL_TARGETS:
        monkeypatch.setattr(target, factory)


class FakeMessage:
    def __init__(self, content: str):
        self.content = content


class FakeLLM:
    def invoke(self, prompt):
        if "UI excerpt label" in str(prompt):
            return FakeMessage("CRX cybersecurity funding")
        if "source hover summary" in str(prompt):
            return FakeMessage("Chunk summarizes CRX cybersecurity funding.")
        return FakeMessage("Extracted $10,000,000 for cybersecurity [CRX].")


class FakeStatusError(Exception):
    def __init__(self, status_code: int):
        super().__init__(f"status {status_code}")
        self.status_code = status_code


def test_settings_accepts_and_exports_langsmith_environment(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")
    monkeypatch.setenv("langsmith_tracing", "true")
    monkeypatch.setenv("langsmith_endpoint", "https://api.smith.langchain.com")
    monkeypatch.setenv("langsmith_api_key", "test-langsmith-key")
    monkeypatch.setenv("langsmith_project", "lawsearch")
    monkeypatch.delenv("LANGSMITH_TRACING", raising=False)
    monkeypatch.delenv("LANGSMITH_ENDPOINT", raising=False)
    monkeypatch.delenv("LANGSMITH_API_KEY", raising=False)
    monkeypatch.delenv("LANGSMITH_PROJECT", raising=False)

    settings = Settings(_env_file=None)

    assert settings.langsmith_tracing is True
    assert settings.langsmith_endpoint == "https://api.smith.langchain.com"
    assert settings.langsmith_api_key == "test-langsmith-key"
    assert settings.langsmith_project == "lawsearch"

    _export_langsmith_environment(settings)

    assert os.environ["LANGSMITH_TRACING"] == "true"
    assert os.environ["LANGSMITH_ENDPOINT"] == "https://api.smith.langchain.com"
    assert os.environ["LANGSMITH_API_KEY"] == "test-langsmith-key"
    assert os.environ["LANGSMITH_PROJECT"] == "lawsearch"


class FlakyLLM:
    def __init__(self, status_code: int):
        self.status_code = status_code
        self.calls = 0

    def invoke(self, prompt):
        self.calls += 1
        if self.calls == 1:
            raise FakeStatusError(self.status_code)
        return FakeMessage("Recovered response.")


class FakeStructuredLLM:
    def __init__(self, response):
        self.response = response

    def invoke(self, prompt):
        return self.response


class FakeRewriteLLM:
    def __init__(self, response):
        self.response = response

    def with_structured_output(self, schema):
        return FakeStructuredLLM(self.response)


class CapturingStructuredLLM:
    def __init__(self, response):
        self.response = response
        self.prompts = []

    def with_structured_output(self, schema):
        return self

    def invoke(self, prompt):
        self.prompts.append(prompt)
        return self.response


def test_division_acronym_is_stable():
    assert division_acronym("CONTINUING APPROPRIATIONS, EXTENDERS, HOMELAND SECURITY, AND OTHER MATTERS") == "CRX"


def test_classify_prompt_uses_answer_mode_examples(monkeypatch):
    from app.services.rag_service import AnswerModeDecision, AnswerModeFlags

    llm = CapturingStructuredLLM(
        AnswerModeDecision(
            answer_mode="funding_mechanism_no_amount",
            answer_mode_flags=AnswerModeFlags(mixed_financial_types=False),
            answer_mode_reason="FEMA continuation question.",
        )
    )
    _patch_create_chat_model(monkeypatch, lambda model, task, reasoning_effort=None: llm)
    service = RAGService.__new__(RAGService)
    service.settings = get_settings()

    result = service._classify_answer_mode(
        {
            "query_id": "query-test",
            "question": "How much FEMA funding is continued?",
            "thinking_speed": "normal",
        }
    )

    prompt = llm.prompts[0]
    assert result["answer_mode"] == "funding_mechanism_no_amount"
    assert result["answer_mode_flags"] == {"mixed_financial_types": False}
    assert result["answer_mode_reason"] == "FEMA continuation question."
    assert "Set answer_mode to one of" in prompt[0].content
    assert "The mode examples below are illustrative, not exhaustive" in prompt[0].content
    assert "asking for major allowed uses does not by itself mean reconciliation_breakdown" in prompt[0].content
    assert "Use reconciliation_breakdown only when the user asks for breakdown, allocation, line items" in prompt[0].content
    assert "What amount is appropriated for the FDA Salaries and Expenses account" in prompt[0].content
    assert "Break down FDA Salaries and Expenses by center and user-fee source" in prompt[0].content
    assert "If the best mode is ambiguous, use broad_topic_total" in prompt[0].content
    assert "answer_mode_flags.mixed_financial_types=true" in prompt[0].content
    assert "Allowed FY2026 divisions and routing hints:" not in prompt[0].content


def test_route_prompt_uses_fy2026_labels_and_aliases(monkeypatch):
    from app.services.rag_service import RouteDecision

    llm = CapturingStructuredLLM(
        RouteDecision(divisions=["CONTINUING APPROPRIATIONS, EXTENDERS, HOMELAND SECURITY, AND OTHER MATTERS"])
    )
    _patch_create_chat_model(monkeypatch, lambda model, task, reasoning_effort=None: llm)
    service = RAGService.__new__(RAGService)
    service.settings = get_settings()

    result = service._route_divisions(
        {
            "query_id": "query-test",
            "question": "How much FEMA funding is continued?",
            "thinking_speed": "normal",
            "answer_mode": "funding_mechanism_no_amount",
            "answer_mode_flags": {"mixed_financial_types": False},
            "answer_mode_reason": "FEMA continuation question.",
        }
    )

    prompt = llm.prompts[0]
    assert result["selected_divisions"] == [
        "CONTINUING APPROPRIATIONS, EXTENDERS, HOMELAND SECURITY, AND OTHER MATTERS"
    ]
    assert "answer_mode" not in result
    assert "Allowed FY2026 divisions and routing hints:" in prompt[1].content
    assert "CONTINUING APPROPRIATIONS, EXTENDERS, HOMELAND SECURITY, AND OTHER MATTERS" in prompt[1].content
    assert "FEMA" in prompt[1].content
    assert "DEPARTMENT OF HOMELAND SECURITY" not in prompt[1].content
    assert "Select the relevant appropriations divisions" in prompt[0].content
    assert "Do not classify the answer style" in prompt[0].content
    assert "Appropriations routing follows bill-division jurisdiction" in prompt[0].content
    assert "FDA Salaries and Expenses" in prompt[0].content
    assert "not LHHS" in prompt[0].content
    assert "NIH, CDC, CMS" in prompt[0].content
    assert "EPA routes to DEPARTMENT OF THE INTERIOR" in prompt[0].content
    assert "Set answer_mode to one of" not in prompt[0].content
    assert "What amount is appropriated for the FDA Salaries and Expenses account" not in prompt[0].content


def test_route_divisions_filter_bypasses_router(monkeypatch):
    def fail_create_chat_model(*args, **kwargs):
        raise AssertionError("router should not be initialized when divisions_filter is supplied")

    _patch_create_chat_model(monkeypatch, fail_create_chat_model)
    service = RAGService.__new__(RAGService)
    service.settings = get_settings()

    selected = ["CONTINUING APPROPRIATIONS, EXTENDERS, HOMELAND SECURITY, AND OTHER MATTERS"]
    result = service._route_divisions(
        {
            "query_id": "query-test",
            "question": "How much FEMA funding is continued?",
            "thinking_speed": "normal",
            "divisions_filter": selected,
            "answer_mode": "funding_mechanism_no_amount",
            "answer_mode_flags": {"mixed_financial_types": False},
            "answer_mode_reason": "Manual filter.",
        }
    )

    assert result == {"selected_divisions": selected}


def test_route_returns_incompatible_answer_when_no_valid_fy2026_division(monkeypatch):
    from app.services.rag_service import RouteDecision

    llm = CapturingStructuredLLM(RouteDecision(divisions=["DEPARTMENT OF HOMELAND SECURITY"]))
    _patch_create_chat_model(monkeypatch, lambda model, task, reasoning_effort=None: llm)
    service = RAGService.__new__(RAGService)
    service.settings = get_settings()

    result = service._route_divisions(
        {
            "query_id": "query-test",
            "question": "Who won the World Series?",
            "thinking_speed": "normal",
        }
    )

    assert result["selected_divisions"] == []
    assert result["final_answer"] == FY2026_INCOMPATIBLE_QUESTION_ANSWER
    assert "answer_mode" not in result


def test_route_normalizes_known_division_acronyms(monkeypatch):
    from app.core.config import FY2026_DIVISIONS
    from app.services.rag_service import RouteDecision

    llm = CapturingStructuredLLM(RouteDecision(divisions=["AG"]))
    _patch_create_chat_model(monkeypatch, lambda model, task, reasoning_effort=None: llm)
    service = RAGService.__new__(RAGService)
    service.settings = get_settings()

    result = service._route_divisions(
        {
            "query_id": "query-test",
            "question": "What amount is appropriated for FDA Salaries and Expenses?",
            "thinking_speed": "normal",
        }
    )

    assert result["selected_divisions"] == [FY2026_DIVISIONS[0]]
    assert "answer_mode" not in result
    assert "final_answer" not in result


def test_query_source_model_does_not_persist_source_text_or_scores():
    from app.db.models import QuerySource

    assert not hasattr(QuerySource, "content_snippet")
    assert not hasattr(QuerySource, "source_metadata")
    assert not hasattr(QuerySource, "score")


def test_number_annotation_model_does_not_persist_source_text_or_summaries():
    from app.models.query import NumberAnnotation

    annotation = NumberAnnotation(
        id="src_a",
        kind="source",
        figure="$10",
        value=10,
        label="A",
        source={"chunk_id": "chunk-a"},
    )
    dumped = annotation.model_dump(mode="json", exclude_none=True)

    assert dumped["source"] == {"chunk_id": "chunk-a"}
    assert "source_quote" not in dumped
    assert "chunk_summary" not in dumped
    assert "chunk_snapshot" not in dumped


def test_load_conversation_hydrates_sources_from_chroma_only():
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from app.db.models import EmbeddingModel, QueryDivisionResult, QueryRun, QuerySource, VectorStore
    from app.db.session import Base
    from app.services.storage_registry import load_conversation

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    db.add(EmbeddingModel(id="embed", name="text-embedding-3-large"))
    db.add(
        VectorStore(
            id="store",
            name="Current",
            embedding_model_id="embed",
            chunk_size=1000,
            chunk_overlap=100,
            relative_path="store",
            status="ready",
        )
    )
    db.add(
        QueryRun(
            id="query",
            question="How much CRX funding?",
            answer="Answer",
            vector_store_id="store",
            processing_time=1.0,
        )
    )
    db.add(
        QueryDivisionResult(
            id="division",
            query_run_id="query",
            division_key="CONTINUING APPROPRIATIONS, EXTENDERS, HOMELAND SECURITY, AND OTHER MATTERS",
            answer="Division answer",
            chunks_retrieved=2,
            sort_order=0,
        )
    )
    db.add_all(
        [
            QuerySource(
                query_run_id="query",
                query_division_result_id="division",
                chunk_id="missing",
                rank=1,
                chunk_summary="Missing summary",
                chunk_snapshot="Missing snapshot",
            ),
            QuerySource(
                query_run_id="query",
                query_division_result_id="division",
                chunk_id="present",
                rank=2,
                chunk_summary="Present summary",
                chunk_snapshot="Present snapshot",
            ),
        ]
    )
    db.commit()

    def chunk_loader(_store, _division, chunk_id):
        if chunk_id == "present":
            return {"content": "Hydrated Chroma chunk text.", "metadata": {"source_file": "bill.html"}}
        return None

    response = load_conversation(db, "query", chunk_loader)

    assert response.sources is not None
    assert [source.chunk_id for source in response.sources] == ["present"]
    assert response.sources[0].content_snippet == "Hydrated Chroma chunk text."
    assert response.sources[0].chunk_summary == "Present summary"
    assert response.division_results[0].source_chunk_ids == ["present"]


def test_load_conversation_skips_legacy_invalid_division_sources():
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from app.db.models import EmbeddingModel, QueryDivisionResult, QueryRun, QuerySource, VectorStore
    from app.db.session import Base
    from app.services.storage_registry import load_conversation

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    db.add(EmbeddingModel(id="embed", name="text-embedding-3-large"))
    db.add(
        VectorStore(
            id="store",
            name="Current",
            embedding_model_id="embed",
            chunk_size=1000,
            chunk_overlap=100,
            relative_path="store",
            status="ready",
        )
    )
    db.add(
        QueryRun(
            id="query",
            question="How much DHS funding?",
            answer="Saved answer",
            vector_store_id="store",
            processing_time=1.0,
        )
    )
    db.add(
        QueryDivisionResult(
            id="division",
            query_run_id="query",
            division_key="DEPARTMENT OF HOMELAND SECURITY",
            answer="Legacy division answer",
            chunks_retrieved=1,
            sort_order=0,
        )
    )
    db.add(
        QuerySource(
            query_run_id="query",
            query_division_result_id="division",
            chunk_id="legacy-source",
            rank=1,
            chunk_summary="Legacy summary",
            chunk_snapshot="Legacy snapshot",
        )
    )
    db.commit()

    def chunk_loader(_store, division, _chunk_id):
        raise KeyError(division)

    response = load_conversation(db, "query", chunk_loader)

    assert response.answer == "Saved answer"
    assert response.sources == []
    assert response.division_results[0].division == "DEPARTMENT OF HOMELAND SECURITY"
    assert response.division_results[0].source_chunk_ids == []


def test_load_conversation_returns_saved_number_annotations():
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from app.db.models import QueryRun
    from app.db.session import Base
    from app.services.storage_registry import load_conversation

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    db.add(
        QueryRun(
            id="query",
            question="How much funding?",
            answer="Answer $10 [[num:src_crx_1]]",
            processing_time=1.0,
            number_annotations=[
                {
                    "id": "src_crx_1",
                    "kind": "source",
                    "figure": "$10",
                    "value": 10,
                    "label": "CRX funding",
                    "targets": [{"scope": "answer"}],
                    "source": {"chunk_id": "chunk-1"},
                }
            ],
        )
    )
    db.commit()

    response = load_conversation(db, "query", lambda *_args: None)

    assert response.number_annotations[0].id == "src_crx_1"
    assert response.number_annotations[0].targets[0].scope == "answer"
    assert response.number_annotations[0].value == 10
    assert response.number_annotations[0].source.chunk_id == "chunk-1"


def test_list_conversations_strips_hidden_number_markers_from_preview():
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from app.db.models import QueryRun
    from app.db.session import Base
    from app.services.storage_registry import list_conversations

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    db.add(
        QueryRun(
            id="query",
            question="How much funding?",
            answer="Answer $10 [[num:src_crx_1]] for CRX",
            processing_time=1.0,
        )
    )
    db.commit()

    summaries = list_conversations(db)

    assert summaries[0]["answer_preview"] == "Answer $10 for CRX"


def test_save_query_response_persists_answer_mode_debug_metadata():
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from app.db.models import QueryRun
    from app.db.session import Base
    from app.models.query import QueryResponse
    from app.services.storage_registry import save_query_response

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    response = QueryResponse(
        answer="Answer",
        processing_time=1.0,
        selected_divisions=[],
        division_results=[],
        sources=[],
        query_id="query",
    )

    save_query_response(
        db,
        response=response,
        question="How much funding?",
        vector_store=None,
        answer_mode="broad_topic_total",
        answer_mode_flags={"mixed_financial_types": True},
        answer_mode_reason="Broad infrastructure funding question.",
        relevance_metadata=[
            {
                "scope": "division",
                "division_acronym": "AG",
                "counts": {"direct": 2, "adjacent": 1, "not_responsive": 0},
            }
        ],
    )
    db.commit()

    run = db.get(QueryRun, "query")
    assert run.answer_mode == "broad_topic_total"
    assert run.answer_mode_flags == {"mixed_financial_types": True}
    assert run.answer_mode_reason == "Broad infrastructure funding question."
    assert run.relevance_metadata[0]["counts"] == {"direct": 2, "adjacent": 1, "not_responsive": 0}


def test_map_chunk_returns_facts_and_summary(monkeypatch):
    _patch_create_chat_model(monkeypatch, lambda model, task, reasoning_effort=None: FakeLLM())
    service = RAGService.__new__(RAGService)

    result = service._map_chunk(
        {
            "question": "How much cybersecurity funding is provided?",
            "model_used": "gpt-4o",
            "chunk": {
                "chunk_id": "CRX-1-test",
                "division": "CONTINUING APPROPRIATIONS, EXTENDERS, HOMELAND SECURITY, AND OTHER MATTERS",
                "division_acronym": "CRX",
                "content": "For cybersecurity, $10,000,000 shall be available.",
                "chunk_summary": None,
                "score": 0.1,
                "metadata": {"source_file": "bill.html"},
            },
        }
    )

    mapped = result["mapped_chunks"][0]
    assert mapped["division"] == "CONTINUING APPROPRIATIONS, EXTENDERS, HOMELAND SECURITY, AND OTHER MATTERS"
    assert mapped["chunk_summary"] == "Chunk summarizes CRX cybersecurity funding."
    assert mapped["chunk_snapshot"] == "CRX cybersecurity funding"
    assert "$10,000,000" in mapped["extracted_facts"]


def test_invoke_text_retries_once_for_transient_error(monkeypatch):
    monkeypatch.setattr("app.services.rag.llm_invocation.time.sleep", lambda seconds: None)
    service = RAGService.__new__(RAGService)
    llm = FlakyLLM(500)

    result = service._invoke_text(llm, "prompt", stage="route", query_id="query-test")

    assert result == "Recovered response."
    assert llm.calls == 2


def test_invoke_text_does_not_retry_non_transient_error(monkeypatch):
    monkeypatch.setattr("app.services.rag.llm_invocation.time.sleep", lambda seconds: None)
    service = RAGService.__new__(RAGService)
    llm = FlakyLLM(400)

    try:
        service._invoke_text(llm, "prompt", stage="route", query_id="query-test")
    except FakeStatusError:
        pass
    else:
        raise AssertionError("Expected non-transient error to be raised")

    assert llm.calls == 1


def test_response_includes_sources_and_division_results():
    service = RAGService.__new__(RAGService)
    result = {
        "final_answer": "CRX receives $10,000,000 [CRX].",
        "selected_divisions": ["CONTINUING APPROPRIATIONS, EXTENDERS, HOMELAND SECURITY, AND OTHER MATTERS"],
        "include_sources": True,
        "thinking_speed": "normal",
        "model_used": "gpt-4o",
        "division_queries": [
            {
                "division": "CONTINUING APPROPRIATIONS, EXTENDERS, HOMELAND SECURITY, AND OTHER MATTERS",
                "division_acronym": "CRX",
                "query": "How much funding is provided for CRX cybersecurity?",
            }
        ],
        "retrieved_chunks": [
            {
                "chunk_id": "CRX-1-test",
                "division": "CONTINUING APPROPRIATIONS, EXTENDERS, HOMELAND SECURITY, AND OTHER MATTERS",
                "division_acronym": "CRX",
                "content": "For cybersecurity, $10,000,000 shall be available.",
                "chunk_summary": None,
                "score": 0.1,
                "metadata": {"source_file": "bill.html"},
            }
        ],
        "mapped_chunks": [
            {
                "chunk_id": "CRX-1-test",
                "division": "CONTINUING APPROPRIATIONS, EXTENDERS, HOMELAND SECURITY, AND OTHER MATTERS",
                "division_acronym": "CRX",
                "extracted_facts": "Extracted $10,000,000 for cybersecurity [CRX].",
                "chunk_summary": "Chunk summarizes CRX cybersecurity funding.",
                "chunk_snapshot": "CRX cybersecurity funding",
                "source_content": "For cybersecurity, $10,000,000 shall be available.",
                "score": 0.1,
                "metadata": {"source_file": "bill.html"},
            }
        ],
        "division_answers": [
            {
                "division": "CONTINUING APPROPRIATIONS, EXTENDERS, HOMELAND SECURITY, AND OTHER MATTERS",
                "division_acronym": "CRX",
                "answer": "CRX receives $10,000,000 [CRX].",
                "source_chunk_ids": ["CRX-1-test"],
                "chunks_retrieved": 1,
            }
        ],
    }

    response = service._to_response(result, 1.2, "query-test")

    assert response.sources is not None
    assert response.sources[0].chunk_summary == "Chunk summarizes CRX cybersecurity funding."
    assert response.sources[0].chunk_snapshot == "CRX cybersecurity funding"
    assert response.debug_division_queries is None
    assert response.division_results[0].source_chunk_ids == ["CRX-1-test"]


def test_response_excludes_sources_when_requested():
    service = RAGService.__new__(RAGService)
    result = {
        "final_answer": "CRX receives $10,000,000 [CRX].",
        "selected_divisions": ["CONTINUING APPROPRIATIONS, EXTENDERS, HOMELAND SECURITY, AND OTHER MATTERS"],
        "include_sources": False,
        "retrieved_chunks": [
            {
                "chunk_id": "CRX-1-test",
                "division": "CONTINUING APPROPRIATIONS, EXTENDERS, HOMELAND SECURITY, AND OTHER MATTERS",
                "division_acronym": "CRX",
                "content": "For cybersecurity, $10,000,000 shall be available.",
                "chunk_summary": None,
                "score": 0.1,
                "metadata": {},
            }
        ],
        "mapped_chunks": [],
        "division_answers": [],
    }

    response = service._to_response(result, 1.2, "query-test")

    assert response.sources is None


def test_response_includes_debug_division_queries_when_debug_enabled():
    class Settings:
        debug = True

    service = RAGService.__new__(RAGService)
    service.settings = Settings()
    result = {
        "final_answer": "CRX receives $10,000,000 [CRX].",
        "selected_divisions": ["CONTINUING APPROPRIATIONS, EXTENDERS, HOMELAND SECURITY, AND OTHER MATTERS"],
        "include_sources": False,
        "division_queries": [
            {
                "division": "CONTINUING APPROPRIATIONS, EXTENDERS, HOMELAND SECURITY, AND OTHER MATTERS",
                "division_acronym": "CRX",
                "query": "FEMA funding",
            }
        ],
        "retrieved_chunks": [],
        "mapped_chunks": [],
        "division_answers": [],
    }

    response = service._to_response(result, 1.2, "query-test")

    assert response.debug_division_queries is not None
    assert response.debug_division_queries[0].query == "FEMA funding"


def test_response_includes_source_number_annotations_when_markers_are_used():
    service = RAGService.__new__(RAGService)
    result = {
        "final_answer": "CRX receives $10,000,000 [[num:src_crx_dhs_1_test_1]] [CRX].",
        "selected_divisions": ["CONTINUING APPROPRIATIONS, EXTENDERS, HOMELAND SECURITY, AND OTHER MATTERS"],
        "include_sources": True,
        "retrieved_chunks": [
            {
                "chunk_id": "CRX-1-test",
                "division": "CONTINUING APPROPRIATIONS, EXTENDERS, HOMELAND SECURITY, AND OTHER MATTERS",
                "division_acronym": "CRX",
                "content": "For cybersecurity, $10,000,000 shall be available.",
                "chunk_summary": None,
                "score": 0.1,
                "metadata": {"source_file": "bill.html"},
            }
        ],
        "mapped_chunks": [
            {
                "chunk_id": "CRX-1-test",
                "division": "CONTINUING APPROPRIATIONS, EXTENDERS, HOMELAND SECURITY, AND OTHER MATTERS",
                "division_acronym": "CRX",
                "extracted_facts": "Extracted $10,000,000 [[num:src_crx_dhs_1_test_1]] for cybersecurity [CRX].",
                "chunk_summary": "Chunk summarizes CRX cybersecurity funding.",
                "chunk_snapshot": "CRX cybersecurity funding",
                "source_content": "For cybersecurity, $10,000,000 shall be available.",
                "score": 0.1,
                "metadata": {"source_file": "bill.html"},
                "number_annotations": [
                    {
                        "id": "src_crx_dhs_1_test_1",
                        "kind": "source",
                        "figure": "$10,000,000",
                        "value": 10_000_000,
                        "label": "CRX cybersecurity funding",
                        "targets": [],
                        "source": {"chunk_id": "CRX-1-test"},
                    }
                ],
            }
        ],
        "division_answers": [
            {
                "division": "CONTINUING APPROPRIATIONS, EXTENDERS, HOMELAND SECURITY, AND OTHER MATTERS",
                "division_acronym": "CRX",
                "answer": "CRX receives $10,000,000 [[num:src_crx_dhs_1_test_1]] [CRX].",
                "source_chunk_ids": ["CRX-1-test"],
                "chunks_retrieved": 1,
                "number_annotations": [],
            }
        ],
        "number_annotations": [
            {
                "id": "src_crx_dhs_1_test_1",
                "kind": "source",
                "figure": "$10,000,000",
                "value": 10_000_000,
                "label": "CRX cybersecurity funding",
                "targets": [],
                "source": {"chunk_id": "CRX-1-test"},
            }
        ],
    }

    response = service._to_response(result, 1.2, "query-test")

    assert response.number_annotations[0].id == "src_crx_dhs_1_test_1"
    assert {target.scope for target in response.number_annotations[0].targets} == {"answer", "division"}


def test_derived_number_validation_requires_source_backing_and_matching_total():
    from app.models.query import NumberAnnotation, NumberAnnotationTarget
    from app.services.rag_service import ProposedDerivedAnnotation

    service = RAGService.__new__(RAGService)
    source_a = NumberAnnotation(
        id="src_a",
        kind="source",
        figure="$10",
        value=10,
        label="A",
        source={"chunk_id": "a"},
    )
    source_b = NumberAnnotation(
        id="src_b",
        kind="source",
        figure="$5",
        value=5,
        label="B",
        source={"chunk_id": "b"},
    )

    accepted = service._validate_derived_annotations(
        proposed=[
            ProposedDerivedAnnotation(
                id="drv_total",
                figure="$15",
                value=15,
                label="Total",
                equation="$10 + $5 = $15",
                rationale="Both inputs are source-backed.",
                input_ids=["src_a", "src_b"],
            )
        ],
        target_answer="Total is $15 [[num:drv_total]].",
        available=[source_a, source_b],
        target=NumberAnnotationTarget(scope="answer"),
    )

    rejected = service._validate_derived_annotations(
        proposed=[
            ProposedDerivedAnnotation(
                id="drv_bad",
                figure="$20",
                value=20,
                label="Bad total",
                equation="$10 + $5 = $20",
                input_ids=["src_a", "src_b"],
            )
        ],
        target_answer="Total is $20 [[num:drv_bad]].",
        available=[source_a, source_b],
        target=NumberAnnotationTarget(scope="answer"),
    )

    assert accepted[0].derived.source_input_ids == ["src_a", "src_b"]
    assert [item.id for item in rejected] == []


def test_derived_number_validation_accepts_bare_comma_formatted_figure():
    from app.models.query import NumberAnnotation, NumberAnnotationTarget
    from app.services.rag_service import ProposedDerivedAnnotation

    service = RAGService.__new__(RAGService)
    source_a = NumberAnnotation(
        id="src_fema",
        kind="source",
        figure="$20,261,000,000",
        value=20_261_000_000,
        label="FEMA Disaster Relief Fund",
        source={"chunk_id": "dhs"},
    )
    source_b = NumberAnnotation(
        id="src_river",
        kind="source",
        figure="$368,037,000",
        value=368_037_000,
        label="Mississippi River and Tributaries",
        source={"chunk_id": "ewd"},
    )

    accepted = service._validate_derived_annotations(
        proposed=[
            ProposedDerivedAnnotation(
                id="drv_combined",
                figure="20,629,037,000",
                value=20_629_037_000,
                label="Combined FEMA and river total",
                equation="$20,261,000,000 + $368,037,000 = $20,629,037,000",
                input_ids=["src_fema", "src_river"],
            )
        ],
        target_answer="The combined total is $20,629,037,000 [[num:drv_combined]].",
        available=[source_a, source_b],
        target=NumberAnnotationTarget(scope="answer"),
    )

    assert accepted[0].id == "drv_combined"
    assert accepted[0].value == 20_629_037_000


def test_derived_number_validation_uses_visible_marker_figure_when_structured_figure_is_label():
    from app.models.query import NumberAnnotation, NumberAnnotationTarget
    from app.services.rag_service import ProposedDerivedAnnotation

    service = RAGService.__new__(RAGService)
    source_a = NumberAnnotation(
        id="src_operations",
        kind="source",
        figure="$1,483,990,000",
        value=1_483_990_000,
        label="FEMA operations and support",
        source={"chunk_id": "ops"},
    )
    source_b = NumberAnnotation(
        id="src_pci",
        kind="source",
        figure="$99,528,000",
        value=99_528_000,
        label="FEMA procurement, construction, and improvements",
        source={"chunk_id": "pci"},
    )
    source_c = NumberAnnotation(
        id="src_assistance",
        kind="source",
        figure="$3,497,019,369",
        value=3_497_019_369,
        label="FEMA federal assistance",
        source={"chunk_id": "assistance"},
    )

    accepted = service._validate_derived_annotations(
        proposed=[
            ProposedDerivedAnnotation(
                id="drv_dhs_1",
                figure="FEMA total",
                value=5_080_537_369,
                label="FEMA total",
                equation="$1,483,990,000 + $99,528,000 + $3,497,019,369 = $5,080,537,369",
                input_ids=["src_operations", "src_pci", "src_assistance"],
            )
        ],
        target_answer="**FEMA total:** **$5,080,537,369** [[num:drv_dhs_1]]",
        available=[source_a, source_b, source_c],
        target=NumberAnnotationTarget(scope="division", division="CRX"),
    )

    assert accepted[0].id == "drv_dhs_1"
    assert accepted[0].figure == "$5,080,537,369"
    assert accepted[0].value == 5_080_537_369


def test_derived_number_validation_logs_unparseable_figures():
    from app.models.query import NumberAnnotation, NumberAnnotationTarget
    from app.services.rag_service import ProposedDerivedAnnotation

    service = RAGService.__new__(RAGService)
    logs = []
    service._debug_log = lambda message, *args: logs.append(message % args)
    source = NumberAnnotation(
        id="src_a",
        kind="source",
        figure="$10",
        value=10,
        label="A",
        source={"chunk_id": "a"},
    )

    rejected = service._validate_derived_annotations(
        proposed=[
            ProposedDerivedAnnotation(
                id="drv_bad",
                figure="combined total",
                value=10,
                label="Bad total",
                equation="$10 = $10",
                input_ids=["src_a"],
            )
        ],
        target_answer="The combined total is not numeric [[num:drv_bad]].",
        available=[source],
        target=NumberAnnotationTarget(scope="answer"),
    )

    assert rejected == []
    assert "missing_or_unparseable_displayed_marker_figure" in logs[0]
    assert "combined total" in logs[0]


def test_dollar_parser_handles_scaled_figures():
    service = RAGService.__new__(RAGService)

    assert service.parse_dollar_figure("$10") == 10
    assert service.parse_dollar_figure("$1,234,000") == 1_234_000
    assert service.parse_dollar_figure("$10.2 million") == 10_200_000
    assert service.parse_dollar_figure("$3 billion") == 3_000_000_000
    assert service.parse_dollar_figure("20,629,037,000") == 20_629_037_000
    assert service.parse_dollar_figure("10.2 million") == 10_200_000
    assert service.parse_dollar_figure("2024") is None


def test_source_number_annotations_allow_repeated_equal_amounts_with_different_labels():
    from app.services.rag_service import SourceNumberCandidate

    service = RAGService.__new__(RAGService)
    chunk = {
        "chunk_id": "chunk-a",
        "division": "AAA",
        "division_acronym": "AAA",
        "content": "Program A receives $5,000,000. Program B receives $5,000,000.",
        "chunk_summary": None,
        "score": 0.1,
        "metadata": {},
    }

    annotations = service._source_number_annotations(
        chunk,
        "Program A receives $5,000,000.\nProgram B receives $5,000,000.",
        [
            SourceNumberCandidate(figure="$5,000,000", value=5_000_000, label="Program A"),
            SourceNumberCandidate(figure="$5,000,000", value=5_000_000, label="Program B"),
        ],
    )

    assert [annotation.label for annotation in annotations] == ["Program A", "Program B"]


def test_source_marker_insertion_repeats_single_annotation_for_reused_number():
    from app.models.query import NumberAnnotation

    service = RAGService.__new__(RAGService)
    annotation = NumberAnnotation(
        id="src_a",
        kind="source",
        figure="$103,189,080",
        value=103_189_080,
        label="Emergency operations center grants",
        source={"chunk_id": "chunk-a"},
    )

    marked = service._mark_text_with_source_annotations(
        "Emergency operations center grants receive $103,189,080, and the repeated amount is $103,189,080.",
        [annotation],
    )

    assert marked.count("[[num:src_a]]") == 2
    assert service._unmarked_figures(marked) == []


def test_source_marker_insertion_uses_distinct_annotations_before_reuse():
    from app.models.query import NumberAnnotation

    service = RAGService.__new__(RAGService)
    annotations = [
        NumberAnnotation(
            id="src_program_a",
            kind="source",
            figure="$5,000,000",
            value=5_000_000,
            label="Program A",
            source={"chunk_id": "chunk-a"},
        ),
        NumberAnnotation(
            id="src_program_b",
            kind="source",
            figure="$5,000,000",
            value=5_000_000,
            label="Program B",
            source={"chunk_id": "chunk-a"},
        ),
    ]

    marked = service._mark_text_with_source_annotations(
        "Program A receives $5,000,000. Program B receives $5,000,000. Total repeats $5,000,000.",
        annotations,
    )

    assert "[[num:src_program_a]]" in marked
    assert marked.count("[[num:src_program_b]]") == 2


def test_unmarked_figures_allows_markdown_closer_before_marker():
    service = RAGService.__new__(RAGService)

    assert service._unmarked_figures("**$20,629,037,000** [[num:drv_final_1]]") == []


def test_graph_preserves_one_mapped_chunk_per_retrieved_chunk(monkeypatch):
    from app.services.rag_service import AnswerModeDecision, DivisionQueryDecision, DivisionQueryPlan, RouteDecision

    def fake_create_chat_model(model, task, reasoning_effort=None):
        if task == "classify":
            return FakeRewriteLLM(
                AnswerModeDecision(
                    answer_mode="broad_topic_total",
                    answer_mode_flags={"mixed_financial_types": False},
                )
            )
        if task == "routing":
            return FakeRewriteLLM(RouteDecision(divisions=["AAA", "BBB"]))
        if task == "division_query_rewrite":
            return FakeRewriteLLM(
                DivisionQueryPlan(
                    division_queries=[
                        DivisionQueryDecision(division="AAA", query="AAA-specific funding"),
                        DivisionQueryDecision(division="BBB", query="BBB-specific funding"),
                    ]
                )
            )
        return FakeLLM()

    _patch_create_chat_model(monkeypatch, fake_create_chat_model)

    class FakeVectorStore:
        def __init__(self):
            self.calls = []

        def retrieve(self, question, division, k, vectorstore_root, embedding_model):
            self.calls.append((question, division, k, vectorstore_root, embedding_model))
            return [
                {
                    "chunk_id": f"{division}-{index}",
                    "division": division,
                    "division_acronym": division,
                    "content": f"content for {division}",
                    "chunk_summary": None,
                    "score": 0.1,
                    "metadata": {},
                }
                for index in range(k)
            ]

    service = RAGService.__new__(RAGService)
    vectorstores = FakeVectorStore()
    service.vectorstores = vectorstores
    service._graph = service._build_graph()

    result = service._graph.invoke(
        {
            "question": "How much funding?",
            "thinking_speed": "normal",
            "max_results": 1,
            "include_sources": True,
            "divisions_filter": ["AAA", "BBB"],
            "model_used": "gpt-4o",
            "vector_store_id": "store",
            "vector_store_root": "/tmp/store",
            "vector_store_embedding_model": "text-embedding-3-large",
            "answer_mode": "broad_topic_total",
            "answer_mode_flags": {"mixed_financial_types": False},
            "answer_mode_reason": "",
            "selected_divisions": [],
            "retrieved_chunks": [],
            "mapped_chunks": [],
            "division_answers": [],
            "final_answer": "",
        },
        config={"recursion_limit": 50},
    )

    assert len(result["retrieved_chunks"]) == 2
    assert len(result["mapped_chunks"]) == 2
    assert len(result["division_answers"]) == 2
    assert {chunk["division"] for chunk in result["mapped_chunks"]} == {"AAA", "BBB"}
    assert sorted(vectorstores.calls) == [
        ("AAA-specific funding", "AAA", 1, "/tmp/store", "text-embedding-3-large"),
        ("BBB-specific funding", "BBB", 1, "/tmp/store", "text-embedding-3-large"),
    ]


def test_rewrite_division_queries_falls_back_for_missing_division(monkeypatch):
    from app.services.rag_service import DivisionQueryDecision, DivisionQueryPlan

    _patch_create_chat_model(
        monkeypatch,
        lambda model, task, reasoning_effort=None: FakeRewriteLLM(
            DivisionQueryPlan(
                division_queries=[
                    DivisionQueryDecision(division="AAA", query="AAA-specific funding"),
                ]
            )
        ),
    )
    service = RAGService.__new__(RAGService)

    result = service._rewrite_division_queries(
        {
            "query_id": "query-test",
            "question": "How much funding for AAA and BBB?",
            "selected_divisions": ["AAA", "BBB"],
        }
    )

    assert result["division_queries"] == [
        {"division": "AAA", "division_acronym": "A", "query": "AAA-specific funding"},
        {"division": "BBB", "division_acronym": "B", "query": "How much funding for AAA and BBB?"},
    ]


def test_reduce_fanout_sends_one_job_per_selected_division():
    service = RAGService.__new__(RAGService)

    sends = service._send_divisions_to_reduce(
        {
            "question": "How much funding?",
            "model_used": "gpt-4o",
            "selected_divisions": ["AAA", "BBB"],
            "retrieved_chunks": [
                {
                    "chunk_id": "AAA-1",
                    "division": "AAA",
                    "division_acronym": "AAA",
                    "content": "A",
                    "chunk_summary": None,
                    "score": 0.1,
                    "metadata": {},
                },
                {
                    "chunk_id": "BBB-1",
                    "division": "BBB",
                    "division_acronym": "BBB",
                    "content": "B",
                    "chunk_summary": None,
                    "score": 0.1,
                    "metadata": {},
                },
            ],
            "mapped_chunks": [
                {
                    "chunk_id": "AAA-1",
                    "division": "AAA",
                    "division_acronym": "AAA",
                    "extracted_facts": "AAA fact",
                    "chunk_summary": "AAA summary",
                    "source_content": "A",
                    "score": 0.1,
                    "metadata": {},
                },
                {
                    "chunk_id": "BBB-1",
                    "division": "BBB",
                    "division_acronym": "BBB",
                    "extracted_facts": "BBB fact",
                    "chunk_summary": "BBB summary",
                    "source_content": "B",
                    "score": 0.1,
                    "metadata": {},
                },
            ],
        }
    )

    assert [send.node for send in sends] == ["reduce_division", "reduce_division"]
    assert [send.arg["division"] for send in sends] == ["AAA", "BBB"]
    assert [len(send.arg["mapped_items"]) for send in sends] == [1, 1]


def test_reduce_prompt_includes_accounting_scope_examples(monkeypatch):
    from app.services.rag_service import MarkedAnswer

    llm = CapturingStructuredLLM(MarkedAnswer(answer="Answer"))
    _patch_create_chat_model(monkeypatch, lambda model, task, reasoning_effort=None: llm)
    service = RAGService.__new__(RAGService)

    service._reduce_division(
        {
            "question": "how much for fema and immigration combined",
            "query_id": "query-test",
            "division": "CONTINUING APPROPRIATIONS, EXTENDERS, HOMELAND SECURITY, AND OTHER MATTERS",
            "division_acronym": "CRX",
            "mapped_items": [
                {
                    "chunk_id": "chunk-1",
                    "division": "CONTINUING APPROPRIATIONS, EXTENDERS, HOMELAND SECURITY, AND OTHER MATTERS",
                    "division_acronym": "CRX",
                    "extracted_facts": (
                        "- FEMA Federal Assistance $3,497,019,369 [[num:src_fema]] [CRX]\n"
                        "- CBP operations and support $18,426,870,000 [[num:src_cbp]] [CRX]\n"
                        "- ICE operations and support $9,501,542,000 [[num:src_ice]] [CRX]\n"
                        "- USCIS operations and support $271,140,000 [[num:src_uscis]] [CRX]"
                    ),
                    "chunk_summary": "summary",
                    "chunk_snapshot": "snapshot",
                    "source_content": "content",
                    "score": 0.1,
                    "metadata": {},
                    "number_annotations": [],
                }
            ],
            "chunks_retrieved": 1,
            "thinking_speed": "normal",
            "answer_mode": "reconciliation_breakdown",
            "answer_mode_flags": {"mixed_financial_types": False},
        }
    )

    prompt = llm.prompts[0]
    assert "Selected answer_mode: reconciliation_breakdown" in prompt
    assert "Active safety flags: none" in prompt
    assert "Reconciliation and breakdown reduce prompt:" in prompt
    assert "Use Direct facts for substantive answer content" in prompt
    assert "Do not use Not responsive facts in the answer" in prompt
    assert "Preserve enough detail to audit the math" in prompt
    assert "Use the markdown structure above when the user asks for a breakdown" in prompt
    assert "Keep Included for amounts that directly answer the requested breakdown" in prompt
    assert "Do not use internal pipeline language in the answer" in prompt
    assert "When explaining uncertainty, do not say the extracted facts do not resolve it" in prompt
    assert "separate programmatic/activity allocations from financing-source or fee-source amounts" in prompt
    assert "For combined-topic questions, provide one total found per topic" in prompt
    assert "Reconciliation example:" in prompt
    assert "Immigration-related total found" in prompt
    assert "Combined FEMA + immigration-related total found" in prompt
    assert "Do not add the ICE enforcement/detention/removal component separately" in prompt
    assert "Direct account reduce prompt:" not in prompt
    assert "Responsiveness rules:" not in prompt
    assert "Reduce compactness rules:" not in prompt
    assert "classify facts internally as DIRECT, SUPPORTING, or IRRELEVANT" not in prompt
    assert "FDA Salaries and Expenses" not in prompt
    assert "Mixed financial types example:" not in prompt


def test_reduce_prompt_uses_direct_account_module_without_unrelated_examples(monkeypatch):
    from app.services.rag_service import MarkedAnswer

    llm = CapturingStructuredLLM(MarkedAnswer(answer="Answer"))
    _patch_create_chat_model(monkeypatch, lambda model, task, reasoning_effort=None: llm)
    service = RAGService.__new__(RAGService)

    service._reduce_division(
        {
            "question": "What amount is appropriated for FDA Salaries and Expenses?",
            "query_id": "query-test",
            "division": "AGRICULTURE, RURAL DEVELOPMENT, FOOD AND DRUG ADMINISTRATION, AND RELATED AGENCIES",
            "division_acronym": "AG",
            "mapped_items": [
                {
                    "chunk_id": "chunk-1",
                    "division": "AGRICULTURE, RURAL DEVELOPMENT, FOOD AND DRUG ADMINISTRATION, AND RELATED AGENCIES",
                    "division_acronym": "AG",
                    "extracted_facts": "- FDA Salaries and Expenses receives $6,957,972,000 [[num:src_fda]] [AG]",
                    "chunk_summary": "summary",
                    "chunk_snapshot": "snapshot",
                    "source_content": "content",
                    "score": 0.1,
                    "metadata": {},
                    "number_annotations": [],
                }
            ],
            "chunks_retrieved": 1,
            "thinking_speed": "normal",
            "answer_mode": "direct_account_amount",
            "answer_mode_flags": {"mixed_financial_types": False},
        }
    )

    prompt = llm.prompts[0]
    assert "Selected answer_mode: direct_account_amount" in prompt
    assert "Direct account reduce prompt:" in prompt
    assert "Direct account example:" in prompt
    assert "Default shape: main amount first, then 1 short paragraph" in prompt
    assert "use a short bullet list for readability" in prompt
    assert 'write "Major allowed uses include:"' in prompt
    assert "category-only bullets" in prompt
    assert "do not list every center, activity, rent line, transfer, limitation, or user-fee amount" in prompt
    assert "name categories only" in prompt
    assert "do not include center-by-center dollar figures" in prompt
    assert "do not list individual user-fee dollar figures" in prompt
    assert "Bad answer pattern:" in prompt
    assert "Do not create Included / Not added separately sections" in prompt
    assert "FDA Salaries and Expenses" in prompt
    assert "do not include the separate nearby $3,000,000 provision" in prompt
    assert "Reconciliation example:" not in prompt
    assert "Mixed financial types example:" not in prompt
    assert "Preserve all relevant dollar figures from the extracted facts" not in prompt
    assert "Do not omit relevant accounts or programs just to be concise" not in prompt


def test_reduce_prompt_uses_broad_topic_mode_owned_mixed_financial_rules(monkeypatch):
    from app.services.rag_service import MarkedAnswer

    llm = CapturingStructuredLLM(MarkedAnswer(answer="Answer"))
    _patch_create_chat_model(monkeypatch, lambda model, task, reasoning_effort=None: llm)
    service = RAGService.__new__(RAGService)

    service._reduce_division(
        {
            "question": "What FY2026 funding is available for rural water/wastewater infrastructure?",
            "query_id": "query-test",
            "division": "AGRICULTURE, RURAL DEVELOPMENT, FOOD AND DRUG ADMINISTRATION, AND RELATED AGENCIES",
            "division_acronym": "AG",
            "mapped_items": [
                {
                    "chunk_id": "chunk-1",
                    "division": "AGRICULTURE, RURAL DEVELOPMENT, FOOD AND DRUG ADMINISTRATION, AND RELATED AGENCIES",
                    "division_acronym": "AG",
                    "extracted_facts": "- RUS direct loan authority is $X and grant funding is $Z [AG]",
                    "chunk_summary": "summary",
                    "chunk_snapshot": "snapshot",
                    "source_content": "content",
                    "score": 0.1,
                    "metadata": {},
                    "number_annotations": [],
                }
            ],
            "chunks_retrieved": 1,
            "thinking_speed": "normal",
            "answer_mode": "broad_topic_total",
            "answer_mode_flags": {"mixed_financial_types": True},
        }
    )

    prompt = llm.prompts[0]
    assert "Selected answer_mode: broad_topic_total" in prompt
    assert "Active safety flags: mixed_financial_types" in prompt
    assert "Broad topic total reduce prompt:" in prompt
    assert "Output a compact division brief for synthesis, not a full ledger" in prompt
    assert "Key buckets: <2-4 bullets max" in prompt
    assert "Do not create separate bullets for suballocations within the same parent account" in prompt
    assert "Omit tiny sub-set-asides, internal earmarks, administrative amounts" in prompt
    assert "Do not compute or lead with a mixed identified total unless the user explicitly asks" in prompt
    assert "Before aggregating, classify each amount internally by financial type" in prompt
    assert "Do not add account totals plus suballocations" in prompt
    assert "rural water/wastewater infrastructure" in prompt
    assert "one Rural Water and Waste Disposal Program Account bullet" in prompt
    assert "Do not split every section 306 set-aside into separate bullets" in prompt
    assert "Do not present direct loans plus guarantees plus grants as one clean total" in prompt
    assert "Target 8-12 substantive bullets" not in prompt
    assert "Mixed financial-type safety rules:" not in prompt
    assert "Reconciliation and breakdown reduce prompt:" not in prompt


def test_map_prompt_filters_unrelated_dollars_for_funding_mechanisms(monkeypatch):
    llm = CapturingStructuredLLM(
        {
            "extracted_facts": "- No relevant facts found.",
            "source_numbers": [],
        }
    )
    _patch_create_chat_model(monkeypatch, lambda model, task, reasoning_effort=None: llm)
    service = RAGService.__new__(RAGService)

    service._map_chunk(
        {
            "question": "how much money for FEMA?",
            "query_id": "query-test",
            "thinking_speed": "normal",
            "chunk": {
                "chunk_id": "chunk-1",
                "division": "CONTINUING APPROPRIATIONS, EXTENDERS, HOMELAND SECURITY, AND OTHER MATTERS",
                "division_acronym": "CRX",
                "content": (
                    "FEMA Disaster Relief Fund may be apportioned up to the rate for operations. "
                    "Indian Health Service receives $72,265,000."
                ),
                "chunk_summary": None,
                "score": 0.1,
                "metadata": {},
            },
        }
    )

    prompt = llm.prompts[0]
    assert "Relevance must be tied to the agency, account, program, authority, or topic in the question" in prompt
    assert "relevant funding-mechanism evidence but no relevant dollar figure" in prompt
    assert "Do not extract unrelated dollar figures merely because the question asks how much" in prompt
    assert "Preserve financial-type language around each dollar figure" in prompt
    assert "direct loan authority, guaranteed loan authority, loan subsidy cost" in prompt
    assert "Preserve relationship language such as 'of which', 'to remain available', 'derived from fees'" in prompt
    assert "Return fact-level responsiveness tiers: direct, adjacent, or not_responsive" in prompt
    assert "A single chunk may contain a mix of direct, adjacent, and not_responsive facts" in prompt


def test_map_chunk_tracks_fact_level_relevance_and_marks_direct_numbers_only(monkeypatch):
    response = {
        "facts": [
            {
                "fact": "- Direct rural water program receives $10,000,000 [AG]",
                "responsiveness_tier": "direct",
                "reason": "Directly answers rural water funding.",
                "source_numbers": [
                    {
                        "figure": "$10,000,000",
                        "value": 10_000_000,
                        "label": "Direct rural water program",
                    }
                ],
            },
            {
                "fact": "- Adjacent community development account receives $20,000,000 [AG]",
                "responsiveness_tier": "adjacent",
                "reason": "Related infrastructure account but not identified as rural water.",
                "source_numbers": [
                    {
                        "figure": "$20,000,000",
                        "value": 20_000_000,
                        "label": "Adjacent community development",
                    }
                ],
            },
        ],
        "source_numbers": [],
    }
    llm = CapturingStructuredLLM(response)
    _patch_create_chat_model(monkeypatch, lambda model, task, reasoning_effort=None: llm)
    service = RAGService.__new__(RAGService)

    result = service._map_chunk(
        {
            "question": "What rural water funding is available?",
            "query_id": "query-test",
            "thinking_speed": "normal",
            "answer_mode": "broad_topic_total",
            "answer_mode_flags": {"mixed_financial_types": False},
            "chunk": {
                "chunk_id": "chunk-1",
                "division": "AGRICULTURE, RURAL DEVELOPMENT, FOOD AND DRUG ADMINISTRATION, AND RELATED AGENCIES",
                "division_acronym": "AG",
                "content": (
                    "Direct rural water program receives $10,000,000. "
                    "Adjacent community development account receives $20,000,000."
                ),
                "chunk_summary": None,
                "score": 0.1,
                "metadata": {},
            },
        }
    )

    mapped = result["mapped_chunks"][0]
    assert mapped["relevance_counts"] == {"direct": 1, "adjacent": 1, "not_responsive": 0}
    assert "Direct facts:" in mapped["extracted_facts"]
    assert "Adjacent facts:" in mapped["extracted_facts"]
    assert "$10,000,000 [[num:" in mapped["extracted_facts"]
    assert "$20,000,000 [[num:" not in mapped["extracted_facts"]
    assert len(result["number_annotations"]) == 1
    assert result["number_annotations"][0]["figure"] == "$10,000,000"
    assert result["relevance_metadata"][0]["scope"] == "chunk"
    assert result["relevance_metadata"][0]["counts"] == {"direct": 1, "adjacent": 1, "not_responsive": 0}


def test_synthesis_prompt_preserves_scoped_buckets_and_caveats(monkeypatch):
    from app.services.rag_service import MarkedAnswer

    llm = CapturingStructuredLLM(MarkedAnswer(answer="Final answer"))
    _patch_create_chat_model(monkeypatch, lambda model, task, reasoning_effort=None: llm)
    service = RAGService.__new__(RAGService)

    service._synthesize_final(
        {
            "question": "how much for fema and immigration combined",
            "query_id": "query-test",
            "thinking_speed": "normal",
            "answer_mode": "broad_topic_total",
            "answer_mode_flags": {"mixed_financial_types": True},
            "number_annotations": [],
            "division_answers": [
                {
                    "division": "CONTINUING APPROPRIATIONS, EXTENDERS, HOMELAND SECURITY, AND OTHER MATTERS",
                    "division_acronym": "CRX",
                    "answer": (
                        "### [CRX] CONTINUING APPROPRIATIONS, EXTENDERS, HOMELAND SECURITY, AND OTHER MATTERS\n"
                        "- **Bottom line:** Separate buckets are safer than a grand total.\n"
                        "- **Notes:** CBP is kept separate."
                    ),
                    "source_chunk_ids": ["chunk-1"],
                    "chunks_retrieved": 1,
                    "number_annotations": [],
                },
                {
                    "division": "DEPARTMENT OF DEFENSE",
                    "division_acronym": "DOD",
                    "answer": (
                        "### [DOD] DEPARTMENT OF DEFENSE\n"
                        "- **Bottom line:** No comparable immigration bucket identified."
                    ),
                    "source_chunk_ids": ["chunk-2"],
                    "chunks_retrieved": 1,
                    "number_annotations": [],
                },
            ],
        }
    )

    prompt = llm.prompts[0]
    assert "Selected answer_mode: broad_topic_total" in prompt
    assert "Active safety flags: mixed_financial_types" in prompt
    assert "Broad topic synthesis prompt:" in prompt
    assert "Only include sections that have content" in prompt
    assert "## Topic-Specific or Targeted Funding" in prompt
    assert "## Broader Related Funding" in prompt
    assert "## Identified But Not Cleanly Topic-Specific" in prompt
    assert "## Not Included" in prompt
    assert "## By Division" not in prompt
    assert "Do not append full division answers. Combine already-shaped division results." in prompt
    assert "if it has no direct evidence, put it in Not Included as one line" in prompt
    assert "Do not mention \"division answers\", \"extracted facts\", \"retrieved facts\", \"provided facts\"" in prompt
    assert "Use these section titles exactly when applicable" in prompt
    assert "Do not generate long topic-expanded section names" in prompt
    assert "organize by specificity before account detail" in prompt
    assert "Use one heading per controlling account" in prompt
    assert "Preserve direct subamounts that help the user identify funding sources" in prompt
    assert "Use valid markdown bullets for all account details and nested amounts" in prompt
    assert "Label each amount by financial type" in prompt
    assert "Do not repeat the same agency, account, bucket, or dollar figure" in prompt
    assert "Caveats must be cross-cutting only" in prompt
    assert "Do not add account totals plus suballocations" in prompt
    assert "Do not compute or lead with a mixed identified total unless the user explicitly asks" in prompt
    assert "Good pattern:" in prompt
    assert "Bad pattern:" in prompt
    assert "USDA RUS — same account/heading" in prompt
    assert "## By Agency / Account" not in prompt
    assert "Synthesis rules:" not in prompt
    assert "Mixed financial-type safety rules:" not in prompt


def test_synthesis_prompts_are_mode_owned():
    from app.services.rag_prompting import build_synthesis_prompt

    cases = {
        "direct_account_amount": ["Direct account synthesis prompt:", "## Source Scope", "Do not introduce By Agency / Account"],
        "broad_topic_total": ["Broad topic synthesis prompt:", "## Topic-Specific or Targeted Funding", "## Not Included"],
        "funding_mechanism_no_amount": ["Funding mechanism synthesis prompt:", "## Mechanism Found", "## Missing Amount"],
        "reconciliation_breakdown": [
            "Reconciliation synthesis prompt:",
            "## Included",
            "## Not Added Separately",
            "Do not flatten a structured reduce answer into dense paragraphs",
            "programmatic/activity allocations and financing-source or fee-source amounts",
        ],
        "general_summary": ["General summary synthesis prompt:", "Do not force accounting sections"],
    }

    for mode, expected_fragments in cases.items():
        prompt = build_synthesis_prompt(
            question="test question",
            answer_mode=mode,
            answer_mode_flags={"mixed_financial_types": mode == "broad_topic_total"},
            annotation_context="none",
            division_context="division answer",
        )

        assert f"Selected answer_mode: {mode}" in prompt
        assert "Use only the division answers. Do not invent facts, dollar figures, or totals." in prompt
        assert "SYNTHESIS_BASE_RULES" not in prompt
        assert "Synthesis rules:" not in prompt
        for fragment in expected_fragments:
            assert fragment in prompt


def test_division_fanout_preserves_vector_store_context():
    service = RAGService.__new__(RAGService)

    sends = service._fan_out_divisions(
        {
            "question": "How much funding?",
            "query_id": "query",
            "selected_divisions": ["DEPARTMENT OF DEFENSE"],
            "division_queries": [
                {
                    "division": "DEPARTMENT OF DEFENSE",
                    "division_acronym": "DOD",
                    "query": "DOD funding",
                }
            ],
            "max_results": 8,
            "vector_store_id": "store",
            "vector_store_root": "/tmp/store",
            "vector_store_embedding_model": "text-embedding-3-large",
        }
    )

    assert len(sends) == 1
    assert sends[0].arg["vector_store_id"] == "store"
    assert sends[0].arg["vector_store_root"] == "/tmp/store"
    assert sends[0].arg["vector_store_embedding_model"] == "text-embedding-3-large"


def test_vector_store_retrieve_requires_explicit_root():
    service = VectorStoreService.__new__(VectorStoreService)

    try:
        service.retrieve("How much funding?", "DEPARTMENT OF DEFENSE", 1)
    except ValueError as exc:
        assert "Vector store root is required" in str(exc)
    else:
        raise AssertionError("Expected missing vector store root to fail")


def test_model_strategy_resolves_by_speed_and_task():
    config_module._settings = None
    assert resolve_model("quick", "classify").model == "gpt-5.4-mini"
    assert resolve_model("quick", "route").model == "gpt-5.4-mini"
    assert resolve_model("quick", "rewrite").model == "gpt-5.4-mini"
    assert resolve_model("quick", "routing").model == "gpt-5.4-mini"
    assert resolve_model("quick", "map").model == "gpt-5.4-nano"
    assert resolve_model("quick", "synthesize").model == "gpt-5.4-mini"
    assert resolve_model("normal", "classify").reasoning_effort == "medium"
    assert resolve_model("normal", "route").reasoning_effort == "medium"
    assert resolve_model("normal", "rewrite").reasoning_effort == "medium"
    assert resolve_model("normal", "map").reasoning_effort == "medium"
    assert resolve_model("normal", "summary").reasoning_effort == "medium"
    assert resolve_model("normal", "synthesize").reasoning_effort == "medium"
    assert resolve_model("long", "classify").reasoning_effort == "medium"
    assert resolve_model("long", "route").reasoning_effort == "medium"
    assert resolve_model("long", "rewrite").reasoning_effort == "medium"
    assert resolve_model("long", "map").reasoning_effort == "medium"
    assert resolve_model("long", "summary").reasoning_effort == "medium"
    assert resolve_model("long", "reduce").reasoning_effort == "medium"
    assert resolve_model("long", "synthesize").reasoning_effort == "medium"
    assert (
        describe_model_strategy("long")
        == "profile:openai, classify:gpt-5.4-mini(reasoning=medium), route:gpt-5.4-mini(reasoning=medium), "
        "rewrite:gpt-5.4-mini(reasoning=medium), map:gpt-5.4-mini(reasoning=medium), "
        "summary:gpt-5.4-nano(reasoning=medium), reduce:gpt-5.4(reasoning=medium), "
        "synthesize:gpt-5.4(reasoning=medium)"
    )


def test_deepseek_model_strategy_resolves_by_speed_and_task(monkeypatch):
    monkeypatch.setenv("LAWSEARCH_MODEL_PROFILE", "deepseek")
    config_module._settings = None

    assert resolve_model("quick", "classify").model == "deepseek-v4-flash"
    assert resolve_model("quick", "classify").reasoning_effort is None
    assert resolve_model("quick", "route").reasoning_effort is None
    assert resolve_model("quick", "rewrite").reasoning_effort is None
    assert resolve_model("quick", "map").reasoning_effort == "high"
    assert resolve_model("quick", "summary").reasoning_effort is None
    assert resolve_model("quick", "reduce").model == "deepseek-v4-pro"
    assert resolve_model("quick", "reduce").reasoning_effort == "high"
    assert resolve_model("quick", "synthesize").model == "deepseek-v4-pro"
    assert resolve_model("quick", "synthesize").reasoning_effort == "high"

    assert resolve_model("normal", "classify").reasoning_effort == "high"
    assert resolve_model("normal", "route").reasoning_effort == "high"
    assert resolve_model("normal", "rewrite").reasoning_effort == "high"
    assert resolve_model("normal", "map").reasoning_effort == "high"
    assert resolve_model("normal", "summary").reasoning_effort == "high"
    assert resolve_model("normal", "reduce").model == "deepseek-v4-pro"
    assert resolve_model("normal", "reduce").reasoning_effort == "high"
    assert resolve_model("normal", "synthesize").model == "gpt-5.4"
    assert resolve_model("normal", "synthesize").reasoning_effort == "medium"

    assert resolve_model("long", "classify").reasoning_effort == "high"
    assert resolve_model("long", "route").reasoning_effort == "high"
    assert resolve_model("long", "rewrite").reasoning_effort == "high"
    assert resolve_model("long", "map").reasoning_effort == "high"
    assert resolve_model("long", "summary").reasoning_effort == "high"
    assert resolve_model("long", "reduce").model == "deepseek-v4-pro"
    assert resolve_model("long", "reduce").reasoning_effort == "max"
    assert resolve_model("long", "synthesize").model == "deepseek-v4-pro"
    assert resolve_model("long", "synthesize").reasoning_effort == "max"

    assert "profile:deepseek" in describe_model_strategy("quick")
    assert "classify:deepseek-v4-flash(provider=deepseek, thinking=off)" in describe_model_strategy(
        "quick"
    )
    assert "reduce:deepseek-v4-pro(provider=deepseek, thinking=max)" in describe_model_strategy(
        "long"
    )


def test_rewrite_resolves_speed_specific_model(monkeypatch):
    config_module._settings = None
    calls = []

    class RewriteLLM:
        def with_structured_output(self, schema):
            return self

        def invoke(self, messages):
            from app.services.rag.schemas import DivisionQueryPlan

            return DivisionQueryPlan(division_queries=[])

    def fake_create_chat_model(model, task, reasoning_effort=None):
        calls.append((model, task, reasoning_effort))
        return RewriteLLM()

    monkeypatch.setattr("app.services.rag.stages.rewrite.create_chat_model", fake_create_chat_model)
    rewrite_division_queries(
        {
            "question": "How much for FDA?",
            "query_id": "test",
            "selected_divisions": [
                "AGRICULTURE, RURAL DEVELOPMENT, FOOD AND DRUG ADMINISTRATION, AND RELATED AGENCIES"
            ],
            "thinking_speed": "long",
        },
        type(
            "Ctx",
            (),
            {
                "emit_progress": lambda *args, **kwargs: None,
                "debug_log": lambda *args, **kwargs: None,
            },
        )(),
    )

    assert calls == [("gpt-5.4-mini", "division_query_rewrite", "medium")]
