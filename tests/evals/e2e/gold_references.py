"""Gold standard references for e2e eval judging.

Each entry maps a question ID (from questions.py) to a GoldReference
containing the facts the answer must include, errors it must avoid,
and the expected classify/route outputs.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class GoldReference:
    required_facts: list[str] = field(default_factory=list)
    prohibited_errors: list[str] = field(default_factory=list)
    expected_answer_mode: str = ""
    expected_divisions: list[str] = field(default_factory=list)
    notes: str = ""


GOLD_REFERENCES: dict[str, GoldReference] = {}
