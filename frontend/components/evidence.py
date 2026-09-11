"""RAG / evidence panel component.

Renders an expandable "Why did the agent reach this conclusion?" section from
the REAL backend response. Per retrieved candidate it shows:
  * retrieved report id
  * the retrieved text (raw_text)
  * similarity score
  * field agreement
  * the backend's per-candidate evidence strings
  * source metadata (kind, status, created_at)

Nothing here is invented — every value comes from the candidate dicts returned
by /report/lost. If the backend returned no candidates, that fact is stated.
"""

from __future__ import annotations

from typing import Any

import streamlit as st


def _pct(x: Any) -> str:
    try:
        return f"{round(float(x) * 100)}%"
    except (TypeError, ValueError):
        return "—"


def render_evidence(candidates: list[dict[str, Any]], *, expanded: bool = False) -> None:
    """Render the evidence panel for the retrieved candidates."""
    with st.expander("🔍 Why did the agent reach this conclusion?", expanded=expanded):
        if not candidates:
            st.caption("The backend returned no retrieved candidates for this query.")
            return

        st.markdown(
            f'<div class="lf-evidence-meta">Retrieved {len(candidates)} candidate(s) '
            f'from the found-item corpus via pgvector semantic search.</div>',
            unsafe_allow_html=True,
        )

        for i, cand in enumerate(candidates, start=1):
            cid = cand.get("id", "—")
            similarity = _pct(cand.get("similarity"))
            agreement = _pct(cand.get("field_agreement"))
            raw_text = cand.get("raw_text", "")
            kind = cand.get("kind", "—")
            status = cand.get("status", "—")
            created = str(cand.get("created_at", "—"))[:19]

            st.markdown(
                f"""
                <div class="lf-card" style="margin-top:.6rem;">
                  <div class="lf-evidence-meta">
                    Report <b>#{cid}</b> · similarity <b>{similarity}</b> ·
                    field agreement <b>{agreement}</b>
                  </div>
                  <div class="lf-evidence-item" style="font-weight:600;">“{raw_text}”</div>
                  <div class="lf-evidence-meta" style="margin-top:.3rem;">
                    source: kind=<b>{kind}</b>, status=<b>{status}</b>, created=<b>{created}</b>
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            reasons = cand.get("evidence") or []
            if reasons:
                items = "".join(f'<div class="lf-evidence-item">• {r}</div>' for r in reasons)
                st.markdown(items, unsafe_allow_html=True)
