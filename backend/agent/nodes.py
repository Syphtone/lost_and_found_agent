import os
import re
import json
from typing import Dict, Any
from dotenv import load_dotenv

from agent.state import LostFoundState
from tools.search_items import search_items, get_raw_item_by_id
from confidence.confidence import calculate_confidence
from observability.tracer import trace_node_execution

load_dotenv()


def rule_based_extract(message: str) -> Dict[str, Any]:
    """Fallback natural language extractor when LLM key is not provided."""
    msg = message.lower()
    extracted = {
        "intent": "LOST_ITEM" if any(w in msg for w in ["lost", "misplaced", "missing", "left"]) else "GENERAL_QUERY",
        "category": None,
        "brand": None,
        "color": None,
        "location": None,
        "time": None,
        "distinctive_feature": None
    }

    # Categories
    categories = ["headphones", "airpods", "phone", "wallet", "backpack", "laptop", "water bottle", "bottle", "keys", "jacket"]
    for cat in categories:
        if cat in msg:
            extracted["category"] = cat
            break

    # Brands
    brands = ["sony", "apple", "fossil", "north face", "dell", "hydro flask", "samsung", "bose", "nike"]
    for b in brands:
        if b in msg:
            extracted["brand"] = b.capitalize() if b != "hydro flask" else "Hydro Flask"
            break

    # Colors
    colors = ["black", "white", "brown", "blue", "red", "silver", "green", "grey", "gray"]
    for c in colors:
        if c in msg:
            extracted["color"] = c
            break

    # Locations
    locations = ["library", "student center", "cafeteria", "engineering building", "gym", "lab", "quad"]
    for loc in locations:
        if loc in msg:
            extracted["location"] = loc
            break

    # Time extraction (e.g. 4 PM, 16:00, 2:30 pm, morning, afternoon)
    time_match = re.search(r'\b(\d{1,2}(?::\d{2})?\s*(?:am|pm)?|\d{1,2}\s*o\'?clock|morning|afternoon|evening)\b', msg)
    if time_match:
        extracted["time"] = time_match.group(1)

    return extracted


def llm_extract(message: str) -> Dict[str, Any]:
    """LLM structured extraction using Gemini / LangChain."""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return rule_based_extract(message)

    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        from langchain_core.messages import SystemMessage, HumanMessage

        llm = ChatGoogleGenerativeAI(
            model="gemini-pro",
            google_api_key=api_key,
            temperature=0
        )

        sys_prompt = """You are a lost and found item extraction specialist. Extract structured information from the user's message about a lost item.

Extract the following fields into a JSON object:
- "intent": "LOST_ITEM" if the user is reporting a lost item, "GENERAL_QUERY" otherwise
- "category": The type of item (e.g., "wallet", "phone", "headphones", "keys", "water bottle", "backpack", "laptop", "watch", "id card", "umbrella") or null if not mentioned
- "brand": The brand name if mentioned (e.g., "Apple", "Samsung", "Sony", "Fossil", "North Face", "Dell") or null
- "color": The color if mentioned (e.g., "black", "brown", "blue", "white", "silver", "red") or null
- "location": The location where the item was lost (e.g., "library", "classroom", "cafeteria", "gym", "parking area") or null
- "time": Time information if mentioned (e.g., "yesterday", "4 PM", "morning", "afternoon") or null
- "distinctive_feature": Any distinctive features mentioned (e.g., "leather", "with case", "scratched") or null

IMPORTANT: Return ONLY valid JSON, no markdown formatting, no additional text."""

        response = llm.invoke([
            SystemMessage(content=sys_prompt),
            HumanMessage(content=message)
        ])

        # Handle different response formats
        content = response.content
        if isinstance(content, list):
            # If response is a list, join the parts
            text = "".join([str(part) for part in content])
        else:
            text = str(content)

        text = text.strip()
        # Clean up any markdown formatting
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

        data = json.loads(text)
        
        # Ensure all expected keys exist
        return {
            "intent": data.get("intent", "LOST_ITEM"),
            "category": data.get("category"),
            "brand": data.get("brand"),
            "color": data.get("color"),
            "location": data.get("location"),
            "time": data.get("time"),
            "distinctive_feature": data.get("distinctive_feature")
        }
    except Exception as e:
        # Fallback if LLM fails
        print(f"LLM extraction failed: {e}, falling back to rule-based extraction")
        return rule_based_extract(message)


# ----------------------------------------------------
# LangGraph Nodes
# ----------------------------------------------------

def intake_node(state: LostFoundState) -> LostFoundState:
    """INTAKE Node: Extract details or handle verification turn."""
    input_state = dict(state)
    current_stage = state.get("stage", "understanding")
    message = state.get("user_message", "")

    # If we are waiting for verification from previous turn
    if current_stage == "verification_required" or state.get("verification_status") == "PENDING":
        state["distinctive_feature"] = message
        state["verification_status"] = "ANSWER_SUBMITTED"
        state["stage"] = "verifying"
        trace_node_execution("intake", input_state, dict(state))
        return state

    # Standard extraction
    extracted = llm_extract(message)
    state["intent"] = extracted.get("intent", "LOST_ITEM")
    state["category"] = state.get("category") or extracted.get("category")
    state["brand"] = state.get("brand") or extracted.get("brand")
    state["color"] = state.get("color") or extracted.get("color")
    state["location"] = state.get("location") or extracted.get("location")
    state["time"] = state.get("time") or extracted.get("time")
    state["stage"] = "searching"

    trace_node_execution("intake", input_state, dict(state))
    return state


