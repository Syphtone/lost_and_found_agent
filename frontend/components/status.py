"""Sidebar System Status component.

Renders real backend health, never fabricated values:
  * Backend/API   -> whether GET /health succeeded
  * Database      -> health.data['database']
  * LLM           -> health.data['llm_model']
  * MCP tools     -> derived honestly: MCP runs in-process inside the API, so it
                     is shown as "in-process (bundled)" and marked Verified only
                     once a real /report/lost trace containing an `mcp:` step has
                     been observed this session.

The status derivation is a pure function (`derive_statuses`) so it can be tested
without a running Streamlit server; `render_status` only draws the result.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

import streamlit as st

from frontend.api_client import ApiResult


@dataclass
class StatusRow:
    label: str
    state: str          # "ok" | "bad" | "unknown"
    detail: str = ""


def mcp_seen_in_trace(trace: Optional[list[dict[str, Any]]]) -> bool:
    """True if any trace event is an MCP tool call (step starts with 'mcp:')."""
    if not trace:
        return False
    return any(str(e.get("step", "")).startswith("mcp:") for e in trace)


def derive_statuses(health: ApiResult, mcp_verified: bool) -> list[StatusRow]:
    """Turn a /health result + MCP-verified flag into sidebar status rows."""
    rows: list[StatusRow] = []

    # Backend / API
    if health.ok:
        rows.append(StatusRow("Backend API", "ok", "reachable"))
    else:
        rows.append(StatusRow("Backend API", "bad", "unreachable"))

    # Database
    if health.ok and isinstance(health.data, dict):
        db_ok = bool(health.data.get("database"))
        rows.append(StatusRow("Database", "ok" if db_ok else "bad",
                              "connected" if db_ok else "unavailable"))
    else:
        rows.append(StatusRow("Database", "unknown", "unknown"))

    # MCP tools — honest derivation
    if not health.ok:
        rows.append(StatusRow("MCP tools", "unknown", "unknown"))
    elif mcp_verified:
        rows.append(StatusRow("MCP tools", "ok", "verified"))
    else:
        rows.append(StatusRow("MCP tools", "unknown", "in-process"))

    # LLM model (informational)
    if health.ok and isinstance(health.data, dict) and health.data.get("llm_model"):
        rows.append(StatusRow("LLM", "ok", str(health.data["llm_model"])))

    return rows


def _row_html(row: StatusRow) -> str:
    dot = {"ok": "dot-ok", "bad": "dot-bad"}.get(row.state, "dot-unknown")
    return (
        f'<div class="lf-status-row"><span class="status-dot {dot}"></span>'
        f'<span>{row.label}</span>'
        f'<span class="lf-status-sub">{row.detail}</span></div>'
    )


def render_status(health: ApiResult, mcp_verified: bool) -> None:
    """Render the System Status block in the sidebar."""
    st.markdown('<div class="lf-section-title">System Status</div>', unsafe_allow_html=True)
    rows = derive_statuses(health, mcp_verified)
    html = "".join(_row_html(r) for r in rows)
    st.markdown(html, unsafe_allow_html=True)
    if not health.ok:
        st.caption(f"⚠️ {health.error}")
    elif not mcp_verified:
        st.caption("MCP is bundled in-process; runs a live report to verify tool calls.")
