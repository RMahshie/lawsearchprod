"""Chat model selection for query routing and RAG generation."""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from typing import Any

from langchain_openai import ChatOpenAI

from app.core.config import get_settings


@dataclass(frozen=True)
class ModelSpec:
    model: str
    provider: str = "openai"
    reasoning_effort: str | None = None


def format_model_spec(spec: ModelSpec) -> str:
    """Format model labels with reasoning when relevant."""
    if spec.provider == "deepseek":
        effort = spec.reasoning_effort or "off"
        return f"{spec.model}(provider=deepseek, thinking={effort})"
    if spec.provider != "openai":
        return f"{spec.model}(provider={spec.provider})"
    if spec.reasoning_effort:
        return f"{spec.model}(reasoning={spec.reasoning_effort})"
    return spec.model


OPENAI_MODEL_STRATEGIES = {
    "quick": {
        "classify": ModelSpec("gpt-5.4-mini"),
        "route": ModelSpec("gpt-5.4-mini"),
        "rewrite": ModelSpec("gpt-5.4-mini"),
        "map": ModelSpec("gpt-5.4-nano"),
        "summary": ModelSpec("gpt-5.4-nano"),
        "reduce": ModelSpec("gpt-5.4-mini"),
        "synthesize": ModelSpec("gpt-5.4-mini"),
    },
    "normal": {
        "classify": ModelSpec("gpt-5.4-mini", reasoning_effort="medium"),
        "route": ModelSpec("gpt-5.4-mini", reasoning_effort="medium"),
        "rewrite": ModelSpec("gpt-5.4-mini", reasoning_effort="medium"),
        "map": ModelSpec("gpt-5.4-mini", reasoning_effort="medium"),
        "summary": ModelSpec("gpt-5.4-nano", reasoning_effort="medium"),
        "reduce": ModelSpec("gpt-5.4", reasoning_effort="low"),
        "synthesize": ModelSpec("gpt-5.4", reasoning_effort="medium"),
    },
    "long": {
        "classify": ModelSpec("gpt-5.4-mini", reasoning_effort="medium"),
        "route": ModelSpec("gpt-5.4-mini", reasoning_effort="medium"),
        "rewrite": ModelSpec("gpt-5.4-mini", reasoning_effort="medium"),
        "map": ModelSpec("gpt-5.4-mini", reasoning_effort="medium"),
        "summary": ModelSpec("gpt-5.4-nano", reasoning_effort="medium"),
        "reduce": ModelSpec("gpt-5.4", reasoning_effort="medium"),
        "synthesize": ModelSpec("gpt-5.4", reasoning_effort="medium"),
    },
}

DEEPSEEK_MODEL_STRATEGIES = {
    "quick": {
        "classify": ModelSpec("deepseek-v4-flash", provider="deepseek"),
        "route": ModelSpec("deepseek-v4-flash", provider="deepseek"),
        "rewrite": ModelSpec("deepseek-v4-flash", provider="deepseek"),
        "map": ModelSpec("deepseek-v4-flash", provider="deepseek"),
        "summary": ModelSpec("deepseek-v4-flash", provider="deepseek"),
        "reduce": ModelSpec("gpt-5.4-mini", reasoning_effort="low"),
        "synthesize": ModelSpec("gpt-5.4-mini", reasoning_effort="low"),
    },
    "normal": {
        "classify": ModelSpec("deepseek-v4-flash", provider="deepseek", reasoning_effort="high"),
        "route": ModelSpec("deepseek-v4-flash", provider="deepseek", reasoning_effort="high"),
        "rewrite": ModelSpec("deepseek-v4-flash", provider="deepseek", reasoning_effort="high"),
        "map": ModelSpec("deepseek-v4-flash", provider="deepseek"),
        "summary": ModelSpec("deepseek-v4-flash", provider="deepseek", reasoning_effort="high"),
        "reduce": ModelSpec("gpt-5.4-mini", reasoning_effort="low"),
        "synthesize": ModelSpec("gpt-5.4", reasoning_effort="low"),
    },
    "long": {
        "classify": ModelSpec("deepseek-v4-flash", provider="deepseek", reasoning_effort="high"),
        "route": ModelSpec("deepseek-v4-flash", provider="deepseek", reasoning_effort="high"),
        "rewrite": ModelSpec("deepseek-v4-flash", provider="deepseek", reasoning_effort="high"),
        "map": ModelSpec("deepseek-v4-flash", provider="deepseek"),
        "summary": ModelSpec("deepseek-v4-flash", provider="deepseek", reasoning_effort="high"),
        "reduce": ModelSpec("deepseek-v4-flash", provider="deepseek", reasoning_effort="high"),
        "synthesize": ModelSpec("deepseek-v4-pro", provider="deepseek", reasoning_effort="max"),
    },
}

