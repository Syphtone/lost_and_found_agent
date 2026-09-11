"""LangGraph node functions for the Lost & Found agent.

Pipeline:  intake -> retrieval -> matching -> safety -> respond

  * intake    : LLM extracts structured fields from the raw report.
  * retrieval : calls the REAL MCP tool `find_potential_matches` (in-process
                FastMCP client) -> pgvector candidates. This is genuine tool
                use, recorded in the trace.
  * matching  : computes per-candidate field agreement + human-readable
                evidence.
  * safety    : combines similarity + field agreement into an explicit
                confidence score and a routing decision (guardrail).
  * respond   : LLM writes the final answer grounded in the evidence.

Every node records observability events and returns its updated `trace` so the
accumulated trace survives LangGraph state merging.
"""

from __future__ import annotations

import json
from typing import Any

from app.agent.observability import record
from app.agent.state import AgentState, Candidate
from app.config import settings
from app.llm import chat_json, complete
from app.mcp.server import mcp

# Structured fields we try to extract / compare.
_FIELDS = ("item_type", "color", "brand", "location")


# --------------------------------------------------------------------------
# MCP helper
# --------------------------------------------------------------------------
async def _call_mcp(name: str, args: dict[str, Any]) -> Any:
    """Invoke an MCP tool in-process and unwrap its structured result."""
    result = await mcp.call_tool(name, args)
    sc = result.structured_content
    if isinstance(sc, dict) and set(sc.keys()) == {"result"}:
        return sc["result"]
    return sc


# --------------------------------------------------------------------------
# Nodes
# --------------------------------------------------------------------------
def intake_node(state: AgentState) -> dict[str, Any]:
    """Extract structured fields from the raw report using the LLM."""
    raw_text = state["raw_text"]
    system = (
        "You extract structured attributes from a lost/found item report. "
        "Return ONLY a JSON object with keys: item_type, color, brand, location, "
        "reported_date. Use null for anything not stated. reported_date must be "
        "an ISO date (YYYY-MM-DD) or null."
    )
    try:
        query = chat_json(
            [
                {"role": "system", "content": system},
                {"role": "user", "content": raw_text},
            ]
        )
    except Exception as exc:  # LLM/JSON failure must not crash the pipeline
        query = {f: None for f in _FIELDS}
        record(state, "intake", error=str(exc), fallback=True)
    else:
        query = {k: query.get(k) for k in ("item_type", "color", "brand", "location", "reported_date")}
        record(state, "intake", extracted={k: v for k, v in query.items() if v})
    return {"query": query, "trace": state["trace"]}


async def retrieval_node(state: AgentState) -> dict[str, Any]:
    """Retrieve candidate matches via the real MCP `find_potential_matches` tool."""
    result = await _call_mcp(
        "find_potential_matches",
        {"query_text": state["raw_text"], "top_k": settings.retrieval_top_k},
    )
    candidates = result.get("candidates", []) if isinstance(result, dict) else []
    target_kind = result.get("target_kind") if isinstance(result, dict) else None
    top_sim = candidates[0]["similarity"] if candidates else 0.0
    record(
        state,
        "mcp:find_potential_matches",
        target_kind=target_kind,
        candidates=candidates,
        top_similarity=top_sim,
    )
    return {"candidates": candidates, "target_kind": target_kind, "trace": state["trace"]}


def _field_agreement(query: dict[str, Any], cand: dict[str, Any]) -> tuple[float, list[str]]:
    """Fraction of stated query fields that agree with the candidate, + evidence."""
    evidence: list[str] = []
    comparable = 0
    matches = 0
    for field in _FIELDS:
        q = (query.get(field) or "").strip().lower()
        c = (cand.get(field) or "").strip().lower()
        if not q:
            continue
        comparable += 1
        if c and (q in c or c in q):
            matches += 1
            evidence.append(f"{field} matches ('{query.get(field)}')")
        elif c:
            evidence.append(f"{field} differs ('{query.get(field)}' vs '{cand.get(field)}')")
        else:
            evidence.append(f"{field} not recorded on candidate")
    agreement = matches / comparable if comparable else 0.0
    return agreement, evidence


def matching_node(state: AgentState) -> dict[str, Any]:
    """Score each candidate and attach evidence."""
    query = state.get("query", {})
    scored: list[Candidate] = []
    for cand in state.get("candidates", []):
        similarity = float(cand.get("similarity", 0.0))
        agreement, evidence = _field_agreement(query, cand)
        score = round(0.7 * similarity + 0.3 * agreement, 4)
        evidence.insert(0, f"semantic similarity {similarity:.2f}")
        enriched: Candidate = {**cand, "field_agreement": round(agreement, 4),
                               "score": score, "evidence": evidence}
        scored.append(enriched)
    scored.sort(key=lambda c: c["score"], reverse=True)
    record(state, "matching", scored=scored,
           top_score=(scored[0]["score"] if scored else 0.0))
    return {"candidates": scored, "trace": state["trace"]}


def safety_node(state: AgentState) -> dict[str, Any]:
    """Guardrail: pick the best candidate and decide matched/escalated/no_match."""
    candidates = state.get("candidates", [])
    best = candidates[0] if candidates else None
    confidence = float(best["score"]) if best else 0.0

    if best and confidence >= settings.confidence_high_threshold:
        decision = "matched"
    elif best and confidence >= settings.confidence_low_threshold:
        decision = "escalated"
    else:
        decision = "no_match"

    record(state, "safety", confidence=confidence, decision=decision,
           high=settings.confidence_high_threshold,
           low=settings.confidence_low_threshold)
    return {"best_candidate": best, "confidence": confidence,
            "decision": decision, "trace": state["trace"]}


def respond_node(state: AgentState) -> dict[str, Any]:
    """Produce the final user-facing message, grounded in evidence."""
    decision = state.get("decision", "no_match")
    best = state.get("best_candidate")
    confidence = state.get("confidence", 0.0)

    if decision == "matched" and best:
        context = (
            f"A likely match was found (confidence {confidence:.2f}).\n"
            f"Matched record: {best['raw_text']}\n"
            f"Evidence: {'; '.join(best.get('evidence', []))}"
        )
        instruction = ("Tell the user a likely match was found, summarize the matched "
                       "item, and cite the evidence briefly. Be concise and helpful.")
    elif decision == "escalated" and best:
        context = (
            f"Best candidate is ambiguous (confidence {confidence:.2f}).\n"
            f"Candidate: {best['raw_text']}\n"
            f"Evidence: {'; '.join(best.get('evidence', []))}"
        )
        instruction = ("Tell the user we found a possible but uncertain match and are "
                       "flagging it for human review. Mention the candidate briefly. Be concise.")
    else:
        context = f"No sufficiently confident match was found (confidence {confidence:.2f})."
        instruction = ("Tell the user no confident match was found yet, that their report "
                       "is recorded, and it will be reviewed. Be concise and reassuring.")

    try:
        response = complete(context, system=instruction, max_tokens=200)
    except Exception as exc:
        response = f"[{decision}] (LLM unavailable: {exc})"

    record(state, "respond", decision=decision, chars=len(response))
    return {"response": response, "trace": state["trace"]}
