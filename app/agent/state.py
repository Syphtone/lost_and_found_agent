"""Shared state for the LangGraph agent.

`AgentState` is the single object that flows through the graph:

    Intake -> Retrieval -> Matching -> Safety/Confidence -> Router

Each node reads the fields it needs and writes the fields it produces. Keeping
the schema in one place gives every node a typed contract and makes the run
inspectable for observability.

`total=False` means nodes may populate fields incrementally; early nodes need
not set fields that later nodes fill in.
"""

from __future__ import annotations

from typing import Any, Literal, Optional, TypedDict

# Routing decisions emitted by the router node / safety component.
Decision = Literal["matched", "escalated", "no_match"]


class StructuredQuery(TypedDict, total=False):
    """Fields extracted from the raw report by the intake node."""

    item_type: Optional[str]
    color: Optional[str]
    brand: Optional[str]
    location: Optional[str]
    reported_date: Optional[str]  # ISO date string if present


class Candidate(TypedDict, total=False):
    """A retrieved report plus its match analysis."""

    id: int
    kind: str
    raw_text: str
    item_type: Optional[str]
    color: Optional[str]
    brand: Optional[str]
    location: Optional[str]
    similarity: float          # cosine similarity in [0, 1] from retrieval
    field_agreement: float     # fraction of structured fields that agree
    score: float               # combined confidence for this candidate
    evidence: list[str]        # human-readable reasons this candidate matches


class TraceEvent(TypedDict):
    """One observability record: what a node/step did."""

    step: str                  # e.g. "intake", "retrieval", "mcp:find_potential_matches"
    detail: dict[str, Any]     # structured payload for that step


class AgentState(TypedDict, total=False):
    """The state passed between LangGraph nodes."""

    # ---- input ----
    raw_text: str
    kind: str                          # 'lost' (default use case) or 'found'

    # ---- intake output ----
    query: StructuredQuery

    # ---- retrieval output ----
    candidates: list[Candidate]
    target_kind: str                   # opposite kind that was searched

    # ---- matching + safety output ----
    best_candidate: Optional[Candidate]
    confidence: float                  # confidence of the best candidate [0, 1]
    decision: Decision                 # matched | escalated | no_match

    # ---- final response ----
    response: str

    # ---- observability ----
    trace: list[TraceEvent]
