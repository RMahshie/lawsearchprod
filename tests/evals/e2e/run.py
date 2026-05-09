"""E2E eval runner — runs questions through the full RAG pipeline and judges answers.

Usage:
    # Reference mode (no gold refs needed — dumps pipeline outputs for writing golds):
    python3 -m tests.evals.e2e.run --reference

    # Judge mode (requires gold references):
    python3 -m tests.evals.e2e.run

    # Run 5 at a time:
    python3 -m tests.evals.e2e.run --reference --concurrency 5
"""

from __future__ import annotations

import argparse
import logging
import sys
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from app.core.config import get_settings
from app.services.llm_factory import describe_model_strategy
from app.services.rag.service import RAGService
from app.services.rag.state import RAGState
from app.services.rag_prompting import DEFAULT_ANSWER_MODE
from app.services.vector_store_service import division_acronym
from tests.evals.e2e.gold_references import GOLD_REFERENCES, GoldReference
from tests.evals.e2e.judge import judge_answer
from tests.evals.e2e.report import generate_report
from tests.evals.questions import EVAL_QUESTIONS, EvalQuestion

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

DEFAULT_VECTOR_STORE_ID = "609b2b98-104e-4286-b410-a34337ba0ed5"
DEFAULT_EMBEDDING_MODEL = "voyage-law-2"
DEFAULT_THINKING_SPEED = "normal"
DEFAULT_K = 12
DEFAULT_CONCURRENCY = 3

RESULTS_DIR = Path(__file__).resolve().parent / "results"


def _build_initial_state(
    question: EvalQuestion,
    *,
    vector_store_id: str,
    embedding_model: str,
    thinking_speed: str,
    k: int,
    vectorstore_root: str,
) -> RAGState:
    query_id = f"eval_{question.id}_{uuid.uuid4().hex[:8]}"
    return {
        "query_id": query_id,
        "question": question.question,
        "thinking_speed": thinking_speed,
        "max_results": k,
        "include_sources": True,
        "divisions_filter": None,
        "model_used": describe_model_strategy(thinking_speed),
        "vector_store_id": vector_store_id,
        "vector_store_root": vectorstore_root,
        "vector_store_embedding_model": embedding_model,
        "answer_mode": DEFAULT_ANSWER_MODE,
        "answer_mode_flags": {"mixed_financial_types": False},
        "answer_mode_reason": "",
        "selected_divisions": [],
        "division_queries": [],
        "retrieved_chunks": [],
        "mapped_chunks": [],
        "division_answers": [],
        "number_annotations": [],
        "relevance_metadata": [],
        "final_answer": "",
    }


def _extract_intermediates(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "answer_mode": result.get("answer_mode", ""),
        "answer_mode_reason": result.get("answer_mode_reason", ""),
        "answer_mode_flags": result.get("answer_mode_flags", {}),
        "selected_divisions": result.get("selected_divisions", []),
        "division_queries": result.get("division_queries", []),
        "retrieved_chunk_count": len(result.get("retrieved_chunks", [])),
        "mapped_chunk_count": len(result.get("mapped_chunks", [])),
        "division_answers": [
            {
                "division": da.get("division", ""),
                "division_acronym": da.get("division_acronym", ""),
                "answer": da.get("answer", ""),
                "chunks_retrieved": da.get("chunks_retrieved", 0),
            }
            for da in result.get("division_answers", [])
        ],
        "final_answer": result.get("final_answer", ""),
    }


def run_pipeline(
    service: RAGService,
    question: EvalQuestion,
    *,
    vector_store_id: str,
    embedding_model: str,
    thinking_speed: str,
    k: int,
    vectorstore_root: str,
) -> dict[str, Any]:
    """Run one question through the full RAG pipeline."""
    state = _build_initial_state(
        question,
        vector_store_id=vector_store_id,
        embedding_model=embedding_model,
        thinking_speed=thinking_speed,
        k=k,
        vectorstore_root=vectorstore_root,
    )
    result = service._graph.invoke(state, config={"recursion_limit": 50})
    return _extract_intermediates(result)


