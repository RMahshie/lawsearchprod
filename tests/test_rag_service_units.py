from app.services.llm_factory import describe_model_strategy, resolve_model
from app.services.rag_service import RAGService
from app.services.vector_store_service import division_acronym, stable_chunk_id


class FakeMessage:
    def __init__(self, content: str):
        self.content = content


class FakeLLM:
    def invoke(self, prompt):
        if "UI hover summary" in str(prompt):
            return FakeMessage("Chunk summarizes DHS cybersecurity funding.")
        return FakeMessage("Extracted $10,000,000 for cybersecurity [DHS].")


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


def test_division_acronym_and_chunk_id_are_stable():
    content = "For cybersecurity, $10,000,000 shall be available."

    assert division_acronym("DEPARTMENT OF HOMELAND SECURITY") == "DHS"
    assert stable_chunk_id("DEPARTMENT OF HOMELAND SECURITY", 0, content) == stable_chunk_id(
        "DEPARTMENT OF HOMELAND SECURITY",
        0,
        content,
    )


def test_map_chunk_returns_facts_and_summary(monkeypatch):
    monkeypatch.setattr("app.services.rag_service.create_chat_model", lambda model, task, reasoning_effort=None: FakeLLM())
    service = RAGService.__new__(RAGService)

    result = service._map_chunk(
        {
            "question": "How much cybersecurity funding is provided?",
            "model_used": "gpt-4o",
            "chunk": {
                "chunk_id": "DHS-1-test",
                "division": "DEPARTMENT OF HOMELAND SECURITY",
                "division_acronym": "DHS",
                "content": "For cybersecurity, $10,000,000 shall be available.",
                "chunk_summary": None,
                "score": 0.1,
                "metadata": {"source_file": "bill.html"},
            },
        }
    )

    mapped = result["mapped_chunks"][0]
    assert mapped["division"] == "DEPARTMENT OF HOMELAND SECURITY"
    assert mapped["chunk_summary"] == "Chunk summarizes DHS cybersecurity funding."
    assert "$10,000,000" in mapped["extracted_facts"]


def test_response_includes_sources_debug_chunks_and_division_results():
    service = RAGService.__new__(RAGService)
    result = {
        "final_answer": "DHS receives $10,000,000 [DHS].",
        "selected_divisions": ["DEPARTMENT OF HOMELAND SECURITY"],
        "include_sources": True,
        "debug_chunks": True,
        "thinking_speed": "normal",
        "model_used": "gpt-4o",
        "division_queries": [
            {
                "division": "DEPARTMENT OF HOMELAND SECURITY",
                "division_acronym": "DHS",
                "query": "How much funding is provided for DHS cybersecurity?",
            }
        ],
        "retrieved_chunks": [
            {
                "chunk_id": "DHS-1-test",
                "division": "DEPARTMENT OF HOMELAND SECURITY",
                "division_acronym": "DHS",
                "content": "For cybersecurity, $10,000,000 shall be available.",
                "chunk_summary": None,
                "score": 0.1,
                "metadata": {"source_file": "bill.html"},
            }
        ],
        "mapped_chunks": [
            {
                "chunk_id": "DHS-1-test",
                "division": "DEPARTMENT OF HOMELAND SECURITY",
                "division_acronym": "DHS",
                "extracted_facts": "Extracted $10,000,000 for cybersecurity [DHS].",
                "chunk_summary": "Chunk summarizes DHS cybersecurity funding.",
                "source_content": "For cybersecurity, $10,000,000 shall be available.",
                "score": 0.1,
                "metadata": {"source_file": "bill.html"},
            }
        ],
        "division_answers": [
            {
                "division": "DEPARTMENT OF HOMELAND SECURITY",
                "division_acronym": "DHS",
                "answer": "DHS receives $10,000,000 [DHS].",
                "source_chunk_ids": ["DHS-1-test"],
                "chunks_retrieved": 1,
            }
        ],
    }

    response = service._to_response(result, 1.2, "query-test")

    assert response.sources is not None
    assert response.sources[0].chunk_summary == "Chunk summarizes DHS cybersecurity funding."
    assert response.debug_chunks is not None
    assert response.debug_chunks[0].division_acronym == "DHS"
    assert response.debug_division_queries is not None
    assert response.debug_division_queries[0].query == "How much funding is provided for DHS cybersecurity?"
    assert response.division_results[0].source_chunk_ids == ["DHS-1-test"]


def test_graph_preserves_one_mapped_chunk_per_retrieved_chunk(monkeypatch):
    from app.services.rag_service import DivisionQueryDecision, DivisionQueryPlan

    def fake_create_chat_model(model, task, reasoning_effort=None):
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

    monkeypatch.setattr("app.services.rag_service.create_chat_model", fake_create_chat_model)

    class FakeVectorStore:
        def __init__(self):
            self.calls = []

        def retrieve(self, question, division, k):
            self.calls.append((question, division, k))
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
            "debug_chunks": False,
            "divisions_filter": ["AAA", "BBB"],
            "model_used": "gpt-4o",
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
    assert vectorstores.calls == [
        ("AAA-specific funding", "AAA", 1),
        ("BBB-specific funding", "BBB", 1),
    ]


def test_rewrite_division_queries_falls_back_for_missing_division(monkeypatch):
    from app.services.rag_service import DivisionQueryDecision, DivisionQueryPlan

    monkeypatch.setattr(
        "app.services.rag_service.create_chat_model",
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


def test_model_strategy_resolves_by_speed_and_task():
    assert resolve_model("quick", "routing").model == "gpt-5.4-nano"
    assert resolve_model("quick", "map").model == "gpt-5.4-nano"
    assert resolve_model("quick", "synthesize").model == "gpt-5.4-mini"
    assert resolve_model("normal", "synthesize").reasoning_effort == "low"
    assert resolve_model("long", "reduce").reasoning_effort == "medium"
    assert resolve_model("long", "synthesize").reasoning_effort == "medium"
    assert (
        describe_model_strategy("long")
        == "map:gpt-5.4-mini, reduce:gpt-5.4(reasoning=medium), synthesize:gpt-5.4(reasoning=medium)"
    )
