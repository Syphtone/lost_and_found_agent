from typing import Literal
from langgraph.graph import StateGraph, END, START

from agent.state import LostFoundState
from agent.nodes import (
    intake_node,
    search_node,
    confidence_node,
    verify_node,
    ask_more_node,
    escalate_node
)


def route_after_intake(state: LostFoundState) -> str:
    """Route to verify directly if user is submitting a verification answer."""
    if state.get("verification_status") == "ANSWER_SUBMITTED":
        return "verify"
    return "search"


def route_by_confidence(state: LostFoundState) -> str:
    """Route depending on calculated confidence level."""
    level = state.get("confidence_level", "LOW")
    if level == "HIGH":
        return "verify"
    elif level == "MEDIUM":
        return "ask_more"
    else:
        return "escalate"


def build_graph():
    """Construct the LangGraph workflow."""
    workflow = StateGraph(LostFoundState)

    # Add Nodes
    workflow.add_node("intake", intake_node)
    workflow.add_node("search", search_node)
    workflow.add_node("confidence", confidence_node)
    workflow.add_node("verify", verify_node)
    workflow.add_node("ask_more", ask_more_node)
    workflow.add_node("escalate", escalate_node)

    # Add Edges
    workflow.add_edge(START, "intake")

    workflow.add_conditional_edges(
        "intake",
        route_after_intake,
        {
            "verify": "verify",
            "search": "search"
        }
    )

    workflow.add_edge("search", "confidence")

    workflow.add_conditional_edges(
        "confidence",
        route_by_confidence,
        {
            "verify": "verify",
            "ask_more": "ask_more",
            "escalate": "escalate"
        }
    )

    workflow.add_edge("verify", END)
    workflow.add_edge("ask_more", END)
    workflow.add_edge("escalate", END)

    return workflow.compile()


agent_graph = build_graph()


from observability.tracer import get_langfuse_callback

# ...

def run_agent(state: LostFoundState) -> LostFoundState:
    """Helper runner to execute the state graph."""
    handler = get_langfuse_callback(session_id=state.get("conversation_id"))
    config = {}
    if handler:
        config["callbacks"] = [handler]
        config["metadata"] = {"conversation_id": state.get("conversation_id")}

    result = agent_graph.invoke(state, config=config if config else None)
    return result
