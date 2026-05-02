"""Pure helpers for invoking chat models with retry and structured-output fallback.

These functions are intentionally free of any RAGService state. Callers pass a
``debug_log`` callable (typically ``RAGService._debug_log``) to surface retry
and fallback events through the same logging gate as the rest of the pipeline.
"""

from __future__ import annotations

import time
from typing import Any, Callable, TypeVar

from pydantic import BaseModel


StructuredResponseT = TypeVar("StructuredResponseT", bound=BaseModel)


_RETRYABLE_STATUSES: frozenset[int] = frozenset({429, 500, 502, 503, 504})


def llm_error_status(exc: Exception) -> int | None:
    """Extract an HTTP status code from an LLM exception when present.

    Args:
        exc: Exception raised by an LLM client.

    Returns:
        Integer HTTP status code if found, otherwise None.
    """
    status_code = getattr(exc, "status_code", None)
    if isinstance(status_code, int):
        return status_code

    response = getattr(exc, "response", None)
    response_status = getattr(response, "status_code", None)
    if isinstance(response_status, int):
        return response_status

    return None


def is_retryable_llm_error(exc: Exception) -> bool:
    """Determine whether an LLM exception should be retried.

    Args:
        exc: Exception raised by an LLM invocation.

    Returns:
        True when the exception status code is transient, otherwise False.
    """
    return llm_error_status(exc) in _RETRYABLE_STATUSES


def invoke_with_retry(
    invoke_fn: Callable[[], Any],
    *,
    stage: str,
    query_id: str,
    debug_log: Callable[..., None],
) -> Any:
    """Invoke a callable once and retry once for retryable LLM failures.

    Args:
        invoke_fn: Zero-argument callable that performs the model request.
        stage: Pipeline stage name used for debug logging.
        query_id: Query identifier used for debug logging.
        debug_log: Callable used to emit retry events behind the debug flag.

    Returns:
        Result returned by invoke_fn.
    """
    try:
        return invoke_fn()
    except Exception as exc:
        if not is_retryable_llm_error(exc):
            raise

        debug_log(
            "retry query_id=%s stage=%s attempt=2 status=%s error=%s",
            query_id,
            stage,
            llm_error_status(exc),
            type(exc).__name__,
        )
        time.sleep(0.75)
        return invoke_fn()


def invoke_text(
    llm: Any,
    prompt: str,
    *,
    stage: str,
    query_id: str,
    debug_log: Callable[..., None],
) -> str:
    """Invoke an LLM and normalize its response content to plain text.

    Args:
        llm: Chat model or compatible object with an invoke method.
        prompt: Prompt string to send to the model.
        stage: Pipeline stage name used for retry/debug logging.
        query_id: Query identifier used for retry/debug logging.
        debug_log: Callable used to emit retry events behind the debug flag.

    Returns:
        Stripped text content from the model response.
    """
    response = invoke_with_retry(
        lambda: llm.invoke(prompt),
        stage=stage,
        query_id=query_id,
        debug_log=debug_log,
    )
    content = getattr(response, "content", response)
    if isinstance(content, list):
        return "\n".join(str(block) for block in content)
    return str(content).strip()


def invoke_structured_or_text(
    llm: Any,
    prompt: str,
    *,
    schema: type[StructuredResponseT],
    fallback: Callable[[str], StructuredResponseT],
    stage: str,
    query_id: str,
    debug_log: Callable[..., None],
) -> StructuredResponseT:
    """Invoke a structured LLM response with a plain-text compatibility fallback.

    Args:
        llm: Chat model or compatible object with ``with_structured_output``.
        prompt: Prompt string to send to the model.
        schema: Pydantic schema the model is expected to return.
        fallback: Callable that builds the schema from plain text when structured
            output is unavailable or the structured request fails.
        stage: Pipeline stage name used for retry/debug logging.
        query_id: Query identifier used for retry/debug logging.
        debug_log: Callable used to emit retry/fallback events.

    Returns:
        Structured schema instance, either parsed from the model response or
        built by the fallback from plain text.
    """
    try:
        structured_llm = llm.with_structured_output(schema)
    except AttributeError:
        return fallback(
            invoke_text(llm, prompt, stage=stage, query_id=query_id, debug_log=debug_log)
        )

    try:
        response = invoke_with_retry(
            lambda: structured_llm.invoke(prompt),
            stage=stage,
            query_id=query_id,
            debug_log=debug_log,
        )
    except Exception as exc:
        debug_log(
            "structured_fallback query_id=%s stage=%s schema=%s error=%s",
            query_id,
            stage,
            schema.__name__,
            type(exc).__name__,
        )
        return fallback(
            invoke_text(llm, prompt, stage=stage, query_id=query_id, debug_log=debug_log)
        )

    if isinstance(response, schema):
        return response
    if isinstance(response, dict):
        return schema.model_validate(response)
    return schema.model_validate(getattr(response, "model_dump", lambda: response)())


__all__ = [
    "llm_error_status",
    "is_retryable_llm_error",
    "invoke_with_retry",
    "invoke_text",
    "invoke_structured_or_text",
]
