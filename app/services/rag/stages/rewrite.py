"""Rewrite stage: turn the user's question into per-Division retrieval queries."""

from __future__ import annotations

import logging
import time
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from app.services.llm_factory import create_chat_model, format_model_spec, resolve_model
from app.services.rag.context import RAGContext
from app.services.rag.llm_invocation import invoke_structured
from app.services.rag.schemas import DivisionQueryPlan
from app.services.rag.state import RAGState
from app.services.vector_store_service import division_acronym


logger = logging.getLogger(__name__)


_REWRITE_SYSTEM_PROMPT = (
    "Create one targeted retrieval query for each selected appropriations division. "
    "Keep the user's intent, but only include entities, programs, agencies, or terms "
    "likely relevant to that division. Do not force unrelated entities into every query. "
    "For broad-topic questions, include concise statutory, account, program, agency, authority, "
    "eligibility, and synonym language likely to appear in appropriations text for that division. "
    "When the user names several broad needs, cover likely parallel account or program headings "
    "for each need instead of giving only one example from the category. "
    "Prefer appropriations account-heading and statutory-heading wording over common public-facing "
    "program nicknames when both are likely. "
    "Do this from the question and division context; do not add a static topic vocabulary. "
    "For summary questions, preserve breadth across distinct provisions instead of narrowing to one amount. "
    "Return exact division names from the selected list."
)


def rewrite_division_queries(state: RAGState, ctx: RAGContext) -> dict[str, Any]:
    """Rewrite the original question into division-specific retrieval queries."""
    start_time = time.time()
    selected_divisions = state.get("selected_divisions", [])
    fallback_queries = [
        {
            "division": division,
            "division_acronym": division_acronym(division),
            "query": state["question"],
        }
        for division in selected_divisions
    ]
    if not selected_divisions:
        return {"division_queries": []}

    rewrite_model = resolve_model(state.get("thinking_speed", "normal"), "rewrite")
    ctx.emit_progress(
        state,
        "rewriting",
        "Tailoring division search questions",
        divisions=[division_acronym(division) for division in selected_divisions],
        model=format_model_spec(rewrite_model),
    )

    try:
        rewrite_llm = create_chat_model(
            rewrite_model.model,
            "division_query_rewrite",
            rewrite_model.reasoning_effort,
        )
        allowed_divisions = "\n- ".join(selected_divisions)
        rewrite_messages = [
            SystemMessage(content=_REWRITE_SYSTEM_PROMPT),
            HumanMessage(
                content=(
                    f"Selected divisions:\n- {allowed_divisions}\n\n"
                    f"Original question:\n{state['question']}"
                )
            ),
        ]
        plan = invoke_structured(
            rewrite_llm,
            rewrite_messages,
            schema=DivisionQueryPlan,
            model_spec=rewrite_model,
            stage="rewrite",
            query_id=state.get("query_id", "unknown"),
            debug_log=ctx.debug_log,
        )
        by_division = {
            item.division: item.query.strip()
            for item in plan.division_queries
            if item.division in selected_divisions and item.query.strip()
        }
        division_queries = [
            {
                "division": division,
                "division_acronym": division_acronym(division),
                "query": by_division.get(division, state["question"]),
            }
            for division in selected_divisions
        ]
        ctx.debug_log(
            "rewrite query_id=%s model=%s duration=%.2fs divisions=%s rewritten=%s",
            state.get("query_id", "unknown"),
            format_model_spec(rewrite_model),
            time.time() - start_time,
            [division_acronym(division) for division in selected_divisions],
            len(by_division),
        )
        return {"division_queries": division_queries}
    except Exception as exc:
        logger.warning("Division query rewrite failed; using original question: %s", exc)
        ctx.debug_log(
            "rewrite_fallback query_id=%s model=%s duration=%.2fs divisions=%s",
            state.get("query_id", "unknown"),
            format_model_spec(rewrite_model),
            time.time() - start_time,
            [division_acronym(division) for division in selected_divisions],
        )
        return {"division_queries": fallback_queries}


__all__ = ["rewrite_division_queries"]
