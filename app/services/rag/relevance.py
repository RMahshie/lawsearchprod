"""Mapped-fact normalization and relevance bookkeeping helpers."""

from __future__ import annotations

from typing import Any

from app.services.rag.schemas import MappedFact, MappedFacts


_TIERS: tuple[str, ...] = ("direct", "adjacent", "not_responsive")
_VALID_TIERS: frozenset[str] = frozenset(_TIERS)


def normalize_mapped_fact_records(mapped_facts: MappedFacts) -> list[dict[str, Any]]:
    """Return JSON-ready mapped facts with responsiveness tiers.

    Args:
        mapped_facts: Structured map output for one chunk.

    Returns:
        List of fact dicts each carrying ``fact``, ``responsiveness_tier``,
        ``reason``, and ``source_numbers``.
    """
    records: list[dict[str, Any]] = []
    facts = mapped_facts.facts or []
    if not facts and mapped_facts.extracted_facts.strip():
        facts = [
            MappedFact(fact=line.strip(), responsiveness_tier="direct")
            for line in mapped_facts.extracted_facts.splitlines()
            if line.strip()
        ]

    for fact in facts:
        text = fact.fact.strip()
        if not text:
            continue
        tier = fact.responsiveness_tier
        records.append(
            {
                "fact": text,
                "responsiveness_tier": tier if tier in _VALID_TIERS else "direct",
                "reason": fact.reason.strip(),
                "source_numbers": [
                    candidate.model_dump(mode="json", exclude_none=True)
                    for candidate in fact.source_numbers
                ],
            }
        )

    if not records:
        records.append(
            {
                "fact": "- No relevant facts found.",
                "responsiveness_tier": "not_responsive",
                "reason": "No relevant evidence extracted from this chunk.",
                "source_numbers": [],
            }
        )
    return records


def relevance_counts(facts: list[dict[str, Any]]) -> dict[str, int]:
    """Count mapped facts by responsiveness tier.

    Args:
        facts: Normalized mapped-fact records.

    Returns:
        Dictionary with ``direct``, ``adjacent``, and ``not_responsive`` counts.
    """
    counts = {tier: 0 for tier in _TIERS}
    for fact in facts:
        tier = fact.get("responsiveness_tier")
        if tier in counts:
            counts[tier] += 1
    return counts


def merge_relevance_counts(counts_list: list[dict[str, int]]) -> dict[str, int]:
    """Merge responsiveness tier count dictionaries.

    Args:
        counts_list: Per-chunk responsiveness count dictionaries.

    Returns:
        Combined responsiveness counts.
    """
    merged = {tier: 0 for tier in _TIERS}
    for counts in counts_list:
        for key in merged:
            merged[key] += int(counts.get(key, 0))
    return merged


def render_tiered_facts(facts: list[dict[str, Any]]) -> str:
    """Render mapped facts for reduce prompts while preserving tier metadata.

    Args:
        facts: Normalized mapped-fact records.

    Returns:
        Multi-section markdown string suitable for reduce prompts.
    """
    groups = [
        ("Direct facts", "direct"),
        ("Adjacent facts", "adjacent"),
        ("Not responsive facts", "not_responsive"),
    ]
    sections: list[str] = []
    for label, tier in groups:
        tier_facts = [fact for fact in facts if fact.get("responsiveness_tier") == tier]
        if not tier_facts:
            continue
        lines = [f"{label}:"]
        for fact in tier_facts:
            reason = fact.get("reason")
            suffix = f" (scope note: {reason})" if reason else ""
            prompt_id = str(fact.get("prompt_id", "") or "").strip()
            id_prefix = f"[{prompt_id}] " if prompt_id else ""
            lines.append(f"- {id_prefix}{fact.get('fact', '').strip()}{suffix}")
        sections.append("\n".join(lines))
    return "\n\n".join(sections) or "Not responsive facts:\n- No relevant facts found."


def summarize_relevance(facts: list[dict[str, Any]], limit: int = 3) -> dict[str, Any]:
    """Build a compact relevance summary for logging and persistence.

    Args:
        facts: Normalized mapped-fact records.
        limit: Maximum number of examples per tier to include.

    Returns:
        Dictionary with ``direct_examples`` and ``adjacent_examples`` arrays.
    """
    direct = [fact.get("fact", "").strip() for fact in facts if fact.get("responsiveness_tier") == "direct"]
    adjacent = [
        {
            "fact": fact.get("fact", "").strip(),
            "reason": fact.get("reason", "").strip(),
        }
        for fact in facts
        if fact.get("responsiveness_tier") == "adjacent"
    ]
    return {
        "direct_examples": direct[:limit],
        "adjacent_examples": adjacent[:limit],
    }


__all__ = [
    "normalize_mapped_fact_records",
    "relevance_counts",
    "merge_relevance_counts",
    "render_tiered_facts",
    "summarize_relevance",
]
