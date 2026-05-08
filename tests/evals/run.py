"""Embedding model eval runner.

Usage:
    python -m tests.evals.run
"""

from __future__ import annotations

import logging
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Any

# Ensure project root is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from langchain_core.messages import HumanMessage, SystemMessage

from app.core.config import FY2026_DIVISION_ACRONYMS, FY2026_SUBCOMMITTEE_STORES, get_settings
from app.services.embedding_factory import create_embeddings
from app.services.llm_factory import ModelSpec, create_chat_model
from app.services.rag.llm_invocation import invoke_structured
from app.services.rag.schemas import DivisionQueryPlan
from app.services.vector_store_service import VectorStoreService, division_acronym
from tests.evals.judge import judge_chunks
from tests.evals.questions import EVAL_QUESTIONS, EvalQuestion
from tests.evals.report import generate_report

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# ── Config ──

EVAL_STORES: dict[str, str] = {
    "voyage-law-2": "609b2b98-104e-4286-b410-a34337ba0ed5",
    "voyage-4-large-2048": "e059672c-d13e-4694-901a-e6c237bacb61",
    "text-embedding-3-large": "4089d764-2024-4d44-83ca-978446ef23f3",
}

EMBEDDING_MODELS = list(EVAL_STORES.keys())
K_PER_DIVISION = 12

REWRITE_MODEL = "deepseek-v4-flash"
REWRITE_REASONING = "high"
REWRITE_SPEC = ModelSpec(REWRITE_MODEL, provider="deepseek", reasoning_effort=REWRITE_REASONING)

REWRITE_SYSTEM_PROMPT = (
    "Create one targeted retrieval query for each selected appropriations division. "
    "Keep the user's intent, but only include entities, programs, agencies, or terms "
    "likely relevant to that division. Do not force unrelated entities into every query. "
    "Return exact division names from the selected list."
)

RESULTS_DIR = Path(__file__).resolve().parent / "results"


def _noop_log(*_args: Any, **_kwargs: Any) -> None:
    pass


# ── Rewrite ──

def rewrite_question(question: EvalQuestion) -> dict[str, str]:
    """Run the rewrite stage once, returning {division: rewritten_query}."""
    llm = create_chat_model(REWRITE_MODEL, "rewrite", REWRITE_REASONING)
    allowed = "\n- ".join(question.divisions)
    messages = [
        SystemMessage(content=REWRITE_SYSTEM_PROMPT),
        HumanMessage(
            content=f"Selected divisions:\n- {allowed}\n\nOriginal question:\n{question.question}"
        ),
    ]
    try:
        plan = invoke_structured(
            llm,
            messages,
            schema=DivisionQueryPlan,
            model_spec=REWRITE_SPEC,
            stage="eval_rewrite",
            query_id=question.id,
            debug_log=_noop_log,
        )
        by_division = {
            item.division: item.query.strip()
            for item in plan.division_queries
            if item.division in question.divisions and item.query.strip()
        }
    except Exception as exc:
        logger.warning("Rewrite failed for %s, using original: %s", question.id, exc)
        by_division = {}

    return {
        div: by_division.get(div, question.question)
        for div in question.divisions
    }


# ── Retrieve ──

def retrieve_chunks(
    query: str,
    division: str,
    embedding_model: str,
) -> list[dict[str, Any]]:
    """Retrieve k chunks from a specific model's vector store."""
    settings = get_settings()
    store_uuid = EVAL_STORES[embedding_model]
    vectorstore_root = str(settings.vectorstore_dir / "vector_stores" / store_uuid)

    svc = VectorStoreService(embedding_model=embedding_model)
    return svc.retrieve(
        question=query,
        division=division,
        k=K_PER_DIVISION,
        vectorstore_root=vectorstore_root,
        embedding_model=embedding_model,
    )


# ── Per-question orchestration ──

def eval_question(question: EvalQuestion) -> list[dict[str, Any]]:
    """Run retrieval + judging for one question across all models.

    Returns a list of judge results (one per model per division).
    """
    logger.info("── %s [%s] ──", question.id, question.answer_mode)

    # Rewrite once
    logger.info("  Rewriting...")
    rewritten = rewrite_question(question)
    for div, query in rewritten.items():
        logger.info("    %s → %s", division_acronym(div), query[:80])

    # Retrieve in parallel across models
    logger.info("  Retrieving (k=%d per division)...", K_PER_DIVISION)
    retrieval_results: dict[str, dict[str, list[dict[str, Any]]]] = {}

    with ThreadPoolExecutor(max_workers=len(EMBEDDING_MODELS)) as pool:
        futures = {}
        for model in EMBEDDING_MODELS:
            for div in question.divisions:
                key = (model, div)
                futures[pool.submit(retrieve_chunks, rewritten[div], div, model)] = key

        for future in as_completed(futures):
            model, div = futures[future]
            try:
                chunks = future.result()
            except Exception as exc:
                logger.error("    Retrieve failed %s/%s: %s", model, division_acronym(div), exc)
                chunks = []
            retrieval_results.setdefault(model, {})[div] = chunks
            logger.info(
                "    %s [%s]: %d chunks",
                model, division_acronym(div), len(chunks),
            )

    # Judge in parallel across models
    logger.info("  Judging...")
    all_judge_results: list[dict[str, Any]] = []

    with ThreadPoolExecutor(max_workers=len(EMBEDDING_MODELS)) as pool:
        futures = {}
        for model in EMBEDDING_MODELS:
            for div in question.divisions:
                chunks = retrieval_results.get(model, {}).get(div, [])
                future = pool.submit(
                    judge_chunks,
                    question.question,
                    question.answer_mode,
                    div,
                    division_acronym(div),
                    model,
                    chunks,
                )
                futures[future] = (model, div)

        for future in as_completed(futures):
            model, div = futures[future]
            try:
                result = future.result()
                all_judge_results.append(result)
                logger.info(
                    "    %s [%s]: coverage=%s direct=%s adj=%s nr=%s",
                    model,
                    division_acronym(div),
                    result.get("coverage_score", "?"),
                    result.get("tier_counts", {}).get("direct", "?"),
                    result.get("tier_counts", {}).get("adjacent", "?"),
                    result.get("tier_counts", {}).get("not_responsive", "?"),
                )
            except Exception as exc:
                logger.error("    Judge failed %s/%s: %s", model, division_acronym(div), exc)

    return all_judge_results


# ── Main ──

def main() -> None:
    start = time.time()
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    output_dir = RESULTS_DIR / timestamp

    logger.info("Embedding eval starting — %d questions, %d models", len(EVAL_QUESTIONS), len(EMBEDDING_MODELS))
    logger.info("Models: %s", ", ".join(EMBEDDING_MODELS))
    logger.info("Output: %s", output_dir)

    all_results: list[dict[str, Any]] = []

    for i, question in enumerate(EVAL_QUESTIONS, 1):
        logger.info("\n[%d/%d] %s", i, len(EVAL_QUESTIONS), question.question[:80])
        try:
            results = eval_question(question)
            all_results.extend(results)
        except Exception as exc:
            logger.error("Question %s failed entirely: %s", question.id, exc)

    elapsed = time.time() - start
    logger.info("\nEval complete — %d judge results in %.1fs", len(all_results), elapsed)

    generate_report(all_results, output_dir)
    logger.info("Report: %s/report.md", output_dir)
    logger.info("Raw:    %s/raw_results.json", output_dir)


if __name__ == "__main__":
    main()
