"""Lightweight observability for the agent.

A single `record()` helper appends a structured `TraceEvent` to the agent state
AND logs it, so every run produces:
  * an in-state `trace` (returned in the API response for the demo), and
  * console logs for live inspection.

Nodes call `record(state, step, **detail)` on entry/exit, for retrieval hits,
MCP calls, confidence, and the routing decision — giving the demo-ready
visibility the brief requires without cluttering node logic.
"""

from __future__ import annotations

import logging
import time
from typing import Any

from app.agent.state import AgentState, TraceEvent

logger = logging.getLogger("lost_and_found.agent")
if not logger.handlers:
    _handler = logging.StreamHandler()
    _handler.setFormatter(logging.Formatter("%(asctime)s [%(name)s] %(message)s"))
    logger.addHandler(_handler)
    logger.setLevel(logging.INFO)


def record(state: AgentState, step: str, **detail: Any) -> TraceEvent:
    """Append a trace event to `state['trace']` and log it.

    `step` is a short label (e.g. "intake", "retrieval",
    "mcp:find_potential_matches", "router"). `detail` is arbitrary structured
    context for that step. Returns the created event.
    """
    event: TraceEvent = {"step": step, "detail": {"ts": time.time(), **detail}}
    state.setdefault("trace", []).append(event)
    logger.info("%s | %s", step, _summarize(detail))
    return event


def _summarize(detail: dict[str, Any]) -> str:
    """Compact one-line rendering of a detail dict for console logs."""
    parts = []
    for key, value in detail.items():
        if isinstance(value, (list, tuple)):
            parts.append(f"{key}={len(value)} items")
        elif isinstance(value, float):
            parts.append(f"{key}={value:.3f}")
        else:
            text = str(value)
            parts.append(f"{key}={text[:60]}")
    return ", ".join(parts) if parts else "(no detail)"


def new_trace() -> list[TraceEvent]:
    """Return a fresh, empty trace list for initializing agent state."""
    return []