MODEL_PROFILES = {
    "openai": OPENAI_MODEL_STRATEGIES,
    "deepseek": DEEPSEEK_MODEL_STRATEGIES,
}

SPEED_ALIASES = {
    "medium": "normal",
    "thinking": "long",
}

TASK_ALIASES = {
    "routing": "route",
    "division_query_rewrite": "rewrite",
}


def normalize_speed(thinking_speed: str) -> str:
    """Normalize UI/user aliases to internal speed keys."""
    return SPEED_ALIASES.get(thinking_speed, thinking_speed)


def active_model_profile() -> str:
    """Return the active model profile."""
    profile = get_settings().model_profile
    return profile if profile in MODEL_PROFILES else "openai"


def _active_strategy() -> dict[str, dict[str, ModelSpec]]:
    """Return the strategy table for the active model profile."""
    return MODEL_PROFILES[active_model_profile()]


def resolve_model(thinking_speed: str, task: str) -> ModelSpec:
    """Resolve the effective chat model for a speed/task pair."""
    speed = normalize_speed(thinking_speed)
    normalized_task = TASK_ALIASES.get(task, task)
    strategies = _active_strategy()
    strategy = strategies.get(speed, strategies["normal"])
    return strategy.get(normalized_task, strategy["synthesize"])


def describe_model_strategy(thinking_speed: str) -> str:
    """Return a compact response label for the active model strategy."""
    profile = active_model_profile()
    speed = normalize_speed(thinking_speed)
    strategies = _active_strategy()
    strategy = strategies.get(speed, strategies["normal"])
    ordered_tasks = ("classify", "route", "rewrite", "map", "summary", "reduce", "synthesize")
    labels = ", ".join(f"{task}:{format_model_spec(strategy[task])}" for task in ordered_tasks)
    return f"profile:{profile}, {labels}"


@lru_cache(maxsize=64)
def create_chat_model(model: str, task: str, reasoning_effort: str | None = None) -> Any:
    """Create and cache chat clients by provider/model/task."""
    if model.startswith("deepseek-"):
        try:
            from langchain_deepseek import ChatDeepSeek
        except ImportError as exc:
            raise RuntimeError(
                "langchain-deepseek is required when LAWSEARCH_MODEL_PROFILE=deepseek"
            ) from exc

        api_key = os.getenv("DEEPSEEK_API_KEY") or get_settings().deepseek_api_key
        if not api_key:
            raise RuntimeError(
                "DEEPSEEK_API_KEY is required when LAWSEARCH_MODEL_PROFILE=deepseek"
            )

        thinking = "enabled" if reasoning_effort else "disabled"
        kwargs: dict[str, Any] = {
            "model": model,
            "api_key": api_key,
            "extra_body": {"thinking": {"type": thinking}},
        }
        base_url = os.getenv("DEEPSEEK_API_BASE") or get_settings().deepseek_api_base
        if base_url:
            kwargs["base_url"] = base_url
        if reasoning_effort:
            kwargs["reasoning_effort"] = reasoning_effort
        else:
            kwargs["temperature"] = 0
        return ChatDeepSeek(**kwargs)

    if reasoning_effort:
        return ChatOpenAI(
            model=model,
            reasoning_effort=reasoning_effort,
            verbosity="medium",
        )

    return ChatOpenAI(model=model, temperature=0)
