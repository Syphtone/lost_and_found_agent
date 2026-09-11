import pytest
from fastapi.testclient import TestClient

from main import app
from tools.search_items import load_items, search_items, sanitize_item
from confidence.confidence import calculate_confidence, ConfidenceConfig
from agent.graph import run_agent
from agent.state import LostFoundState

client = TestClient(app)


def test_load_and_sanitize_items():
    """Test loading database items and sanitizing protected verification features."""
    items = load_items()
    assert len(items) > 0
    first = items[0]
    assert "verification_feature" in first

    sanitized = sanitize_item(first)
    assert "verification_feature" not in sanitized
    assert "id" in sanitized
    assert "category" in sanitized


def test_search_items():
    """Test searching items by criteria."""
    candidates = search_items({"category": "headphones"})
    assert len(candidates) > 0
    for item in candidates:
        assert "verification_feature" not in item


def test_confidence_calculation_high():
    """Test confidence scoring for high match."""
    extracted = {
        "category": "headphones",
        "brand": "Sony",
        "color": "black",
        "location": "library"
    }
    candidate = {
        "id": "item001",
        "category": "headphones",
        "brand": "Sony",
        "color": "black",
        "location": "library",
        "description": "Black Sony wireless noise-canceling headphones with carrying case"
    }
    score, level = calculate_confidence(extracted, candidate, "I lost my black Sony headphones near the library")
    assert score >= 0.85
    assert level == "HIGH"


def test_confidence_calculation_low():
    """Test confidence scoring for low match."""
    extracted = {
        "category": "dragon statue",
        "brand": "unknown",
        "color": "gold",
        "location": "space station"
    }
    candidate = {
        "id": "item001",
        "category": "headphones",
        "brand": "Sony",
        "color": "black",
        "location": "library",
        "description": "Black Sony wireless noise-canceling headphones with carrying case"
    }
    score, level = calculate_confidence(extracted, candidate, "I lost a gold dragon statue")
    assert score < 0.60
    assert level == "LOW"


def test_agent_flow_high_confidence_and_verification_pass():
    """Test full agent flow: High confidence prompt -> Verification question -> Verification success."""
    conv_id = "test_conv_high_pass"

    # Step 1: Initial query
    state1: LostFoundState = {
        "conversation_id": conv_id,
        "user_message": "I lost my black Sony headphones near the library"
    }
    res1 = run_agent(state1)
    assert res1.get("confidence_level") == "HIGH"
    assert res1.get("stage") == "verification_required"
    assert "distinctive feature" in res1.get("response", "").lower()
    assert res1.get("selected_match") is not None

    # Step 2: User provides correct distinctive feature ("small scratch on left earcup")
    state2: LostFoundState = {
        **res1,
        "user_message": "There is a small scratch on the left earcup"
    }
    res2 = run_agent(state2)
    assert res2.get("verification_status") == "VERIFIED"
    assert res2.get("stage") == "verified"
    assert res2.get("pickup") is not None
    assert res2.get("pickup", {}).get("status") == "Ready for pickup"


def test_agent_flow_high_confidence_and_verification_fail():
    """Test full agent flow: High confidence prompt -> Verification question -> Verification failure."""
    conv_id = "test_conv_high_fail"

    # Step 1: Initial query
    state1: LostFoundState = {
        "conversation_id": conv_id,
        "user_message": "I lost my black Sony headphones near the library"
    }
    res1 = run_agent(state1)
    assert res1.get("stage") == "verification_required"

    # Step 2: User provides wrong distinctive feature
    state2: LostFoundState = {
        **res1,
        "user_message": "It has a yellow cartoon sticker on the headband"
    }
    res2 = run_agent(state2)
    assert res2.get("verification_status") == "FAILED"
    assert res2.get("stage") == "escalated"
    assert "referred to lost & found staff" in res2.get("response", "").lower() or "escalated" in res2.get("response", "").lower()


def test_agent_flow_low_confidence():
    """Test agent flow for low confidence query."""
    state: LostFoundState = {
        "conversation_id": "test_conv_low",
        "user_message": "I lost a purple umbrella with green polkadots on mars"
    }
    res = run_agent(state)
    assert res.get("stage") == "escalated"
    assert "couldn't confidently identify" in res.get("response", "").lower() or "referred" in res.get("response", "").lower()


def test_fastapi_chat_endpoint():
    """Test POST /chat API endpoint using TestClient."""
    payload = {
        "conversation_id": "api_test_01",
        "message": "I lost my black Sony headphones near the library."
    }
    response = client.post("/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["conversation_id"] == "api_test_01"
    assert data["stage"] == "verification_required"
    assert data["match"] is not None
    assert data["match"]["category"] == "headphones"
    assert data["match"]["brand"] == "Sony"
    # Ensure verification_feature is NOT leaked in API response
    assert "verification_feature" not in data["match"]


def test_fastapi_health_endpoint():
    """Test GET /health API endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_langfuse_observability_safe_fallback():
    """Test that Langfuse observability functions cleanly without crashing when credentials are not configured."""
    from observability.tracer import is_langfuse_enabled, get_langfuse_callback, sanitize_trace_data

    # Without keys set, enabled should be False
    assert is_langfuse_enabled() is False

    # Callback handler should safely return None
    cb = get_langfuse_callback("test_session")
    assert cb is None

    # Sanitizer must strip forbidden keys like verification_feature
    unsafe_data = {
        "user_message": "test",
        "verification_feature": "secret scratch on ear",
        "nested": {"verification_feature": "hidden", "valid": "visible"}
    }
    clean_data = sanitize_trace_data(unsafe_data)
    assert "verification_feature" not in clean_data
    assert "verification_feature" not in clean_data["nested"]
    assert clean_data["nested"]["valid"] == "visible"

