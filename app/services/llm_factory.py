"""OpenAI model selection for query routing and RAG generation."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from langchain_openai import ChatOpenAI


@dataclass(frozen=True)
class ModelSpec:
    model: str
    reasoning_effort: str | None = None


def format_model_spec(spec: ModelSpec) -> str:
    """Format model labels with reasoning when relevant."""
    if spec.reasoning_effort:
        return f"{spec.model}(reasoning={spec.reasoning_effort})"
    return spec.model


ROUTING_MODEL = ModelSpec("gpt-5.4-nano")

MODEL_STRATEGIES = {
    "quick": {
        "map": ModelSpec("gpt-5.4-nano"),
        "summary": ModelSpec("gpt-5.4-nano"),
        "reduce": ModelSpec("gpt-5.4-nano"),
        "synthesize": ModelSpec("gpt-5.4-mini"),
    },
    "normal": {
        "map": ModelSpec("gpt-5.4-mini"),
        "summary": ModelSpec("gpt-5.4-mini"),
        "reduce": ModelSpec("gpt-5.4", reasoning_effort="low"),
        "synthesize": ModelSpec("gpt-5.4", reasoning_effort="low"),
    },
    "long": {
        "map": ModelSpec("gpt-5.4-mini"),
        "summary": ModelSpec("gpt-5.4-mini"),
        "reduce": ModelSpec("gpt-5.4", reasoning_effort="medium"),
        "synthesize": ModelSpec("gpt-5.4", reasoning_effort="medium"),
    },
}

SPEED_ALIASES = {
    "medium": "normal",
    "thinking": "long",
}


def normalize_speed(thinking_speed: str) -> str:
    """Normalize UI/user aliases to internal speed keys."""
    return SPEED_ALIASES.get(thinking_speed, thinking_speed)


def resolve_model(thinking_speed: str, task: str, model_override: str | None = None) -> ModelSpec:
    """Resolve the effective OpenAI model for a speed/task pair."""
    if task == "routing":
        return ROUTING_MODEL

    if model_override:
        return ModelSpec(model_override)

    speed = normalize_speed(thinking_speed)
    strategy = MODEL_STRATEGIES.get(speed, MODEL_STRATEGIES["normal"])
    return strategy.get(task, strategy["synthesize"])


def describe_model_strategy(thinking_speed: str, model_override: str | None = None) -> str:
    """Return a compact response label for the active model strategy."""
    if model_override:
        return model_override

    speed = normalize_speed(thinking_speed)
    strategy = MODEL_STRATEGIES.get(speed, MODEL_STRATEGIES["normal"])
    ordered_tasks = ("map", "reduce", "synthesize")
    return ", ".join(f"{task}:{format_model_spec(strategy[task])}" for task in ordered_tasks)


@lru_cache(maxsize=64)
def create_chat_model(model: str, task: str, reasoning_effort: str | None = None) -> ChatOpenAI:
    """Create and cache ChatOpenAI clients by model/task."""
    if reasoning_effort:
        return ChatOpenAI(
            model=model,
            reasoning_effort=reasoning_effort,
            verbosity="medium",
        )

    return ChatOpenAI(model=model, temperature=0)