def _generate_reference_output(
    all_outputs: list[dict[str, Any]],
    output_dir: Path,
) -> None:
    """Write pipeline_outputs.md for gold reference authoring."""
    output_dir.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    lines.append("# Pipeline Outputs — Reference for Writing Gold Standards\n")
    lines.append(f"Generated: {datetime.now().isoformat()}\n")

    for out in all_outputs:
        qid = out["question_id"]
        q = out["question"]
        lines.append(f"---\n\n## {qid}\n")
        lines.append(f"**Question**: {q}\n")
        lines.append(f"**Answer Mode** (classify output): `{out['actual_answer_mode']}`")
        lines.append(f"**Answer Mode Reason**: {out.get('answer_mode_reason', '')}")

        divs = out.get("actual_divisions", [])
        div_strs = [f"{division_acronym(d)} ({d})" for d in divs]
        lines.append(f"**Selected Divisions** (route output): {', '.join(div_strs)}\n")

        lines.append("### Division Answers\n")
        for da in out.get("division_answers", []):
            acr = da.get("division_acronym", "?")
            lines.append(f"#### [{acr}] {da.get('division', '?')}\n")
            lines.append(da.get("answer", "(no answer)"))
            lines.append("")

        lines.append("### Final Answer\n")
        lines.append(out.get("final_answer", "(no answer)"))
        lines.append("\n")

    text = "\n".join(lines)
    path = output_dir / "pipeline_outputs.md"
    path.write_text(text, encoding="utf-8")
    logger.info("Reference output: %s", path)


