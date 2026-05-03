"""Classify stage: pick the answer-mode shape for a question before routing."""

from __future__ import annotations

import time
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from app.services.llm_factory import create_chat_model, format_model_spec, resolve_model
from app.services.rag.context import RAGContext
from app.services.rag.llm_invocation import invoke_with_retry
from app.services.rag.schemas import AnswerModeDecision, AnswerModeFlags
from app.services.rag.state import RAGState
from app.services.rag_prompting import DEFAULT_ANSWER_MODE, normalize_answer_mode


_CLASSIFY_SYSTEM_PROMPT = (
    "Classify the answer style for this question. Do not select divisions. "
    "Set answer_mode to one of: direct_account_amount, broad_topic_total, "
    "funding_mechanism_no_amount, reconciliation_breakdown, general_summary. "
    "The mode examples below are illustrative, not exhaustive. "
    "Use direct_account_amount when the user asks about one named account, program, agency line, "
    "or appropriation and wants the amount, purpose, allowed uses, or compact explanation; asking "
    "for major allowed uses does not by itself mean reconciliation_breakdown. "
    "Use broad_topic_total when the user asks about a broad topic across accounts, agencies, "
    "programs, or divisions and may need grouped funding buckets. "
    "Use funding_mechanism_no_amount when the FY2026 text likely explains how funding continues "
    "or is made available but may not include a dollar figure. "
    "Use reconciliation_breakdown only when the user asks for breakdown, allocation, line items, "
    "show math, included/excluded amounts, double-counting, comparison, or combined totals. "
    "Use general_summary for non-accounting explanatory questions. "
    "Examples: direct_account_amount: 'What amount is appropriated for the FDA Salaries and "
    "Expenses account in FY2026, and what are the major allowed uses?' "
    "broad_topic_total: 'What FY2026 funding is available for rural water or wastewater "
    "infrastructure, and which agencies or accounts control it?' "
    "funding_mechanism_no_amount: 'How much money does FEMA get under the continuing "
    "appropriations division?' when the text provides continuation or rate-for-operations "
    "language but no explicit FEMA amount. "
    "reconciliation_breakdown: 'Break down FDA Salaries and Expenses by center and user-fee source.' "
    "general_summary: 'What does the Agriculture division do for FDA facilities?' "
    "If the best mode is ambiguous, use broad_topic_total. "
    "Set answer_mode_flags.mixed_financial_types=true when relevant figures may include "
    "non-comparable financial types such as grants, loan authority, subsidy costs, user fees, "
    "transfers, rescissions, caps, limitations, or set-asides. "
    "Keep answer_mode_reason short."
)


def answer_mode_update(decision: Any) -> dict[str, Any]:
    """Normalize route-classifier answer-mode metadata for graph state."""
    raw_mode = getattr(decision, "answer_mode", DEFAULT_ANSWER_MODE)
    flags = getattr(decision, "answer_mode_flags", None)
    if isinstance(flags, AnswerModeFlags):
        flags_dict = flags.model_dump()
    elif isinstance(flags, dict):
        flags_dict = {"mixed_financial_types": bool(flags.get("mixed_financial_types"))}
    else:
        flags_dict = {
            "mixed_financial_types": bool(getattr(flags, "mixed_financial_types", False)),
        }
    return {
        "answer_mode": normalize_answer_mode(raw_mode),
        "answer_mode_flags": flags_dict,
        "answer_mode_reason": str(getattr(decision, "answer_mode_reason", "") or "").strip(),
    }


def classify_answer_mode(state: RAGState, ctx: RAGContext) -> dict[str, Any]:
    """Classify the requested answer shape before division routing."""
    start_time = time.time()
    ctx.emit_progress(state, "classifying", "Classifying answer style")
    classification_model = resolve_model(state.get("thinking_speed", "normal"), "classify")
    classification_llm = create_chat_model(
        classification_model.model,
        "classify",
        classification_model.reasoning_effort,
    ).with_structured_output(AnswerModeDecision)
    messages = [
        SystemMessage(content=_CLASSIFY_SYSTEM_PROMPT),
        HumanMessage(content=f"Question: {state['question']}"),
    ]
    decision = invoke_with_retry(
        lambda: classification_llm.invoke(messages),
        stage="classify",
        query_id=state.get("query_id", "unknown"),
        debug_log=ctx.debug_log,
    )
    update = answer_mode_update(decision)
    ctx.debug_log(
        "classify query_id=%s model=%s duration=%.2fs answer_mode=%s flags=%s reason=%s",
        state.get("query_id", "unknown"),
        format_model_spec(classification_model),
        time.time() - start_time,
        update["answer_mode"],
        update["answer_mode_flags"],
        update["answer_mode_reason"],
    )
    return update


__all__ = ["classify_answer_mode", "answer_mode_update"]
