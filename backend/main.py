import os
import uuid
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from agent.graph import run_agent
from agent.state import LostFoundState
from tools.search_items import load_items, sanitize_item

app = FastAPI(
    title="Lost & Found AI Backup MVP Backend",
    description="FastAPI + LangGraph backup backend agent for Lost & Found item recovery.",
    version="1.0.0"
)

# Enable CORS for React frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory store for active conversations
session_store: Dict[str, LostFoundState] = {}


class ChatRequest(BaseModel):
    conversation_id: Optional[str] = Field(None, description="Unique conversation/session identifier")
    session_id: Optional[str] = Field(None, description="Alternative session identifier name")
    message: str = Field(..., description="User prompt message")


class ChatResponse(BaseModel):
    conversation_id: str
    response: str
    stage: str
    match: Optional[Dict[str, Any]] = None
    confidence_level: Optional[str] = None
    confidence_score: Optional[float] = None
    pickup: Optional[Dict[str, Any]] = None
    pickup_request_id: Optional[str] = None
    escalation_id: Optional[str] = None


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "lost-found-ai-backend"}


@app.get("/items")
def get_public_items():
    """Return list of current found items in database (sanitized)."""
    raw = load_items()
    return [sanitize_item(item) for item in raw]


@app.post("/chat", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest = Body(...)):
    """Main conversational endpoint for Lost & Found AI."""
    # 1. Validation
    if not request.message or not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    conv_id = request.conversation_id or request.session_id or f"session_{uuid.uuid4().hex[:8]}"

    # 2. Retrieve existing state or initialize new
    existing_state = session_store.get(conv_id, {})
    
    current_state: LostFoundState = {
        **existing_state,
        "conversation_id": conv_id,
        "user_message": request.message.strip(),
    }

    # 3. Run LangGraph workflow
    try:
        updated_state = run_agent(current_state)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent workflow error: {str(e)}")

    # 4. Save state back to session store
    session_store[conv_id] = updated_state

    # 5. Format response matching frontend spec
    selected_match = updated_state.get("selected_match")
    if selected_match:
        sanitized_match = sanitize_item(selected_match)
    else:
        sanitized_match = None

    pickup_info = updated_state.get("pickup")
    pickup_id = f"PK-{uuid.uuid4().hex[:6].upper()}" if pickup_info else None
    escalation_id = f"ESC-{uuid.uuid4().hex[:6].upper()}" if updated_state.get("stage") == "escalated" else None

    return ChatResponse(
        conversation_id=conv_id,
        response=updated_state.get("response", "Thank you for reaching out."),
        stage=updated_state.get("stage", "understanding"),
        match=sanitized_match,
        confidence_level=updated_state.get("confidence_level"),
        confidence_score=updated_state.get("confidence_score"),
        pickup=pickup_info,
        pickup_request_id=pickup_id,
        escalation_id=escalation_id
    )


if __name__ == "__main__":
    import uvicorn
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host=host, port=port, reload=True)
