"""Anthropic (Claude) helpers: structured JSON + vision, mirroring openai_client.

Claude has no native JSON-schema response_format, so we force a single tool call
whose `input_schema` is our schema and read the tool input back as the result.
Both helpers share the signatures used by the OpenAI client so callers can swap
providers without changing their code.
"""
from __future__ import annotations

import base64
import mimetypes
import os
from pathlib import Path
from typing import Any

from anthropic import Anthropic

from .env import load_project_env

MAX_TOKENS = 4096


def make_client(api_key: str | None = None) -> Anthropic:
    load_project_env()
    return Anthropic(api_key=api_key or os.environ["ANTHROPIC_API_KEY"])


def _tool_result(message: Any, schema_name: str) -> dict[str, Any]:
    for block in getattr(message, "content", []) or []:
        if getattr(block, "type", None) == "tool_use" and getattr(block, "name", None) == schema_name:
            return dict(getattr(block, "input", {}) or {})
    raise RuntimeError("Claude did not return the expected structured tool call")


def _tool(schema_name: str, schema: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": schema_name,
        "description": "Return the result strictly matching this JSON schema.",
        "input_schema": schema,
    }


def chat_json(
    client: Anthropic,
    *,
    model: str,
    system: str,
    user: str,
    schema_name: str,
    schema: dict[str, Any],
) -> dict[str, Any]:
    message = client.messages.create(
        model=model,
        max_tokens=MAX_TOKENS,
        system=system,
        messages=[{"role": "user", "content": user}],
        tools=[_tool(schema_name, schema)],
        tool_choice={"type": "tool", "name": schema_name},
    )
    return _tool_result(message, schema_name)


def _image_block(path: Path) -> dict[str, Any]:
    mime = mimetypes.guess_type(path.name)[0] or "image/png"
    data = base64.b64encode(path.read_bytes()).decode("ascii")
    return {
        "type": "image",
        "source": {"type": "base64", "media_type": mime, "data": data},
    }


def vision_json(
    client: Anthropic,
    *,
    model: str,
    system: str,
    user: str,
    image_paths: list[Path],
    schema_name: str,
    schema: dict[str, Any],
    detail: str = "high",  # accepted for signature parity; unused by Claude
) -> dict[str, Any]:
    content: list[dict[str, Any]] = [{"type": "text", "text": user}]
    for path in image_paths:
        content.append(_image_block(path))
    message = client.messages.create(
        model=model,
        max_tokens=MAX_TOKENS,
        system=system,
        messages=[{"role": "user", "content": content}],
        tools=[_tool(schema_name, schema)],
        tool_choice={"type": "tool", "name": schema_name},
    )
    return _tool_result(message, schema_name)
