"""Agent Activity / trace component.

Turns the backend's real observability trace into a readable step timeline:

    ✓ Intake Agent
    ✓ Retrieval (MCP: find_potential_matches)
    ✓ Matching Agent
    ✓ Safety / Confidence Check
    ✓ Final Response

Only steps actually present in the trace are shown — nothing is fabricated.
Per-step durations are derived honestly from consecutive `ts` timestamps in the
trace events (the backend records a `ts` on every event).

`step_label`, `summarize_detail`, and `compute_durations` are pure helpers and
are unit-tested without a running Streamlit server.
"""

from __future__ import annotations

from typing import Any, Optional

import streamlit as st

# Friendly labels for known trace steps. MCP steps are handled dynamically.
_LABELS = {
    "start": "Request received",
    "intake": "Intake Agent (field extraction)",
    "matching": "Matching Agent",
    "safety": "Safety / Confidence Check",
    "respond": "Final Response",
}


def step_label(step: str) -> str:
    """Human-friendly label for a trace step name."""
    if step.startswith("mcp:"):
        tool = step.split(":", 1)[1]
        return f"Retrieval — MCP: {tool}"
    return _LABELS.get(step, step)


def summarize_detail(step: str, detail: dict[str, Any]) -> str:
    """One-line, honest summary of a step's detail payload."""
    if step == "intake":
        extracted = detail.get("extracted")
        if extracted:
            return ", ".join(f"{k}={v}" for k, v in extracted.items())
        if detail.get("fallback"):
            return "extraction failed — used fallback"
        return "no fields extracted"
    if step.startswith("mcp:"):
        n = len(detail.get("candidates", []) or [])
        return f"{n} candidate(s), top similarity {detail.get('top_similarity', 0):.2f}"
    if step == "matching":
        return f"top score {detail.get('top_score', 0):.2f}"
    if step == "safety":
        return f"confidence {detail.get('confidence', 0):.2f} → {detail.get('decision', '—')}"
    if step == "respond":
        return f"{detail.get('chars', 0)} chars, decision {detail.get('decision', '—')}"
    if step == "start":
        return f"kind={detail.get('kind', '—')}"
    return ""


def compute_durations(trace: list[dict[str, Any]]) -> list[Optional[float]]:
    """Per-step duration (seconds) from consecutive `ts` values.

    Duration of step i is ts[i+1] - ts[i]; the last step has no successor, so
    its duration is None. Returns None entries when timestamps are missing.
    """
    ts = []
    for e in trace:
        detail = e.get("detail", {}) or {}
        ts.append(detail.get("ts"))

    durations: list[Optional[float]] = []
    for i in range(len(trace)):
        if i + 1 < len(trace) and isinstance(ts[i], (int, float)) and isinstance(ts[i + 1], (int, float)):
            durations.append(max(0.0, ts[i + 1] - ts[i]))
        else:
            durations.append(None)
    return durations


def render_trace(trace: list[dict[str, Any]], *, expanded: bool = False) -> None:
    """Render the Agent Activity panel from the backend trace."""
    with st.expander("⚙️ Agent Activity", expanded=expanded):
        if not trace:
            st.caption("No trace information was returned for this request.")
            return

        durations = compute_durations(trace)
        rows = []
        for e, dur in zip(trace, durations):
            step = str(e.get("step", ""))
            label = step_label(step)
            summary = summarize_detail(step, e.get("detail", {}) or {})
            dur_str = f"{dur*1000:.0f} ms" if isinstance(dur, float) else ""
            summary_html = f'<span style="color:var(--lf-muted);">— {summary}</span>' if summary else ""
            rows.append(
                f'<div class="lf-step"><span class="tick">✓</span>'
                f'<span>{label}</span> {summary_html}'
                f'<span class="dur">{dur_str}</span></div>'
            )
        st.markdown("".join(rows), unsafe_allow_html=True)
