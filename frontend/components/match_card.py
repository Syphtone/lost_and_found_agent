"""Match card component.

Renders a retrieved candidate as a polished card and maps its confidence
`score` to one of three tiers, mirroring the backend guardrail thresholds
(default 0.75 / 0.45, but the caller can pass the exact values from the
`safety` trace event):

  * HIGH CONFIDENCE       score >= high
  * POSSIBLE MATCH        low <= score < high
  * LOW / NEEDS REVIEW    score <  low

An uncertain match is never styled as confirmed: the tier drives the badge,
border color, meter color, and the status label.

`confidence_tier` and `field` are pure helpers (testable). Values shown come
only from the candidate dict returned by the backend.
"""

from __future__ import annotations

from typing import Any, Optional

import streamlit as st

# Defaults mirror the backend (settings.confidence_high/low_threshold).
DEFAULT_HIGH = 0.75
DEFAULT_LOW = 0.45

_TIERS = {
    "high": {"label": "HIGH CONFIDENCE", "badge": "badge-high", "border": "conf-high",
             "fill": "fill-high", "status": "Match suggested"},
    "mid":  {"label": "POSSIBLE MATCH", "badge": "badge-mid", "border": "conf-mid",
             "fill": "fill-mid", "status": "Needs review"},
    "low":  {"label": "LOW CONFIDENCE / NEEDS REVIEW", "badge": "badge-low", "border": "conf-low",
             "fill": "fill-low", "status": "Not confirmed"},
}


def confidence_tier(score: float, high: float = DEFAULT_HIGH, low: float = DEFAULT_LOW) -> str:
    """Return 'high' | 'mid' | 'low' for a confidence score."""
    if score >= high:
        return "high"
    if score >= low:
        return "mid"
    return "low"


def field(cand: dict[str, Any], key: str, default: str = "—") -> str:
    """Safely read a candidate field for display."""
    value = cand.get(key)
    if value is None or value == "":
        return default
    return str(value)


def _pct(x: Optional[float]) -> int:
    try:
        return max(0, min(100, round(float(x) * 100)))
    except (TypeError, ValueError):
        return 0


def render_match_card(
    cand: dict[str, Any],
    *,
    high: float = DEFAULT_HIGH,
    low: float = DEFAULT_LOW,
    rank: Optional[int] = None,
) -> None:
    """Render a single candidate as a match card."""
    score = float(cand.get("score", 0.0))
    similarity = cand.get("similarity")
    tier = confidence_tier(score, high, low)
    t = _TIERS[tier]

    # date: prefer explicit reported_date, else created_at (trimmed).
    date_val = cand.get("reported_date") or cand.get("created_at")
    date_str = str(date_val)[:10] if date_val else "—"

    title = f"Match #{rank}" if rank else "Potential match"
    chips = (
        f'<span class="lf-chip">Category: <b>{field(cand, "item_type")}</b></span>'
        f'<span class="lf-chip">Location: <b>{field(cand, "location")}</b></span>'
        f'<span class="lf-chip">Date: <b>{date_str}</b></span>'
        f'<span class="lf-chip">Report ID: <b>{field(cand, "id")}</b></span>'
        f'<span class="lf-chip">Status: <b>{field(cand, "status")}</b></span>'
    )

    sim_line = f"Similarity {_pct(similarity)}%" if similarity is not None else "Similarity —"

    html = f"""
    <div class="lf-card lf-match {t['border']}">
      <div style="display:flex;align-items:center;gap:.6rem;margin-bottom:.4rem;">
        <span class="lf-badge {t['badge']}">{t['label']}</span>
        <span style="margin-left:auto;color:var(--lf-muted);font-size:.8rem;">{title}</span>
      </div>
      <div class="lf-match-desc">{field(cand, "raw_text")}</div>
      <div class="lf-meta">{chips}</div>
      <div class="lf-meter-track">
        <div class="lf-meter-fill {t['fill']}" style="width:{_pct(score)}%;"></div>
      </div>
      <div class="lf-meter-label">Confidence {_pct(score)}% · {sim_line} · {t['status']}</div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def render_matches(
    candidates: list[dict[str, Any]],
    *,
    high: float = DEFAULT_HIGH,
    low: float = DEFAULT_LOW,
    limit: Optional[int] = None,
) -> None:
    """Render a list of candidates as ranked match cards."""
    shown = candidates[:limit] if limit else candidates
    for i, cand in enumerate(shown, start=1):
        render_match_card(cand, high=high, low=low, rank=i)
