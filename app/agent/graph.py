"""LangGraph wiring for the Lost & Found agent.

Builds the pipeline as a StateGraph:

    intake -> retrieval -> matching -> safety -> respond -> END

and exposes a single async entrypoint, `run_agent`, that the FastAPI layer
calls. The graph is compiled once at import time and reused.
"""

from __future__ import annotations

from typing import Any

from langgraph.graph import END, StateGraph

from app.agent.nodes import (
    intake_node,
    matching_node,
    respond_node,
    retrieval_node,
    safety_node,
)
from app.agent.observability import new_trace, record
from app.agent.state import AgentState


def build_graph():
    """Construct and compile the agent StateGraph."""
    graph = StateGraph(AgentState)

    graph.add_node("intake", intake_node)
    graph.add_node("retrieval", retrieval_node)
    graph.add_node("matching", matching_node)
    graph.add_node("safety", safety_node)
    graph.add_node("respond", respond_node)

    graph.set_entry_point("intake")
    graph.add_edge("intake", "retrieval")
    graph.add_edge("retrieval", "matching")
    graph.add_edge("matching", "safety")
    graph.add_edge("safety", "respond")
    graph.add_edge("respond", END)

    return graph.compile()


# Compile once and reuse across requests.
compiled_graph = build_graph()


async def run_agent(raw_text: str, kind: str = "lost") -> AgentState:
    """Run the full agent pipeline for a report and return the final state.

    The returned state includes the structured query, ranked candidates, the
    best candidate, confidence, decision, final response, and the full
    observability trace.
    """
    initial: AgentState = {"raw_text": raw_text, "kind": kind, "trace": new_trace()}
    record(initial, "start", raw_text=raw_text, kind=kind)
    final_state: AgentState = await compiled_graph.ainvoke(initial)
    return final_state
