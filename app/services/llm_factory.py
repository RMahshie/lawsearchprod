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
    """Format model labels with reasoning when relevant.

    Args:
        spec: Model specification containing model name and optional reasoning effort.

    Returns:
        Human-readable model label.
    """
    if spec.reasoning_effort:
        return f"{spec.model}(reasoning={spec.reasoning_effort})"
    return spec.model


ROUTING_MODEL = ModelSpec("gpt-5.4-mini")

MODEL_STRATEGIES = {
    "quick": {
        "map": ModelSpec("gpt-5.4-nano"),
        "summary": ModelSpec("gpt-5.4-nano"),
        "reduce": ModelSpec("gpt-5.4-mini"),
        "synthesize": ModelSpec("gpt-5.4-mini"),
    },
    "normal": {
        "map": ModelSpec("gpt-5.4-mini"),
        "summary": ModelSpec("gpt-5.4-nano"),
        "reduce": ModelSpec("gpt-5.4", reasoning_effort="low"),
        "synthesize": ModelSpec("gpt-5.4", reasoning_effort="medium"),
    },
    "long": {
        "map": ModelSpec("gpt-5.4-mini"),
        "summary": ModelSpec("gpt-5.4-nano"),
        "reduce": ModelSpec("gpt-5.4", reasoning_effort="medium"),
        "synthesize": ModelSpec("gpt-5.4", reasoning_effort="medium"),
    },
}

SPEED_ALIASES = {
    "medium": "normal",
    "thinking": "long",
}


def normalize_speed(thinking_speed: str) -> str:
    """Normalize UI/user aliases to internal speed keys.

    Args:
        thinking_speed: Thinking speed string from the API or UI.

    Returns:
        Canonical speed key used for model strategy lookup.
    """
    return SPEED_ALIASES.get(thinking_speed, thinking_speed)


def resolve_model(thinking_speed: str, task: str) -> ModelSpec:
    """Resolve the effective OpenAI model for a speed/task pair.

    Args:
        thinking_speed: Canonical or aliased speed key.
        task: RAG task name such as routing, map, reduce, or synthesize.

    Returns:
        ModelSpec for the requested task.
    """
    if task == "routing":
        return ROUTING_MODEL

    speed = normalize_speed(thinking_speed)
    strategy = MODEL_STRATEGIES.get(speed, MODEL_STRATEGIES["normal"])
    return strategy.get(task, strategy["synthesize"])


def describe_model_strategy(thinking_speed: str) -> str:
    """Return a compact response label for the active model strategy.

    Args:
        thinking_speed: Canonical or aliased speed key.

    Returns:
        Comma-separated summary of model choices for the main RAG stages.
    """
    speed = normalize_speed(thinking_speed)
    strategy = MODEL_STRATEGIES.get(speed, MODEL_STRATEGIES["normal"])
    ordered_tasks = ("map", "reduce", "synthesize")
    return ", ".join(f"{task}:{format_model_spec(strategy[task])}" for task in ordered_tasks)


@lru_cache(maxsize=64)
def create_chat_model(model: str, task: str, reasoning_effort: str | None = None) -> ChatOpenAI:
    """Create and cache ChatOpenAI clients by model/task.

    Args:
        model: OpenAI chat model name.
        task: RAG task name included in the cache key.
        reasoning_effort: Optional reasoning effort for reasoning-capable models.

    Returns:
        Cached ChatOpenAI client configured for the requested model.
    """
    if reasoning_effort:
        return ChatOpenAI(
            model=model,
            reasoning_effort=reasoning_effort,
            verbosity="medium",
        )

    return ChatOpenAI(model=model, temperature=0)
