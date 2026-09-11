"""Report Lost / Report Found form components.

Fields map to the real backend schema (item_type, color, brand, location,
reported_date, plus free description):

  * Found form -> api_client.report_found(...) which persists the row and
    returns a real `id`.
  * Lost form  -> the backend's /report/lost accepts only `raw_text`, so the
    structured fields are composed into a natural-language description and run
    through the agent. Lost reports are NOT persisted, so there is no lost-item
    id to show — the form returns the agent's match result instead.

`compose_description` is a pure function (testable). Each render function shows
the form and, on submit, returns the api_client ApiResult to the caller (the
main app), which is responsible for rendering matches. Forms stay presentation
only.
"""

from __future__ import annotations

from typing import Any, Optional

import streamlit as st

from frontend import api_client
from frontend.api_client import ApiResult


def compose_description(
    *,
    description: str = "",
    item_type: Optional[str] = None,
    color: Optional[str] = None,
    brand: Optional[str] = None,
    location: Optional[str] = None,
    date: Optional[str] = None,
    kind: str = "lost",
) -> str:
    """Build a natural-language report from structured fields.

    Used for the lost form (backend takes free text) and to enrich the found
    report's raw_text. Only non-empty fields are included.
    """
    verb = "Lost" if kind == "lost" else "Found"
    descriptor = " ".join(p for p in [color, brand, item_type] if p) or "item"
    sentence = f"{verb} a {descriptor}".strip()
    if location:
        sentence += f" near {location}"
    if date:
        sentence += f" on {date}"
    sentence += "."
    if description:
        sentence += f" {description.strip()}"
    return sentence


def _clean(value: str) -> Optional[str]:
    value = (value or "").strip()
    return value or None


def render_found_form() -> Optional[ApiResult]:
    """Render the Report Found form. Returns the ApiResult on submit, else None."""
    st.markdown('<div class="lf-section-title">Report a Found Item</div>',
                unsafe_allow_html=True)
    with st.form("found_form", clear_on_submit=False):
        c1, c2 = st.columns(2)
        with c1:
            item_type = st.text_input("Item name / category", placeholder="e.g. headphones")
            color = st.text_input("Color", placeholder="e.g. black")
            location = st.text_input("Location found", placeholder="e.g. library")
        with c2:
            brand = st.text_input("Brand", placeholder="e.g. Sony")
            date = st.text_input("Date found (YYYY-MM-DD)", placeholder="optional")
            _ = st.empty()
        description = st.text_area("Additional details / description",
                                   placeholder="Describe the item you found…")
        submitted = st.form_submit_button("Submit found report", type="primary")

    if not submitted:
        return None

    raw_text = compose_description(
        description=description, item_type=item_type, color=color, brand=brand,
        location=location, date=date, kind="found",
    )
    with st.spinner("Registering found item…"):
        return api_client.report_found(
            raw_text,
            item_type=_clean(item_type), color=_clean(color), brand=_clean(brand),
            location=_clean(location), reported_date=_clean(date),
        )


def render_lost_form() -> Optional[ApiResult]:
    """Render the Report Lost form. Returns the agent ApiResult on submit, else None."""
    st.markdown('<div class="lf-section-title">Report a Lost Item</div>',
                unsafe_allow_html=True)
    st.caption("Submitting a lost item runs the matching agent against found reports.")
    with st.form("lost_form", clear_on_submit=False):
        c1, c2 = st.columns(2)
        with c1:
            item_type = st.text_input("Item name / category", placeholder="e.g. headphones")
            color = st.text_input("Color", placeholder="e.g. black")
            location = st.text_input("Location lost", placeholder="e.g. library")
        with c2:
            brand = st.text_input("Brand", placeholder="e.g. Sony")
            date = st.text_input("Date lost (YYYY-MM-DD)", placeholder="optional")
            _ = st.empty()
        description = st.text_area("Additional details / description",
                                   placeholder="Describe the item you lost…")
        submitted = st.form_submit_button("Find matches", type="primary")

    if not submitted:
        return None

    raw_text = compose_description(
        description=description, item_type=item_type, color=color, brand=brand,
        location=location, date=date, kind="lost",
    )
    with st.spinner("Running the matching agent…"):
        return api_client.report_lost(raw_text)
