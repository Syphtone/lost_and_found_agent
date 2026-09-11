"""FastAPI application — the HTTP surface for the Lost & Found Agent.

Endpoints:
  * GET  /health              -> liveness + DB reachability
  * POST /report/lost         -> run the full agent on a lost-item report
  * POST /report/found        -> register a found-item report (for seeding)
  * GET  /items/{item_id}     -> fetch a single report

The lost-report endpoint returns the agent's decision, confidence, matched
record, evidence, final response, and the full observability trace, so the
whole run is inspectable from a single call.

Run:  uvicorn app.main:app --host 127.0.0.1 --port 8000
"""

from __future__ import annotations

from typing import Any, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.agent.graph import run_agent
from app.config import settings
from app.db import healthcheck
from app.services import items as items_service

app = FastAPI(title="Lost & Found Agent", version="0.1.0")


# ---- request / response models ----
class LostReportRequest(BaseModel):
    raw_text: str = Field(..., description="Free-text description of the lost item")


class FoundReportRequest(BaseModel):
    raw_text: str = Field(..., description="Free-text description of the found item")
    item_type: Optional[str] = None
    color: Optional[str] = None
    brand: Optional[str] = None
    location: Optional[str] = None
    reported_date: Optional[str] = None


class LostReportResponse(BaseModel):
    decision: str
    confidence: float
    response: str
    query: dict[str, Any]
    best_candidate: Optional[dict[str, Any]] = None
    candidates: list[dict[str, Any]] = []
    trace: list[dict[str, Any]] = []


# ---- endpoints ----
@app.get("/health")
def health() -> dict[str, Any]:
    """Liveness + database reachability."""
    return {"status": "ok", "database": healthcheck(), "llm_model": settings.llm_model}


@app.post("/report/lost", response_model=LostReportResponse)
async def report_lost(req: LostReportRequest) -> LostReportResponse:
    """Run the full agent pipeline on a lost-item report."""
    state = await run_agent(req.raw_text, kind="lost")
    return LostReportResponse(
        decision=state.get("decision", "no_match"),
        confidence=state.get("confidence", 0.0),
        response=state.get("response", ""),
        query=state.get("query", {}),
        best_candidate=state.get("best_candidate"),
        candidates=state.get("candidates", []),
        trace=state.get("trace", []),
    )


@app.post("/report/found")
def report_found(req: FoundReportRequest) -> dict[str, Any]:
    """Register a found-item report (used to seed the corpus)."""
    return items_service.create_report(
        "found",
        req.raw_text,
        item_type=req.item_type,
        color=req.color,
        brand=req.brand,
        location=req.location,
        reported_date=req.reported_date,
    )


@app.get("/items/{item_id}")
def get_item(item_id: int) -> dict[str, Any]:
    """Fetch a single report by id."""
    item = items_service.get_item(item_id)
    if item is None:
        raise HTTPException(status_code=404, detail=f"item {item_id} not found")
    return item