def search_node(state: LostFoundState) -> LostFoundState:
    """SEARCH Node: Query item database."""
    input_state = dict(state)
    if state.get("verification_status") == "ANSWER_SUBMITTED":
        trace_node_execution("search", input_state, dict(state))
        return state

    extracted_criteria = {
        "category": state.get("category"),
        "brand": state.get("brand"),
        "color": state.get("color"),
        "location": state.get("location"),
        "time": state.get("time")
    }

    candidates = search_items(extracted_criteria)
    state["candidate_matches"] = candidates
    trace_node_execution("search", input_state, dict(state))
    return state


def confidence_node(state: LostFoundState) -> LostFoundState:
    """CONFIDENCE Node: Calculate confidence score for candidates."""
    input_state = dict(state)
    if state.get("verification_status") == "ANSWER_SUBMITTED":
        trace_node_execution("confidence", input_state, dict(state))
        return state

    candidates = state.get("candidate_matches", [])
    user_msg = state.get("user_message", "")

    if not candidates:
        state["confidence_score"] = 0.0
        state["confidence_level"] = "LOW"
        state["selected_match"] = None
        trace_node_execution("confidence", input_state, dict(state))
        return state

    extracted_criteria = {
        "category": state.get("category"),
        "brand": state.get("brand"),
        "color": state.get("color"),
        "location": state.get("location"),
        "time": state.get("time")
    }

    scored_candidates = []
    for item in candidates:
        score, level = calculate_confidence(extracted_criteria, item, user_msg)
        scored_candidates.append((score, level, item))

    # Sort descending by score
    scored_candidates.sort(key=lambda x: x[0], reverse=True)

    top_score, top_level, top_item = scored_candidates[0]

    state["confidence_score"] = top_score
    state["confidence_level"] = top_level
    state["selected_match"] = top_item
    trace_node_execution("confidence", input_state, dict(state))
    return state


def verify_node(state: LostFoundState) -> LostFoundState:
    """VERIFY Node: Prompt for feature or check user's feature answer."""
    input_state = dict(state)
    selected = state.get("selected_match")
    v_status = state.get("verification_status")

    if not selected:
        state["next_action"] = "ESCALATE"
        trace_node_execution("verify", input_state, dict(state))
        return state

    # If first time reaching HIGH confidence (asking user for distinctive feature)
    if v_status != "ANSWER_SUBMITTED":
        state["stage"] = "verification_required"
        state["verification_status"] = "PENDING"
        state["response"] = "I found a potential match. Can you describe a distinctive feature of your item?"
        state["next_action"] = "WAIT_FOR_USER"
        trace_node_execution("verify", input_state, dict(state))
        return state

    # User has provided an answer to the feature prompt
    user_feature = (state.get("distinctive_feature") or "").lower().strip()
    raw_item = get_raw_item_by_id(selected.get("id", ""))
    
    protected_feature = (raw_item.get("verification_feature") if raw_item else "").lower().strip()

    # Compare user answer with protected feature (never expose protected_feature!)
    words_user = set(user_feature.split())
    words_protected = set(protected_feature.split())
    
    # Remove stopwords
    stopwords = {"it", "has", "a", "the", "on", "in", "my", "is", "there"}
    words_user -= stopwords
    words_protected -= stopwords

    overlap = words_user.intersection(words_protected)
    
    # If key words overlap or sub-string matches
    if len(overlap) >= 1 or user_feature in protected_feature or protected_feature in user_feature:
        state["verification_status"] = "VERIFIED"
        state["stage"] = "verified"
        state["response"] = "Your item has been successfully verified. A pickup request has been created."
        state["pickup"] = {
            "location": f"{selected.get('location', 'Security Desk').title()} Desk",
            "status": "Ready for pickup",
            "item_id": selected.get("id")
        }
        state["next_action"] = "COMPLETE"
    else:
        state["verification_status"] = "FAILED"
        state["stage"] = "escalated"
        state["response"] = "Verification could not be confirmed. Your request has been referred to Lost & Found staff for manual review."
        state["next_action"] = "ESCALATE"

    trace_node_execution("verify", input_state, dict(state))
    return state


def ask_more_node(state: LostFoundState) -> LostFoundState:
    """MEDIUM Confidence Node: Ask for more information."""
    input_state = dict(state)
    state["stage"] = "need_more_information"
    state["response"] = "I found a possible match, but I need a few more details to be sure. Can you tell me the approximate time, location, or any specific color/brand details?"
    state["next_action"] = "ASK_MORE"
    trace_node_execution("ask_more", input_state, dict(state))
    return state


def escalate_node(state: LostFoundState) -> LostFoundState:
    """LOW Confidence / Failure Node: Refer to staff."""
    input_state = dict(state)
    state["stage"] = "escalated"
    state["response"] = "I couldn't confidently identify a matching item. Your case has been referred to Lost & Found staff."
    state["next_action"] = "ESCALATE"
    trace_node_execution("escalate", input_state, dict(state))
    return state
