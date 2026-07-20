"""Pydantic schemas for structured LLM outputs across the RAG pipeline."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.services.rag_prompting import DEFAULT_ANSWER_MODE


class AnswerModeFlags(BaseModel):
    """Safety flags selected with the route decision."""

    mixed_financial_types: bool = False


class AnswerModeDecision(BaseModel):
    """Structured answer-mode classification response."""

    answer_mode: Literal[
        "direct_account_amount",
        "broad_topic_total",
        "funding_mechanism_no_amount",
        "reconciliation_breakdown",
        "general_summary",
    ] = DEFAULT_ANSWER_MODE
    answer_mode_flags: AnswerModeFlags = Field(default_factory=AnswerModeFlags)
    answer_mode_reason: str = ""


class RouteDecision(BaseModel):
    """Structured routing response."""

    divisions: list[str] = Field(default_factory=list)


class DivisionQueryDecision(BaseModel):
    """Structured per-division retrieval query response."""

    division: str
    query: str


class DivisionQueryPlan(BaseModel):
    """Structured query rewrite response."""

    division_queries: list[DivisionQueryDecision] = Field(default_factory=list)


class ProposedDerivedAnnotation(BaseModel):
    """LLM-proposed Derived Figure Handle before deterministic validation."""

    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(
        description="Stage-local Derived Figure Handle such as D1, without braces.",
    )
    proposed_figure: str = Field(
        alias="figure",
        description="Model-proposed figure text. The displayed figure is read from the answer marker context.",
    )
    value: float
    label: str
    equation: str
    rationale: str = ""
    input_ids: list[str] = Field(
        default_factory=list,
        description="Stage-local Figure Handles, such as F1 or an earlier D1.",
    )

    @model_validator(mode="before")
    @classmethod
    def normalize_legacy_value(cls, data):
        """Accept current annotation proposals that still use normalized_value."""
        if isinstance(data, dict) and "value" not in data and "normalized_value" in data:
            data = dict(data)
            data["value"] = data.get("normalized_value")
        return data


class MarkedAnswer(BaseModel):
    """Answer markdown with Figure Handles plus proposed Derived Figures."""

    answer: str = Field(
        description=(
            "Markdown using registered {{F#}} source handles (the evidence may show "
            "them as {{F#:$...}}) or {{D#}} derived handles instead of raw dollar figures."
        ),
    )
    derived_annotations: list[ProposedDerivedAnnotation] = Field(default_factory=list)
    covered_fact_ids: list[str] = Field(
        default_factory=list,
        description=(
            "Internal prompt-local required fact ids materially represented in the answer. "
            "Do not print these ids in answer markdown."
        ),
    )
    excluded_fact_ids: list[str] = Field(
        default_factory=list,
        description=(
            "Internal prompt-local required fact ids deliberately excluded under the "
            "answer-mode coverage rule."
        ),
    )


class SourceNumberCandidate(BaseModel):
    """LLM-proposed source-backed figure extracted from one mapped chunk."""

    figure: str
    value: float | None = None
    label: str


class MappedFact(BaseModel):
    """One mapped fact with scope responsiveness metadata."""

    fact: str
    responsiveness_tier: Literal["direct", "adjacent", "not_responsive"] = "direct"
    reason: str = ""
    source_numbers: list[SourceNumberCandidate] = Field(default_factory=list)


class MappedFacts(BaseModel):
    """Structured map output with facts and relevant source-backed numbers."""

    extracted_facts: str = ""
    facts: list[MappedFact] = Field(default_factory=list)
    source_numbers: list[SourceNumberCandidate] = Field(default_factory=list)

    @model_validator(mode="after")
    def normalize_fact_objects(self):
        """Keep legacy extracted_facts/source_numbers output compatible with tiered facts."""
        if not self.facts and self.extracted_facts.strip() and self.extracted_facts.strip() != "- No relevant facts found.":
            self.facts = [
                MappedFact(
                    fact=line.strip(),
                    responsiveness_tier="direct",
                    source_numbers=self.source_numbers,
                )
                for line in self.extracted_facts.splitlines()
                if line.strip()
            ]
        if not self.extracted_facts.strip() and self.facts:
            self.extracted_facts = "\n".join(fact.fact for fact in self.facts)
        return self


__all__ = [
    "AnswerModeFlags",
    "AnswerModeDecision",
    "RouteDecision",
    "DivisionQueryDecision",
    "DivisionQueryPlan",
    "ProposedDerivedAnnotation",
    "MarkedAnswer",
    "SourceNumberCandidate",
    "MappedFact",
    "MappedFacts",
]
