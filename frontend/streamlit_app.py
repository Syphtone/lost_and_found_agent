"""Lost & Found Agent — Streamlit frontend (presentation layer only).

Wires together the API client and components into a polished campus Lost & Found
app: a conversational chat interface, report forms, semantic search, live system
status, and real demo scenarios. All data comes from the existing backend over
HTTP; no business logic, DB access, embeddings, or agent reasoning live here.

Run from the project root:
    streamlit run frontend/streamlit_app.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# `streamlit run frontend/streamlit_app.py` puts frontend/ on sys.path, not the
# project root — insert the root so `frontend.*` package imports resolve.
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import streamlit as st  # noqa: E402

from frontend import api_client  # noqa: E402
from frontend.components import chat, forms, status  # noqa: E402

# --------------------------------------------------------------------------
# Page config + CSS
# --------------------------------------------------------------------------
st.set_page_config(page_title="Lost & Found Agent", page_icon="🎒", layout="wide")


def _inject_css() -> None:
    css_path = Path(__file__).with_name("styles") / "style.css"
    try:
        st.markdown(f"<style>{css_path.read_text(encoding='utf-8')}</style>",
                    unsafe_allow_html=True)
    except OSError:
        pass  # styling is non-critical


# Demo scenarios (call the REAL backend; not hard-coded responses).
DEMO_SCENARIOS = [
    ("🎧 High-confidence match", "I lost a black Sony headphone near the library yesterday"),
    ("🔌 Possible / semantic match", "I lost a silver laptop charger in one of the lecture halls"),
    ("🚲 No match", "I lost my red bicycle near the sports complex"),
    ("❓ Low-confidence escalation", "I think I lost some black electronics somewhere on campus"),
]


# --------------------------------------------------------------------------
# Session state
# --------------------------------------------------------------------------
def _init_state() -> None:
    st.session_state.setdefault("messages", [])
    st.session_state.setdefault("mcp_verified", False)
    st.session_state.setdefault("view", "Chat")


def _run_lost_query(text: str) -> None:
    """Send a lost-item query through the agent and append the turn to chat."""
    st.session_state.messages.append({"role": "user", "content": text})
    result = api_client.report_lost(text)
    if result.ok:
        data = result.data or {}
        # Honestly flag MCP as verified if the real trace shows an mcp: step.
        if status.mcp_seen_in_trace(data.get("trace")):
            st.session_state.mcp_verified = True
        st.session_state.messages.append(
            {"role": "assistant", "content": "", "result": data}
        )
    else:
        st.session_state.messages.append(
            {"role": "assistant",
             "content": f"⚠️ {result.error}", "result": None}
        )


# --------------------------------------------------------------------------
# Sidebar
# --------------------------------------------------------------------------
def _render_sidebar(health: api_client.ApiResult) -> None:
    with st.sidebar:
        st.markdown(
            '<div class="lf-brand"><span class="lf-logo">🎒</span> Lost &amp; Found</div>'
            '<div class="lf-tagline">Campus item recovery, powered by an AI agent</div>',
            unsafe_allow_html=True,
        )
        st.markdown("<hr/>", unsafe_allow_html=True)

        if st.button("💬 New Conversation", use_container_width=True):
            st.session_state.messages = []
            st.session_state.view = "Chat"

        st.markdown('<div class="lf-section-title">Actions</div>', unsafe_allow_html=True)
        for label, view in [("🔎 Search Items", "Chat"),
                            ("📢 Report Lost Item", "Report Lost"),
                            ("📦 Report Found Item", "Report Found")]:
            if st.button(label, use_container_width=True):
                st.session_state.view = view

        st.markdown("<hr/>", unsafe_allow_html=True)
        status.render_status(health, st.session_state.mcp_verified)


# --------------------------------------------------------------------------
# Views
# --------------------------------------------------------------------------
def _render_chat_view() -> None:
    st.markdown('<div class="lf-brand" style="font-size:1.5rem;margin-bottom:.2rem;">'
                'Find your lost item</div>', unsafe_allow_html=True)
    st.caption("Describe what you lost in plain language — the agent searches found reports "
               "and explains its reasoning.")

    if not st.session_state.messages:
        with st.expander("✨ Try a demo scenario", expanded=True):
            cols = st.columns(2)
            for i, (label, query) in enumerate(DEMO_SCENARIOS):
                if cols[i % 2].button(label, use_container_width=True, key=f"demo_{i}"):
                    with st.spinner("Running the matching agent…"):
                        _run_lost_query(query)
                    st.rerun()

    chat.render_history(st.session_state.messages)

    prompt = st.chat_input("e.g. I lost my black Sony headphones near the library yesterday")
    if prompt:
        with st.spinner("Running the matching agent…"):
            _run_lost_query(prompt)
        st.rerun()


def _render_report_lost_view() -> None:
    result = forms.render_lost_form()
    if result is not None:
        if result.ok:
            chat.render_result(result.data or {})
        else:
            st.error(result.error)


def _render_report_found_view() -> None:
    result = forms.render_found_form()
    if result is not None:
        if result.ok and isinstance(result.data, dict):
            row = result.data
            st.success(f"✅ Found report registered — Report ID **#{row.get('id')}**.")
            st.markdown(
                f'<div class="lf-card"><div class="lf-match-desc">{row.get("raw_text","")}</div>'
                f'<div class="lf-meta">'
                f'<span class="lf-chip">Category: <b>{row.get("item_type") or "—"}</b></span>'
                f'<span class="lf-chip">Color: <b>{row.get("color") or "—"}</b></span>'
                f'<span class="lf-chip">Location: <b>{row.get("location") or "—"}</b></span>'
                f'</div></div>',
                unsafe_allow_html=True,
            )
            st.caption("This item is now searchable. Lost-item reports will be matched against it.")
        else:
            st.error(result.error or "Could not register the found report.")


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------
def main() -> None:
    _inject_css()
    _init_state()
    health = api_client.check_health()
    _render_sidebar(health)

    if not health.ok:
        st.error(f"Backend unavailable: {health.error}")

    view = st.session_state.view
    if view == "Report Lost":
        _render_report_lost_view()
    elif view == "Report Found":
        _render_report_found_view()
    else:
        _render_chat_view()


if __name__ == "__main__":
    main()
