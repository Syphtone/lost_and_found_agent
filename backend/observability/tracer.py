import os
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("lost_found_langfuse")

_langfuse_client = None
_langfuse_callback_handler = None


def is_langfuse_enabled() -> bool:
    """Check if Langfuse credentials are properly set in environment."""
    public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
    secret_key = os.getenv("LANGFUSE_SECRET_KEY")
    return bool(public_key and secret_key and public_key.strip() and secret_key.strip())


def sanitize_trace_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ensure sensitive fields (e.g. verification_feature, api_keys, passwords)
    are strictly excluded from trace payloads before sending to Langfuse.
    """
    if not isinstance(data, dict):
        return {}

    clean = {}
    forbidden_keys = {"verification_feature", "secret", "password", "api_key", "key"}

    for k, v in data.items():
        if k.lower() in forbidden_keys:
            continue
        if isinstance(v, dict):
            clean[k] = sanitize_trace_data(v)
        elif isinstance(v, list):
            clean[k] = [sanitize_trace_data(item) if isinstance(item, dict) else v_elem for v_elem in v]
        else:
            clean[k] = v

    return clean


def get_langfuse_callback(session_id: Optional[str] = None) -> Optional[Any]:
    """
    Retrieve Langfuse CallbackHandler for LangChain/LangGraph if enabled.
    Returns None if Langfuse is not configured.
    """
    if not is_langfuse_enabled():
        return None

    try:
        from langfuse.callback import CallbackHandler
        
        pk = os.getenv("LANGFUSE_PUBLIC_KEY")
        sk = os.getenv("LANGFUSE_SECRET_KEY")
        host = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")

        handler = CallbackHandler(
            public_key=pk,
            secret_key=sk,
            host=host,
            session_id=session_id
        )
        return handler
    except Exception as e:
        logger.warning(f"Failed to initialize Langfuse CallbackHandler: {e}")
        return None


def get_langfuse_client() -> Optional[Any]:
    """Retrieve or initialize native Langfuse client instance."""
    global _langfuse_client
    if not is_langfuse_enabled():
        return None

    if _langfuse_client is not None:
        return _langfuse_client

    try:
        from langfuse import Langfuse
        pk = os.getenv("LANGFUSE_PUBLIC_KEY")
        sk = os.getenv("LANGFUSE_SECRET_KEY")
        host = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")

        _langfuse_client = Langfuse(
            public_key=pk,
            secret_key=sk,
            host=host
        )
        return _langfuse_client
    except Exception as e:
        logger.warning(f"Failed to initialize Langfuse client: {e}")
        return None


def trace_node_execution(
    node_name: str,
    state_input: Dict[str, Any],
    state_output: Dict[str, Any],
    trace_id: Optional[str] = None
) -> None:
    """
    Record an execution span for a LangGraph node.
    Sanitizes state_output to prevent leaking hidden fields.
    """
    if not is_langfuse_enabled():
        return

    try:
        client = get_langfuse_client()
        if not client:
            return

        clean_input = sanitize_trace_data(state_input)
        clean_output = sanitize_trace_data(state_output)

        # Create or update trace span
        span_name = f"Node: {node_name.upper()}"
        
        # Log event / span metadata
        client.trace(
            id=trace_id or clean_input.get("conversation_id"),
            name=f"LangGraph Workflow: {clean_input.get('conversation_id', 'Session')}",
            input={"user_message": clean_input.get("user_message"), "stage": clean_input.get("stage")},
            output={"stage": clean_output.get("stage"), "response": clean_output.get("response")},
            metadata={
                "node": node_name,
                "confidence_score": clean_output.get("confidence_score"),
                "confidence_level": clean_output.get("confidence_level"),
                "verification_status": clean_output.get("verification_status"),
                "candidate_count": len(clean_output.get("candidate_matches", [])) if clean_output.get("candidate_matches") else 0
            }
        )
        client.flush()
    except Exception as e:
        logger.warning(f"Langfuse tracing exception in node {node_name}: {e}")