def main() -> None:
    parser = argparse.ArgumentParser(description="E2E eval runner for LawSearch RAG pipeline")
    parser.add_argument("--reference", action="store_true",
                        help="Reference mode: dump pipeline outputs for writing gold standards")
    parser.add_argument("--vector-store-id", default=DEFAULT_VECTOR_STORE_ID)
    parser.add_argument("--embedding-model", default=DEFAULT_EMBEDDING_MODEL)
    parser.add_argument("--thinking-speed", default=DEFAULT_THINKING_SPEED)
    parser.add_argument("--k", type=int, default=DEFAULT_K)
    parser.add_argument("--concurrency", type=int, default=DEFAULT_CONCURRENCY,
                        help="Number of questions to run in parallel (default: 3)")
    parser.add_argument("--questions", nargs="*",
                        help="Run only these question IDs (default: all 25)")
    args = parser.parse_args()

    start = time.time()
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    output_dir = RESULTS_DIR / timestamp

    settings = get_settings()
    vectorstore_root = str(
        settings.vectorstore_dir / "vector_stores" / args.vector_store_id
    )

    questions = EVAL_QUESTIONS
    if args.questions:
        question_ids = set(args.questions)
        questions = [q for q in EVAL_QUESTIONS if q.id in question_ids]
        if not questions:
            logger.error("No matching question IDs found. Available: %s",
                         [q.id for q in EVAL_QUESTIONS])
            return

    logger.info(
        "E2E eval starting — %d questions, mode=%s, store=%s, speed=%s, k=%d, concurrency=%d",
        len(questions), "reference" if args.reference else "judge",
        args.embedding_model, args.thinking_speed, args.k, args.concurrency,
    )

    logger.info("Initializing RAGService...")
    service = RAGService()

    def _process_question(question: EvalQuestion) -> dict[str, Any]:
        logger.info("[%s] Starting [%s]", question.id, question.answer_mode)

        try:
            pipeline_out = run_pipeline(
                service,
                question,
                vector_store_id=args.vector_store_id,
                embedding_model=args.embedding_model,
                thinking_speed=args.thinking_speed,
                k=args.k,
                vectorstore_root=vectorstore_root,
            )
        except Exception as exc:
            logger.error("[%s] Pipeline failed: %s", question.id, exc, exc_info=True)
            pipeline_out = {
                "answer_mode": "",
                "selected_divisions": [],
                "division_answers": [],
                "final_answer": f"PIPELINE ERROR: {exc}",
            }

        actual_mode = pipeline_out.get("answer_mode", "")
        actual_divs = pipeline_out.get("selected_divisions", [])
        gold = GOLD_REFERENCES.get(question.id, GoldReference())

        entry: dict[str, Any] = {
            "question_id": question.id,
            "question": question.question,
            "answer_mode": question.answer_mode,
            "expected_answer_mode": gold.expected_answer_mode or question.answer_mode,
            "actual_answer_mode": actual_mode,
            "classify_match": actual_mode == (gold.expected_answer_mode or question.answer_mode),
            "expected_divisions": gold.expected_divisions or question.divisions,
            "actual_divisions": actual_divs,
            "route_match": set(actual_divs) == set(gold.expected_divisions or question.divisions),
            "answer_mode_reason": pipeline_out.get("answer_mode_reason", ""),
            "division_answers": pipeline_out.get("division_answers", []),
            "final_answer": pipeline_out.get("final_answer", ""),
            "retrieved_chunk_count": pipeline_out.get("retrieved_chunk_count", 0),
            "mapped_chunk_count": pipeline_out.get("mapped_chunk_count", 0),
        }

        logger.info("[%s] Classify: %s (%s) | Route: %s (%s) | Chunks: %d/%d",
                     question.id, actual_mode,
                     "OK" if entry["classify_match"] else "MISS",
                     [division_acronym(d) for d in actual_divs],
                     "OK" if entry["route_match"] else "MISS",
                     entry["retrieved_chunk_count"], entry["mapped_chunk_count"])

        if not args.reference:
            gold_dict = {
                "required_facts": gold.required_facts,
                "prohibited_errors": gold.prohibited_errors,
                "notes": gold.notes,
            }
            if gold.required_facts or gold.prohibited_errors:
                logger.info("[%s] Judging...", question.id)
                try:
                    judge_result = judge_answer(
                        question.id,
                        question.question,
                        actual_mode,
                        entry["final_answer"],
                        gold_dict,
                    )
                    entry["judge"] = judge_result
                    logger.info("[%s] Score: %s/10", question.id,
                                judge_result.get("overall_score", "?"))
                except Exception as exc:
                    logger.error("[%s] Judge failed: %s", question.id, exc)
                    entry["judge"] = {
                        "overall_score": -1,
                        "reasoning": f"Judge error: {exc}",
                        "fact_checks": [],
                        "error_checks": [],
                        "structural_checks": {"passed": False, "issues": [str(exc)]},
                    }
            else:
                entry["judge"] = {
                    "overall_score": -1,
                    "reasoning": "No gold reference available.",
                    "fact_checks": [],
                    "error_checks": [],
                    "structural_checks": {"passed": True, "issues": ["No gold reference"]},
                }

        return entry

    results_by_id: dict[str, dict[str, Any]] = {}
    completed = 0

    with ThreadPoolExecutor(max_workers=args.concurrency) as pool:
        futures = {
            pool.submit(_process_question, q): q.id
            for q in questions
        }
        for future in as_completed(futures):
            qid = futures[future]
            completed += 1
            try:
                results_by_id[qid] = future.result()
                logger.info("(%d/%d) %s done", completed, len(questions), qid)
            except Exception as exc:
                logger.error("(%d/%d) %s unhandled error: %s", completed, len(questions), qid, exc)

    all_outputs = [results_by_id[q.id] for q in questions if q.id in results_by_id]

    elapsed = time.time() - start
    logger.info("\nEval complete — %d questions in %.1fs", len(all_outputs), elapsed)

    if args.reference:
        _generate_reference_output(all_outputs, output_dir)
    else:
        generate_report(all_outputs, output_dir)
        logger.info("Report: %s/report.md", output_dir)
        logger.info("Raw:    %s/raw_results.json", output_dir)


if __name__ == "__main__":
    main()
