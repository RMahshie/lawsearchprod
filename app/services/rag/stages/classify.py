"""Classify stage: pick the answer-mode shape for a question before routing."""

from __future__ import annotations

import time
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from app.services.llm_factory import create_chat_model, format_model_spec, resolve_model
from app.services.rag.context import RAGContext
from app.services.rag.llm_invocation import invoke_structured
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
    "programs, or divisions and asks for funding, totals, amounts, available money, or grouped "
    "funding buckets. "
    "Use funding_mechanism_no_amount when the user asks how funding works, what mechanism is used, "
    "whether an explicit amount exists, what happens under a continuing resolution, or whether a "
    "full-year amount is provided. The key distinction is mechanism/availability versus how much; "
    "a conceptual compare/contrast question about different appropriation types is general_summary "
    "unless it asks whether a specific amount exists. "
    "Use reconciliation_breakdown only when the user asks for breakdown, allocation, line items, "
    "show math, included/excluded amounts, double-counting, comparison, or combined totals. "
    "Use general_summary for non-accounting explanatory questions, especially when the user asks to "
    "summarize, explain in plain English, describe what a division/account does, describe what "
    "kinds of projects or activities it supports, compare concepts, or avoid a detailed dollar "
    "breakdown. "
    "Examples: direct_account_amount: 'What amount is appropriated for a named account in FY2026, "
    "and what are its major allowed uses?' "
    "broad_topic_total: 'What FY2026 funding is available for a broad infrastructure topic, "
    "and which agencies or accounts control it?' "
    "funding_mechanism_no_amount: 'How much money does a named agency get under a continuing "
    "appropriations division?' when the text provides continuation or rate-for-operations "
    "language but no explicit agency amount. "
    "funding_mechanism_no_amount: 'How is a department's funding handled, and is there a full-year amount?' "
    "funding_mechanism_no_amount: 'What funding mechanism does the continuing appropriations act use?' "
    "funding_mechanism_no_amount: 'Does the text provide a specific dollar amount for this topic, or only a continuing-appropriations mechanism?' "
    "funding_mechanism_no_amount: 'What happens to agencies under the continuing resolution if no full-year appropriation is provided?' "
    "reconciliation_breakdown: 'Break down a named account by activity and financing source.' "
    "general_summary: 'What does this division do for a named agency's facilities?' "
    "general_summary: 'What kinds of projects or activities does this division generally support?' "
    "general_summary: 'What is the difference between regular appropriations and continuing appropriations?' "
    "general_summary: 'Summarize how FY2026 appropriations treat a broad policy area without doing a detailed dollar breakdown.' "
    "If the question asks for dollars, funding, totals, or available money and the best mode is ambiguous, use broad_topic_total; "
    "otherwise prefer general_summary for explanatory coverage questions. "
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
    )
    messages = [
        SystemMessage(content=_CLASSIFY_SYSTEM_PROMPT),
        HumanMessage(content=f"Question: {state['question']}"),
    ]
    decision = invoke_structured(
        classification_llm,
        messages,
        schema=AnswerModeDecision,
        model_spec=classification_model,
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
