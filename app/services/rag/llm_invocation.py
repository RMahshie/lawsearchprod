"""Pure helpers for invoking chat models with retry and structured-output fallback.

These functions are intentionally free of any RAGService state. Callers pass a
``debug_log`` callable (typically ``RAGService._debug_log``) to surface retry
and fallback events through the same logging gate as the rest of the pipeline.
"""

from __future__ import annotations

import json
import time
from typing import Any, Callable, TypeVar

from langchain_core.messages import HumanMessage
from pydantic import BaseModel

from app.services.llm_factory import ModelSpec


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


def _response_content(response: Any) -> str:
    """Normalize a model response to text content."""
    content = getattr(response, "content", response)
    if isinstance(content, list):
        return "\n".join(str(block) for block in content)
    return str(content).strip()


def _json_schema_instruction(schema: type[BaseModel]) -> str:
    """Render compact JSON-mode instructions for a Pydantic schema."""
    schema_json = json.dumps(schema.model_json_schema(), separators=(",", ":"))
    return (
        "Return only valid JSON matching this schema. Do not wrap it in markdown. "
        "Do not include explanatory text outside the JSON object.\n"
        f"Schema:\n{schema_json}"
    )


def _with_json_instruction(payload: Any, schema: type[BaseModel]) -> Any:
    """Append JSON schema instructions to string or chat-message payloads."""
    instruction = _json_schema_instruction(schema)
    if isinstance(payload, str):
        return f"{payload}\n\n{instruction}"
    if isinstance(payload, list):
        return [*payload, HumanMessage(content=instruction)]
    return payload


def _parse_json_object(text: str) -> Any:
    """Parse a JSON object, tolerating accidental fenced JSON."""
    stripped = text.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        stripped = "\n".join(lines).strip()
    return json.loads(stripped)


def _validate_structured_response(
    response: Any,
    schema: type[StructuredResponseT],
) -> StructuredResponseT:
    """Validate model output against a Pydantic structured-response schema."""
    if isinstance(response, schema):
        return response
    if isinstance(response, dict):
        return schema.model_validate(response)
    return schema.model_validate(getattr(response, "model_dump", lambda: response)())


def invoke_structured(
    llm: Any,
    payload: Any,
    *,
    schema: type[StructuredResponseT],
    model_spec: ModelSpec,
    fallback: Callable[[str], StructuredResponseT] | None = None,
    stage: str,
    query_id: str,
    debug_log: Callable[..., None],
) -> StructuredResponseT:
    """Invoke a structured response using the provider-appropriate mechanism."""
    if model_spec.provider == "deepseek":
        try:
            json_llm = llm.bind(response_format={"type": "json_object"})
            response = invoke_with_retry(
                lambda: json_llm.invoke(_with_json_instruction(payload, schema)),
                stage=stage,
                query_id=query_id,
                debug_log=debug_log,
            )
            return schema.model_validate(_parse_json_object(_response_content(response)))
        except Exception as exc:
            debug_log(
                "structured_json_failed query_id=%s stage=%s model=%s schema=%s error=%s",
                query_id,
                stage,
                model_spec.model,
                schema.__name__,
                type(exc).__name__,
            )
            if fallback is None:
                raise
            return fallback(
                invoke_text(llm, payload, stage=stage, query_id=query_id, debug_log=debug_log)
            )

    try:
        structured_llm = llm.with_structured_output(schema)
    except AttributeError:
        if fallback is None:
            raise
        return fallback(
            invoke_text(llm, payload, stage=stage, query_id=query_id, debug_log=debug_log)
        )

    try:
        response = invoke_with_retry(
            lambda: structured_llm.invoke(payload),
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
        if fallback is None:
            raise
        return fallback(
            invoke_text(llm, payload, stage=stage, query_id=query_id, debug_log=debug_log)
        )

    return _validate_structured_response(response, schema)


def invoke_structured_or_text(
    llm: Any,
    prompt: str,
    *,
    schema: type[StructuredResponseT],
    model_spec: ModelSpec,
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
    return invoke_structured(
        llm,
        prompt,
        schema=schema,
        model_spec=model_spec,
        fallback=fallback,
        stage=stage,
        query_id=query_id,
        debug_log=debug_log,
    )


__all__ = [
    "llm_error_status",
    "is_retryable_llm_error",
    "invoke_with_retry",
    "invoke_text",
    "invoke_structured",
    "invoke_structured_or_text",
]
