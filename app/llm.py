"""LLM interface for the agent.

This module is the ONLY place that knows how the language model is reached.
Everything else (LangGraph nodes, MCP tools) depends solely on the functions
exposed here — `chat`, `complete`, and `chat_json` — so the model backend can
change without touching agent, tool, or storage logic.

Backend: a local Unsloth-supported model (default `llama3.1:latest`) served via
Ollama's OpenAI-compatible endpoint. Because the interface is OpenAI-style,
this can later point at a true Unsloth runtime or any OpenAI-compatible server
by changing only `.env` (LLM_BASE_URL / LLM_MODEL) — no code change here.
"""

from __future__ import annotations

import json
from functools import lru_cache
from typing import Any

from openai import OpenAI

from app.config import settings

# A chat message is a plain dict: {"role": "system"|"user"|"assistant", "content": str}
Message = dict[str, str]


@lru_cache(maxsize=1)
def _get_client() -> OpenAI:
    """Create the OpenAI-compatible client once per process.

    Points at the local Ollama endpoint. The api_key is a placeholder Ollama
    ignores; no credential ever leaves the machine.
    """
    return OpenAI(base_url=settings.llm_base_url, api_key=settings.llm_api_key)


def chat(
    messages: list[Message],
    *,
    temperature: float | None = None,
    max_tokens: int | None = None,
) -> str:
    """Send a list of chat messages and return the assistant's text reply."""
    response = _get_client().chat.completions.create(
        model=settings.llm_model,
        messages=messages,
        temperature=settings.llm_temperature if temperature is None else temperature,
        max_tokens=settings.llm_max_tokens if max_tokens is None else max_tokens,
    )
    return (response.choices[0].message.content or "").strip()


def complete(
    prompt: str,
    *,
    system: str | None = None,
    temperature: float | None = None,
    max_tokens: int | None = None,
) -> str:
    """Convenience wrapper: a single user prompt (+ optional system) -> text."""
    messages: list[Message] = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    return chat(messages, temperature=temperature, max_tokens=max_tokens)


def chat_json(
    messages: list[Message],
    *,
    temperature: float | None = None,
    max_tokens: int | None = None,
) -> dict[str, Any]:
    """Ask the model for JSON and parse it into a dict.

    Requests JSON mode (supported by Ollama's OpenAI-compatible API). Falls back
    to extracting the first {...} block if the model wraps its output. Raises
    ValueError if no valid JSON can be parsed, so callers can handle it.
    """
    response = _get_client().chat.completions.create(
        model=settings.llm_model,
        messages=messages,
        temperature=settings.llm_temperature if temperature is None else temperature,
        max_tokens=settings.llm_max_tokens if max_tokens is None else max_tokens,
        response_format={"type": "json_object"},
    )
    text = (response.choices[0].message.content or "").strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        if start != -1 and end != -1 and end > start:
            return json.loads(text[start : end + 1])
        raise ValueError(f"LLM did not return valid JSON: {text!r}")
