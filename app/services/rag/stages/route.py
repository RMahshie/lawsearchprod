"""Route stage: select which Divisions to query for a given question."""

from __future__ import annotations

import logging
import time
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from app.core.config import FY2026_DIVISION_ACRONYMS, FY2026_INCOMPATIBLE_QUESTION_ANSWER
from app.services.llm_factory import create_chat_model, format_model_spec, resolve_model
from app.services.rag.context import RAGContext
from app.services.rag.llm_invocation import invoke_structured
from app.services.rag.schemas import RouteDecision
from app.services.rag.state import RAGState
from app.services.rag_prompting import DEFAULT_ANSWER_MODE
from app.services.vector_store_service import division_acronym


logger = logging.getLogger(__name__)
INCOMPATIBLE_QUESTION_ANSWER = FY2026_INCOMPATIBLE_QUESTION_ANSWER


_ROUTE_SYSTEM_PROMPT = (
    "Select the relevant appropriations divisions for this question. "
    "Return only exact FY2026 division names from the allowed list. "
    "Use the aliases only as routing hints, never as returned labels. "
    "Do not classify the answer style. Do not return aliases, acronyms, agencies, accounts, "
    "or shortened division names. Return no divisions only when the question is outside the "
    "available FY2026 appropriations divisions. "
    "Appropriations routing follows bill-division jurisdiction, not cabinet department organization. "
    "Important jurisdiction notes: FDA, Food and Drug Administration, FDA Salaries and Expenses, "
    "food safety, and tobacco product user fees route to AGRICULTURE, RURAL DEVELOPMENT, FOOD "
    "AND DRUG ADMINISTRATION, AND RELATED AGENCIES, not LHHS. NIH, CDC, CMS, HRSA, SAMHSA, "
    "ACF, ACL, and general HHS accounts route to LHHS. FEMA, DHS, continuing appropriations, "
    "extenders, and disaster relief continuation language route to CONTINUING APPROPRIATIONS, "
    "EXTENDERS, HOMELAND SECURITY, AND OTHER MATTERS. EPA routes to DEPARTMENT OF THE INTERIOR, "
    "ENVIRONMENT, AND RELATED AGENCIES, not ENERGY AND WATER DEVELOPMENT, unless the question "
    "is about Corps of Engineers, Bureau of Reclamation, or DOE water accounts."
)


def normalize_route_divisions(divisions: list[str], valid_divisions: dict[str, str]) -> list[str]:
    """Normalize route outputs to canonical division names.

    The router is instructed to return exact division names, but small routing
    models sometimes return stable FY2026 acronyms such as AG. Treat known
    acronyms and case variants as the same canonical division; do not infer
    fuzzy matches outside the configured division/acronym set.
    """
    canonical_by_upper = {division.upper(): division for division in valid_divisions}
    acronym_to_division = {
        acronym.upper(): division
        for division, acronym in FY2026_DIVISION_ACRONYMS.items()
        if division in valid_divisions
    }
    selected: list[str] = []
    seen: set[str] = set()

    for raw_division in divisions:
        normalized_key = str(raw_division or "").strip().strip("[]").upper()
        division = canonical_by_upper.get(normalized_key) or acronym_to_division.get(normalized_key)
        if division and division not in seen:
            selected.append(division)
            seen.add(division)

    return selected


def route_divisions(state: RAGState, ctx: RAGContext) -> dict[str, Any]:
    """Select which appropriations divisions should be searched for the query."""
    start_time = time.time()
    ctx.emit_progress(state, "routing", "Finding relevant divisions")
    requested_filter = state.get("divisions_filter")
    settings = ctx.settings
    routing_model = resolve_model(state.get("thinking_speed", "normal"), "route")
    if requested_filter:
        ctx.debug_log(
            "route query_id=%s source=filter model=%s duration=%.2fs selected=%s answer_mode=%s flags=%s reason=%s",
            state.get("query_id", "unknown"),
            format_model_spec(routing_model),
            time.time() - start_time,
            len(requested_filter),
            state.get("answer_mode", DEFAULT_ANSWER_MODE),
            state.get("answer_mode_flags", {}),
            state.get("answer_mode_reason", ""),
        )
        return {"selected_divisions": requested_filter}

    valid_divisions = list(settings.subcommittee_stores.keys())
    routing_llm = create_chat_model(
        routing_model.model,
        "routing",
        routing_model.reasoning_effort,
    )
    allowed_divisions = "\n".join(
        f"- {division}: {settings.routing_aliases.get(division, '')}"
        for division in valid_divisions
    )
    route_messages = [
        SystemMessage(content=_ROUTE_SYSTEM_PROMPT),
        HumanMessage(
            content=(
                f"Allowed FY2026 divisions and routing hints:\n{allowed_divisions}\n\n"
                f"Question: {state['question']}"
            )
        ),
    ]
    decision = invoke_structured(
        routing_llm,
        route_messages,
        schema=RouteDecision,
        model_spec=routing_model,
        stage="route",
        query_id=state.get("query_id", "unknown"),
        debug_log=ctx.debug_log,
    )
    selected = normalize_route_divisions(decision.divisions, settings.subcommittee_stores)
    if not selected:
        logger.info("Router returned no valid FY2026 divisions; ending as incompatible question")
        ctx.debug_log(
            "route query_id=%s source=llm model=%s duration=%.2fs selected=0 incompatible=true "
            "answer_mode=%s flags=%s reason=%s raw_divisions=%s",
            state.get("query_id", "unknown"),
            format_model_spec(routing_model),
            time.time() - start_time,
            state.get("answer_mode", DEFAULT_ANSWER_MODE),
            state.get("answer_mode_flags", {}),
            state.get("answer_mode_reason", ""),
            decision.divisions,
        )
        return {
            "selected_divisions": [],
            "final_answer": INCOMPATIBLE_QUESTION_ANSWER,
        }
    ctx.debug_log(
        "route query_id=%s source=llm model=%s duration=%.2fs selected=%s divisions=%s "
        "answer_mode=%s flags=%s reason=%s",
        state.get("query_id", "unknown"),
        format_model_spec(routing_model),
        time.time() - start_time,
        len(selected),
        [division_acronym(division) for division in selected],
        state.get("answer_mode", DEFAULT_ANSWER_MODE),
        state.get("answer_mode_flags", {}),
        state.get("answer_mode_reason", ""),
    )
    return {"selected_divisions": selected}


__all__ = ["route_divisions", "normalize_route_divisions", "INCOMPATIBLE_QUESTION_ANSWER"]
