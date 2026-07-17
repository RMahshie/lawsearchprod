"""Pure helpers for one-shot chat-model invocation and structured output.

These functions are intentionally free of any RAGService state. Callers pass a
``debug_log`` callable (typically ``RAGService._debug_log``) to surface
structured-output failures through the same logging gate as the pipeline.
"""

from __future__ import annotations

import json
from typing import Any, Callable, TypeVar

from langchain_core.messages import HumanMessage
from pydantic import BaseModel

from app.services.llm_factory import ModelSpec


StructuredResponseT = TypeVar("StructuredResponseT", bound=BaseModel)


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
        stage: Pipeline stage name retained for a consistent invocation API.
        query_id: Query identifier retained for a consistent invocation API.
        debug_log: Debug callable retained for a consistent invocation API.

    Returns:
        Stripped text content from the model response.
    """
    del stage, query_id, debug_log
    response = llm.invoke(prompt)
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
    stage: str,
    query_id: str,
    debug_log: Callable[..., None],
) -> StructuredResponseT:
    """Invoke a structured response using the provider-appropriate mechanism."""
    if model_spec.provider == "deepseek":
        try:
            json_llm = llm.bind(response_format={"type": "json_object"})
            response = json_llm.invoke(_with_json_instruction(payload, schema))
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
            raise

    try:
        structured_llm = llm.with_structured_output(schema)
        response = structured_llm.invoke(payload)
    except Exception as exc:
        debug_log(
            "structured_failed query_id=%s stage=%s schema=%s error=%s",
            query_id,
            stage,
            schema.__name__,
            type(exc).__name__,
        )
        raise

    return _validate_structured_response(response, schema)


__all__ = [
    "invoke_text",
    "invoke_structured",
]
