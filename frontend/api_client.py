"""HTTP client for the Lost & Found backend.

This is the ONLY module in the frontend that talks to the backend. It
centralizes:
  * the base URL (from the LOSTFOUND_API_URL env var),
  * request + timeout handling,
  * graceful error handling (never raises to the UI; returns a result object),
  * response parsing.

Every call returns an `ApiResult` dataclass: `ok` plus either `data` (parsed
JSON) or a user-friendly `error` string and `status` code. The UI branches on
`result.ok` and never sees a stack trace.

The frontend is a presentation layer only — no business logic, DB access,
embeddings, or agent reasoning happens here.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Optional

import requests

# Base URL is configurable; defaults to the local dev server.
BASE_URL = os.getenv("LOSTFOUND_API_URL", "http://127.0.0.1:8000").rstrip("/")

# The first /report/lost call loads the embedding + LLM models into memory, so
# allow a generous timeout for agent calls; health checks stay short.
AGENT_TIMEOUT = float(os.getenv("LOSTFOUND_AGENT_TIMEOUT", "180"))
QUICK_TIMEOUT = float(os.getenv("LOSTFOUND_QUICK_TIMEOUT", "5"))


@dataclass
class ApiResult:
    """Normalized result of an API call."""

    ok: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    status: Optional[int] = None

    @property
    def is_error(self) -> bool:
        return not self.ok


def _request(
    method: str,
    path: str,
    *,
    json: Optional[dict] = None,
    timeout: float = QUICK_TIMEOUT,
) -> ApiResult:
    """Perform an HTTP request and normalize the outcome to an ApiResult."""
    url = f"{BASE_URL}{path}"
    try:
        resp = requests.request(method, url, json=json, timeout=timeout)
    except requests.exceptions.ConnectTimeout:
        return ApiResult(False, error="The backend took too long to respond (connection timeout).")
    except requests.exceptions.ReadTimeout:
        return ApiResult(False, error="The agent is taking longer than expected. Please try again.")
    except requests.exceptions.ConnectionError:
        return ApiResult(
            False,
            error=f"Cannot reach the backend at {BASE_URL}. Is the API server running?",
        )
    except requests.exceptions.RequestException as exc:
        return ApiResult(False, error=f"Request failed: {exc}")

    # HTTP-level errors -> friendly message, don't leak internals.
    if resp.status_code >= 400:
        detail = _safe_detail(resp)
        return ApiResult(False, error=detail, status=resp.status_code)

    try:
        return ApiResult(True, data=resp.json(), status=resp.status_code)
    except ValueError:
        return ApiResult(False, error="Backend returned an unexpected (non-JSON) response.",
                         status=resp.status_code)


def _safe_detail(resp: requests.Response) -> str:
    """Extract a readable error message from a response without exposing internals."""
    try:
        body = resp.json()
        if isinstance(body, dict) and "detail" in body:
            return str(body["detail"])
    except ValueError:
        pass
    if resp.status_code == 404:
        return "Not found."
    if resp.status_code >= 500:
        return "The backend encountered an internal error. Please try again."
    return f"Request failed (HTTP {resp.status_code})."


# --------------------------------------------------------------------------
# Public API — one function per backend capability
# --------------------------------------------------------------------------
def check_health() -> ApiResult:
    """GET /health — API reachability + database status + LLM model."""
    return _request("GET", "/health", timeout=QUICK_TIMEOUT)


def report_lost(raw_text: str) -> ApiResult:
    """POST /report/lost — run the full agent pipeline on a lost-item report."""
    return _request("POST", "/report/lost", json={"raw_text": raw_text},
                    timeout=AGENT_TIMEOUT)


def report_found(
    raw_text: str,
    *,
    item_type: Optional[str] = None,
    color: Optional[str] = None,
    brand: Optional[str] = None,
    location: Optional[str] = None,
    reported_date: Optional[str] = None,
) -> ApiResult:
    """POST /report/found — persist a found-item report. Returns the created row."""
    payload = {
        "raw_text": raw_text,
        "item_type": item_type,
        "color": color,
        "brand": brand,
        "location": location,
        "reported_date": reported_date,
    }
    return _request("POST", "/report/found", json=payload, timeout=AGENT_TIMEOUT)


def get_item(item_id: int) -> ApiResult:
    """GET /items/{id} — fetch a single report by id."""
    return _request("GET", f"/items/{item_id}", timeout=QUICK_TIMEOUT)


def search(query_text: str) -> ApiResult:
    """Semantic search over found items.

    The backend exposes no dedicated search route, so this reuses the agent
    pipeline (/report/lost), which performs semantic retrieval over found
    items. Callers can read `data['candidates']` for the results.
    """
    return report_lost(query_text)
