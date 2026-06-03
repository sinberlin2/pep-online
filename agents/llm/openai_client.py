"""OpenAI helpers: web research (Responses API) + structured JSON (Chat API)."""
from __future__ import annotations

import json
import os
from typing import Any

from openai import OpenAI

from .env import load_project_env


def make_client(api_key: str | None = None) -> OpenAI:
    load_project_env()
    return OpenAI(api_key=api_key or os.environ["OPENAI_API_KEY"])


def _responses_text(response: Any) -> str:
    chunks: list[str] = []
    for item in getattr(response, "output", []) or []:
        if getattr(item, "type", None) != "message":
            continue
        for block in getattr(item, "content", []) or []:
            if getattr(block, "type", None) == "output_text":
                chunks.append(getattr(block, "text", "") or "")
    return "\n".join(chunks).strip()


def web_research(client: OpenAI, *, model: str, instructions: str) -> tuple[str, bool]:
    """
    Run OpenAI web search preview. Returns (research_text, success).
    """
    try:
        response = client.responses.create(
            model=model,
            tools=[{"type": "web_search_preview"}],
            input=instructions,
        )
        text = _responses_text(response)
        return (text if text else "(Web search returned no text.)", True)
    except Exception as exc:
        return (f"(Web search skipped: {exc})", False)


def chat_json(
    client: OpenAI,
    *,
    model: str,
    system: str,
    user: str,
    schema_name: str,
    schema: dict[str, Any],
) -> dict[str, Any]:
    completion = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": schema_name,
                "strict": True,
                "schema": schema,
            },
        },
    )
    raw = completion.choices[0].message.content
    if not raw:
        raise RuntimeError("Empty response from OpenAI")
    return json.loads(raw)
