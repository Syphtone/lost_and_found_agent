from typing import TypedDict, List, Dict, Any, Optional


class LostFoundState(TypedDict, total=False):
    conversation_id: str
    user_message: str
    intent: Optional[str]
    category: Optional[str]
    brand: Optional[str]
    color: Optional[str]
    location: Optional[str]
    time: Optional[str]
    distinctive_feature: Optional[str]
    
    candidate_matches: List[Dict[str, Any]]
    selected_match: Optional[Dict[str, Any]]
    
    confidence_score: float
    confidence_level: Optional[str]  # "HIGH", "MEDIUM", "LOW"
    
    verification_status: Optional[str]  # "PENDING", "VERIFIED", "FAILED"
    next_action: Optional[str]  # "VERIFY", "ASK_MORE", "ESCALATE", "COMPLETE"
    
    stage: str
    response: str
    pickup: Optional[Dict[str, Any]]
