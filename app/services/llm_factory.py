"""OpenAI model selection for query routing and RAG generation."""

from __future__ import annotations

from functools import lru_cache

from langchain_openai import ChatOpenAI


DEFAULT_MODELS = {
    "quick": "gpt-4o-mini",
    "normal": "gpt-4o",
    "long": "gpt-5",
}

ROUTING_MODEL = "gpt-4o-mini"


def model_for_speed(thinking_speed: str) -> str:
    """Return the default generation model for a thinking-speed preset."""
    return DEFAULT_MODELS.get(thinking_speed, DEFAULT_MODELS["normal"])


def resolve_model(thinking_speed: str, model_override: str | None = None) -> str:
    """Resolve the effective OpenAI model for a request."""
    return model_override or model_for_speed(thinking_speed)


@lru_cache(maxsize=32)
def create_chat_model(model: str, task: str) -> ChatOpenAI:
    """Create and cache ChatOpenAI clients by model/task."""
    if task == "routing":
        return ChatOpenAI(model=ROUTING_MODEL, temperature=0)

    if model == "gpt-5":
        reasoning_effort = "high" if task in {"reduce", "synthesize"} else "medium"
        return ChatOpenAI(
            model=model,
            reasoning_effort=reasoning_effort,
            model_kwargs={"verbosity": "medium"},
        )

    return ChatOpenAI(model=model, temperature=0)
