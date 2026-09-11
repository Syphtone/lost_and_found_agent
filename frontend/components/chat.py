"""Chat rendering + assistant-turn orchestration.

Renders the conversation and, for an assistant turn carrying an agent result,
assembles the full reply using the other components:

  1. the LLM `response` text
  2. confidence meter + decision (req 8)
  3. escalation banner (escalated) or no-match note + suggestions (req 9)
  4. match cards        (components.match_card)
  5. evidence panel     (components.evidence)
  6. agent trace panel  (components.agent_trace)

Message shape in session state:
    {"role": "user"|"assistant", "content": str, "result": <LostReportResponse|None>}

`extract_thresholds` and `decision_headline` are pure helpers (testable). All
displayed values come from the backend response; nothing is invented.
"""

from __future__ import annotations

from typing import Any, Optional

import streamlit as st

from frontend.components import agent_trace, evidence, match_card

_DECISION = {
    "matched":   ("MATCH SUGGESTED", "badge-high", "fill-high"),
    "escalated": ("HUMAN REVIEW REQUIRED", "badge-mid", "fill-mid"),
    "no_match":  ("NO CONFIDENT MATCH", "badge-low", "fill-low"),
}


def extract_thresholds(trace: list[dict[str, Any]]) -> tuple[float, float]:
    """Read the real high/low thresholds from the safety trace event.

    Falls back to the backend defaults (0.75 / 0.45) if not present.
    """
    for e in trace or []:
        if e.get("step") == "safety":
            d = e.get("detail", {}) or {}
            return (float(d.get("high", 0.75)), float(d.get("low", 0.45)))
    return (0.75, 0.45)


def decision_headline(decision: str) -> str:
    """User-facing headline for a decision."""
    return _DECISION.get(decision, ("UNKNOWN", "badge-low", "fill-low"))[0]


def _pct(x: Any) -> int:
    try:
        return max(0, min(100, round(float(x) * 100)))
    except (TypeError, ValueError):
        return 0


def _render_confidence(confidence: float, decision: str) -> None:
    headline, badge, fill = _DECISION.get(decision, ("UNKNOWN", "badge-low", "fill-low"))
    pct = _pct(confidence)
    st.markdown(
        f"""
        <div class="lf-card">
          <div style="display:flex;align-items:center;gap:.6rem;margin-bottom:.5rem;">
            <span class="lf-section-title" style="margin:0;">Confidence</span>
            <span class="lf-badge {badge}" style="margin-left:auto;">{headline}</span>
          </div>
          <div class="lf-meter-track">
            <div class="lf-meter-fill {fill}" style="width:{pct}%;"></div>
          </div>
          <div class="lf-meter-label">{pct}% confidence · decision: {decision}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_result(result: dict[str, Any]) -> None:
    """Render the full assistant result block from a LostReportResponse dict."""
    decision = result.get("decision", "no_match")
    confidence = float(result.get("confidence", 0.0))
    candidates = result.get("candidates", []) or []
    best = result.get("best_candidate")
    trace = result.get("trace", []) or []
    high, low = extract_thresholds(trace)

    # 1. LLM response text
    if result.get("response"):
        st.markdown(result["response"])

    # 2. confidence + decision
    _render_confidence(confidence, decision)

    # 3. escalation / no-match states
    if decision == "escalated":
        st.markdown(
            '<div class="lf-escalation">⚠️ This case requires review because the agent '
            'is not sufficiently confident in the match.</div>',
            unsafe_allow_html=True,
        )
    elif decision == "no_match":
        st.markdown(
            '<div class="lf-nomatch">No strong match found yet. You could:'
            '<ul style="margin:.4rem 0 0 1rem;">'
            '<li>add more detail (brand, color, exact location)</li>'
            '<li>check a different location or date</li>'
            '<li>submit a found-item report so others can match it</li></ul></div>',
            unsafe_allow_html=True,
        )

    # 4. match cards (only for matched / escalated; a no-match shows none as matches)
    if decision in ("matched", "escalated") and candidates:
        st.markdown('<div class="lf-section-title">Potential Matches</div>',
                    unsafe_allow_html=True)
        # For an escalated case, highlight only the best candidate to avoid
        # implying multiple confident matches.
        to_show = candidates if decision == "matched" else ([best] if best else [])
        match_card.render_matches([c for c in to_show if c], high=high, low=low, limit=5)

    # 5. evidence panel (always available when candidates were retrieved)
    evidence.render_evidence(candidates, expanded=False)

    # 6. agent trace
    agent_trace.render_trace(trace, expanded=False)


def render_history(messages: list[dict[str, Any]]) -> None:
    """Render the full chat history."""
    for msg in messages:
        with st.chat_message(msg["role"]):
            if msg.get("content"):
                st.markdown(msg["content"])
            if msg["role"] == "assistant" and msg.get("result"):
                render_result(msg["result"])
